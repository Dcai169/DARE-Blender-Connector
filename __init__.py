import bpy
from bpy.types import Operator

from os.path import exists, join
from time import sleep
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import threading

bl_info = {
    "name": "DARE Blender Connector",
    "blender": (3, 0, 1),
    "category": "Import-Export",
}

PORT = 41786
ADDRESS = ('localhost', PORT)


def import_from_path(context):
    print(context)
    sleep(4)  # Wait for ripping to settle

    content_path = globals()['DARE_BC_Path']

    if not content_path:
        return {'FINISHED'}

    # Use the presence of the `Raws` folder to determine shaders or model
    is_model = exists(join(content_path, 'Raws'))
    print('Model' if is_model else 'Shader')

    if is_model:
        model_path = join(content_path, 'model.dae')
        print(bpy.context.area)
        print(model_path)
        bpy.ops.wm.collada_import(model_path, auto_connect=True, find_chains=True) # Throws an error due to incorrect context
        # bpy.ops.import_mesh.stl(filepath=model_path)
    else:
        print('shader')

    return {'FINISHED'}


class ImportRequestHandler(Operator):
    bl_idname = "dare_blender_connector.py"
    bl_label = "DARE Blender Connector"

    def execute(self, context):
        print(bpy.ops.wm.collada_import.poll(context))
        return import_from_path(context)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.headers['X-Content-Path'])
        globals()['DARE_BC_Path'] = self.headers['X-Content-Path']
        import_from_path('INVOKE_DEFAULT')

        self.send_response(200)
        self.end_headers()


def register():
    http_server = ThreadingHTTPServer(ADDRESS, RequestHandler)
    http_thread = threading.Thread(
        target=http_server.serve_forever, name='DAREBC_server')
    http_thread.start()
    print('DARE BC server started')

    bpy.utils.register_class(ImportRequestHandler)


def unregister():
    http_thread = [thread for thread in threading.enumerate()
                   if thread.name == "DAREBC_server"][0]
    bpy.utils.unregister_class(ImportRequestHandler)


if __name__ == '__main__':
    register()
