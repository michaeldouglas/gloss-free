"""Livi sidebar. The rig itself works without this optional UI module."""

import bpy

CONTROL = "Livi_CONTROLES_FACIAIS"
FIELDS = (
    "piscar", "piscar_esquerdo", "piscar_direito", "abrir_olhos",
    "olhar_horizontal", "olhar_vertical", "convergencia",
    "sobrancelha_esquerda", "sobrancelha_direita", "franzir_sobrancelhas",
    "sobrancelhas_internas", "abrir_boca", "cabeca_horizontal",
    "cabeca_vertical", "cabeca_inclinar",
)
PRESETS = {
    "NEUTRAL": {},
    "BLINK": {"piscar": 1},
    "WINK": {"piscar_esquerdo": 1},
    "UP": {"olhar_vertical": 1},
    "DOWN": {"olhar_vertical": -1},
    "LEFT": {"olhar_horizontal": -1},
    "RIGHT": {"olhar_horizontal": 1},
    "BROWS": {"sobrancelha_esquerda": 1, "sobrancelha_direita": 1},
    "MOUTH": {"abrir_boca": .65},
}


def refresh():
    control = bpy.data.objects.get(CONTROL)
    if control:
        control.update_tag()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("Livi_"):
            obj.update_tag()
    bpy.context.view_layer.update()
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        area.tag_redraw()


class LIVI_OT_facial_preset(bpy.types.Operator):
    bl_idname = "livi.facial_preset"
    bl_label = "Pose facial da Livi"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.StringProperty(default="NEUTRAL")

    def execute(self, context):
        control = bpy.data.objects.get(CONTROL)
        if control is None:
            self.report({"ERROR"}, "Controles faciais nao encontrados")
            return {"CANCELLED"}
        if control.animation_data and control.animation_data.action:
            self.report({"WARNING"}, "Ha animacao ativa: edite os controles e seus keyframes diretamente")
            return {"CANCELLED"}
        for field in FIELDS:
            control[field] = float(PRESETS[self.preset].get(field, 0))
        refresh()
        return {"FINISHED"}


class LIVI_OT_facial_keyframe(bpy.types.Operator):
    bl_idname = "livi.facial_keyframe"
    bl_label = "Inserir pose na linha do tempo"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        control = bpy.data.objects.get(CONTROL)
        if control is None:
            return {"CANCELLED"}
        for field in FIELDS:
            control.keyframe_insert(data_path='["'+field+'"]',
                                    frame=context.scene.frame_current, group="Livi - Rosto")
        return {"FINISHED"}


class LIVI_PT_facial_controls(bpy.types.Panel):
    bl_label = "Controles faciais"
    bl_idname = "LIVI_PT_facial_controls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Livi"

    def draw(self, context):
        layout = self.layout
        control = bpy.data.objects.get(CONTROL)
        if control is None:
            layout.label(text="Abra o arquivo livi.blend com o rig facial")
            return
        def slider(box, field, label):
            box.prop(control, '["'+field+'"]', text=label, slider=True)
        box = layout.box()
        box.label(text="Olhos e palpebras")
        for field, label in [("piscar","Fechar ambos"),("piscar_esquerdo","Fechar esquerdo"),
                             ("piscar_direito","Fechar direito"),("abrir_olhos","Abrir mais")]:
            slider(box, field, label)
        box = layout.box()
        box.label(text="Olhar (lados da personagem)")
        for field, label in [("olhar_horizontal","Esquerda / direita"),("olhar_vertical","Baixo / cima"),
                             ("convergencia","Olhar de perto")]:
            slider(box, field, label)
        box = layout.box()
        box.label(text="Sobrancelhas")
        for field, label in [("sobrancelha_esquerda","Esquerda"),("sobrancelha_direita","Direita"),
                             ("franzir_sobrancelhas","Franzir"),("sobrancelhas_internas","Levantar internas")]:
            slider(box, field, label)
        slider(layout.box(), "abrir_boca", "Abrir boca")
        box = layout.box()
        box.label(text="Cabeca")
        for field, label in [("cabeca_horizontal","Esquerda / direita"),("cabeca_vertical","Baixo / cima"),
                             ("cabeca_inclinar","Inclinar")]:
            slider(box, field, label)
        layout.operator("livi.facial_keyframe", icon="KEY_HLT")
        layout.operator("livi.facial_preset", text="Voltar ao neutro", icon="LOOP_BACK").preset="NEUTRAL"
        row = layout.row(align=True)
        for preset, label in [("BLINK","Fechar olhos"),("MOUTH","Abrir boca")]:
            row.operator("livi.facial_preset", text=label).preset=preset
        row = layout.row(align=True)
        for preset, label in [("LEFT","Esq."),("UP","Cima"),("DOWN","Baixo"),("RIGHT","Dir.")]:
            row.operator("livi.facial_preset", text=label).preset=preset


CLASSES = (LIVI_OT_facial_preset, LIVI_OT_facial_keyframe, LIVI_PT_facial_controls)


def register():
    for cls in CLASSES:
        previous = getattr(bpy.types, cls.__name__, None)
        if previous:
            bpy.utils.unregister_class(previous)
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        previous = getattr(bpy.types, cls.__name__, None)
        if previous:
            bpy.utils.unregister_class(previous)


register()
