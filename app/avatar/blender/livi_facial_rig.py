"""Build Livi's editable facial controls in the inspected Blender scene.

Run through Blender MCP, with this file's path as __file__. Never saves over
the .blend automatically. Existing artistic keys and neutral geometry survive.
The first build needs the original MakeHuman source in the local asset cache;
the vertex correspondence is then stored in the head mesh for reproducibility.
"""

import hashlib
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT = Path(globals().get("__file__", bpy.data.filepath)).resolve().parent
ASSETS = ROOT / "assets" / "faceunits"
SOURCE_COMMIT = "7eaba3453134385bb5ea9811ef0b33b85b4b556d"
CONTROL = "Livi_CONTROLES_FACIAIS"
PREFIX = "Livi_Facial_"
PROPS = {
    "piscar": (0, 1, "0 = olhos abertos; 1 = ambos fechados"),
    "piscar_esquerdo": (0, 1, "Fechamento independente do olho esquerdo da Livi"),
    "piscar_direito": (0, 1, "Fechamento independente do olho direito da Livi"),
    "abrir_olhos": (0, 1, "Aumenta a abertura das palpebras; piscar tem prioridade"),
    "olhar_horizontal": (-1, 1, "-1 = esquerda da Livi; +1 = direita da Livi"),
    "olhar_vertical": (-1, 1, "-1 = baixo; +1 = cima"),
    "convergencia": (0, 1, "Convergencia dos olhos para um ponto proximo"),
    "sobrancelha_esquerda": (-1, 1, "-1 = baixar; +1 = levantar sobrancelha esquerda"),
    "sobrancelha_direita": (-1, 1, "-1 = baixar; +1 = levantar sobrancelha direita"),
    "franzir_sobrancelhas": (0, 1, "Baixa e aproxima a parte interna de ambas"),
    "sobrancelhas_internas": (0, 1, "Levanta a parte interna das sobrancelhas"),
    "abrir_boca": (0, 1, "Abertura gradual da mandibula e dos labios"),
    "cabeca_horizontal": (-1, 1, "-1 = virar a esquerda; +1 = virar a direita"),
    "cabeca_vertical": (-1, 1, "-1 = baixar; +1 = levantar a cabeca"),
    "cabeca_inclinar": (-1, 1, "Inclinacao lateral da cabeca"),
}


def coordinates(data):
    values = np.empty(len(data) * 3, dtype=np.float64)
    data.foreach_get("co", values)
    return values.reshape(-1, 3)


def neutral_coordinates(head):
    keys = head.data.shape_keys
    points = coordinates(keys.reference_key.data)
    for key in keys.key_blocks[1:]:
        if not key.name.startswith(PREFIX):
            points += key.value * (coordinates(key.data) - coordinates(key.relative_key.data))
    return points


def source_mapping(head):
    attribute = head.data.attributes.get("Livi_MakeHuman_Vertex_ID")
    if attribute:
        return [item.value for item in attribute.data]
    cached = bpy.app.driver_namespace.get("livi_rig_source")
    if not cached:
        raise RuntimeError("Load and verify MakeHuman vertex correspondence before the first build.")
    ids = cached["ids"]
    assert len(ids) == len(head.data.vertices)
    attribute = head.data.attributes.new("Livi_MakeHuman_Vertex_ID", "INT", "POINT")
    attribute.data.foreach_set("value", ids)
    return ids


def load_targets(ids):
    lookup = {source: local for local, source in enumerate(ids)}
    targets = {}
    paths = sorted(ASSETS.glob("*.target"))
    sources = {path.stem: path.read_text(encoding="utf-8") for path in paths}
    if not sources:
        prefix = "Livi_Facial_Target_"
        sources = {text.name[len(prefix):-7]: text.as_string()
                   for text in bpy.data.texts
                   if text.name.startswith(prefix) and text.name.endswith(".target")}
    assert len(sources) == 10, "The ten facial source targets must be available."
    import io
    for name, body in sources.items():
        delta = np.zeros((len(ids), 3))
        for row in np.loadtxt(io.StringIO(body), ndmin=2):
            local = lookup.get(int(row[0]))
            if local is not None:
                delta[local] = (row[1] * 1.45, -row[3] * 1.10, row[2] * 1.40)
        targets[name] = delta
    return targets


def driver(owner, path, expression, variables, index=None):
    curve = owner.driver_add(path) if index is None else owner.driver_add(path, index)
    d = curve.driver
    d.type = "SCRIPTED"
    while d.variables:
        d.variables.remove(d.variables[0])
    for name, (target, target_path) in variables.items():
        var = d.variables.new()
        var.name = name
        var.type = "SINGLE_PROP"
        var.targets[0].id = target
        var.targets[0].data_path = target_path
    d.expression = expression
    return curve


def control_variables(ctrl, **names):
    return {name: (ctrl, '["' + prop + '"]') for name, prop in names.items()}


def add_key(obj, name, delta, reference=None):
    if not obj.data.shape_keys:
        obj.shape_key_add(name="Basis")
    reference = reference or obj.data.shape_keys.reference_key
    key = obj.data.shape_keys.key_blocks.get(name)
    if key is None:
        key = obj.shape_key_add(name=name, from_mix=False)
    key.relative_key = reference
    key.data.foreach_set("co", (coordinates(reference.data) + delta).ravel())
    key.slider_min = 0
    key.slider_max = 1
    key.value = 0
    return key


def eye_parameters(side):
    eye = bpy.data.objects["Livi_Olho_Anatomico_" + side]
    points = coordinates(eye.data.vertices)
    center = (points.min(0) + points.max(0)) * 0.5
    radii = (points.max(0) - points.min(0)) * 0.5
    return center, radii


def fit_blinks(neutral, targets):
    """Correct MakeHuman closure for Livi's enlarged, sculpted eye sockets."""
    lower_ids = [2280, 2261, 2258, 2255, 2252, 2249, 2244, 2241, 2238, 2235, 2232]
    rim = neutral[lower_ids]
    order = np.argsort(rim[:, 0])
    rim = rim[order]
    for side, suffix, sign in [("L", "Left", 1), ("R", "Right", -1)]:
        center, radii = eye_parameters(side)
        key = "eyeBlink" + suffix
        delta = targets[key].copy()
        x = neutral[:, 0] * sign
        # Keep the tear duct and outer corner in place during closure.
        delta[:, 0] = 0
        upper = delta[:, 2] < -0.006
        delta[upper, 2] *= 1.16
        lower_z = np.interp(x, rim[:, 0], rim[:, 2])
        lower_weight = np.exp(-((neutral[:, 2] - lower_z) / .055) ** 2)
        lower_weight *= np.clip((x-.17)/.06, 0, 1) * np.clip((.66-x)/.05, 0, 1)
        lower_weight *= np.clip((-neutral[:, 1]-.65)/.10, 0, 1)
        lower_weight[upper] = 0
        delta[:, 2] += .017 * lower_weight
        full = neutral + delta
        active = (np.abs(delta[:, 2]) > .002) & (neutral[:, 1] < -.65)
        active &= (x > .155) & (x < .68) & (neutral[:, 2] > .12) & (neutral[:, 2] < .55)
        def project(points):
            r2 = ((points[:, 0]-center[0])/radii[0])**2 + ((points[:, 2]-center[2])/radii[2])**2
            surface_y = center[1]-radii[1]*np.sqrt(np.maximum(0, 1-r2))-.045
            mask = active & (r2 < 1)
            points[mask, 1] = np.minimum(points[mask, 1], surface_y[mask])
            return points
        full = project(full)
        cover = np.exp(-((full[:, 0]-center[0])/.20)**4-((full[:, 2]-center[2])/.17)**4)
        cover *= np.clip((-neutral[:, 1]-.62)/.10, 0, 1)
        full[:, 1] -= .028*cover
        targets[key] = full-neutral
        half_linear = (neutral+full)*.5
        half = project(half_linear.copy())
        targets["blinkArc"+suffix] = half-half_linear


def make_controls(collection):
    ctrl = bpy.data.objects.get(CONTROL)
    if ctrl is None:
        ctrl = bpy.data.objects.new(CONTROL, None)
        collection.objects.link(ctrl)
        ctrl.empty_display_type = "CUBE"
        ctrl.empty_display_size = 0.16
        ctrl.location = (-1.7, -0.9, 0.7)
    for name, (low, high, description) in PROPS.items():
        if name not in ctrl:
            ctrl[name] = 0.0
        ctrl.id_properties_ui(name).update(min=float(low), max=float(high),
                                           soft_min=float(low), soft_max=float(high),
                                           default=0.0, description=description)
    ctrl["rig_version"] = "1.0"
    return ctrl


def build_head_keys(head, ctrl, targets):
    bindings = {}
    for side, suffix in [("Left", "esquerdo"), ("Right", "direito")]:
        blink = f"min(1,max(0,b)+max(0,s))"
        variables = control_variables(ctrl, b="piscar", s="piscar_" + suffix)
        bindings["eyeBlink" + side] = (blink, variables)
        bindings["blinkArc" + side] = (f"4*({blink})*(1-({blink}))", variables)
        for direction, sign in [("Up", 1), ("Down", -1)]:
            bindings["gazeLid"+direction+side] = (
                f"max(0,{sign}*v)*(1-min(1,max(0,b)+max(0,s)))*(1-w)",
                control_variables(ctrl, v="olhar_vertical", b="piscar", s="piscar_"+suffix, w="abrir_olhos"))
        bindings["eyeWide" + side] = (
            "max(0,w)*(1-min(1,max(0,b)+max(0,s)))",
            control_variables(ctrl, w="abrir_olhos", b="piscar", s="piscar_" + suffix))
        brow_prop = "sobrancelha_" + ("esquerda" if side == "Left" else "direita")
        bindings["browOuterUp" + side] = ("max(0,b)", control_variables(ctrl, b=brow_prop))
        bindings["browDown" + side] = (
            "min(1,max(0,-b)+f)", control_variables(ctrl, b=brow_prop, f="franzir_sobrancelhas"))
    bindings["browInnerUp"] = ("min(1,max(0,i)+0.45*(max(0,l)+max(0,r)))",
                               control_variables(ctrl, i="sobrancelhas_internas",
                                                 l="sobrancelha_esquerda", r="sobrancelha_direita"))
    bindings["jawOpen"] = ("min(1,max(0,j))", control_variables(ctrl, j="abrir_boca"))
    for name, delta in targets.items():
        key = add_key(head, PREFIX + name, delta)
        expression, variables = bindings[name]
        driver(key, "value", expression, variables)
    head.data.update()
    return bindings


def sample_weights(points, neutral, count=4):
    tree = KDTree(len(neutral))
    for i, point in enumerate(neutral):
        tree.insert(point, i)
    tree.balance()
    indices, weights = [], []
    for point in points:
        nearest = tree.find_n(point, count)
        indices.append([item[1] for item in nearest])
        w = 1 / np.maximum([item[2] for item in nearest], .001) ** 3
        weights.append(w / w.sum())
    return np.asarray(indices), np.asarray(weights)


def build_brows(head, ctrl, neutral, targets, bindings):
    for side in ["L", "R"]:
        obj = bpy.data.objects["Livi_Sobrancelha_Fios_Anatomicos_"+side]
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")
        basis = coordinates(obj.data.shape_keys.reference_key.data)
        indices, weights = sample_weights(basis, neutral)
        for name, delta in targets.items():
            if not name.startswith("brow"):
                continue
            displacement = (delta[indices]*weights[:, :, None]).sum(1)
            key = add_key(obj, PREFIX+name, displacement)
            driver(key, "value", *bindings[name])


def build_lashes(head, ctrl, neutral, targets, bindings):
    for side, suffix in [("L", "Left"), ("R", "Right")]:
        full_bvh = BVHTree.FromPolygons(neutral+targets["eyeBlink"+suffix],
                                       [list(f.vertices) for f in head.data.polygons])
        lower_rim = neutral[[2280,2261,2258,2255,2252,2249,2244,2241,2238,2235,2232]]
        lower_rim = lower_rim[np.argsort(lower_rim[:, 0])]
        for level in ["Superior", "Inferior"]:
            obj = bpy.data.objects[f"Livi_Cilios_Anatomicos_{level}_{side}_Fios_Nativos"]
            data = obj.data
            positions = np.empty(len(data.attributes["position"].data)*3, dtype=np.float32)
            data.attributes["position"].data.foreach_get("vector", positions)
            positions = positions.reshape(-1, 3)
            starts = [curve.first_point_index for curve in data.curves]
            counts = [curve.points_length for curve in data.curves]
            roots = positions[starts]
            indices, weights = sample_weights(roots, neutral, 3)
            node_name = PREFIX+"Cilios_"+level+"_"+side
            group = bpy.data.node_groups.get(node_name)
            if group is None:
                group = bpy.data.node_groups.new(node_name, "GeometryNodeTree")
                group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
                group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
            group.nodes.clear()
            inp = group.nodes.new("NodeGroupInput")
            out = group.nodes.new("NodeGroupOutput")
            current = inp.outputs["Geometry"]
            for name in ["eyeBlink"+suffix, "blinkArc"+suffix, "eyeWide"+suffix,
                         "gazeLidUp"+suffix, "gazeLidDown"+suffix]:
                root_delta = (targets[name][indices]*weights[:, :, None]).sum(1)
                if name.startswith("eyeBlink"):
                    # All roots meet the same eyelid seam; interpolating nearest
                    # vertices alone mixes inner-socket and outer-lid weights.
                    seam = np.interp(np.abs(roots[:, 0]), lower_rim[:, 0], lower_rim[:, 2])+.014
                    for i, root in enumerate(roots):
                        z = seam[i] if level == "Superior" else seam[i]-.006
                        hit, _, _, _ = full_bvh.ray_cast((float(root[0]), -3, float(z)), (0,1,0))
                        y = hit.y-.008 if hit else root[1]+root_delta[i,1]
                        root_delta[i] = (0, y-root[1], z-root[2])
                displacement = np.zeros_like(positions)
                for i, (start, count) in enumerate(zip(starts, counts)):
                    displacement[start:start+count] = root_delta[i]
                    if name.startswith("eyeBlink") and level == "Superior":
                        # Fold lash tips with the upper eyelid instead of leaving
                        # them pointing up over the closed eye.
                        offset = positions[start:start+count]-roots[i]
                        angle = 1.30
                        rot = np.array(Matrix.Rotation(angle, 3, "X"))
                        displacement[start:start+count] += offset@rot.T-offset
                attr = data.attributes.get(PREFIX+name)
                if attr is None:
                    attr = data.attributes.new(PREFIX+name, "FLOAT_VECTOR", "POINT")
                attr.data.foreach_set("vector", displacement.ravel())
                named = group.nodes.new("GeometryNodeInputNamedAttribute")
                named.data_type = "FLOAT_VECTOR"
                named.inputs["Name"].default_value = attr.name
                scale = group.nodes.new("ShaderNodeVectorMath")
                scale.operation = "SCALE"
                group.links.new(named.outputs["Attribute"], scale.inputs[0])
                driver(scale.inputs["Scale"], "default_value", *bindings[name])
                set_position = group.nodes.new("GeometryNodeSetPosition")
                group.links.new(current, set_position.inputs["Geometry"])
                group.links.new(scale.outputs["Vector"], set_position.inputs["Offset"])
                current = set_position.outputs["Geometry"]
            group.links.new(current, out.inputs["Geometry"])
            mod = obj.modifiers.get("Livi - palpebras e cilios")
            if mod is None:
                mod = obj.modifiers.new("Livi - palpebras e cilios", "NODES")
            mod.node_group = group
            data.update_tag()


def material(name, color, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat


def build_mouth(head, ctrl, collection, neutral, targets, bindings):
    # The existing MakeHuman head already contains an oral cavity. Find the
    # connected interior behind the lip contour without painting external skin.
    centers = np.array([neutral[list(f.vertices)].mean(0) for f in head.data.polygons])
    x, y, z = centers.T
    candidate = (y > (-.89+.10*(np.abs(x)/.32)**2)) & (np.abs(x) < .6)
    candidate &= (z < -.30) & (z > -1.25) & (y < .6)
    edge_faces = {}
    for face in head.data.polygons:
        for edge in face.edge_keys:
            edge_faces.setdefault(tuple(sorted(edge)), []).append(face.index)
    adjacent = [[] for _ in head.data.polygons]
    for faces in edge_faces.values():
        for face in faces:
            adjacent[face].extend(other for other in faces if other != face)
    seen, todo = set(), [2609]
    while todo:
        face = todo.pop()
        if face in seen or not candidate[face]:
            continue
        seen.add(face)
        todo.extend(adjacent[face])
    assert 200 < len(seen) < 500, "Unexpected oral cavity region."
    inner = material("Livi_Facial_Interior_Boca", (.045, .006, .009), .7)
    if inner.name not in head.data.materials:
        head.data.materials.append(inner)
    slot = list(head.data.materials).index(inner)
    original = head.data.attributes.get("Livi_Material_Antes_Rig")
    if original is None:
        original = head.data.attributes.new("Livi_Material_Antes_Rig", "INT", "FACE")
        original.data.foreach_set("value", [f.material_index for f in head.data.polygons])
    for index in seen:
        head.data.polygons[index].material_index = slot
    enamel = material("Livi_Facial_Esmalte", (.75, .70, .58), .28)
    tongue_mat = material("Livi_Facial_Lingua", (.28, .055, .065), .5)
    for row in ["Superior", "Inferior"]:
        for i, x in enumerate([-.245, -.184, -.118, -.041, .041, .118, .184, .245]):
            name = f"Livi_Dente_{row}_{i+1:02d}"
            obj = bpy.data.objects.get(name)
            if obj is None:
                width = .075 if abs(x) < .09 else (.064 if abs(x) < .2 else .049)
                y = (-.855 if row == "Superior" else -.755)+.12*(abs(x)/.28)**1.6
                z = (-.545 if row == "Superior" else -.570)-.025*(abs(x)/.28)
                height = .115 if row == "Superior" else .085
                vertices = [(x+dx*width/2, y+dy*.045, z+dz*height/2)
                            for dx, dy, dz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                                              (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
                faces = [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
                mesh = bpy.data.meshes.new(name)
                mesh.from_pydata(vertices, [], faces)
                mesh.materials.append(enamel)
                obj = bpy.data.objects.new(name, mesh)
                collection.objects.link(obj)
                obj.parent = head
                bevel = obj.modifiers.new("Bordas suaves", "BEVEL")
                bevel.width = .009
                bevel.segments = 3
                for face in mesh.polygons:
                    face.use_smooth = True
            if row == "Inferior":
                points = coordinates(obj.data.vertices)
                delta = np.tile([0, .16, -.35], (len(points), 1))
                key = add_key(obj, PREFIX+"jawOpen", delta)
                driver(key, "value", *bindings["jawOpen"])
    tongue = bpy.data.objects.get("Livi_Lingua_Interior")
    if tongue is None:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(0,0,0))
        tongue = bpy.context.object
        tongue.name = "Livi_Lingua_Interior"
        for col in list(tongue.users_collection):
            col.objects.unlink(tongue)
        collection.objects.link(tongue)
        tongue.parent = head
        points = coordinates(tongue.data.vertices)*np.array([.205,.20,.045])+np.array([0,-.60,-.69])
        tongue.data.vertices.foreach_set("co", points.ravel())
        tongue.data.materials.append(tongue_mat)
        for face in tongue.data.polygons:
            face.use_smooth = True
    key = add_key(tongue, PREFIX+"jawOpen", np.tile([0,.10,-.27], (len(tongue.data.vertices),1)))
    driver(key, "value", *bindings["jawOpen"])
    return len(seen)


def parent_preserving_world(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = world


def build_eye_pivots(head, ctrl, collection):
    for side, sign in [("L", 1), ("R", -1)]:
        name = "Livi_Pivo_Olho_" + side
        pivot = bpy.data.objects.get(name)
        if pivot is None:
            center, radii = eye_parameters(side)
            pivot = bpy.data.objects.new(name, None)
            collection.objects.link(pivot)
            pivot.parent = head
            pivot.location = center
            # Conjugated rotations on the fitted ellipsoid keep the iris and
            # the sclera on the same ocular surface throughout the gaze range.
            pivot.scale = radii / radii[1]
            pivot.empty_display_type = "SPHERE"
            pivot.empty_display_size = 0.1
            pivot.rotation_mode = "XYZ"
            bpy.context.view_layer.update()
            for stem in ["Livi_Olho_Anatomico_", "Livi_Iris_Fibras_3D_",
                         "Livi_Pupila_Rebaixada_", "Livi_Cornea_Reflexo_3D_"]:
                parent_preserving_world(bpy.data.objects[stem + side], pivot)
        driver(pivot, "rotation_euler", "-max(-1,min(1,v))*(0.32 if v>0 else 0.42)",
               control_variables(ctrl, v="olhar_vertical"), 0)
        driver(pivot, "rotation_euler", f"-max(-1,min(1,h))*0.42-{sign}*max(0,min(1,c))*0.10",
               control_variables(ctrl, h="olhar_horizontal", c="convergencia"), 2)


def build_head_pivot(head, ctrl, collection):
    pivot = bpy.data.objects.get("Livi_Pivo_Cabeca")
    if pivot is None:
        pivot = bpy.data.objects.new("Livi_Pivo_Cabeca", None)
        collection.objects.link(pivot)
        pivot.location = (0, 0, -1.35)
        pivot.empty_display_type = "CIRCLE"
        pivot.empty_display_size = 0.3
        bpy.context.view_layer.update()
        parent_preserving_world(head, pivot)
    driver(pivot, "rotation_euler", "-v*0.35", control_variables(ctrl, v="cabeca_vertical"), 0)
    driver(pivot, "rotation_euler", "-h*0.55", control_variables(ctrl, h="cabeca_horizontal"), 2)
    driver(pivot, "rotation_euler", "t*0.25", control_variables(ctrl, t="cabeca_inclinar"), 1)


def build():
    head = bpy.data.objects["Livi_Head_Base"]
    assert bpy.context.mode == "OBJECT", "Use Object Mode before building the facial rig."
    assert len(head.data.vertices) == 4304, "Unexpected Livi head topology."
    collection = bpy.data.collections.get("Livi_Rig_Facial")
    if collection is None:
        collection = bpy.data.collections.new("Livi_Rig_Facial")
        bpy.context.scene.collection.children.link(collection)
    ctrl = make_controls(collection)
    for prop in PROPS:
        ctrl[prop] = 0.0
    ctrl.update_tag()
    bpy.context.view_layer.update()
    ids = source_mapping(head)
    neutral = neutral_coordinates(head)
    targets = load_targets(ids)
    targets["jawOpen"] *= .8
    # Keep the eye sockets and the base of the neck stable while the jaw opens.
    fade = np.clip((.05-neutral[:, 2])/.40, 0, 1)
    fade = fade*fade*(3-2*fade)
    neck = np.clip((neutral[:, 2]+1.9)/.65, 0, 1)
    neck = neck*neck*(3-2*neck)
    targets["jawOpen"] *= (fade*neck)[:, None]
    targets["jawOpen"][np.abs(neutral[:, 0]) < .0001, 0] = 0
    fit_blinks(neutral, targets)
    for side in ["Left", "Right"]:
        targets["gazeLidUp"+side] = targets["eyeWide"+side]*.45
        targets["gazeLidDown"+side] = targets["eyeBlink"+side]*.18
    bindings = build_head_keys(head, ctrl, targets)
    build_brows(head, ctrl, neutral, targets, bindings)
    build_lashes(head, ctrl, neutral, targets, bindings)
    mouth_faces = build_mouth(head, ctrl, collection, neutral, targets, bindings)
    build_eye_pivots(head, ctrl, collection)
    build_head_pivot(head, ctrl, collection)
    bpy.context.view_layer.update()
    bpy.app.driver_namespace["livi_facial_build"] = {
        "neutral": neutral, "targets": targets, "bindings": bindings,
    }
    manifest = {"repository": "https://github.com/makehumancommunity/extra-targets",
                "commit": SOURCE_COMMIT, "license": "CC0-1.0",
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in ASSETS.iterdir() if p.is_file()} if ASSETS.exists() else {}}
    text = bpy.data.texts.get("Livi_Rig_Facial_Fontes.json") or bpy.data.texts.new("Livi_Rig_Facial_Fontes.json")
    text.clear()
    text.write(json.dumps(manifest, indent=2, ensure_ascii=False))
    return {"control": ctrl.name, "controls": list(PROPS), "head_keys": len(targets), "mouth_faces": mouth_faces,
            "neutral_max_delta": float(np.max(np.abs(neutral_coordinates(head)-neutral)))}


if __name__ == "__main__":
    result = build()
