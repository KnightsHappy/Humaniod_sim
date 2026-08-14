import xml.etree.ElementTree as ET

tree = ET.parse('/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro')
root = tree.getroot()

for link in root.findall('link'):
    link_name = link.get('name')
    for i, visual in enumerate(link.findall('visual')):
        geom = visual.find('geometry')
        if geom is not None:
            mesh = geom.find('mesh')
            if mesh is not None:
                filename = mesh.get('filename')
                if any(x in filename for x in ['Part_1', 'Part_13', 'Part 1', 'Part 13']):
                    origin = visual.find('origin')
                    xyz = origin.get('xyz') if origin is not None else "0 0 0"
                    rpy = origin.get('rpy') if origin is not None else "0 0 0"
                    print(f"Link: {link_name} | Visual {i} | Mesh: {filename} | XYZ: {xyz} | RPY: {rpy}")
