import bpy
from bpy.app.handlers import persistent

from os import listdir
from os.path import exists, isfile, join
from time import sleep
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import threading

_CONTEXT = None

bl_info = {
    "name": "DARE Blender Connector",
    "description": "DARE Blender Connector",
    "location": "File > Import",
    "blender": (3, 0, 1),
    "support": "COMMUNITY",
    "category": "Import-Export",
}

PORT = 41786
ADDRESS = ('localhost', PORT)

globals()['DARE_BC_Path'] = None

def import_from_path(context, base_content_path):
    sleep(4)  # Wait for ripping to settle

    try:
        # store a list of selected objects and deselect all
        selected_objects = [obj for obj in bpy.context.selected_objects]
        bpy.ops.object.select_all(action='DESELECT')

        # Use the presence of the `Raws` folder to determine shaders or model
        is_model = exists(join(base_content_path, 'Raws'))

        if is_model:
            # compile a list of all objects in the scene
            prior_objects = [object.name for object in list(bpy.data.objects)]

            model_path = join(base_content_path, 'model.dae')
            if exists(model_path):
                bpy.ops.wm.collada_import(filepath=model_path, auto_connect=True, find_chains=True)

            # compile a list of all objects that were added by the import
            new_objects = [object for object in list(bpy.data.objects) if object.name not in prior_objects]

            # find all imported armatures
            new_armatures = [object for object in new_objects if object.type == 'ARMATURE']

            # delete all imported armatures
            bpy.ops.object.delete({"selected_objects": new_armatures})

            # remove loose vertices in imported meshes
            new_meshes = [object for object in new_objects if object.type == 'MESH']
        
        # import shaders from ./Shaders/Blender/*.py
        shader_path = join(base_content_path, 'Shaders', 'Blender')
        shader_scripts = [f for f in listdir(shader_path) if isfile(join(shader_path, f)) if f.endswith('.py')]
        print(shader_scripts)

        if not is_model:
            return {'FINISHED'}

        # import template shader material
        # copy template shader material to objects
        # assign shader to object shader material
        # assign textures to object shader material

        return {'FINISHED'}
    except Exception as e:
        print('Error in importer')
        print(e)
        return {'FAILED'}

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        globals()['DARE_BC_Path'] = self.headers['X-Content-Path']

        self.send_response(200)
        self.end_headers()

class ImportRequestHandler(bpy.types.Operator):
    bl_idname = "dare_bc.import_request_handler"
    bl_label = "DARE Blender Connector"

    def execute(self, context):
        try:
            globals()['DARE_BC_Path'] = None

            # Start the http server
            self.server = ThreadingHTTPServer(ADDRESS, HTTPRequestHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, name='DAREBC_server')
            self.server_thread.start()
            print('DARE BC server started')

            # Start the data monitor
            bpy.app.timers.register(self.data_monitor)
            print('DARE BC data monitor started')

            # Store context
            # this is super hacky, but it works
            # I think the class member is being garbage collected
            # but if context is stored in a global variable, it is not
            global _CONTEXT 
            _CONTEXT = context

            return {'FINISHED'}
        except Exception as e:
            print('Error in DARE BC initialization')
            print(e)
            return {'FAILED'}

    def data_monitor(self):
        try:
            global _CONTEXT
            base_content_path = globals()['DARE_BC_Path']
            if base_content_path != None and _CONTEXT != None: 
                import_from_path(_CONTEXT, base_content_path)
                globals()['DARE_BC_Path'] = None
        except Exception as e:
            print('Error in DARE BC data monitor')
            print(e)
            return None
        return 1.0

@persistent
def load_darebc(scene):
    try:
        bpy.ops.dare_bc.import_request_handler()
    except Exception as e:
        print('Error in DARE BC load_addon')
        print(e)

def register():
    # prevent double initalization
    if len(bpy.app.handlers.load_post) > 0:
        if load_darebc in bpy.app.handlers.load_post:
            print("DARE BC already loaded")
            return
    
    bpy.utils.register_class(ImportRequestHandler)
    bpy.app.handlers.load_post.append(load_darebc)


def unregister():
    # http_thread = [thread for thread in threading.enumerate() if thread.name == "DAREBC_server"][0]
    bpy.utils.unregister_class(ImportRequestHandler)


if __name__ == '__main__':
    register()
