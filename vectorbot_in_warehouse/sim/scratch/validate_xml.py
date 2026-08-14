import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

try:
    tree = ET.parse(xacro_path)
    print("XML Parsing SUCCESSFUL! No syntax/tag structure errors.")
except Exception as e:
    print(f"XML Parsing FAILED: {e}")
