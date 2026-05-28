# COLMOD - Collision Mesh Generator for Blender

A Blender addon for creating collision meshes optimized for game engines like Unreal Engine.

## Features

- **Create Mass Hull**: Generates a single convex hull collision around all selected objects or face groups
- **Create Individual Hulls**: Creates separate convex hull collisions for each selected object or face group
- **Create Box Collision**: Creates axis-aligned bounding boxes around selected objects or vertices

## Installation

1. Download the addon as a ZIP file
2. In Blender, go to **Edit > Preferences > Add-ons**
3. Click **Install...** and select the ZIP file
4. Enable the addon by checking the box next to "COLMOD - Collision Mesh Generator"

## Usage

### Panel Location
The COLMOD panel appears in the **3D Viewport > N-Panel > COLMOD**

### Controls
- **Decimation Ratio**: Adjusts the simplification level (0.01-1.0, lower = more simplified)
- **Create Mass Hull**: Single convex hull for all selected objects
- **Create Individual Hulls**: Separate convex hull for each selected object
- **Create Box Collision**: Axis-aligned bounding box for selection

### Workflow

#### Object Mode
1. Select one or more mesh objects
2. Click the desired collision button
3. Collision mesh(es) will be created with appropriate naming

#### Edit Mode (for face/vertex selection)
1. Enter Edit Mode on a mesh
2. Select faces or vertices
3. Click the desired collision button
4. Collision will be created from the selected geometry

### Naming Conventions
- **UCX_**: Convex hull collisions (Unreal Engine standard)
- **UBX_**: Box collisions (Unreal Engine standard)

Each collision object gets a unique name with an incrementing suffix (e.g., `UCX_MyObject_01`, `UCX_MyObject_02`)

## Technical Details

- **Blender Version**: 5.1+
- **Material**: Collision meshes use a "collision" material (loaded from `materials.blend` or created as fallback)
- **Original Meshes**: Never modified - all operations create new objects
- **Selection**: Original selection is preserved after collision creation
- **Mode**: Original mode (Object/Edit) is restored after operation

## Requirements

- Blender 5.1 or later
- The addon includes a `materials.blend` file with a pre-configured collision material

## License

This addon is provided as-is. See LICENSE file for details.
