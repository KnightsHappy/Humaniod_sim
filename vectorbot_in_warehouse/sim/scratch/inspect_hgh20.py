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

for link in root.findall('link'):
    link_name = link.get('name')
    for i, visual in enumerate(link.findall('visual')):
        geom = visual.find('geometry')
        if geom is not None:
            mesh = geom.find('mesh')
            if mesh is not None:
                filename = mesh.get('filename')
                if 'HGH20' in filename:
                    origin = visual.find('origin')
                    xyz = origin.get('xyz') if origin is not None else "0 0 0"
                    rpy = origin.get('rpy') if origin is not None else "0 0 0"
                    
                    # Get mesh name from URI
                    mesh_name = os.path.basename(filename)
                    path = os.path.join(mesh_dir, mesh_name)
                    bounds = get_stl_bounding_box(path)
                    if bounds:
                        (x1, x2), (y1, y2), (z1, z2) = bounds
                        print(f"\nLink: {link_name} | Visual {i} | Mesh: {mesh_name}")
                        print(f"  XYZ: {xyz} | RPY: {rpy}")
                        print(f"  Local Z bounds: [{z1:.6f}, {z2:.6f}], size={z2-z1:.6f}")
                        # Compute absolute bounds in base coordinates if Link is base_link
                        # Or relative to the link
                        offset_parts = [float(x) for x in xyz.split()]
                        print(f"  Link Z bounds: [{z1 + offset_parts[2]:.6f}, {z2 + offset_parts[2]:.6f}]")
