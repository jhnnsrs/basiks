"""The app's logo, and one logo per action

The app's logo is a LOGO blok (an ``<AgentLogo>`` root): an SVG in colours of its own,
which a client shows beside the app's name. Each action's logo is an ACTION_LOGO blok
(an ``<ActionLogo>`` root): the same SVG shapes, but painted only with the viewer's palette (``ink``, ``muted``, ``brand``,
``brand-strong``, ``brand-soft``, ``surface``), so the actions of every app look like
one set and follow the viewer's brand and dark mode. A shape that ``animate``s plays
while the logo is hovered, and while the viewer's run of the action is going.

Every logo is drawn on a 24 x 24 grid to read at 16 px. Blok names are the
organization's, so each carries the app's name.
"""

from arkitekt import App

APP = "basiks"

APP_LOGO = f"{APP}_logo"

# Four building blocks on a dark tile: a histogram, a binarized disc, a pyramid and
# a stack of slices. What the standard library does, in one picture.
APP_LOGO_SOURCE = """
<AgentLogo viewBox="0 0 64 64" title="basiks">
  <Defs>
    <LinearGradient id="ground" x1="0" y1="0" x2="1" y2="1">
      <Stop offset="0" stopColor="ink" />
      <Stop offset="1" stopColor="ink" />
    </LinearGradient>
  </Defs>
  <Rect x="0" y="0" width="64" height="64" rx="14" fill="url(#ground)" />
  <Rect x="9" y="9" width="21" height="21" rx="5" fill="spectrum-cyan" />
  <Rect x="34" y="9" width="21" height="21" rx="5" fill="spectrum-yellow" />
  <Rect x="9" y="34" width="21" height="21" rx="5" fill="spectrum-violet" />
  <Rect x="34" y="34" width="21" height="21" rx="5" fill="spectrum-red" />
  <G fill="ink">
    <Rect x="13" y="19.5" width="3.5" height="6" rx="0.8" />
    <Rect x="18.25" y="14" width="3.5" height="11.5" rx="0.8" />
    <Rect x="23.5" y="17.5" width="3.5" height="8" rx="0.8" />
  </G>
  <Circle cx="44.5" cy="19.5" r="6.5" fill="none" stroke="ink" strokeWidth="2.2" />
  <Path d="M44.5 13a6.5 6.5 0 0 0 0 13Z" fill="ink" />
  <G fill="ink">
    <Rect x="12.5" y="47.5" width="14" height="3.5" rx="0.8" />
    <Rect x="15" y="43" width="9" height="3.5" rx="0.8" />
    <Rect x="17.5" y="38.5" width="4" height="3.5" rx="0.8" />
  </G>
  <G fill="none" stroke="ink" strokeWidth="2" strokeLinejoin="round">
    <Polygon points="44.5,43 51.5,46.5 44.5,50 37.5,46.5" fill="ink" fillOpacity="0.3" />
    <Polygon points="44.5,38 51.5,41.5 44.5,45 37.5,41.5" />
  </G>
  <Rect x="0.5" y="0.5" width="63" height="63" rx="13.5" fill="none" stroke="muted" strokeOpacity="0.3" strokeWidth="1" />
</AgentLogo>
"""

# Shared strokes: an outline in ink, rounded.
_LINE = 'fill="none" stroke="ink" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"'

ACTION_LOGOS: dict[str, str] = {
    # The tallest bar of a histogram, marked.
    "measure_max": f"""
<ActionLogo viewBox="0 0 24 24" title="Measure Max">
  <Rect x="3.5" y="14" width="3.5" height="6" rx="1" fill="brand-soft" />
  <Rect x="8.25" y="10" width="3.5" height="10" rx="1" fill="brand-soft" />
  <Rect x="13" y="6.5" width="3.5" height="13.5" rx="1" fill="brand" animate="pulse" />
  <Rect x="17.75" y="12" width="3.5" height="8" rx="1" fill="brand-soft" />
  <Path d="M12.75 4.5 14.75 2.5 16.75 4.5" {_LINE} />
  <Line x1="2.5" y1="21" x2="21.5" y2="21" {_LINE} />
</ActionLogo>
""",
    # A sigma, traced.
    "measure_sum": """
<ActionLogo viewBox="0 0 24 24" title="Measure Sum">
  <Circle cx="12" cy="12" r="9.5" fill="brand-soft" />
  <Path d="M16 6.5H8l5 5.5-5 5.5h8" fill="none" stroke="ink" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" animate="draw" />
</ActionLogo>
""",
    # A slice of a pie.
    "measure_fraction": f"""
<ActionLogo viewBox="0 0 24 24" title="Measure Fraction">
  <Circle cx="12" cy="12" r="8.5" fill="brand-soft" />
  <Path d="M12 12V3.5A8.5 8.5 0 0 1 20.08 14.63Z" fill="brand" animate="pulse" />
  <Circle cx="12" cy="12" r="8.5" {_LINE} />
</ActionLogo>
""",
    # A box plot: the max, the mean and the min in one glyph.
    "measure_basics": f"""
<ActionLogo viewBox="0 0 24 24" title="Measure Basic Metrics">
  <Path d="M12 3.5V20.5M9 3.5h6M9 20.5h6" {_LINE} />
  <G animate="float">
    <Rect x="7" y="8" width="10" height="7.5" rx="1.5" fill="brand" stroke="ink" strokeWidth="1.6" />
    <Line x1="7.8" y1="11.75" x2="16.2" y2="11.75" stroke="surface" strokeWidth="1.6" />
  </G>
</ActionLogo>
""",
    # A stack of images, the front one shown.
    "iterate_images": """
<ActionLogo viewBox="0 0 24 24" title="Iterate Images">
  <Rect x="8" y="2.5" width="13" height="13" rx="2.5" fill="brand-soft" stroke="ink" strokeWidth="1.4" opacity="0.5" animate="float" animateDelay="0.3" />
  <Rect x="6" y="4.75" width="13" height="13" rx="2.5" fill="brand-soft" stroke="ink" strokeWidth="1.4" opacity="0.8" animate="float" animateDelay="0.15" />
  <Rect x="3.5" y="7.5" width="13.5" height="13.5" rx="2.5" fill="surface" stroke="ink" strokeWidth="1.6" />
  <Path d="M6 18.5l3.2-4 2.3 2.6 1.8-1.8 2 2.4" fill="none" stroke="brand-strong" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  <Circle cx="13.25" cy="11.25" r="1.3" fill="brand" />
</ActionLogo>
""",
    # Two tables flowing into one.
    "merge_tables": """
<ActionLogo viewBox="0 0 24 24" title="Merge Tables">
  <G fill="brand-soft" stroke="ink" strokeWidth="1.4" strokeLinejoin="round">
    <Rect x="2.5" y="3.5" width="7" height="6.5" rx="1.2" />
    <Rect x="2.5" y="14" width="7" height="6.5" rx="1.2" />
  </G>
  <Rect x="14.5" y="5" width="7" height="14" rx="1.2" fill="brand" stroke="ink" strokeWidth="1.4" />
  <G stroke="ink" strokeWidth="1">
    <Line x1="2.5" y1="6.75" x2="9.5" y2="6.75" />
    <Line x1="2.5" y1="17.25" x2="9.5" y2="17.25" />
  </G>
  <G stroke="surface" strokeWidth="1">
    <Line x1="15.2" y1="8.5" x2="20.8" y2="8.5" />
    <Line x1="15.2" y1="12" x2="20.8" y2="12" />
    <Line x1="15.2" y1="15.5" x2="20.8" y2="15.5" />
  </G>
  <G fill="none" stroke="brand-strong" strokeWidth="1.6" strokeLinecap="round">
    <Path d="M9.5 6.8C12.5 6.8 11.5 12 14.5 12" animate="draw" />
    <Path d="M9.5 17.2C12.5 17.2 11.5 12 14.5 12" animate="draw" />
  </G>
</ActionLogo>
""",
    # A strip of film, cut into frames.
    "t_to_frame": """
<ActionLogo viewBox="0 0 24 24" title="Timeseries to Frames">
  <Rect x="2.5" y="5" width="19" height="14" rx="2" fill="ink" />
  <Rect x="4.5" y="8.5" width="4.3" height="7" rx="0.8" fill="brand-soft" />
  <Rect x="9.85" y="8.5" width="4.3" height="7" rx="0.8" fill="brand" animate="pulse" />
  <Rect x="15.2" y="8.5" width="4.3" height="7" rx="0.8" fill="brand-soft" />
  <G stroke="surface" strokeWidth="1.1" strokeDasharray="1.5 1.5">
    <Line x1="4" y1="6.75" x2="20" y2="6.75" animate="march" />
    <Line x1="4" y1="17.25" x2="20" y2="17.25" animate="march" />
  </G>
</ActionLogo>
""",
    # A volume, one slice lifted out.
    "z_to_slice": """
<ActionLogo viewBox="0 0 24 24" title="Volume to Slices">
  <Polygon points="12,12.5 21,17 12,21.5 3,17" fill="brand-soft" stroke="ink" strokeWidth="1.4" strokeLinejoin="round" />
  <Polygon points="12,8 21,12.5 12,17 3,12.5" fill="brand" stroke="ink" strokeWidth="1.4" strokeLinejoin="round" animate="float" />
  <Polygon points="12,3 21,7.5 12,12 3,7.5" fill="brand-soft" stroke="ink" strokeWidth="1.4" strokeLinejoin="round" />
</ActionLogo>
""",
    # Crop brackets around a drawn shape.
    "crop_image": """
<ActionLogo viewBox="0 0 24 24" title="Crop to Annotation">
  <Polygon points="9.6,9.2 14.8,9.9 14.4,14.8 9.3,14.2" fill="brand" />
  <Rect x="8.6" y="8.6" width="6.8" height="6.8" fill="none" stroke="brand-strong" strokeWidth="0.8" strokeDasharray="1.5 1.5" animate="march" />
  <Path d="M7 2.5V17H21.5" fill="none" stroke="ink" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  <Path d="M2.5 7H17V21.5" fill="none" stroke="ink" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
</ActionLogo>
""",
    # Noise: cells of every tone, some flickering.
    "create_random_image": """
<ActionLogo viewBox="0 0 24 24" title="Create Random Image">
  <Rect x="3" y="3" width="18" height="18" rx="3" fill="surface" stroke="ink" strokeWidth="1.6" />
  <Rect x="5" y="5" width="3.25" height="3.25" rx="0.6" fill="brand-soft" />
  <Rect x="8.6" y="5" width="3.25" height="3.25" rx="0.6" fill="brand" animate="blink" />
  <Rect x="12.2" y="5" width="3.25" height="3.25" rx="0.6" fill="muted" />
  <Rect x="15.75" y="5" width="3.25" height="3.25" rx="0.6" fill="brand-soft" />
  <Rect x="5" y="8.6" width="3.25" height="3.25" rx="0.6" fill="brand-strong" />
  <Rect x="8.6" y="8.6" width="3.25" height="3.25" rx="0.6" fill="brand-soft" />
  <Rect x="12.2" y="8.6" width="3.25" height="3.25" rx="0.6" fill="brand" />
  <Rect x="15.75" y="8.6" width="3.25" height="3.25" rx="0.6" fill="brand-strong" animate="blink" animateDelay="0.5" />
  <Rect x="5" y="12.2" width="3.25" height="3.25" rx="0.6" fill="brand" />
  <Rect x="8.6" y="12.2" width="3.25" height="3.25" rx="0.6" fill="muted" animate="blink" animateDelay="0.25" />
  <Rect x="12.2" y="12.2" width="3.25" height="3.25" rx="0.6" fill="brand-soft" />
  <Rect x="15.75" y="12.2" width="3.25" height="3.25" rx="0.6" fill="brand" />
  <Rect x="5" y="15.75" width="3.25" height="3.25" rx="0.6" fill="brand-soft" />
  <Rect x="8.6" y="15.75" width="3.25" height="3.25" rx="0.6" fill="brand-strong" />
  <Rect x="12.2" y="15.75" width="3.25" height="3.25" rx="0.6" fill="brand" animate="blink" animateDelay="0.75" />
  <Rect x="15.75" y="15.75" width="3.25" height="3.25" rx="0.6" fill="brand-soft" />
</ActionLogo>
""",
    # A picture, freshly made.
    "generate_test_image": """
<ActionLogo viewBox="0 0 24 24" title="Generate Test Image">
  <Rect x="2.5" y="6" width="15.5" height="15" rx="2.5" fill="brand-soft" stroke="ink" strokeWidth="1.6" />
  <Path d="M5 18.5l3.6-4.6 3 3.4 2-2 2.4 3.2" fill="none" stroke="brand-strong" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  <Circle cx="13" cy="10.5" r="1.5" fill="brand" />
  <Path d="M19.5 1.8 20.4 4.1 22.7 5 20.4 5.9 19.5 8.2 18.6 5.9 16.3 5 18.6 4.1Z" fill="brand" animate="pulse" />
</ActionLogo>
""",
    # A small image in the frame of a larger one.
    "resize": f"""
<ActionLogo viewBox="0 0 24 24" title="Resize">
  <Rect x="3" y="3" width="18" height="18" rx="3" fill="none" stroke="ink" strokeWidth="1.6" strokeDasharray="2 2" />
  <Rect x="3" y="11" width="10" height="10" rx="2.5" fill="brand" animate="pulse" />
  <Path d="M14.5 9.5 19 5M15 5h4v4" {_LINE} />
</ActionLogo>
""",
    # A disc split into dark and light.
    "threshold_image": f"""
<ActionLogo viewBox="0 0 24 24" title="Binarize">
  <Circle cx="12" cy="12" r="8.5" fill="brand-soft" />
  <Path d="M12 3.5a8.5 8.5 0 0 0 0 17Z" fill="ink" />
  <Circle cx="12" cy="12" r="8.5" {_LINE} animate="draw" />
</ActionLogo>
""",
    # Four tiles, each cut at its own level.
    "adaptive_threshold_image": f"""
<ActionLogo viewBox="0 0 24 24" title="Adaptive Binarize">
  <Rect x="3" y="3" width="18" height="18" rx="3" fill="brand-soft" />
  <Rect x="3.8" y="8.5" width="7.4" height="2.7" fill="brand-strong" animate="blink" />
  <Rect x="12.8" y="5.5" width="7.4" height="5.7" fill="brand-strong" animate="blink" animateDelay="0.3" />
  <Rect x="3.8" y="13.8" width="7.4" height="6.4" fill="brand-strong" animate="blink" animateDelay="0.6" />
  <Rect x="12.8" y="17" width="7.4" height="3.2" fill="brand-strong" animate="blink" animateDelay="0.9" />
  <Path d="M12 3.5V20.5M3.5 12h17" stroke="surface" strokeWidth="1.6" />
  <Rect x="3" y="3" width="18" height="18" rx="3" {_LINE} />
</ActionLogo>
""",
    # Two humps of a histogram, and the threshold that parts them.
    "otsu_thresholding": f"""
<ActionLogo viewBox="0 0 24 24" title="Otsu Thresholding">
  <Path d="M3 20C5 20 5.5 8 8 8S10.5 17 12 17 14 5 16.5 5 19 20 21 20Z" fill="brand-soft" />
  <Path d="M3 20C5 20 5.5 8 8 8S10.5 17 12 17 14 5 16.5 5 19 20 21 20" {_LINE} />
  <Line x1="12" y1="2.5" x2="12" y2="21" stroke="brand-strong" strokeWidth="1.6" strokeDasharray="2 1" animate="march" />
  <Line x1="2.5" y1="21" x2="21.5" y2="21" {_LINE} />
</ActionLogo>
""",
    # Slices above, their brightest pixels falling onto one plane.
    "maximum_intensity_projection": """
<ActionLogo viewBox="0 0 24 24" title="Maximum Intensity Projection">
  <Polygon points="12,2 19.5,5 12,8 4.5,5" fill="brand-soft" stroke="ink" strokeWidth="1.2" strokeLinejoin="round" />
  <Polygon points="12,5 19.5,8 12,11 4.5,8" fill="brand-soft" stroke="ink" strokeWidth="1.2" strokeLinejoin="round" />
  <G stroke="brand-strong" strokeWidth="1.4" strokeLinecap="round" strokeDasharray="1.5 1.5">
    <Line x1="7.5" y1="10.5" x2="7.5" y2="16" animate="march" />
    <Line x1="12" y1="12" x2="12" y2="17.5" animate="march" />
    <Line x1="16.5" y1="10.5" x2="16.5" y2="16" animate="march" />
  </G>
  <Polygon points="12,14.5 21,18 12,21.5 3,18" fill="brand" stroke="ink" strokeWidth="1.4" strokeLinejoin="round" />
</ActionLogo>
""",
    # Three levels of resolution, smaller and smaller.
    "multiscale_image": """
<ActionLogo viewBox="0 0 24 24" title="Build Pyramid">
  <Rect x="3" y="16" width="18" height="4.5" rx="1.2" fill="brand-soft" stroke="ink" strokeWidth="1.4" />
  <Rect x="6" y="10.5" width="12" height="4.5" rx="1.2" fill="brand" stroke="ink" strokeWidth="1.4" animate="float" animateDelay="0.15" />
  <Rect x="9" y="5" width="6" height="4.5" rx="1.2" fill="brand-strong" stroke="ink" strokeWidth="1.4" animate="float" animateDelay="0.3" />
</ActionLogo>
""",
    # An eye over a smooth ramp: contrast stretched linearly.
    "rescale_channel": """
<ActionLogo viewBox="0 0 24 24" title="Show Normalized">
  <Defs>
    <LinearGradient id="ramp" x1="0" y1="0" x2="1" y2="0">
      <Stop offset="0" stopColor="surface" />
      <Stop offset="1" stopColor="brand-strong" />
    </LinearGradient>
  </Defs>
  <Path d="M2.5 9.5C5 5.5 8.3 3.5 12 3.5s7 2 9.5 6c-2.5 4-5.8 6-9.5 6s-7-2-9.5-6Z" fill="surface" stroke="ink" strokeWidth="1.6" strokeLinejoin="round" />
  <Circle cx="12" cy="9.5" r="3.2" fill="brand" animate="pulse" />
  <Circle cx="12" cy="9.5" r="1.3" fill="ink" />
  <Rect x="3" y="17.5" width="18" height="3.5" rx="1.75" fill="url(#ramp)" stroke="ink" strokeWidth="1.2" />
</ActionLogo>
""",
    # An eye over a stepped ramp: contrast in perceptually even steps.
    "rescale_channel_perceptually": """
<ActionLogo viewBox="0 0 24 24" title="Show Perceptually">
  <Path d="M2.5 9.5C5 5.5 8.3 3.5 12 3.5s7 2 9.5 6c-2.5 4-5.8 6-9.5 6s-7-2-9.5-6Z" fill="surface" stroke="ink" strokeWidth="1.6" strokeLinejoin="round" />
  <Circle cx="12" cy="9.5" r="3.2" fill="brand-strong" animate="pulse" />
  <Circle cx="12" cy="9.5" r="1.3" fill="ink" />
  <Rect x="3" y="17.5" width="4.5" height="3.5" rx="1" fill="brand-soft" />
  <Rect x="7.5" y="17.5" width="4.5" height="3.5" fill="brand" />
  <Rect x="12" y="17.5" width="4.5" height="3.5" fill="brand-strong" />
  <Rect x="16.5" y="17.5" width="4.5" height="3.5" rx="1" fill="ink" />
  <Rect x="3" y="17.5" width="18" height="3.5" rx="1" fill="none" stroke="ink" strokeWidth="1.2" />
</ActionLogo>
""",
    # Scattered objects, and a box around the dense ones.
    "mark_clusters_of_size_rectangle": """
<ActionLogo viewBox="0 0 24 24" title="Mark Clusters">
  <G fill="muted">
    <Circle cx="4" cy="5" r="1.3" />
    <Circle cx="19.5" cy="4" r="1.3" />
    <Circle cx="4.5" cy="19.5" r="1.3" />
    <Circle cx="20" cy="19.5" r="1.3" />
    <Circle cx="20" cy="11.5" r="1.3" />
  </G>
  <G fill="brand">
    <Circle cx="10" cy="10" r="1.4" />
    <Circle cx="13.5" cy="9.5" r="1.4" />
    <Circle cx="11.25" cy="13" r="1.4" />
    <Circle cx="14.25" cy="13.5" r="1.4" />
  </G>
  <Rect x="7" y="7" width="10" height="9.5" rx="1.5" fill="none" stroke="brand-strong" strokeWidth="1.4" strokeDasharray="2 1" animate="march" />
</ActionLogo>
""",
}


def logo_of(action: str) -> str:
    """The name of the action logo blok that draws ``action`` (its function's name)."""
    if action not in ACTION_LOGOS:
        raise KeyError(f"No logo is drawn for the action {action!r}")
    return f"{APP}_{action}"


def declare_logos(app: App) -> None:
    """Declares the app's logo, as its default, and every action logo."""
    app.blok(
        APP_LOGO,
        APP_LOGO_SOURCE,
        description="Four building blocks: a histogram, a binarized disc, a pyramid and a stack of slices.",
        default=True,
    )
    for action, source in ACTION_LOGOS.items():
        app.blok(logo_of(action), source)
