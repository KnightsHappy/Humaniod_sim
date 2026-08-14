import os
import struct

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

mesh_dir = "sim/vector_description/meshes"

# List of files we want to inspect
files_to_check = [
    "Part_1_5.stl", # Part 1 <1> under Assembly 13 (base)
    "Part_13_1.stl", # Part 13 <1> under Top-lidar (base)
    "Part_13_2.stl", # Part 13 <1> under Torso (torso)
    "Part_1_7.stl"   # Part 1 <1> under Torso (torso)
]

for fname in files_to_check:
    path = os.path.join(mesh_dir, fname)
    if os.path.exists(path):
        bounds = get_stl_bounding_box(path)
        if bounds:
            (x1, x2), (y1, y2), (z1, z2) = bounds
            print(f"\nFile: {fname}")
            print(f"  Local X: [{x1:.6f}, {x2:.6f}], size={x2-x1:.6f}")
            print(f"  Local Y: [{y1:.6f}, {y2:.6f}], size={y2-y1:.6f}")
            print(f"  Local Z: [{z1:.6f}, {z2:.6f}], size={z2-z1:.6f}")
