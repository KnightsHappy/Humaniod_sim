"""
Applies uniform mass/inertia scaling to vector.xacro so that total mass = 110 kg.
Reads values from temp_vector.urdf (already compiled), computes scale factor,
then applies the updates directly to vector.xacro using regex-based replacement.

Safe approach: we find each <link name="X"> block in the xacro and replace only
the <mass value="..."/> and <inertia .../> lines inside it.
"""
import re
import xml.etree.ElementTree as ET

URDF_PATH  = "/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/temp_vector.urdf"
XACRO_PATH = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
TARGET_MASS = 110.0  # kg

# ── Step 1: read current masses from URDF ──────────────────────────────────
tree = ET.parse(URDF_PATH)
root = tree.getroot()

total_mass = 0.0
link_data  = {}   # name → {mass, ixx, ixy, ixz, iyy, iyz, izz}

for link in root.findall("link"):
    inertial = link.find("inertial")
    if inertial is None:
        continue
    mass_el = inertial.find("mass")
    if mass_el is None:
        continue
    name = link.get("name")
    m    = float(mass_el.get("value"))
    total_mass += m

    inertia_el = inertial.find("inertia")
    link_data[name] = {
        "mass": m,
        "ixx": float(inertia_el.get("ixx", 0)),
        "ixy": float(inertia_el.get("ixy", 0)),
        "ixz": float(inertia_el.get("ixz", 0)),
        "iyy": float(inertia_el.get("iyy", 0)),
        "iyz": float(inertia_el.get("iyz", 0)),
        "izz": float(inertia_el.get("izz", 0)),
    }

k = TARGET_MASS / total_mass
print(f"Current total mass: {total_mass:.4f} kg")
print(f"Target total mass:  {TARGET_MASS:.4f} kg")
print(f"Scale factor k:     {k:.8f}\n")

# ── Step 2: read xacro source ──────────────────────────────────────────────
with open(XACRO_PATH, "r") as f:
    xacro_text = f.read()

# ── Step 3: patch each link ────────────────────────────────────────────────
changes = 0
for name, d in link_data.items():
    new_mass = d["mass"] * k
    new_ixx  = d["ixx"]  * k
    new_ixy  = d["ixy"]  * k
    new_ixz  = d["ixz"]  * k
    new_iyy  = d["iyy"]  * k
    new_iyz  = d["iyz"]  * k
    new_izz  = d["izz"]  * k

    # --- replace <mass value="OLD"/> ---
    old_mass_str = f'{d["mass"]:.6f}'
    # Also try scientific notation variants
    old_mass_candidates = [
        f'{d["mass"]:.6f}',
        f'{d["mass"]:.1f}',
        f'{d["mass"]}',
    ]
    # Use a regex that matches the exact value (allowing slight formatting)
    mass_pattern = r'(<mass\s+value=")([^"]+)(")'

    def replace_mass_in_block(block_text, new_val):
        return re.sub(mass_pattern,
                      lambda m: f'{m.group(1)}{new_val:.6f}{m.group(3)}',
                      block_text, count=1)

    # --- replace <inertia .../> ---
    inertia_pattern = (
        r'<inertia\s+'
        r'ixx="[^"]*"\s+ixy="[^"]*"\s+ixz="[^"]*"\s+'
        r'iyy="[^"]*"\s+iyz="[^"]*"\s+izz="[^"]*"\s*/>'
    )
    new_inertia_str = (
        f'<inertia ixx="{new_ixx:.9e}" ixy="{new_ixy:.9e}" ixz="{new_ixz:.9e}" '
        f'iyy="{new_iyy:.9e}" iyz="{new_iyz:.9e}" izz="{new_izz:.9e}" />'
    )

    # Find the link block boundaries in the xacro
    # Pattern: <link name="NAME"> ... </link>
    link_block_pattern = rf'(<link\s+name="{re.escape(name)}".*?</link>)'
    link_match = re.search(link_block_pattern, xacro_text, re.DOTALL)
    if link_match is None:
        print(f"  [SKIP] Could not find link block: {name}")
        continue

    original_block = link_match.group(1)
    patched_block  = original_block

    # Patch mass
    patched_block = re.sub(mass_pattern,
                            lambda m: f'{m.group(1)}{new_mass:.6f}{m.group(3)}',
                            patched_block, count=1)

    # Patch inertia
    patched_block = re.sub(inertia_pattern, new_inertia_str, patched_block, count=1)

    if patched_block != original_block:
        xacro_text = xacro_text.replace(original_block, patched_block, 1)
        print(f"  [OK]   {name:<45} mass: {d['mass']:.4f} → {new_mass:.4f} kg")
        changes += 1
    else:
        print(f"  [WARN] No change for {name}")

print(f"\nTotal links patched: {changes}")

# ── Step 4: write back ─────────────────────────────────────────────────────
with open(XACRO_PATH, "w") as f:
    f.write(xacro_text)
print(f"Saved: {XACRO_PATH}")
