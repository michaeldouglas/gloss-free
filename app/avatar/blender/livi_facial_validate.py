"""Geometry/driver checks for the delivered Livi rig, runnable via Blender MCP."""

import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CONTROL = "Livi_CONTROLES_FACIAIS"
POSES = {
    "neutro": {}, "fechados": {"piscar": 1}, "meio_piscar": {"piscar": .5},
    "piscar_esquerdo": {"piscar_esquerdo": 1}, "piscar_direito": {"piscar_direito": 1},
    "cima": {"olhar_vertical": 1}, "baixo": {"olhar_vertical": -1},
    "esquerda": {"olhar_horizontal": -1}, "direita": {"olhar_horizontal": 1},
    "convergencia": {"convergencia": 1}, "olhos_abertos": {"abrir_olhos": 1},
    "sobrancelhas_altas": {"sobrancelha_esquerda": 1, "sobrancelha_direita": 1},
    "sobrancelhas_baixas": {"sobrancelha_esquerda": -1, "sobrancelha_direita": -1},
    "franzir": {"franzir_sobrancelhas": 1}, "internas": {"sobrancelhas_internas": 1},
    "boca": {"abrir_boca": 1}, "meia_boca": {"abrir_boca": .5},
    "cabeca_cima": {"cabeca_vertical": 1}, "cabeca_baixo": {"cabeca_vertical": -1},
    "cabeca_esquerda": {"cabeca_horizontal": -1}, "cabeca_direita": {"cabeca_horizontal": 1},
    "cabeca_inclinada": {"cabeca_inclinar": 1},
    "combinado": {"piscar": 1, "olhar_horizontal": 1, "olhar_vertical": 1,
                  "sobrancelha_esquerda": 1, "sobrancelha_direita": -1, "abrir_boca": 1},
}


def set_pose(values):
    ctrl = bpy.data.objects[CONTROL]
    for key in list(ctrl.keys()):
        if isinstance(ctrl[key], (int, float)):
            ctrl[key] = float(values.get(key, 0))
    ctrl.update_tag()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("Livi_"):
            obj.update_tag()
            if obj.type in {"MESH", "CURVE"} and obj.data.shape_keys:
                obj.data.shape_keys.update_tag()
    bpy.context.view_layer.update()


def evaluated_head():
    obj = bpy.data.objects["Livi_Head_Base"].evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    positions = np.empty(len(mesh.vertices)*3)
    mesh.vertices.foreach_get("co", positions)
    positions = positions.reshape(-1, 3)
    faces = [list(face.vertices) for face in mesh.polygons]
    obj.to_mesh_clear()
    return positions, faces


def eye_occlusion(points, faces, stem):
    """Check that the closed head surface hides sampled eye surfaces frontally."""
    head = bpy.data.objects["Livi_Head_Base"]
    world = [head.matrix_world@Vector(p) for p in points]
    bvh = BVHTree.FromPolygons(world, faces)
    result = {}
    for side in ["L", "R"]:
        iris = bpy.data.objects[stem+side]
        visible = 0
        samples = list(iris.data.vertices)[::31]
        for vertex in samples:
            point = iris.matrix_world@vertex.co
            origin = Vector((point.x, -5, point.z))
            hit, _, _, _ = bvh.ray_cast(origin, Vector((0,1,0)))
            if hit is None or hit.y > point.y+.0005:
                visible += 1
        result[side] = {"samples": len(samples), "visible_samples": visible}
    return result


def validate():
    ctrl = bpy.data.objects[CONTROL]
    original = {key: value for key, value in ctrl.items() if isinstance(value, (int, float))}
    report = {"blender": bpy.app.version_string, "poses": {}, "invalid_drivers": []}
    try:
        set_pose({})
        neutral, faces = evaluated_head()
        for name, values in POSES.items():
            set_pose(values)
            points, pose_faces = evaluated_head()
            assert np.isfinite(points).all(), name+": non-finite vertices"
            assert len(points) == len(neutral) and len(pose_faces) == len(faces)
            head_change = float(np.linalg.norm(points-neutral, axis=1).max())
            pivots = {side: list(bpy.data.objects["Livi_Pivo_Olho_"+side].rotation_euler)
                      for side in ["L", "R"]}
            report["poses"][name] = {"max_head_delta": head_change, "eye_rotations": pivots}
            if name in {"fechados", "combinado"}:
                report["poses"][name]["occlusion"] = {
                    "iris": eye_occlusion(points, faces, "Livi_Iris_Fibras_3D_"),
                    "cornea": eye_occlusion(points, faces, "Livi_Cornea_Reflexo_3D_")}
        for datablock in list(bpy.data.objects)+list(bpy.data.shape_keys)+list(bpy.data.node_groups):
            if datablock.animation_data:
                for curve in datablock.animation_data.drivers:
                    if not curve.driver.is_valid:
                        report["invalid_drivers"].append(datablock.name+":"+curve.data_path)
        set_pose({})
        recovered, _ = evaluated_head()
        report["neutral_return_error"] = float(np.abs(recovered-neutral).max())
        report["head_vertices"] = len(bpy.data.objects["Livi_Head_Base"].data.vertices)
        report["head_polygons"] = len(bpy.data.objects["Livi_Head_Base"].data.polygons)
        report["head_evaluated_vertices"] = len(neutral)
        assert not report["invalid_drivers"], report["invalid_drivers"]
        assert report["neutral_return_error"] < 1e-6
        for name in ["fechados", "piscar_esquerdo", "piscar_direito", "sobrancelhas_altas", "boca"]:
            assert report["poses"][name]["max_head_delta"] > .01, name+": no deformation"
        for side in ["L", "R"]:
            assert report["poses"]["cima"]["eye_rotations"][side][0] < 0
            assert report["poses"]["baixo"]["eye_rotations"][side][0] > 0
            assert report["poses"]["esquerda"]["eye_rotations"][side][2] > 0
            assert report["poses"]["direita"]["eye_rotations"][side][2] < 0
            for name in ["fechados", "combinado"]:
                for surface in ["iris", "cornea"]:
                    assert report["poses"][name]["occlusion"][surface][side]["visible_samples"] == 0
        report["status"] = "passed"
        return report
    finally:
        set_pose(original)


if __name__ == "__main__":
    result = validate()
