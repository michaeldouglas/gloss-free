"""Render one facial inspection image while restoring production settings."""

from pathlib import Path

import bpy
from mathutils import Vector


def render_preview(name, values, folder, angle=0):
    validator = bpy.data.texts.get("livi_facial_validate.py")
    if validator:
        code = validator.as_string()
    else:
        code = (Path(__file__).parent/"livi_facial_validate.py").read_text(encoding="utf-8")
    namespace = {"__name__": "livi_validation"}
    exec(compile(code, "livi_facial_validate.py", "exec"), namespace)
    scene = bpy.context.scene
    camera = scene.camera
    ctrl = bpy.data.objects["Livi_CONTROLES_FACIAIS"]
    original_pose = {key: value for key, value in ctrl.items() if isinstance(value, (int, float))}
    camera_matrix = camera.matrix_world.copy()
    camera_type, camera_scale = camera.data.type, camera.data.ortho_scale
    render = scene.render
    previous = {key: getattr(render, key) for key in
                ["resolution_x", "resolution_y", "resolution_percentage", "filepath"]}
    media, fmt = render.image_settings.media_type, render.image_settings.file_format
    samples = scene.cycles.samples
    try:
        namespace["set_pose"](values)
        camera.location = (angle, -8, .25)
        camera.rotation_euler = (Vector((0, -.15, .15))-camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = 2.85
        render.resolution_x, render.resolution_y = 512, 640
        render.resolution_percentage = 100
        render.image_settings.media_type = "IMAGE"
        render.image_settings.file_format = "PNG"
        scene.cycles.samples = 16
        output = Path(folder)/(name+".png")
        output.parent.mkdir(parents=True, exist_ok=True)
        render.filepath = str(output)
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        return {"preview": str(output), "pose": values}
    finally:
        camera.matrix_world = camera_matrix
        camera.data.type, camera.data.ortho_scale = camera_type, camera_scale
        for key, value in previous.items():
            setattr(render, key, value)
        render.image_settings.media_type = media
        render.image_settings.file_format = fmt
        scene.cycles.samples = samples
        namespace["set_pose"](original_pose)
