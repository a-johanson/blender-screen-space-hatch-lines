import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, PointerProperty, EnumProperty


def get_gp_layers(props, _context):
    items = []
    if props.target_gp and props.target_gp.type == "GREASEPENCIL":
        layers = props.target_gp.data.layers
        items = [(layer.name, layer.name, f"Use layer: {layer.name}") for layer in layers]

        if not items:
            items = [("", "No Layers Found", "The selected Grease Pencil has no layers")]
    else:
        items = [("", "Select Grease Pencil", "First select a Grease Pencil object")]
    return items


class HatchLineProperties(bpy.types.PropertyGroup):
    # General Settings
    technique: EnumProperty(
        name="Technique",
        description="Select which technique to use",
        items=[
            ("HATCHING", "Hatching", "Use hatching technique"),
            ("STIPPLING", "Stippling & Scribbling", "Use stippling and scribbling technique")
        ],
        default="HATCHING"
    )

    rng_seed: IntProperty(
        name="RNG Seed",
        description="Seed value for placing seed points",
        default=42,
        min=1
    )

    seed_box_size_factor: FloatProperty(
        name="Seed Box Size Factor",
        description="Factor to determine the size of the seed box based on separation distance",
        default=1.9,
        min=0.01,
        max=100.0
    )

    render_resolution: IntProperty(
        name="Render Resolution",
        description="Resolution of the longest render dimension for generating hatch lines",
        default=1000,
        min=100,
        max=10000
    )

    render_engine: EnumProperty(
        name="Render Engine",
        description="Select which rendering engine to use",
        items=[
            ("BLENDER", "Blender", "Use Blender's render engine"),
            ("SHADER", "GLSL Shader", "Use shader-based rendering")
        ],
        default="SHADER"
    )

    clip_luminance: BoolProperty(
        name="Clip Luminance",
        description="Clip luminance values to the range [0, 1]",
        default=False
    )

    normalize_luminance: BoolProperty(
        name="Normalize Luminance",
        description="Normalize luminance values to the range [0, 1]",
        default=False
    )

    # Lighting and Orientation
    input_light: PointerProperty(
        type=bpy.types.Object,
        name="Empty or Light",
        description="Empty or Light object to use as input for lighting",
        poll=lambda _props, obj: obj.type in ["EMPTY", "LIGHT"]
    )

    is_directional_light: BoolProperty(
        name="Directional Light",
        description="Use this empty as a directional light source",
        default=True
    )

    orientation_offset: FloatProperty(
        name="Orientation Offset [rad]",
        description="Offset for the orientation of the hatch lines",
        default=0.0,
        min=-1.57079632679,
        max=1.57079632679 
    )

    # Target Grease Pencil
    target_gp: PointerProperty(
        type=bpy.types.Object,
        name="Target Grease Pencil",
        description="Grease Pencil object to add hatch lines to (v3 only)",
        poll=lambda _props, obj: obj.type == "GREASEPENCIL"
    )

    target_gp_layer: EnumProperty(
        name="Target Layer",
        description="Grease Pencil layer to add hatch lines to",
        items=get_gp_layers
    )

    clear_layer: BoolProperty(
        name="Clear Layer",
        description="Clear the target layer before adding new hatch lines",
        default=True
    )

    gp_stroke_distance: FloatProperty(
        name="Stroke Distance [world units]",
        description="Distance from the camera at which the grease pencil strokes are drawn",
        default=1.0,
        min=0.5,
        max=10.0
    )

    gp_stroke_radius: FloatProperty(
        name="Stroke Radius [world units]",
        description="Radius of the grease pencil strokes",
        default=0.0005,
        min=0.0005,
        max=0.05
    )

    # Hatch Line Settings
    d_sep: FloatProperty(
        name="Separation Distance [px]",
        description="Distance between hatch lines",
        default=10.0,
        min=0.1,
        max=250.0
    )

    d_sep_shadow_factor: FloatProperty(
        name="Separation Shadow Factor",
        description="Factor to reduce the separation distance for shadows",
        default=1.0,
        min=0.01,
        max=1.0
    )

    gamma_hatching: FloatProperty(
        name="Luminance Gamma",
        description="Gamma exponent for transforming luminance values",
        default=1.0,
        min=0.1,
        max=10.0
    )

    d_test_factor: FloatProperty(
        name="Separation Reduction Factor",
        description="Factor to reduce the separation distance for testing",
        default=0.75,
        min=0.01,
        max=1.0
    )

    d_step: FloatProperty(
        name="Step Size [px]",
        description="Step size for generating hatch lines",
        default=1.0,
        min=0.1,
        max=25.0
    )

    max_steps: IntProperty(
        name="Max. Steps",
        description="Maximum number of steps per hatch line",
        default=100,
        min=1,
        max=10000
    )

    min_steps: IntProperty(
        name="Min. Steps",
        description="Minimum number of steps per hatch line",
        default=10,
        min=1,
        max=10000
    )

    line_simplification_error_hatching: FloatProperty(
        name="Max. Line Simplification Error [px^2]",
        description="Maximum error allowed when simplifying hatch lines",
        default=0.02,
        min=0.0001,
        max=10.0
    )

    max_depth_step: FloatProperty(
        name="Max. Depth Step [world units]",
        description="Maximum depth step for hatch lines",
        default=0.05,
        min=0.0001,
        max=10.0
    )

    max_accum_angle: FloatProperty(
        name="Max. Accumulated angle [rad]",
        description="Maximum accumulated angle for hatch lines",
        default=5.0,
        min=0.1,
        max=10.0
    )

    max_hatched_luminance: FloatProperty(
        name="Max. Hatched Luminance",
        description="Maximum luminance value that will receive hatching",
        default=10.0,
        min=0.0,
        max=10.0
    )

    crosshatching_enabled: BoolProperty(
        name="Enable Crosshatching",
        description="Add a second set of hatch lines crossing the primary set",
        default=False
    )

    crossing_orientation_offset: FloatProperty(
        name="Crossing Lines Offset [rad]",
        description="Additional orientation offset for the crossing hatch lines",
        default=0.78539816339,
        min=-0.78539816339,
        max=0.78539816339
    )

    max_crosshatched_luminance: FloatProperty(
        name="Max. Crosshatched Luminance",
        description="Maximum luminance value that will receive crosshatching",
        default=10.0,
        min=0.0,
        max=10.0
    )

    # Stipple Settings
    max_radius: FloatProperty(
        name="Max. Radius [px]",
        description="Maximum exclusion radius for stipples",
        default=15.0,
        min=0.5,
        max=200.0
    )

    min_radius: FloatProperty(
        name="Min. Radius [px]",
        description="Minimum exclusion radius for stipples",
        default=3.0,
        min=0.5,
        max=200.0
    )

    child_count: IntProperty(
        name="Child Count",
        description="Number of child stipples to create",
        default=30,
        min=1,
        max=100
    )

    gamma_stippling: FloatProperty(
        name="Luminance Gamma",
        description="Gamma exponent for transforming luminance values",
        default=1.0,
        min=0.1,
        max=10.0
    )

    max_stippled_luminance: FloatProperty(
        name="Max. Stippled Luminance",
        description="Maximum luminance value that will receive stippling",
        default=1.0,
        min=0.0,
        max=10.0
    )

    stroke_length: FloatProperty(
        name="Stroke Length [px]",
        description="Stroke length for stipples (0.0 for dots)",
        default=0.0,
        min=0.0,
        max=100.0
    )

    # Scribble Settings
    scribbling_enabled: BoolProperty(
        name="Scribble",
        description="Use stipples for scribbling",
        default=False
    )

    scribbling_iterations: IntProperty(
        name="Scribbling Iterations",
        description="Number of iterations for scribbling",
        default=2,
        min=1,
        max=25
    )

    initial_sub_sampling_rate: IntProperty(
        name="Initial Sub-Sampling Rate",
        description="Initial sub-sampling rate for scribbles",
        default=50,
        min=1,
        max=100
    )

    min_remaining_point_share: FloatProperty(
        name="Min. Remaining Point Share",
        description="Minimum share of points to retain in scribbles",
        default=0.01,
        min=0.0,
        max=1.0
    )

    depth_factor: FloatProperty(
        name="Depth Factor",
        description="Factor to adjust depth influence in scribbles",
        default=100.0,
        min=0.0,
        max=1.0e6
    )

    bezier_points_per_segment: IntProperty(
        name="Bezier Points per Segment",
        description="Number of points per segment for Catmull-Rom interpolation",
        default=10,
        min=2,
        max=100
    )

    line_simplification_error_scribbling: FloatProperty(
        name="Max. Line Simplification Error [px^2]",
        description="Maximum error allowed when simplifying scribble lines",
        default=0.05,
        min=0.0001,
        max=10.0
    )


class HATCH_PT_panel(bpy.types.Panel):
    bl_label = "Screen-Space Shading"
    bl_idname = "HATCH_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Screen-Space Shading"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        hatch_props = scene.hatch_line_props

        box = layout.box()
        box.label(text="General Settings:")
        box.prop(hatch_props, "rng_seed")
        box.prop(hatch_props, "seed_box_size_factor")
        box.prop(hatch_props, "render_resolution")
        box.prop(hatch_props, "render_engine")
        if hatch_props.render_engine == "BLENDER":
            box.label(text="Warning: Will overwrite compositor nodes.", icon="ERROR")
            box.prop(hatch_props, "clip_luminance")
            box.prop(hatch_props, "normalize_luminance")

        box = layout.box()
        box.label(text="Lighting and Orientation:")
        box.prop(hatch_props, "input_light")
        box.prop(hatch_props, "is_directional_light")
        box.prop(hatch_props, "orientation_offset")

        box = layout.box()
        box.label(text="Target Grease Pencil:")
        box.prop(hatch_props, "target_gp")

        # Only show layer selection when a GP object is selected
        if hatch_props.target_gp and hatch_props.target_gp.type == "GREASEPENCIL":
            has_layers = len(hatch_props.target_gp.data.layers) > 0
            box.prop(hatch_props, "target_gp_layer")
            if not has_layers:
                box.label(text="No layers found in this Grease Pencil", icon="ERROR")
            else:
                box.prop(hatch_props, "clear_layer")

        box.prop(hatch_props, "gp_stroke_distance")
        box.prop(hatch_props, "gp_stroke_radius")

        # Technique selection
        box = layout.box()
        box.label(text="Shading Settings:")
        box.prop(hatch_props, "technique")
        if hatch_props.technique == "HATCHING":
            box.prop(hatch_props, "d_sep")
            box.prop(hatch_props, "d_sep_shadow_factor")
            box.prop(hatch_props, "gamma_hatching")
            box.prop(hatch_props, "d_test_factor")
            box.prop(hatch_props, "d_step")
            box.prop(hatch_props, "max_steps")
            box.prop(hatch_props, "min_steps")
            box.prop(hatch_props, "line_simplification_error_hatching")
            box.prop(hatch_props, "max_depth_step")
            box.prop(hatch_props, "max_accum_angle")
            box.prop(hatch_props, "max_hatched_luminance")
            box.prop(hatch_props, "crosshatching_enabled")
            if hatch_props.crosshatching_enabled:
                box.prop(hatch_props, "crossing_orientation_offset")
                box.prop(hatch_props, "max_crosshatched_luminance")
        elif hatch_props.technique == "STIPPLING":
            box.prop(hatch_props, "max_radius")
            box.prop(hatch_props, "min_radius")
            box.prop(hatch_props, "child_count")
            box.prop(hatch_props, "gamma_stippling")
            box.prop(hatch_props, "max_stippled_luminance")
            box.prop(hatch_props, "stroke_length")
            box.prop(hatch_props, "scribbling_enabled")
            if hatch_props.scribbling_enabled:
                box.prop(hatch_props, "scribbling_iterations")
                box.prop(hatch_props, "initial_sub_sampling_rate")
                box.prop(hatch_props, "min_remaining_point_share")
                box.prop(hatch_props, "depth_factor")
                box.prop(hatch_props, "bezier_points_per_segment")
                box.prop(hatch_props, "line_simplification_error_scribbling")

        layout.separator()
        layout.operator("hatch.generate", text="Generate")


classes = (
    HatchLineProperties,
    HATCH_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hatch_line_props = PointerProperty(type=HatchLineProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.hatch_line_props
