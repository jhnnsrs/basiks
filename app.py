"""The standard library: small, general actions over mikro data

Measuring, thresholding, projecting, resizing, cutting, generating test data and
merging tables: the everyday steps a workflow strings together between the
specialised apps.

Every array action takes an ``ArrayLens``, a selection over a dataset, and reads
only what it selects through ``lens.data``. Every array it makes is uploaded as a
new dataset whose ``derived_from`` edge points back into the lens it came from, so
the result lands in the input's coordinate space, and the action hands back that
dataset's whole lens. Cutting is not copying: a frame, a slice or a crop is a lens
over the same dataset, and nothing is uploaded for it.

Run:  arkitekt run dev
"""

from enum import Enum
from typing import Annotated, Generator, Iterator, Sequence

import cv2
import numpy as np
import pandas as pd
import xarray as xr
from scipy import ndimage
from skimage import data as skdata
from skimage import transform
from sklearn.cluster import DBSCAN

from arkitekt import (
    App,
    DescriptorOperator,
    Description,
    Provides,
    Requires,
    Task,
    run,
)
from mikro import Mikro, dataset_arrays, mikro_service
from mikro.api.schema import (
    Annotation,
    AnnotationKind,
    Blending,
    BootstrapLayerKind,
    ArrayDatasetFilter,
    ArrayLens,
    AxisInput,
    AxisType,
    ColorMap,
    ColumnInput,
    CoordinateAnchorInput,
    CoordinateSystemDerivedFromInput,
    DerivedFromInput,
    Folder,
    IdentityTransformInput,
    OffsetPaginationInput,
    ProjectionMode,
    Scene,
    ScenePolicyInput,
    SliceInput,
    TableDataset,
    ValueRelation,
)
from mikro.arkitekt.specs import (
    N_CHANNELS,
    N_SPACE_AXES,
    N_TIME_AXES,
    N_TIMEPOINTS,
    VALUE_KIND,
    Timeseries,
    Volume,
)


__version__ = "0.1.0"

app = App(
    "basiks",
    __version__,
    description="The standard library: measuring, thresholding, projecting, resizing, cutting and test data",
    author="jhnnsrs",
)
app.service(mikro_service)

LEVELS = 4
"""Pyramid levels for every dataset this app uploads, the base included."""

PAGE = 50
"""How many datasets one request of a folder listing asks for."""

# Written out as plain assignments of one Annotated each: a spec alias nested inside
# another Annotated is not flattened. An argument check is a Requires (the UI offers
# only lenses that fit, and the run refuses one that does not), a return check a
# Provides.
Planes = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.GTE, value=2),
]
"""Anything with at least two space axes: thresholded plane by plane."""

LabelPlane = Annotated[
    ArrayLens,
    Requires(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
    Requires(key=N_CHANNELS, operator=DescriptorOperator.LTE, value=1),
    Requires(key=N_TIMEPOINTS, operator=DescriptorOperator.LTE, value=1),
    Requires(key=VALUE_KIND, operator=DescriptorOperator.EQUALS, value="categorical"),
]
"""A single plane of object ids."""

Mask = Annotated[
    ArrayLens,
    Provides(key=VALUE_KIND, operator=DescriptorOperator.EQUALS, value="categorical"),
]
"""A binary mask. The value kind is provenance: the derivation edge says it."""

Projection = Annotated[
    ArrayLens,
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=2),
]
"""A volume flattened along its first space axis."""

Frame = Annotated[
    ArrayLens,
    Provides(key=N_TIME_AXES, operator=DescriptorOperator.GTE, value=1),
]
"""A run of timepoints cut out of a timeseries. The time axis survives the cut."""

Slab = Annotated[
    ArrayLens,
    Provides(key=N_SPACE_AXES, operator=DescriptorOperator.EQUALS, value=3),
]
"""A run of planes cut out of a volume. The cut keeps all three space axes."""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _channel_axis(axes: Sequence[AxisInput | str]) -> str | None:
    """The name of the first CHANNEL axis in `axes`, if there is one. A bare name is
    typed by the naming convention, as the server types it."""
    for axis in axes:
        if isinstance(axis, str):
            if axis in ("c", "channel"):
                return axis
        elif AxisType(axis.type) == AxisType.CHANNEL:
            return axis.name
    return None


def _upload(
    mikro: Mikro,
    array: xr.DataArray,
    name: str,
    axes: Sequence[AxisInput | str],
    derived_from: list[DerivedFromInput] | None = None,
    intensity: bool = True,
    rgb: bool = False,
) -> ArrayLens:
    """Upload `array` as a dataset with a pyramid, stage it, and return its whole lens.

    `intensity` decides whether a histogram anchor is computed, one per channel, and
    how the pyramid is reduced. Labels and masks get no anchor, because a histogram
    over object ids would offer contrast limits for values that are not intensities. `rgb` stages a packed RGB
    photo as one RGB layer: its three channels are one picture, not three to toggle.
    """
    # An object id or a mask value averaged or maxed with its neighbours is a value
    # that was never there, so the coarser levels of a non-intensity dataset are
    # picked, not pooled. The server refuses anything else for categorical data.
    data, scales = dataset_arrays(array, levels=LEVELS, method="max" if intensity else "nearest")
    anchors: list[CoordinateAnchorInput] = []
    if intensity:
        anchors = CoordinateAnchorInput.histogram_anchors(
            array, axis=_channel_axis(axes) or "c"
        )

    dataset = mikro.create_array_dataset(
        data=data,
        scales=scales,
        name=name,
        axes=axes,
        anchors=anchors,
        derived_from=derived_from or [],
    )
    policy = ScenePolicyInput(kind=BootstrapLayerKind.RGB) if rgb else None
    dataset.stage(name="Default", policy=policy)
    return dataset.lens()


def _title(mikro: Mikro, image: ArrayLens) -> str:
    """What to call `image` in the name of what is made from it: its own name, else
    its dataset's."""
    if image.name:
        return image.name
    return mikro.get_array_dataset(image.dataset.id).name




def _planes(
    array: xr.DataArray, plane_axes: tuple[str, str]
) -> Iterator[tuple[dict[str, int], np.ndarray]]:
    """Every 2D plane of `array` over `plane_axes`, with the index it sits at."""
    others = [str(d) for d in array.dims if d not in plane_axes]
    for index in np.ndindex(*(array.sizes[d] for d in others)):
        at = dict(zip(others, index))
        yield at, np.asarray(array.isel(at).transpose(*plane_axes).data)


def _to_uint8(plane: np.ndarray) -> np.ndarray:
    """Stretch a plane to 0..255. A flat plane becomes all zeros."""
    plane = plane.astype(np.float64)
    low, high = float(plane.min()), float(plane.max())
    if high <= low:
        return np.zeros(plane.shape, dtype=np.uint8)
    return ((plane - low) / (high - low) * 255).astype(np.uint8)


def _binarize_by_plane(
    image: ArrayLens, task: Task, binarize
) -> tuple[xr.DataArray, list[str]]:
    """Run `binarize` over every plane of the last two space axes of `image`."""
    data = image.data.compute()
    space = image.axes_of_type(AxisType.SPACE)
    plane_axes = (space[-2], space[-1])
    out = xr.DataArray(np.zeros(data.shape, dtype=np.uint8), dims=data.dims)

    planes = list(_planes(data, plane_axes))
    for i, (at, plane) in enumerate(planes):
        out[at] = xr.DataArray(binarize(plane), dims=plane_axes)
        task.progress(int(90 * (i + 1) / len(planes)), f"Plane {i + 1} of {len(planes)}")
    return out, [str(d) for d in data.dims]


def _publish_mask(
    mikro: Mikro, image: ArrayLens, mask: xr.DataArray, dims: list[str], name: str
) -> ArrayLens:
    """Upload a mask computed on the grid of `image`, as a categorical derivation of it."""
    return _upload(
        mikro,
        mask,
        name,
        image.carried_axes(dims),
        derived_from=[image.derive_identity(value_relation=ValueRelation.CATEGORIZED)],
        intensity=False,
    )


# --------------------------------------------------------------------------- #
# Measuring
# --------------------------------------------------------------------------- #
@app.action(name="Measure Max", collections=["quantitative"])
def measure_max(
    image: Annotated[ArrayLens, Description("The image to measure")],
) -> float:
    """Measures the maximum value of an image."""
    return float(image.data.max().compute())


@app.action(name="Measure Sum", collections=["quantitative"])
def measure_sum(
    image: Annotated[ArrayLens, Description("The image to measure")],
) -> float:
    """Measures the sum of all values of an image."""
    return float(image.data.sum().compute())


@app.action(name="Measure Fraction", collections=["quantitative"])
def measure_fraction(
    image: Annotated[ArrayLens, Description("The image to measure")],
    target: Annotated[float, Description("The value to count")] = 1,
) -> float:
    """Measures the fraction of the image (0-1) that has exactly this value."""
    data = image.data
    return float((data == target).sum().compute()) / max(int(data.size), 1)


@app.action(name="Measure Basic Metrics", collections=["quantitative"])
def measure_basics(
    image: Annotated[ArrayLens, Description("The image to measure")],
) -> tuple[float, float, float]:
    """Measures the maximum, the mean and the minimum of an image.

    Returns:
        float: The max
        float: The mean
        float: The min
    """
    x = image.data.compute()
    return float(x.max()), float(x.mean()), float(x.min())


# --------------------------------------------------------------------------- #
# Collections
# --------------------------------------------------------------------------- #
@app.action(name="Iterate Images", collections=["collection"])
def iterate_images(
    folder: Annotated[Folder, Description("The folder to list")],
    *,
    mikro: Mikro,
) -> Generator[ArrayLens, None, None]:
    """Yields the whole lens of every array dataset filed in a folder."""
    offset = 0
    while True:
        page = mikro.get_array_datasets(
            filters=ArrayDatasetFilter(folder=folder.id),
            pagination=OffsetPaginationInput(offset=offset, limit=PAGE),
        )
        for dataset in page:
            yield dataset.lens()
        if len(page) < PAGE:
            return
        offset += PAGE


@app.action(name="Merge Tables", collections=["organization"])
def merge_tables(
    tables: Annotated[list[TableDataset], Description("The tables to merge")],
    *,
    mikro: Mikro,
) -> TableDataset:
    """Stacks the rows of several tables into one.

    Each row records the table it came from in an ``origin`` column. A column keeps
    the declaration (axis type or role, unit, long name) it had in the first table
    that has it.
    """
    if not tables:
        raise ValueError("Pass at least one table to merge")

    frames = []
    declared: dict[str, ColumnInput] = {}
    for table in tables:
        frame = table.data.df()
        frame["origin"] = str(table.id)
        frames.append(frame)
        for column in table.columns:
            if column.name in declared:
                continue
            # An axis-typed column is a coordinate. Stating a role beside it is refused.
            declared[column.name] = ColumnInput(
                name=column.name,
                axis_type=column.axis_type,
                role=None if column.axis_type else column.role,
                unit=column.unit,
                long_name=column.long_name,
            )

    merged = pd.concat(frames, ignore_index=True)
    return mikro.create_table_dataset(
        name=f"Merged {len(tables)} tables",
        data=merged,
        columns=list(declared.values()),
    )


# --------------------------------------------------------------------------- #
# Cutting: lenses over the same data, nothing uploaded
# --------------------------------------------------------------------------- #
def _cut(
    mikro: Mikro, image: ArrayLens, axis: str, interval: int, label: str
) -> Generator[ArrayLens, None, None]:
    """Lenses over `image`, `interval` positions of `axis` at a time."""
    if interval < 1:
        raise ValueError(f"interval must be at least 1, got {interval}")
    size = dict(zip(image.axis_names, image.shape))[axis]
    title = _title(mikro, image)
    for start in range(0, size, interval):
        yield mikro.create_lens(
            lens=image.id,
            slices=[SliceInput(axis=axis, start=start, stop=min(start + interval, size))],
            name=f"{title} {label} {start}",
        )


@app.action(name="Timeseries to Frames", collections=["conversion"])
def t_to_frame(
    image: Annotated[Timeseries, Description("The timeseries to cut")],
    interval: Annotated[int, Description("How many timepoints each frame spans")] = 1,
    *,
    mikro: Mikro,
) -> Generator[Frame, None, None]:
    """Cuts a timeseries into frames along its time axis.

    Each frame is a lens over the same dataset, so no pixel is copied.
    """
    (time_axis, *_) = image.axes_of_type(AxisType.TIME)
    yield from _cut(mikro, image, time_axis, interval, "frame")


@app.action(name="Volume to Slices", collections=["conversion"])
def z_to_slice(
    image: Annotated[Volume, Description("The volume to cut")],
    interval: Annotated[int, Description("How many planes each slice spans")] = 1,
    *,
    mikro: Mikro,
) -> Generator[Slab, None, None]:
    """Cuts a volume into slices along its first space axis (z, by convention).

    Each slice is a lens over the same dataset, so no pixel is copied.
    """
    depth_axis = image.axes_of_type(AxisType.SPACE)[0]
    yield from _cut(mikro, image, depth_axis, interval, "slice")


@app.action(name="Crop to Annotation", collections=["conversion", "cropping"])
def crop_image(
    annotation: Annotated[Annotation, Description("The shape to crop to")],
    image: Annotated[ArrayLens, Description("The lens the shape was drawn over")],
    *,
    mikro: Mikro,
) -> ArrayLens:
    """Crops a lens to the box of an annotation.

    The server composes the annotation's box into the dataset's grid and keeps what
    the lens selects under it. The result is a lens, so no pixel is copied.
    """
    return mikro.create_lens(lens=image.id, annotation=annotation.id, name=annotation.name)


# --------------------------------------------------------------------------- #
# Creation
# --------------------------------------------------------------------------- #
@app.action(name="Create Random Image", collections=["creation"])
def create_random_image(
    width: Annotated[int, Description("The width of the image")] = 100,
    height: Annotated[int, Description("The height of the image")] = 100,
    *,
    mikro: Mikro,
) -> ArrayLens:
    """Creates an image of uniform random noise."""
    array = xr.DataArray(np.random.rand(height, width).astype(np.float32), dims=("y", "x"))
    return _upload(mikro, array, "Random Image", ["y", "x"])


class DataKind(Enum):
    """A sample image shipped with scikit-image."""

    ASTRONAUT = "astronaut"
    BRAIN = "brain"
    BRICK = "brick"
    CAMERA = "camera"
    CAT = "cat"
    CELL = "cell"
    CELLS_3D = "cells3d"
    CHECKERBOARD = "checkerboard"
    CHELSEA = "chelsea"
    CLOCK = "clock"
    COFFEE = "coffee"
    COINS = "coins"
    COLORWHEEL = "colorwheel"
    EAGLE = "eagle"
    GRASS = "grass"
    GRAVEL = "gravel"
    HORSE = "horse"
    HUBBLE_DEEP_FIELD = "hubble_deep_field"
    HUMAN_MITOSIS = "human_mitosis"
    IMMUNOHISTOCHEMISTRY = "immunohistochemistry"
    KIDNEY = "kidney"
    LILY = "lily"
    LOGO = "logo"
    MICROANEURYSMS = "microaneurysms"
    MOON = "moon"
    NICKEL_SOLIDIFICATION = "nickel_solidification"
    PAGE = "page"
    PROTEIN_TRANSPORT = "protein_transport"
    RETINA = "retina"
    ROCKET = "rocket"
    SHEPP_LOGAN_PHANTOM = "shepp_logan_phantom"
    SKIN = "skin"
    TEXT = "text"
    VORTEX = "vortex"


YX = ("y", "x")
YXC = ("y", "x", "c")

SAMPLE_DIMS: dict[DataKind, tuple[str, ...]] = {
    DataKind.ASTRONAUT: YXC,
    DataKind.BRAIN: ("z", "y", "x"),
    DataKind.BRICK: YX,
    DataKind.CAMERA: YX,
    DataKind.CAT: YXC,
    DataKind.CELL: YX,
    DataKind.CELLS_3D: ("z", "c", "y", "x"),
    DataKind.CHECKERBOARD: YX,
    DataKind.CHELSEA: YXC,
    DataKind.CLOCK: YX,
    DataKind.COFFEE: YXC,
    DataKind.COINS: YX,
    DataKind.COLORWHEEL: YXC,
    DataKind.EAGLE: YX,
    DataKind.GRASS: YX,
    DataKind.GRAVEL: YX,
    DataKind.HORSE: YX,
    DataKind.HUBBLE_DEEP_FIELD: YXC,
    DataKind.HUMAN_MITOSIS: YX,
    DataKind.IMMUNOHISTOCHEMISTRY: YXC,
    DataKind.KIDNEY: ("z", "y", "x", "c"),
    DataKind.LILY: YXC,
    DataKind.LOGO: YXC,
    DataKind.MICROANEURYSMS: YX,
    DataKind.MOON: YX,
    DataKind.NICKEL_SOLIDIFICATION: ("t", "y", "x"),
    DataKind.PAGE: YX,
    DataKind.PROTEIN_TRANSPORT: ("t", "c", "y", "x"),
    DataKind.RETINA: YXC,
    DataKind.ROCKET: YXC,
    DataKind.SHEPP_LOGAN_PHANTOM: YX,
    DataKind.SKIN: YXC,
    DataKind.TEXT: YX,
    # An image pair from a PIV challenge: two frames, stacked along time.
    DataKind.VORTEX: ("t", "y", "x"),
}
"""The axes of each sample, in the order scikit-image returns them (row-major)."""

RGB_PHOTOS = {kind for kind, dims in SAMPLE_DIMS.items() if dims == YXC} - {
    DataKind.LILY,  # four fluorescence channels
    DataKind.LOGO,  # RGBA
}
"""The samples that are 8-bit RGB photographs."""


def load_sample(kind: DataKind) -> xr.DataArray:
    """A scikit-image sample with its axes named. Some are downloaded on first use."""
    raw = getattr(skdata, kind.value)()
    if isinstance(raw, tuple):
        raw = np.stack(raw)
    raw = np.asarray(raw)
    if raw.dtype == bool:
        raw = raw.astype(np.uint8)
    elif raw.dtype == np.float64:
        raw = raw.astype(np.float32)
    return xr.DataArray(raw, dims=SAMPLE_DIMS[kind])


@app.action(name="Generate Test Image", collections=["generator"])
def generate_test_image(
    kind: Annotated[DataKind, Description("The sample to load")],
    *,
    mikro: Mikro,
) -> ArrayLens:
    """Uploads one of the sample images that ship with scikit-image."""
    array = load_sample(kind)
    return _upload(
        mikro,
        array,
        f"Test Image {kind.name}",
        [str(d) for d in array.dims],
        rgb=kind in RGB_PHOTOS,
    )


# --------------------------------------------------------------------------- #
# Processing
# --------------------------------------------------------------------------- #
@app.action(name="Resize", collections=["processing", "scaling"])
def resize(
    image: Annotated[ArrayLens, Description("The image to resize")],
    dim_x: Annotated[int | None, Description("The new extent of x (unchanged if unset)")] = None,
    dim_y: Annotated[int | None, Description("The new extent of y (unchanged if unset)")] = None,
    dim_z: Annotated[int | None, Description("The new extent of z (unchanged if unset)")] = None,
    anti_alias: Annotated[bool, Description("Smooth before downsampling")] = True,
    *,
    mikro: Mikro,
) -> ArrayLens:
    """Resizes the x, y and z axes of an image to the extents given.

    Every other axis keeps its extent. The result is registered into the input's
    space by a scale per axis, so it still lines up with it.
    """
    data = image.data.compute()
    wanted = {"x": dim_x, "y": dim_y, "z": dim_z}
    dims = [str(d) for d in data.dims]
    shape = tuple(wanted.get(d) or data.sizes[d] for d in dims)

    resized = transform.resize(
        data.data, shape, anti_aliasing=anti_alias, preserve_range=True
    ).astype(data.dtype)

    # Forward, derived -> source. Voxel centres sit at the integers, so the centre of
    # voxel i of the result lands at i * s + (s - 1) / 2 of the source, s = old / new.
    scale = [data.sizes[d] / new for d, new in zip(dims, shape)]
    translation = [(s - 1) / 2 for s in scale]
    return _upload(
        mikro,
        xr.DataArray(resized, dims=dims),
        f"Resized {_title(mikro, image)}",
        image.carried_axes(dims),
        derived_from=[
            image.derive(
                scale=scale, translation=translation, value_relation=ValueRelation.TRANSFORMED
            )
        ],
    )


class ThresholdMethod(Enum):
    """What the threshold is a fraction of."""

    MEAN = "mean"
    MAX = "max"
    MIN = "min"


@app.action(name="Binarize", collections=["processing", "thresholding"])
def threshold_image(
    image: Annotated[ArrayLens, Description("The image to binarize")],
    threshold: Annotated[float, Description("The fraction of the reference value to cut at")] = 0.5,
    method: Annotated[ThresholdMethod, Description("The reference value")] = ThresholdMethod.MEAN,
    *,
    mikro: Mikro,
) -> Mask:
    """Binarizes an image: 1 where it is above a fraction of its mean, max or min."""
    data = image.data.compute()
    reference = {
        ThresholdMethod.MEAN: data.mean,
        ThresholdMethod.MAX: data.max,
        ThresholdMethod.MIN: data.min,
    }[method]()
    mask = (data > threshold * reference).astype(np.uint8)
    dims = [str(d) for d in data.dims]
    return _publish_mask(mikro, image, mask, dims, f"Binarized {_title(mikro, image)}")


class CV2NormTypes(Enum):
    """How a plane is normalized to 8 bit before adaptive thresholding."""

    NORM_INF = cv2.NORM_INF
    NORM_MINMAX = cv2.NORM_MINMAX


# (alpha, beta) per norm. For MINMAX they are the range to stretch onto. For INF,
# alpha is the norm the plane is scaled to, so it has to be 255: with 0 every
# plane comes out black and the threshold marks all of it.
NORM_BOUNDS = {
    CV2NormTypes.NORM_MINMAX: (0, 255),
    CV2NormTypes.NORM_INF: (255, 0),
}


@app.action(name="Adaptive Binarize", collections=["processing", "thresholding", "adaptive"])
def adaptive_threshold_image(
    image: Annotated[Planes, Description("The image to binarize")],
    normtype: Annotated[CV2NormTypes, Description("How each plane is normalized first")] = CV2NormTypes.NORM_MINMAX,
    *,
    mikro: Mikro,
    task: Task,
) -> Mask:
    """Binarizes each plane against a Gaussian-weighted local threshold (11 px block)."""

    def binarize(plane: np.ndarray) -> np.ndarray:
        alpha, beta = NORM_BOUNDS[normtype]
        normed = cv2.normalize(plane, None, alpha, beta, normtype.value, cv2.CV_8U)
        thresholded = cv2.adaptiveThreshold(
            normed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return (thresholded > 0).astype(np.uint8)

    mask, dims = _binarize_by_plane(image, task, binarize)
    return _publish_mask(mikro, image, mask, dims, f"Adaptive Binarized {_title(mikro, image)}")


@app.action(name="Otsu Thresholding", collections=["processing", "thresholding", "adaptive"])
def otsu_thresholding(
    image: Annotated[Planes, Description("The image to binarize")],
    gaussian_blur: Annotated[bool, Description("Blur each plane first (5x5 kernel)")] = False,
    *,
    mikro: Mikro,
    task: Task,
) -> Mask:
    """Binarizes each plane with Otsu's method.

    Each plane is stretched to 8 bit on its own before its threshold is found.
    """

    def binarize(plane: np.ndarray) -> np.ndarray:
        normed = _to_uint8(plane)
        if gaussian_blur:
            normed = cv2.GaussianBlur(normed, (5, 5), 0)
        _, thresholded = cv2.threshold(normed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return (thresholded > 0).astype(np.uint8)

    mask, dims = _binarize_by_plane(image, task, binarize)
    return _publish_mask(mikro, image, mask, dims, f"Otsu Thresholded {_title(mikro, image)}")


@app.action(name="Maximum Intensity Projection", collections=["processing", "projection"])
def maximum_intensity_projection(
    image: Annotated[Volume, Description("The volume to project")],
    *,
    mikro: Mikro,
) -> Projection:
    """Projects a volume onto the maximum along its first space axis (z, by convention)."""
    depth_axis = image.axes_of_type(AxisType.SPACE)[0]
    projected = image.data.max(dim=depth_axis).compute()
    kept = [str(d) for d in projected.dims]
    return _upload(
        mikro,
        projected,
        f"Max Projection of {_title(mikro, image)}",
        image.carried_axes(kept),
        derived_from=[image.derive_projection(kept, value_relation=ValueRelation.TRANSFORMED)],
    )


@app.action(name="Build Pyramid", collections=["processing", "scaling"])
def multiscale_image(
    image: Annotated[ArrayLens, Description("The image to give a pyramid")],
    *,
    mikro: Mikro,
) -> ArrayLens:
    """Uploads a copy of what a lens selects with a resolution pyramid.

    For datasets that were uploaded with a single level and are too large to view
    smoothly. Every dataset this app uploads already has one.
    """
    data = image.data.compute()
    dims = [str(d) for d in data.dims]
    return _upload(
        mikro,
        data,
        f"Pyramid of {_title(mikro, image)}",
        image.carried_axes(dims),
        derived_from=[image.derive_identity(value_relation=ValueRelation.IDENTICAL)],
    )


# --------------------------------------------------------------------------- #
# Viewing
# --------------------------------------------------------------------------- #
CHANNEL_COLORMAPS = (
    ColorMap.RED,
    ColorMap.GREEN,
    ColorMap.BLUE,
    ColorMap.MAGENTA,
    ColorMap.CYAN,
    ColorMap.YELLOW,
)


def _show_with_contrast(
    mikro: Mikro,
    image: ArrayLens,
    name: str,
    limits,
    gamma: float,
) -> Scene:
    """A new scene over the dataset of `image`, with one layer per channel.

    `limits` maps a channel's values to its contrast limits. A lens spanning three
    space axes is drawn as a volume, projected by its maximum.
    """
    dataset = mikro.get_array_dataset(image.dataset.id)
    if dataset.intrinsic_system is None:
        raise RuntimeError(f"Dataset {dataset.id} has no intrinsic system to show in")
    scene = mikro.create_scene(name=name, coordinate_system=dataset.intrinsic_system.id)

    channel_axes = image.axes_of_type(AxisType.CHANNEL)
    if channel_axes:
        axis = channel_axes[0]
        n = dict(zip(image.axis_names, image.shape))[axis]
        channels = [
            mikro.create_lens(lens=image.id, slices=[SliceInput(axis=axis, start=i, stop=i + 1)])
            for i in range(n)
        ]
    else:
        channels = [image]

    sizes = dict(zip(image.axis_names, image.shape))
    volumetric = sum(sizes[a] > 1 for a in image.axes_of_type(AxisType.SPACE)) >= 3

    for i, channel in enumerate(channels):
        low, high = limits(channel.data.compute().values)
        settings = dict(
            lens=channel.id,
            scene=scene.id,
            colormap=ColorMap.INTENSITY if len(channels) == 1 else CHANNEL_COLORMAPS[i % len(CHANNEL_COLORMAPS)],
            clim_min=float(low),
            clim_max=float(high),
            gamma=gamma,
            blending=Blending.ADDITIVE,
            order=i,
        )
        if volumetric:
            mikro.create_volume_layer(mode=ProjectionMode.MIP, **settings)
        else:
            mikro.create_intensity_layer(**settings)
    return scene


@app.action(name="Show Normalized", collections=["rescale", "viewing"])
def rescale_channel(
    image: Annotated[ArrayLens, Description("The image to show")],
    *,
    mikro: Mikro,
) -> Scene:
    """Shows an image in a new scene, one layer per channel, each with its contrast
    limits set to its own minimum and maximum.
    """
    return _show_with_contrast(
        mikro, image, f"{_title(mikro, image)} (normalized)", lambda v: (v.min(), v.max()), 1.0
    )


@app.action(name="Show Perceptually", collections=["rescale", "viewing"])
def rescale_channel_perceptually(
    image: Annotated[ArrayLens, Description("The image to show")],
    *,
    mikro: Mikro,
) -> Scene:
    """Shows an image in a new scene, one layer per channel, each with its contrast
    limits at its 2nd and 98th percentile and a gamma of 0.8.
    """
    return _show_with_contrast(
        mikro,
        image,
        f"{_title(mikro, image)} (perceptual)",
        lambda v: np.percentile(v, (2, 98)),
        0.8,
    )


# --------------------------------------------------------------------------- #
# Segmentation
# --------------------------------------------------------------------------- #
def cluster_boxes(
    labels: np.ndarray,
    distance: float,
    min_size: int,
    max_size: int | None,
    limit: int | None,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """The bounding boxes of dense clusters of label centroids, as two corners in
    array order: ``((row_min, col_min), (row_max, col_max))``.
    """
    ids = np.unique(labels[labels > 0])
    if len(ids) == 0:
        return []
    centroids = np.array(ndimage.center_of_mass(np.ones_like(labels), labels, ids))
    clusters = DBSCAN(eps=distance, min_samples=min_size).fit(centroids).labels_

    boxes = []
    for cluster in sorted(set(clusters) - {-1}):
        members = ids[clusters == cluster]
        if max_size is not None and len(members) > max_size:
            continue
        rows, cols = np.where(np.isin(labels, members))
        boxes.append(((int(rows.min()), int(cols.min())), (int(rows.max()), int(cols.max()))))
        if limit is not None and len(boxes) >= limit:
            break
    return boxes


@app.action(name="Mark Clusters", collections=["segmentation"])
def mark_clusters_of_size_rectangle(
    image: Annotated[LabelPlane, Description("The label image whose objects to cluster")],
    distance: Annotated[float, Description("The distance between centroids in a cluster (DBSCAN eps)")],
    min_size: Annotated[int, Description("The minimum number of objects in a cluster (DBSCAN min_samples)")],
    max_size: Annotated[int | None, Description("Skip clusters with more objects than this")] = None,
    limit: Annotated[int | None, Description("The maximum number of clusters to mark")] = None,
    *,
    mikro: Mikro,
    task: Task,
) -> list[Annotation]:
    """Marks dense clusters of labelled objects with rectangles.

    The centroids of the objects are clustered with DBSCAN, and each cluster is
    drawn as the bounding box of its objects, into one new annotation collection.
    """
    space_axes = image.axes_of_type(AxisType.SPACE)
    data = image.data
    plane = data.squeeze([d for d in data.dims if d not in space_axes])
    labels = np.asarray(plane.transpose(*space_axes).data).astype(np.int64)

    boxes = cluster_boxes(labels, distance, min_size, max_size, limit)
    task.log(f"Found {len(boxes)} clusters")
    if not boxes:
        return []

    # One collection for all of them: `draw` without one makes a new collection
    # per call. Same axes as the lens, and an identity edge back into it.
    system = image.coordinate_system
    if system is None:
        raise RuntimeError(f"Lens {image.id} was fetched without its coordinate system")
    collection = mikro.create_annotation_collection(
        name=f"Clusters in {_title(mikro, image)}",
        axes=[AxisInput(name=a.name, type=a.type, long_name=a.long_name) for a in system.axes],
        derived_from=[
            CoordinateSystemDerivedFromInput(
                coordinate_system=system.id, transform=IdentityTransformInput()
            )
        ],
    )

    # A rectangle is its two opposite corners, in the lens' axis order.
    return [
        image.draw(
            AnnotationKind.RECTANGLE,
            np.array([low, high]),
            name=f"Cluster {i + 1}",
            collection=collection.id,
        )
        for i, (low, high) in enumerate(boxes)
    ]


if __name__ == "__main__":
    run(app)
