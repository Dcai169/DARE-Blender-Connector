import os
import bpy
import sys
import importlib  



#possible actions
#import model -> textures to materials -> materials to models -> shaders to materials

#should also have
#textures to materials (alone)
#materials to models (alone)
#shaders to materials (alone)

#PLEASE HAVE THE SYSTEM CONSOLE TURNED ON 
#Window -> Toggle System Console

divider = "-------------------------------------------"

#armor class
class Armor:


    file_path = ""
    class_input = ""
    gender = ""
    armors_to_import = [] 

    armors = [] #all armor names and their textures found

    class_keywords = [] #what kind of words identify armor type for this class (helm, greaves, cloak, etc)

    filtered_armor = []

    def __init__(self, file_path, class_input = "no", gender = "no"):
        self.class_input = class_input
        self.file_path = file_path
        self.gender = gender
    
    def do_the_thing(self):
        all_files = os.listdir(self.file_path)
        if(self.gender != "no"):
            all_files = self.filter_gender(all_files)
        if(self.class_input != "no"):
            all_files = self.filter_class(all_files)
        self.armors_to_import = self.find_textures(all_files)

    def filter_gender(self, all_files):
        new_files = []
        for file in all_files:
            if file.split("_")[-1] == self.gender:
                new_files.append(file)
        return new_files
    
    def filter_class(self, all_files):
        new_files = []
        for file in all_files:
            if file.split("_")[0] == self.class_input:
                new_files.append(file)
        return new_files

    def find_textures(self, all_files):
        armors_to_import = []
        for file in all_files:
            print(divider)
            fail = False
            new_armor = {} #contains name and texture dictionary with diffuse/normal/gstack/dyeslot
            new_armor["name"] = file
            print("finding textures for " + file)
            
            textures = {}
            #get main textures MANDATORY
            for tex_name in ["diffuse", "gstack", "normal"]:
                try:
                    self.get_file_name(self.file_path, file, tex_name)
                except Exception as e:
                    print("failed to get textures for " + file + "'s " + tex_name + " for reason ")
                    print(e)
                    print("skipping texture")
                else:
                    textures[tex_name] = self.get_file_name(self.file_path, file, tex_name)
        
            #get dyeslot (not mandatory)
            try:
                self.get_file_name(self.file_path, file, "dyemap")
            except ValueError:
                textures["dyeslot"] = False
            else:
                textures["dyeslot"] = True
                textures["dyeslot"] = self.get_file_name(self.file_path, file, "dyemap")
            new_armor["textures"] = textures
            armors_to_import.append(new_armor)
            print("successfully appended armor!")
            print(divider)
        return armors_to_import

    def get_file_name(self, file_path, name, texture_type):
        times = 0
        return_tex = ""
        all_textures = os.listdir(file_path + "/" + name + "/textures")
        for file in all_textures:
            if texture_type in file.lower():
                times += 1
                return_tex = file
        if times > 1:
            raise ValueError('Multitexture')
        elif times == 0:
            raise ValueError('Cannot find texture type ' + texture_type)
        else: 
            return return_tex


    def find_armors(self):
        armor_folder = os.listdir(self.file_path)
        for armor in armor_folder:
            folder_str = armor.split("_")
            if self.gender in folder_str and self.class_type:
                armor_type = self.deter_armor_type(folder_str)
                
    def return_textures(self):
        return self.armors_to_import

    def show_textures(self):
        print(self.armors_to_import)

















#the blender part
class Blender_time:
    
    file_path = ""
    armor_list = []
    mats = None
    mats = None
    incomplete_armors = []
    texture_map = { #type of texture to the name of texture node in blender
            "diffuse":"Diffuse Texture",
            "gstack":"Gstack Texture",
            "normal":"Normal Map",
            "dyeslot":"Dye Slot Texture (optional)"
        }
    imported_armors = []
    name_map = {} #though once named titan_sdaf_ads. It should now be called asdfad_asdf
    shader_list = ""
    shader_path = ""

    def __init__(self):
        pass
        




    #TEXTURE HANDLER
    def import_the_textures(self):
        self.prelim_check() #will error if fails
        player_shader = self.mats.get("player_shader")
        for armor in self.armor_list:
            print(divider)
            print("importing textures for " + armor['name'])
            new_shader = player_shader.copy()
            new_shader.name = armor['name']
            texture_list = armor['textures']
            
            incomplete = False
            for texture in ['diffuse', 'gstack', 'normal']:
                if texture in texture_list:
                    texture_path_full = self.file_path + "/" + armor['name'] + "/textures/" + texture_list[texture]
                    self.change_texture(texture, texture_path_full, new_shader)
                else:
                    incomplete = True
                    print("skipped importing the " + texture + " texture (missing?)")
                    
            if texture_list['dyeslot']:
                texture_path_full = self.file_path + "/" + armor['name'] + "/textures/" + texture_list['dyeslot']
                self.change_texture('dyeslot', texture_path_full, new_shader)
            if incomplete:
                self.incomplete_armors.append(armor['name'])
            self.imported_armors.append(armor['name'])
            print(divider)
        self.show_incompletes()
            
    def prelim_check(self):
        if self.mats.find("player_shader") == -1:
            raise ValueError('Missing player shader!! (please have one named [player_shader])')
        else:
            shader_nodes = self.mats.get("player_shader")
            shader_nodes = shader_nodes.node_tree.nodes.keys() #gets the keys (names) of the nodes in the shader
            for node in ["Dye Slot Texture (optional)", "Diffuse Texture", "Normal Map", "Gstack Texture"]:
                if node not in shader_nodes:
                    raise ValueError('Incomplete player shader!!\nPlease get a player shader with all texture types (including dyeslot)')
        print("PRELIM CHECK SUCCESS")

    def change_texture(self, texture_type, texture_path_full, mat): #should pass the full texture path 'C:/....diffuse.png'
        texture_node = mat.node_tree.nodes.get(self.texture_map[texture_type])
        texture_node.image = bpy.data.images.load(texture_path_full)
        if texture_type == "gstack" or texture_type == 'normal':
            texture_node.image.colorspace_settings.name = "Non-Color"

    def show_incompletes(self):
        if len(self.incomplete_armors) == 0:
            print("All armors filled successfully! No incomplete armors")
        else:
            print("Please check the following armors for missing textures (otherwise, it works!):")
            for armor in self.incomplete_armors:
                print(armor + "\n")
    
    
    #do this if you're gonna deal with materials n stuff
    def texture_setup(self, file_path, armor_list):
        self.file_path = file_path
        self.armor_list = armor_list
        self.mats = bpy.data.materials
        
    def import_model(self, file_path):
        bpy.ops.wm.collada_import(filepath = file_path + "/model.dae")
    
    def mesh_manipulate(self): #cleans mesh and adds materials
        self.name_map = self.map_names()
        print(self.name_map)
        for armor in self.name_map: #name map organized like 'mat name':[meshes corresponding]
            if self.name_map[armor] == []:
                print("MISSING MAP FOR [" + armor + "] PLEASE APPLY THIS MATERIAL MANUALLY.")
            else:
                print("adding [" + armor + "] material to their meshes")
                mat = bpy.data.materials.get(armor)
                print(mat.name)
                for mesh in self.name_map[armor]:
                    mesh_to_manipulate = bpy.data.objects.get(mesh)
                    mesh_to_manipulate.data.materials.append(mat)
        print("CLEANING  YOUR MESHES")
        
        bpy.ops.object.mode_set(mode = "OBJECT")
        bpy.ops.object.select_by_type(type = 'MESH')
        bpy.ops.object.mode_set(mode = "EDIT")
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode = "OBJECT")
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        
            
    def map_names(self):
        mesh_keys = bpy.data.objects.keys()
        name_map = {}
        for armor in self.imported_armors: #iterates through material names
            armor_mat = bpy.data.materials.get(armor)
            armor_meshes = []
            for mesh in mesh_keys: #iterates through every mesh avaiable
                if len(mesh.split(".")) == 3:
                    print("armor is [" + self.mat_name_translate(armor) + "] and mesh is [" + self.mesh_name_translate(mesh) +  "]")
                    if self.mat_name_translate(armor) == self.mesh_name_translate(mesh):
                        armor_meshes.append(mesh) #appends mesh name like 'Male-Anti-Extinction'
            name_map[armor] = armor_meshes
        return name_map
                
    def mat_name_translate(self, name): #example: titan_anti_greaves_m -> male_anti_greaves
        translated = ""
        mesh_name = name.split("_")
        if mesh_name[-1] == "m":
            translated += "male"
        else:
            translated += "female"
        translated += "_"
        translated += '_'.join(mesh_name[1:-1])
        return translated
    
    def mesh_name_translate(self, name): #example: Female-Mighty-Mark.00.000 -> female_mighty_mark
        return '_'.join((''.join(name.split('.')[0]).split("-"))).lower()




    #SHADER HANDLER
    def do_shaders(self): #shader_path should look like C:/Users/rez/Documents/BLENDERFILES/DESTINYMODELS/SHADERS/ 
        print(divider)
        print("Input all the shaders you want used, separated by commas, no spaces between them.")
        print("Make sure they're also in order, and duplicate the ones that need duplicating.")
        print("MAKE SURE THEY'RE SPELLED EXACTLY AS THEY WERE ORIGINALLY, CAPITALIZATION TOO")
        self.shader_list = input().split(",")
        print("input your shaders folder")
        self.shader_path = flip(input())
        print(divider)


        shader_map = self.show_materials() #should look like {"metro shift":"titan male bruh chestpiece"}

        for shader in shader_map:

            #creates the shader if it doesn't already exist
            if bpy.data.node_groups.get(shader) == None: 
                shader_og = shader #used to name the shader
                cleaned_name = shader_og.replace("_", "'") #calus_s armor -> calus's armor
                py_name = cleaned_name.split(" ")[0].split("'") #calus_s armor -> calus-s-armor i hate everything
                py_name.append("armor")
                py_name = '-'.join(py_name) 
                
                path_to_shader = self.shader_path + "/" + shader_og + "/" + cleaned_name + "/DestinyModel0/Shaders/Blender/"
                print(path_to_shader)
                sys.path.append(path_to_shader) #append to path to import immediately
                
                armor_py = importlib.import_module(py_name) #import
                armor_py.riplocation = (self.shader_path + "/" + shader_og + "/" + cleaned_name + "/DestinyModel0") #set rip location for shader to get textures
                armor_py.create_test_group("this doesn't matter", "neither does this", shader_og) #create node group
            
            for mat_name in shader_map[shader]:
                mat = bpy.data.materials.get(mat_name)
                shader_node = mat.node_tree.nodes.get("Group") #get group instance
                player_node = mat.node_tree.nodes.get("Group.001")
                
                shader_node.node_tree = bpy.data.node_groups.get(shader) #replace group's node_tree with the node_group we just created
                
                for socket in range(0, 13):
                    mat.node_tree.links.new(shader_node.outputs[socket], player_node.inputs[socket+4])
                
                print("applied shader for [" + mat_name + "]")
    
    def show_materials(self):
        print(divider)
        print("This will guide you through the shader mapping process")
        print("You will be shown a list of materials, some may be guardian materials, some may not")
        print("They will be numbered starting from 0")
        print("Enter the numbers in ORDER of the shaders you listed")
        print("No more, no less (If you have 5 shaders an input would look like [5,2,4,3,0])")
        print("Ensure the materials you want the shaders applied to have [titan] [warlock] or [hunter] in them somewhere")
        print("press [enter] to continue")
        fake = input()

        count = 0
        print(divider)
        keys_clean = []
        for key in bpy.data.materials.keys():
            for id in ['titan', 'warlock', 'hunter']:
                if id in key.lower():
                    keys_clean.append(key)
                    print(f'[{count}] {key}\n')
                    count+=1
        print(divider)
        print(f"You have [{len(self.shader_list)}] shaders. Make sure you ONLY enter {len(self.shader_list)} objects (corresponding to shader order)")
        print(self.shader_list)
        print(divider)
        map_input = input().split(",") #looks like 5,3,2,6,1 corresponding to cleaned materials in order

        shader_map = {}
        print(map_input)
        print(keys_clean)
        for i in range(0, len(map_input)):
            
            if self.shader_list[i] not in shader_map:
                shader_map[self.shader_list[i]] = [keys_clean[int(map_input[i])]]
            else:
                shader_map[self.shader_list[i]].append(keys_clean[int(map_input[i])])
        print(shader_map)
        return shader_map




                


        




#utils
def flip(file_path):
    file_flipped = file_path
    if(len(file_flipped.split("\\")) == 1):
        return file_flipped
    else:
        file_flipped = file_flipped.split("\\")
        file_flipped = "/".join(file_flipped)
    return file_flipped




#Toggles whether to import models or textures
import_option = ""
#------------------------------------------
#ALL REQUIRED FOR TEXTURE OR MODEL IMPORT
file_path = "" 
g_class = "" 
gender = "" 
#------------------------------------------
#chooses whether to import shaders
shader_toggle = ""
#------------------------------------------
#REQUIRED FOR SHADER IMPORT
shader_bool = False
#------------------------------------------

blend = Blender_time()

print(divider)
while import_option not in ["model", "textures", "both", "none"]:
    print("Import models or textures? [models] [textures] [both] [none]")
    import_option = input()

if import_option != "none":
    #import MODELS/TEXTURE
    print("enter DARE output path (e.x. C:/Users/rez/Documents/DARE Output/DestinyModel9) (slash direction doesn't matter)")
    file_path = input()
    file_path = flip(file_path)

    g_class = "" 
    while(g_class not in ["warlock", "hunter", "titan", "no"]):
        print("enter class (warlock, hunter, titan) or type [no] to import all textures regardless of class")
        g_class = input()
        #g_class = "titan"

    gender = "" 
    while(gender not in ["f", "m", "no"]):
        print("enter [f] or [m] or type [no] to import all textures regardless of gender")
        gender = input()
        #gender = "f"

    if import_option == "textures" or import_option == "both":
        print("importing textures")
        #initialize armor class, get texture list
        guardian = Armor(file_path + "/HD_Textures", g_class, gender) 
        guardian.do_the_thing() 
        #guardian.show_textures() 
        all_textures = guardian.return_textures() 
        blend.texture_setup(file_path + "/HD_Textures", all_textures)
        blend.import_the_textures()
    if import_option == "model" or import_option == "both":
        print("importing model")
        blend.import_model(file_path)
        blend.mesh_manipulate() #add materials + delete loose things

print("Add shaders (VERY BETA YOU WILL SEE LOTS OF TEXT AND PRECISE INSTRUCTION)? [yes] or [no]")
print("DO NOT DO IF YOU DON'T HAVE EVERY SHADER DOWNLOADED AND UNPACKED")
shader_toggle = input()

if shader_toggle == "yes":
    blend.do_shaders()
    


"""
safety = "" 
while(safety.lower() not in ["yes", "no"]):
    print("Do you want to turn on safety measures? [yes] or [no]")
    print("(It might crash horrifically if it does idk)")
    print("but this doesn't actually do anything right now so don't worry")
    safety = input()
    #safety = "yes"
"""