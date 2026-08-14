import xml.etree.ElementTree as ET
import numpy as np

tree = ET.parse('/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro')
root = tree.getroot()

joints = {}
for j in root.findall('joint'):
    name = j.get('name')
    parent = j.find('parent').get('link')
    child = j.find('child').get('link')
    origin = j.find('origin')
    xyz = [float(x) for x in origin.get('xyz', '0 0 0').split()] if origin is not None else [0., 0., 0.]
    rpy = [float(x) for x in origin.get('rpy', '0 0 0').split()] if origin is not None else [0., 0., 0.]
    joints[child] = (parent, xyz, rpy)

def get_world_pos(link_name):
    pos = np.array([0., 0., 0.])
    curr = link_name
    chain = []
    while curr in joints:
        parent, xyz, rpy = joints[curr]
        chain.append((curr, parent, xyz))
        # Note: since RPY is 0 for these joints (except some), we can just sum xyz if no rotations are active
        # Let's check if any joint in the chain has non-zero rpy.
        if any(abs(r) > 1e-5 for r in rpy):
            print(f"Warning: joint {curr} has non-zero RPY: {rpy}")
        pos += np.array(xyz)
        curr = parent
    return pos, chain

for link in ['right_elbow_link_2', 'wrist_link_1', 'ee_link', 'elbow_link_2']:
    pos, chain = get_world_pos(link)
    print(f"\nLink: {link}")
    print(f"  Cumulated XYZ from joints: {pos}")
    print(f"  Chain: {chain}")
