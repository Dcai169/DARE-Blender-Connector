# DARE Blender Connector

Allows for one-click model ripping from [DARE](https://github.com/Dcai169/Destiny-API-Ripper-Extension).

## Features

* Imports `model.dae` if applicable.
* Deletes default armature.
* Cleans loose vertices.
* Imports shader `.py` files.
  * If an item name includes a period (.), the shader script for that item will not be imported.

## Manual Installation Instructions

1. Close all instances of Blender.
2. Copy `dare_bc.py` to `%APPDATA%\Blender Foundation\Blender\3.0\scripts\addons` (Windows) or `~/.config/blender/3.0/scripts/addons` (Linux).
3. Enable DARE Blender Connector in DARE settings.

### Stretch Goals

* Import template shader material.
* Assign each imported mesh a copy of the template shader material.
* Assign shader to corresponding shader materials.
* Assign textures to corresponding inputs.

### Credits

* [RezPlz](https://github.com/ThickPython): Prototype implementation
* [BIOS](https://github.com/TiredHobgoblin): Technical support
