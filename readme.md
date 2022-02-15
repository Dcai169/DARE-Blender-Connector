# DARE Blender Connector

Allows for one-click model ripping from [DARE](https://github.com/Dcai169/Destiny-API-Ripper-Extension).

## Features

* Imports `model.dae` if applicable.
* Deletes default armature.
* Cleans loose vertices.
* Imports shader `.py` files.
  * If an item name includes a period (.), the shader script for that item will not be imported.
* Composites HD texture plates into one image.

## Prerequisites
* DARE >= v1.6.2
* DARE Blender Connector >= v1.0.0
* DCG >= v1.7.10

## Manual Installation Instructions

1. Launch Blender as an administrator.
2. Install and enable `dare_bc.py` with the Blender add-on manager.
3. Enable DARE Blender Connector in DARE settings.
4. Restart Blender.

### Stretch Goals

* Import template shader material.
* Assign each imported mesh a copy of the template shader material.
* Assign shader to corresponding shader materials.
* Assign textures to corresponding inputs.

### Credits

* [RezPlz](https://github.com/ThickPython): Prototype implementation
* [BIOS](https://github.com/TiredHobgoblin): Technical support
