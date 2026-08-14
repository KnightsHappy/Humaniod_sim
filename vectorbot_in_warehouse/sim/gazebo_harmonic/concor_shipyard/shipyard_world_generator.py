import os
from PIL import Image, ImageDraw, ImageFont

# Configuration
ROWS = 3            # Number of rows
COLS = 10           # Containers per row
STACK_HEIGHT = 3    # How many high

SPACING_X = 6.06 + 0.2 # X spacing
SPACING_Y = 2.44 + 10.0  # Y spacing (10m aisle for the robot)
CONTAINER_HEIGHT = 2.59       # Z spacing

os.makedirs("models", exist_ok=True)

def create_label(text, filename):
    img = Image.new('RGB', (200, 500), color='white')
    d = ImageDraw.Draw(img)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 35) # Size 45 for bold visibility
    except:
        print("System font not found, using default (will be small).")
        font = ImageFont.load_default()
    
    clean_text = text.replace("\n\n", " ")

    current_y = 20
    x_position = 85  # Centered horizontally for a 200px wide image
    line_spacing = 30 # Pixels between letters
    
    for char in clean_text:
        d.text((x_position, current_y), char, fill=(0, 0, 0), font=font)
        current_y += line_spacing

    img = img.rotate(90, expand=True)
    img.save(filename)

def create_model(row, col, stack):
    container_id = f"R{row}C{col}S{stack}"
    model_name = f"container_{container_id}"
    model_path = f"models/{model_name}"
    os.makedirs(f"{model_path}/materials/textures", exist_ok=True)

    # Generate unique texture
    texture_filename = f"label_{container_id}.png"
    texture_path = f"{model_path}/materials/textures/{texture_filename}"
    create_label(f"CONCOR\n{container_id}", texture_path)

    # Generate the model.sdf (Simplified with our black edges and the unique label)
    sdf_content = f"""<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="{model_name}">
    <static>true</static>
    <link name="link">
      <visual name="body"><geometry><box><size>6.06 2.44 2.59</size></box></geometry>
        <material><ambient>0 0.3 0.6 1</ambient><diffuse>0 0.3 0.6 1</diffuse></material>
      </visual>

                 <visual name="vertical_edge_1">
                <pose>3.03 1.22 0 0 0 0</pose>
                <geometry><box><size>0.1 0.1 2.59</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="vertical_edge_2">
                <pose>3.03 -1.22 0 0 0 0</pose>
                <geometry><box><size>0.1 0.1 2.59</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="vertical_edge_3">
                <pose>-3.03 1.22 0 0 0 0</pose>
                <geometry><box><size>0.1 0.1 2.59</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="vertical_edge_4">
                <pose>-3.03 -1.22 0 0 0 0</pose>
                <geometry><box><size>0.1 0.1 2.59</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="edge_long_top_left">
                <pose>0 1.22 1.295 0 0 0</pose>
                <geometry><box><size>6.06 0.1 0.1</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="edge_long_top_right">
                <pose>0 -1.22 1.295 0 0 0</pose>
                <geometry><box><size>6.06 0.1 0.1</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="edge_long_bottom_left">
                <pose>0 1.22 -1.295 0 0 0</pose>
                <geometry><box><size>6.06 0.1 0.1</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="edge_long_bottom_right">
                <pose>0 -1.22 -1.295 0 0 0</pose>
                <geometry><box><size>6.06 0.1 0.1</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>

            <visual name="edge_width_top_front">
                <pose>3.03 0 1.295 0 0 0</pose>
                <geometry><box><size>0.1 2.44 0.1</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>
            <visual name="edge_width_top_back">
                <pose>-3.03 0 1.295 0 0 0</pose>
                <geometry><box><size>0.1 2.44 0.1</size></box></geometry>
                <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
            </visual>

      <visual name="id_plate">
        <pose>2.8 1.226 0.5 0 1.5708 1.5708</pose>
        <geometry><plane><normal>0 0 1</normal><size>1.2 0.4</size></plane></geometry>
        <material><pbr><metal><albedo_map>model://{model_name}/materials/textures/{texture_filename}</albedo_map>
        <emissive_map>model://{model_name}/materials/textures/{texture_filename}</emissive_map></metal></pbr></material>
      </visual>
      </link>
  </model>
</sdf>"""
    
    with open(f"{model_path}/model.sdf", "w") as f: f.write(sdf_content)
    with open(f"{model_path}/model.config", "w") as f:
        f.write(f"<?xml version='1.0'?><model><name>{model_name}</name><version>1.0</version><sdf version='1.8'>model.sdf</sdf></model>")
    
    return model_name

world_sdf_file_header = """<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="concor_shipyard">
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <spherical_coordinates>
      <surface_model>EARTH_WGS84</surface_model>
      <world_frame_orientation>ENU</world_frame_orientation> <latitude_deg>37.7749</latitude_deg> <longitude_deg>-122.4194</longitude_deg>
      <elevation>0</elevation>
      <heading_deg>0</heading_deg>
    </spherical_coordinates>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics" />
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands" />
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster" />
    
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-navsat-system" name="gz::sim::systems::NavSat" />

    <scene>
        <ambient>0.6 0.6 0.6 1</ambient>
        <background>0.5 0.7 0.9 1</background>
        <shadows>true</shadows>
        <sky>
            <clouds>
                <speed>12</speed>
            </clouds>
        </sky>
    </scene>
    
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>100 100 100 0 0 0</pose>
      <diffuse>1.0 0.9 0.5 1</diffuse>
      <specular>0.5 0.5 0.5 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry>
          <material>
            <ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse>
            <pbr><metal><albedo_map>materials/textures/concrete_diffuse.jpg</albedo_map></metal></pbr>
          </material>
        </visual>
      </link>
    </model>

    <include>
      <name>robot</name>
      <uri>model://shipyard_robot</uri>
      <pose>0 5 0.5 0 0 0</pose>
    </include>
"""

world_sdf_file_footer = """
  </world>
</sdf>
"""

with open("shipyard_generated.sdf", "w") as f:
    f.write(world_sdf_file_header)
    for r in range(ROWS):
        for c in range(COLS):
            for s in range(STACK_HEIGHT):
                m_name = create_model(r, c, s)
                x, y, z = c * SPACING_X, r * SPACING_Y, (s * CONTAINER_HEIGHT) + (CONTAINER_HEIGHT/2)

                f.write(f"<include><name>{m_name}</name><uri>model://{m_name}</uri><pose>{x} {y} {z} 0 0 0</pose></include>")
    f.write(world_sdf_file_footer)

print("Generated shipyard_generated.sdf!")