# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
import json

bl_info = {
    "name": "Camera Collection State Switcher",
    "author": "Pavel Fomin",
    "version": (2, 4),
    "blender": (3, 0, 0),
    "location": "Properties > Camera > Collection States",
    "description": "Для камеры сохраняет и загружает настройки Exclude, Hide Viewport и Disable Render для коллекций и объектов",
    "category": "Interface",
}

# Хранилище данных в сцене
class CameraCollectionState(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="State Name", default="New State")
    data: bpy.props.StringProperty()

# --- ОПЕРАТОРЫ ---

class CAM_OT_SaveState(bpy.types.Operator):
    """Сохранить текущее состояние всех коллекций и объектов"""
    bl_idname = "cam.save_collection_state"
    bl_label = "Save Current State"

    def execute(self, context):
        view_layer = context.view_layer
        state_data = {
            'collections': [],
            'objects': []
        }

        # Сохраняем состояния коллекций
        def traverse_collections(layer_collection):
            collection = layer_collection.collection
            state_data['collections'].append({
                'name': layer_collection.name,
                'exclude': layer_collection.exclude,
                'hide_viewport': collection.hide_viewport,
                'hide_render': collection.hide_render
            })
            for child in layer_collection.children:
                traverse_collections(child)

        traverse_collections(view_layer.layer_collection)

        # Сохраняем состояния объектов
        for obj in context.view_layer.objects:
            if obj.name:
                state_data['objects'].append({
                    'name': obj.name,
                    'hide_viewport': obj.hide_viewport,
                    'hide_render': obj.hide_render
                })

        # Используем JSON для сохранения данных
        cam = context.object.data
        new_state = cam.coll_states.add()
        new_state.name = f"State {len(cam.coll_states)}"
        new_state.data = json.dumps(state_data)

        coll_count = len(state_data['collections'])
        obj_count = len(state_data['objects'])
        self.report({'INFO'}, f"Saved: {coll_count} collections, {obj_count} objects")
        print(f"[DEBUG] Saved state with {coll_count} collections and {obj_count} objects")

        return {'FINISHED'}

class CAM_OT_LoadState(bpy.types.Operator):
    """Применить сохраненное состояние"""
    bl_idname = "cam.load_collection_state"
    bl_label = "Load State"
    index: bpy.props.IntProperty()

    def execute(self, context):
        cam = context.object.data
        if not hasattr(cam, 'coll_states') or self.index >= len(cam.coll_states):
            self.report({'ERROR'}, "State not found!")
            return {'CANCELLED'}

        state_data_str = cam.coll_states[self.index].data

        try:
            # Парсим JSON
            state_data = json.loads(state_data_str)
        except:
            self.report({'ERROR'}, "Failed to parse state data! Please re-save this state.")
            print(f"[ERROR] Failed to parse JSON: {state_data_str[:200]}")
            return {'CANCELLED'}

        print(f"[DEBUG] Loaded state with {len(state_data.get('collections', []))} collections and {len(state_data.get('objects', []))} objects")

        view_layer = context.view_layer

        # Функция для поиска layer_collection по имени
        def find_layer_collection(layer_collection, name):
            if layer_collection.name == name:
                return layer_collection
            for child in layer_collection.children:
                result = find_layer_collection(child, name)
                if result:
                    return result
            return None

        # Применяем состояния коллекций
        applied_coll = 0
        for coll_data in state_data.get('collections', []):
            coll_name = coll_data['name']
            layer_coll = find_layer_collection(view_layer.layer_collection, coll_name)
            if layer_coll:
                try:
                    layer_coll.exclude = coll_data['exclude']
                    layer_coll.collection.hide_viewport = coll_data['hide_viewport']
                    layer_coll.collection.hide_render = coll_data['hide_render']
                    applied_coll += 1
                    print(f"[DEBUG] Applied to collection: {coll_name}")
                except Exception as e:
                    print(f"[ERROR] Failed to apply to {coll_name}: {e}")
            else:
                print(f"[WARNING] Collection not found: {coll_name}")

        # Применяем состояния объектов
        applied_obj = 0
        for obj_data in state_data.get('objects', []):
            obj_name = obj_data['name']
            obj = bpy.data.objects.get(obj_name)
            if obj:
                try:
                    obj.hide_viewport = obj_data['hide_viewport']
                    obj.hide_render = obj_data['hide_render']
                    applied_obj += 1
                    print(f"[DEBUG] Applied to object: {obj_name}")
                except Exception as e:
                    print(f"[ERROR] Failed to apply to {obj_name}: {e}")
            else:
                print(f"[WARNING] Object not found: {obj_name}")

        # Обновляем viewport
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report({'INFO'}, f"Loaded: {applied_coll} collections, {applied_obj} objects")
        return {'FINISHED'}

class CAM_OT_DeleteState(bpy.types.Operator):
    """Удалить пресет"""
    bl_idname = "cam.delete_collection_state"
    bl_label = "Delete State"
    bl_description = "Delete this state"
    index: bpy.props.IntProperty()

    def execute(self, context):
        cam = context.object.data
        if hasattr(cam, 'coll_states') and self.index < len(cam.coll_states):
            state_name = cam.coll_states[self.index].name
            cam.coll_states.remove(self.index)
            self.report({'INFO'}, f"State '{state_name}' deleted!")
        return {'FINISHED'}

class CAM_OT_UpdateFromCurrent(bpy.types.Operator):
    """Обновить выбранный пресет текущим состоянием"""
    bl_idname = "cam.update_state_from_current"
    bl_label = "Update State"
    bl_description = "Update selected state with current collections and objects visibility"
    index: bpy.props.IntProperty()

    def execute(self, context):
        view_layer = context.view_layer
        state_data = {
            'collections': [],
            'objects': []
        }

        # Сохраняем состояния коллекций
        def traverse_collections(layer_collection):
            collection = layer_collection.collection
            state_data['collections'].append({
                'name': layer_collection.name,
                'exclude': layer_collection.exclude,
                'hide_viewport': collection.hide_viewport,
                'hide_render': collection.hide_render
            })
            for child in layer_collection.children:
                traverse_collections(child)

        traverse_collections(view_layer.layer_collection)

        # Сохраняем состояния объектов
        for obj in context.view_layer.objects:
            if obj.name:
                state_data['objects'].append({
                    'name': obj.name,
                    'hide_viewport': obj.hide_viewport,
                    'hide_render': obj.hide_render
                })

        cam = context.object.data
        if hasattr(cam, 'coll_states') and self.index < len(cam.coll_states):
            cam.coll_states[self.index].data = json.dumps(state_data)
            self.report({'INFO'}, f"State '{cam.coll_states[self.index].name}' updated!")
        else:
            self.report({'ERROR'}, "State not found!")
            return {'CANCELLED'}

        return {'FINISHED'}

class CAM_OT_ExportState(bpy.types.Operator):
    """Экспортировать состояние в текстовый блок"""
    bl_idname = "cam.export_collection_state"
    bl_label = "Export State"
    bl_description = "Export selected state to text block"
    index: bpy.props.IntProperty()

    def execute(self, context):
        cam = context.object.data
        if not hasattr(cam, 'coll_states') or self.index >= len(cam.coll_states):
            self.report({'ERROR'}, "State not found!")
            return {'CANCELLED'}

        state = cam.coll_states[self.index]

        try:
            state_data = json.loads(state.data)
        except:
            self.report({'ERROR'}, "Failed to parse state data!")
            return {'CANCELLED'}

        text_block_name = f"collection_state_{state.name.replace(' ', '_')}"
        if text_block_name in bpy.data.texts:
            text_block = bpy.data.texts[text_block_name]
            text_block.clear()
        else:
            text_block = bpy.data.texts.new(text_block_name)

        from datetime import datetime
        text_block.write(f"State: {state.name}\n")
        text_block.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        text_block.write("=" * 70 + "\n\n")

        # Пишем коллекции
        text_block.write("COLLECTIONS:\n")
        text_block.write("-" * 70 + "\n")
        text_block.write(f"{'Collection Name':<40} | {'Exclude':<7} | {'Hide Viewport':<12} | {'Disable Render'}\n")
        text_block.write("-" * 70 + "\n")

        for coll in state_data.get('collections', []):
            text_block.write(f"{coll['name']:<40} | {str(coll['exclude']):<7} | {str(coll['hide_viewport']):<12} | {coll['hide_render']}\n")

        # Пишем объекты
        text_block.write("\n\nOBJECTS:\n")
        text_block.write("-" * 70 + "\n")
        text_block.write(f"{'Object Name':<40} | {'Hide Viewport':<12} | {'Disable Render'}\n")
        text_block.write("-" * 70 + "\n")

        for obj in state_data.get('objects', []):
            text_block.write(f"{obj['name']:<40} | {str(obj['hide_viewport']):<12} | {obj['hide_render']}\n")

        self.report({'INFO'}, f"State exported to text block: '{text_block_name}'")
        return {'FINISHED'}

# --- ИНТЕРФЕЙС ---

class CAM_PT_CollectionStates(bpy.types.Panel):
    bl_label = "Collection Visibility States"
    bl_idname = "CAM_PT_collection_states"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'CAMERA'

    def draw(self, context):
        layout = self.layout
        cam = context.object.data

        if not hasattr(cam, 'coll_states'):
            layout.label(text="Property not initialized. Please restart Blender.", icon='ERROR')
            return

        row = layout.row()
        row.operator("cam.save_collection_state", icon='ADD', text="Save Current as New State")

        layout.separator()

        if len(cam.coll_states) > 0:
            col = layout.column(align=True)
            for i, state in enumerate(cam.coll_states):
                box = col.box()

                row = box.row(align=True)
                row.prop(state, "name", text="")

                load_op = row.operator("cam.load_collection_state", text="", icon='FILE_REFRESH')
                load_op.index = i

                update_op = row.operator("cam.update_state_from_current", text="", icon='FILE_TICK')
                update_op.index = i

                export_op = row.operator("cam.export_collection_state", text="", icon='EXPORT')
                export_op.index = i

                del_op = row.operator("cam.delete_collection_state", text="", icon='TRASH')
                del_op.index = i

                # Показываем количество элементов
                try:
                    data = json.loads(state.data)
                    coll_count = len(data.get('collections', []))
                    obj_count = len(data.get('objects', []))
                    row = box.row(align=True)
                    row.label(text=f"Collections: {coll_count} | Objects: {obj_count}", icon='OUTLINER_COLLECTION')
                except:
                    row = box.row(align=True)
                    row.label(text="Invalid state data", icon='ERROR')

        else:
            layout.label(text="No states saved", icon='INFO')
            layout.label(text="Click 'Save Current as New State' to create one")

class CAM_PT_CollectionStatesView3D(bpy.types.Panel):
    bl_label = "Camera Collection States"
    bl_idname = "CAM_PT_collection_states_view3d"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'CAMERA'

    def draw(self, context):
        layout = self.layout
        cam = context.object.data

        if not hasattr(cam, 'coll_states'):
            layout.label(text="Property not initialized.", icon='ERROR')
            return

        row = layout.row()
        row.operator("cam.save_collection_state", icon='ADD', text="Save Current")

        layout.separator()

        if len(cam.coll_states) > 0:
            for i, state in enumerate(cam.coll_states):
                box = layout.box()
                row = box.row(align=True)
                row.label(text=state.name)
                load_op = row.operator("cam.load_collection_state", text="Load", icon='FILE_TICK')
                load_op.index = i

                update_op = row.operator("cam.update_state_from_current", text="", icon='FILE_REFRESH')
                update_op.index = i
                del_op = row.operator("cam.delete_collection_state", text="", icon='TRASH')
                del_op.index = i
        else:
            layout.label(text="No states", icon='INFO')

# --- РЕГИСТРАЦИЯ ---

classes = (
    CameraCollectionState,
    CAM_OT_SaveState,
    CAM_OT_LoadState,
    CAM_OT_DeleteState,
    CAM_OT_UpdateFromCurrent,
    CAM_OT_ExportState,
    CAM_PT_CollectionStates,
    CAM_PT_CollectionStatesView3D,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Camera.coll_states = bpy.props.CollectionProperty(type=CameraCollectionState)

def unregister():
    if hasattr(bpy.types.Camera, 'coll_states'):
        del bpy.types.Camera.coll_states

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
