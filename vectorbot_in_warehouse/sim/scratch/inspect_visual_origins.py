import xml.etree.ElementTree as ET

def analyze_urdf(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    for link in root.findall('link'):
        link_name = link.get('name')
        visuals = link.findall('visual')
        if not visuals:
            continue
            
        z_coords = []
        x_coords = []
        y_coords = []
        for vis in visuals:
            origin = vis.find('origin')
            if origin is not None and origin.get('xyz') is not None:
                xyz = [float(val) for val in origin.get('xyz').split()]
                x_coords.append(xyz[0])
                y_coords.append(xyz[1])
                z_coords.append(xyz[2])
        
        if z_coords:
            print(f"Link: {link_name}")
            print(f"  Count of visuals: {len(z_coords)}")
            print(f"  X range: {min(x_coords):.4f} to {max(x_coords):.4f}")
            print(f"  Y range: {min(y_coords):.4f} to {max(y_coords):.4f}")
            print(f"  Z range: {min(z_coords):.4f} to {max(z_coords):.4f}")
            print("-" * 40)

if __name__ == '__main__':
    analyze_urdf('/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro')
