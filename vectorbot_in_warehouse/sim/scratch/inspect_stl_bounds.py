import os
import struct

def get_stl_bounding_box(filepath):
    # Parse binary or ASCII STL
    try:
        with open(filepath, 'rb') as f:
            header = f.read(80)
            if len(header) < 80:
                return None
            num_triangles_data = f.read(4)
            if len(num_triangles_data) < 4:
                return None
            num_triangles = struct.unpack('<I', num_triangles_data)[0]
            
            # Check if file size matches binary STL
            expected_size = 80 + 4 + num_triangles * 50
            file_size = os.path.getsize(filepath)
            
            min_x, max_x = float('inf'), float('-inf')
            min_y, max_y = float('inf'), float('-inf')
            min_z, max_z = float('inf'), float('-inf')
            
            if abs(file_size - expected_size) < 100:
                # Binary STL
                for _ in range(num_triangles):
                    # read normal (12 bytes), 3 vertices (36 bytes), attribute byte count (2 bytes) = 50 bytes
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
            else:
                # ASCII STL
                f.seek(0)
                lines = f.readlines()
                for line in lines:
                    line = line.strip().lower()
                    if line.startswith(b'vertex'):
                        parts = line.split()
                        v = [float(parts[1]), float(parts[2]), float(parts[3])]
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
files = ["Part_1.stl", "Part_1_1.stl", "Part_1_2.stl", "Part_1_4.stl"]

for fname in files:
    path = os.path.join(mesh_dir, fname)
    if os.path.exists(path):
        bounds = get_stl_bounding_box(path)
        if bounds:
            (x1, x2), (y1, y2), (z1, z2) = bounds
            print(f"\nFile: {fname}")
            print(f"  X: [{x1:.4f}, {x2:.4f}] -> size: {x2-x1:.4f}")
            print(f"  Y: [{y1:.4f}, {y2:.4f}] -> size: {y2-y1:.4f}")
            print(f"  Z: [{z1:.4f}, {z2:.4f}] -> size: {z2-z1:.4f}")
        else:
            print(f"\nFile: {fname} failed to parse or empty")
    else:
        print(f"\nFile: {fname} not found")
