# Blender Add-On: Screen-Space Hatch Lines

This Blender 4.4+ add-on draws hatch lines of the scene as Grease Pencil v3 strokes.
The hatch lines are computed with a screen-space algorithm following Jobard and Lefer’s paper from 1997 on "Creating Evenly-Spaced Streamlines of Arbitrary Density."
The input data for the algorithm is computed via a custom fragment shader.

## Installation

1. Download the contents of the repository as a ZIP file (Code > Download ZIP).

2. Install in Blender:
   - Open Blender and go to Edit > Preferences
   - Select the "Add-ons" tab
   - Select "Install from Disk..." and navigate to the downloaded ZIP file

## Usage

The hatch line controls can be found in the Sidebar of the 3D Viewport (press N to toggle) under the "Hatch Lines" tab.

## Development

Install [fake-bpy-module](https://github.com/nutti/fake-bpy-module) for code completion.
