import bpy
from bpy.app.handlers import persistent

from os import listdir
from os.path import exists, isfile, join
from time import sleep
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import importlib
import re
import sys
import threading
from xml.etree import ElementTree as ET

_CONTEXT = None
PORT = 41786
ADDRESS = ('localhost', PORT)
HAS_PIL = False
HAS_WORKING_ARMATURES = [3317538576, 39, 43, 153950757, 153950761, 13, 6, 1504945536, 12]

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    pass

globals()['DARE_BC_Path'] = None
globals()['DARE_BC_Type'] = None

bl_info = {
    "name": "DARE Blender Connector",
    "description": "DARE Blender Connector",
    "author": "Daniel Cai",
    "location": "File > Import",
    "version": (1, 0, 1),
    "blender": (3, 0, 0),
    "wiki_url": "https://github.com/Dcai169/DARE-Blender-Connector",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


def import_collada_with_normals(context, path: str):
    bpy.ops.wm.collada_import(filepath=path)
    print("Importing normals...")
    tree = ET.parse(path)
    COLLADA = tree.getroot()

    library_geometries = COLLADA.find("./{http://www.collada.org/2005/11/COLLADASchema}library_geometries")
    library_controllers = COLLADA.find("./{http://www.collada.org/2005/11/COLLADASchema}library_controllers")
    library_visual_scenes = COLLADA.find("./{http://www.collada.org/2005/11/COLLADASchema}library_visual_scenes")
    visual_scene = library_visual_scenes.find("./{http://www.collada.org/2005/11/COLLADASchema}visual_scene")

    normals = {"objectname": "objectnormals"}

    for node in visual_scene.iter("{http://www.collada.org/2005/11/COLLADASchema}node"):
        number_with_name = 0
        for object in bpy.context.selected_objects:
            if node.attrib["name"] == object.name:
                number_with_name += 1
        if number_with_name == 0:
            continue

        # Locate geometry for scene node
        instance_geometry = node.find("./{http://www.collada.org/2005/11/COLLADASchema}instance_geometry")
        mesh_id = ""
        if instance_geometry is None:
            instance_controller = node.find("./{http://www.collada.org/2005/11/COLLADASchema}instance_controller")
            if instance_controller is None:
                continue
            
            controller_id = instance_controller.attrib["url"].replace("#", "")
            controller = library_controllers.find("./{http://www.collada.org/2005/11/COLLADASchema}controller[@id='"+controller_id+"']")
            mesh_id = controller.find("./{http://www.collada.org/2005/11/COLLADASchema}skin").attrib["source"].replace("#", "")
        else:
            mesh_id = instance_geometry.attrib["url"].replace("#", "")
        geometry = library_geometries.find("./{http://www.collada.org/2005/11/COLLADASchema}geometry[@id='"+mesh_id+"']")

        # Pick out normals
        mesh = geometry.find("./{http://www.collada.org/2005/11/COLLADASchema}mesh")
        triangles = mesh.find("./{http://www.collada.org/2005/11/COLLADASchema}triangles")
        normal_input = triangles.find("./{http://www.collada.org/2005/11/COLLADASchema}input[@semantic='NORMAL']")
        if normal_input is None:
            print("{0} has no custom normals.".format(node.attrib["name"]))
            continue

        normal_id = normal_input.attrib["source"].replace("#", "")
        normal_source = mesh.find("./{http://www.collada.org/2005/11/COLLADASchema}source[@id='"+normal_id+"']")
        normals[node.attrib["name"]] = normal_source.find("./{http://www.collada.org/2005/11/COLLADASchema}float_array").text.split()

        for object in bpy.context.selected_objects:
            if node.attrib["name"] != object.name:
                continue

            formatted_normals = [[0, 0, 0]for i in range(len(normals[node.attrib["name"]])//3)]
            for i in range(len(normals[node.attrib["name"]])):
                formatted_normals[i//3][i % 3] = float(normals[node.attrib["name"]][i])

            bpy.context.view_layer.objects.active = object
            bpy.ops.mesh.customdata_custom_splitnormals_add()
            object.data.use_auto_smooth = True

            object.data.normals_split_custom_set_from_vertices(formatted_normals)

            print("Imported normals for {0}.".format(object.name))


def install_pip_package(package_name: str):  # requires admin rights
    from subprocess import call
    from pathlib import Path

    py_exec = str(sys.executable)

    # Get lib directory
    lib = join(Path(py_exec).parent.parent, "lib")

    # Ensure pip is installed
    call([py_exec, "-m", "ensurepip", "--user"])

    # Update pip (not mandatory)
    call([py_exec, "-m", "pip", "install", "--upgrade", "pip"])

    # Install packages
    call([py_exec, "-m", "pip", "install", f"--target={str(lib)}", package_name])


def generate_package_install(package_name: str):
    return lambda: install_pip_package(package_name)


def composite_tiles(path, tiles):
    composite = Image.new('RGBA', (2048, 2048))
    for tile in tiles:
        with Image.open(join(path, tile)) as img:
            composite.alpha_composite(img)
    return composite


def get_shader_name(shader_script: str):
    with open(shader_script, 'r') as f:
        return re.search(r"(?<=custom_node_name = \").*(?=\".*)", f.read()).group(0)


def import_from_path(context, base_content_path: str, retain_armature: bool = False, clean_meshes: bool = True, compsite_textures: bool = True,):
    sleep(2)  # Wait for ripping to settle

    try:
        # store a list of selected objects and deselect all
        prior_selections = [obj for obj in bpy.context.selected_objects]
        bpy.ops.object.select_all(action='DESELECT')

        # Use the presence of the `Raws` folder to determine shaders or model
        is_model = exists(join(base_content_path, 'Raws'))

        # import shaders from ./Shaders/Blender/*.py
        shader_path = join(base_content_path, 'Shaders', 'Blender')
        if shader_path not in sys.path:
            sys.path.append(shader_path)

        shader_scripts = [f for f in listdir(shader_path) if isfile(join(shader_path, f)) if f.endswith('.py')]
        print(f'Found {len(shader_scripts)} shader scripts')
        imported_shaders = []  # Future usage

        for shader_script in shader_scripts:
            script_path = join(shader_path, shader_script)
            shader_name = get_shader_name(script_path)

            if bpy.data.node_groups.get(shader_name) is None:
                try:
                    shader_py = importlib.import_module(shader_script[:-3])
                    shader_node_group = shader_py.create_test_group(context, context, shader_name, base_content_path)

                    print(f'Imported shader {shader_name}.py')
                    imported_shaders.append(shader_node_group)

                    shader_node_group.fakeUser = 1
                except Exception as e:  # 'NoneType' object has no attribute 'active_material'
                    print(f'Failed to import shader {shader_name}')
                    print(e)
                    print()

        if is_model:
            # compile a list of all objects in the scene
            prior_objects = [object.name for object in list(bpy.data.objects)]

            model_path = join(base_content_path, 'model.dae')
            if exists(model_path):
                print(f'Importing model from {model_path}')
                import_collada_with_normals(model_path)
                print()

            # compile a list of all objects that were added by the import
            new_objects = [object for object in list(bpy.data.objects) if object.name not in prior_objects]

            if not retain_armature:
                try:
                    # delete imported armature
                    new_armatures = [object for object in new_objects if object.type == 'ARMATURE']
                    bpy.ops.object.delete({"selected_objects": new_armatures})
                except Exception as e:
                    print(f'Failed to delete imported armature')
                    print(e)
                    print()

            if clean_meshes:
                # find all imported meshes
                new_meshes = [object for object in list(bpy.data.objects) if object.type == 'MESH' if object.name not in prior_objects]

                # select all new_meshes
                bpy.ops.object.mode_set(mode='OBJECT')
                for mesh in new_meshes:
                    mesh.select_set(True)

                # switch to edit mode
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')

                try:
                    # remove extra vertices
                    bpy.ops.mesh.delete_loose()
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.remove_doubles()
                except Exception as e:
                    print(f'Failed to clean meshes')
                    print(e)
                    print()

                # deselect everything
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')

            hd_texture_path = join(base_content_path, 'HD_Textures')
            if exists(hd_texture_path):
                if compsite_textures:
                    if not HAS_PIL:
                        print('PIL not installed, skipping texture compsite')
                        print()
                    else:
                        for folder in [join(hd_texture_path, f, 'textures') for f in listdir(hd_texture_path) if not isfile(join(hd_texture_path, f))]:
                            textures = {
                                'Diffuse': [],
                                'GStack': [],
                                'Normal': [],
                                'Dyemap': [],
                            }

                            try:
                                for image in [f for f in listdir(folder) if isfile(join(folder, f)) if f.endswith('.png')]:
                                    with Image.open(join(folder, image)) as img:
                                        if img.size == (2048, 2048):
                                            textures[image.split('.')[0].split('_')[1]].append(image)
                            except Exception as e:
                                print(f'Failed to read textures from {folder}')
                                print(e)
                                print()

                            try:
                                for tex_set in textures:
                                    if len(textures[tex_set]) > 1:
                                        print(f'Compsiting {len(textures[tex_set])} {tex_set} textures')
                                        composite_tiles(folder, textures[tex_set]).save(join(folder, f'composite-{tex_set[0].lower()}.png'))
                            except Exception as e:
                                print(f'Failed to composite textures for {folder}')
                                print(e)
                                print()
                        print(f'Texture compsite complete')
                        print()

            # import template shader material
            # copy template shader material to objects
            # assign shader to object shader material
            # assign textures to object shader material

        # restore selected objects
        for object in bpy.data.objects:
            if object.name in prior_selections:
                object.select_set(True)

        return {'FINISHED'}
    except Exception as e:
        print('Error in importer')
        print(e)
        return {'FAILED'}


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        if self.path == '/':
            if exists(self.headers['X-Content-Path']):
                globals()['DARE_BC_Path'] = self.headers['X-Content-Path']
                try:
                    globals()['DARE_BC_Type'] = self.headers['X-Content-Type']
                except KeyError:
                    pass

                self.send_response(202)
            else:
                self.send_response(404)
        elif self.path == '/ping':
            self.send_response(204)
            self.send_header('X-Ping-Response', 'pong')
        else:
            self.send_response_only(404)

        self.end_headers()


class ImportRequestHandler(bpy.types.Operator):
    bl_idname = "dare_bc.import_request_handler"
    bl_label = "DARE Blender Connector"

    def execute(self, context):
        try:
            globals()['DARE_BC_Path'] = None
            globals()['DARE_BC_Type'] = None

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
            print('DARE BC context stored')
            print()

            return {'FINISHED'}
        except Exception as e:
            print('Error in DARE BC initialization')
            print(e)
            return {'FAILED'}

    def data_monitor(self):
        try:
            global _CONTEXT
            base_content_path = globals()['DARE_BC_Path']
            if base_content_path is not None and _CONTEXT is not None:
                retain_armature = False
                if (globals()['DARE_BC_Type'] != 'undefined' or globals()['DARE_BC_Type'] is not None):
                    for working_item_category in [str(item_category) for item_category in HAS_WORKING_ARMATURES]:
                        if (working_item_category in globals()['DARE_BC_Type']):
                            retain_armature = True
                            break

                import_from_path(_CONTEXT, base_content_path, retain_armature=retain_armature)

                globals()['DARE_BC_Path'] = None
                globals()['DARE_BC_Type'] = None
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
    if not HAS_PIL:
        threading.Thread(target=generate_package_install('Pillow')).start()


def unregister():
    # http_thread = [thread for thread in threading.enumerate() if thread.name == "DAREBC_server"][0]
    bpy.utils.unregister_class(ImportRequestHandler)


if __name__ == '__main__':
    register()
