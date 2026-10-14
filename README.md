# STDLIB

The standard library: small, general actions over mikro data for the Arkitekt
platform. These are the everyday steps that a workflow strings together between
the specialised apps.

Every array action takes a lens (a selection over a dataset) and reads only what
the lens selects. What it computes is uploaded as a new dataset. That dataset
derives from the lens, so it lands in the input's coordinate space. Cutting
(frames, slices, crops) makes lenses over the same dataset and copies nothing.

## Actions

| Collection | Action | In | Out |
| --- | --- | --- | --- |
| quantitative | Measure Max / Sum / Fraction / Basic Metrics | a lens | numbers |
| collection | Iterate Images | a folder | the whole lens of each array dataset in it |
| organization | Merge Tables | tables | one table, with an `origin` column |
| conversion | Timeseries to Frames | a lens with a time axis | lenses, `interval` timepoints each |
| conversion | Volume to Slices | a 3D lens | lenses, `interval` planes each |
| conversion | Crop to Annotation | an annotation and a lens | the lens cut to the annotation's box |
| creation | Create Random Image | width, height | a noise image |
| generator | Generate Test Image | a scikit-image sample | the sample, axes named |
| processing | Resize | a lens, new x/y/z extents | the resized image, scaled into the input's space |
| processing | Binarize / Adaptive Binarize / Otsu Thresholding | a lens | a categorical mask |
| processing | Maximum Intensity Projection | a 3D lens | the projection along the first space axis |
| processing | Build Pyramid | a lens | a copy with a resolution pyramid |
| viewing | Show Normalized / Show Perceptually | a lens | a new scene, one layer per channel, contrast set from the data |
| segmentation | Mark Clusters | a 2D label lens | rectangle annotations around dense clusters of objects |

## Running

```bash
uv sync
uv run arkitekt run dev
```

Dependencies live in `pyproject.toml` and are locked in `uv.lock`: add one with
`uv add <package>`.

The image is built from `.arkitekt/flavours/vanilla/`. It bakes the scikit-image
sample data in via `init.py`.
