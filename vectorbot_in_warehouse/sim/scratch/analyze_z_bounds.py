import os
import struct
import xml.etree.ElementTree as ET

def get_stl_bounding_box(filepath):
    try:
        with open(filepath, 'rb') as f:
            header = f.read(80)
            if len(header) < 80:
                return None
            num_triangles_data = f.read(4)
            if len(num_triangles_data) < 4:
                return None
            num_triangles = struct.unpack('<I', num_triangles_data)[0]
            expected_size = 80 + 4 + num_triangles * 50
            file_size = os.path.getsize(filepath)
            
            min_x, max_x = float('inf'), float('-inf')
            min_y, max_y = float('inf'), float('-inf')
            min_z, max_z = float('inf'), float('-inf')
            
            if abs(file_size - expected_size) < 100:
                for _ in range(num_triangles):
                    data = f.read(50)
                    if len(data) < 50:
                        break
                    v1 = struct.unpack('<fff', data[12:24])
                    v2 = struct.unpack('<fff', data[24:36])
                    v3 = struct.unpack('<fff', data[36:48])
                    for v in (v1, v2, v3):
                        min_x = min(min_x, v[0])
                        max_x = max(max_x, v[0])
                        min_y = min(min_y, v[1])
                        max_y = max(max_y, v[1])
                        min_z = min(min_z, v[2])
                        max_z = max(max_z, v[2])
            return (min_x, max_x), (min_y, max_y), (min_z, max_z)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

tree = ET.parse('/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro')
root = tree.getroot()
mesh_dir = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/meshes"

base_visuals = []
torso_visuals = []

def parse_origin(origin_elem):
    if origin_elem is None:
        return [0., 0., 0.], [0., 0., 0.]
    xyz = [float(x) for x in origin_elem.get('xyz', '0 0 0').split()]
    rpy = [float(x) for x in origin_elem.get('rpy', '0 0 0').split()]
    return xyz, rpy

for link in root.findall('link'):
    link_name = link.get('name')
    if link_name not in ['base_link', 'torso_link']:
        continue
    
    for i, visual in enumerate(link.findall('visual')):
        geom = visual.find('geometry')
        if geom is None:
            continue
        mesh = geom.find('mesh')
        if mesh is None:
            continue
        filename = mesh.get('filename')
        mesh_name = os.path.basename(filename)
        path = os.path.join(mesh_dir, mesh_name)
        
        bounds = get_stl_bounding_box(path)
        if not bounds:
            continue
            
        xyz, rpy = parse_origin(visual.find('origin'))
        
        # Calculate bounding box after applying origin.
        # Since rpy can have rotations (like 180 around Z, or 90 around Y),
        # let's write a simple rotation logic to get the bounds correct.
        import scipy.spatial.transform
        import numpy as np
        
        r = scipy.spatial.transform.Rotation.from_euler('xyz', rpy)
        # We can approximate the rotated bounds by transforming the 8 corners of the box.
        (x1, x2), (y1, y2), (z1, z2) = bounds
        corners = np.array([
            [x1, y1, z1], [x1, y1, z2], [x1, y2, z1], [x1, y2, z2],
            [x2, y1, z1], [x2, y1, z2], [x2, y2, z1], [x2, y2, z2]
        ])
        rotated_corners = r.apply(corners)
        transformed_corners = rotated_corners + np.array(xyz)
        
        min_bounds = transformed_corners.min(axis=0)
        max_bounds = transformed_corners.max(axis=0)
        
        info = {
            'mesh': mesh_name,
            'visual_idx': i,
            'min_z': min_bounds[2],
            'max_z': max_bounds[2],
            'xyz': xyz,
            'rpy': rpy
        }
        if link_name == 'base_link':
            base_visuals.append(info)
        else:
            torso_visuals.append(info)

print("--- base_link Visuals sorted by Max Z ---")
base_visuals.sort(key=lambda x: x['max_z'])
for v in base_visuals:
    print(f"Mesh: {v['mesh']:<35} | Visual: {v['visual_idx']:<3} | Z bounds: [{v['min_z']:.4f}, {v['max_z']:.4f}] | XYZ: {v['xyz']}")

print("\n--- torso_link Visuals sorted by Max Z (relative to torso_link frame) ---")
torso_visuals.sort(key=lambda x: x['max_z'])
for v in torso_visuals:
    print(f"Mesh: {v['mesh']:<35} | Visual: {v['visual_idx']:<3} | Z bounds: [{v['min_z']:.4f}, {v['max_z']:.4f}] | XYZ: {v['xyz']}")
