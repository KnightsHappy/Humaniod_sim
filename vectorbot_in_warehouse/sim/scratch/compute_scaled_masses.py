"""
Scales ALL link masses and inertias in vector.xacro by a uniform factor
so that total robot mass = TARGET_MASS_KG, while preserving COM position.

COM is preserved because:
  COM = Σ(mᵢ * rᵢ) / Σmᵢ
  → scaling all mᵢ by k → k cancels → COM unchanged.
"""
import xml.etree.ElementTree as ET

URDF_PATH  = "/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/temp_vector.urdf"
TARGET_MASS = 110.0  # kg

tree = ET.parse(URDF_PATH)
root = tree.getroot()

# ── Step 1: compute current total mass ────────────────────────────────────────
total_mass = 0.0
links_with_inertial = []
for link in root.findall("link"):
    inertial = link.find("inertial")
    if inertial is None:
        continue
    mass_el = inertial.find("mass")
    if mass_el is None:
        continue
    m = float(mass_el.get("value"))
    total_mass += m
    links_with_inertial.append(link.get("name"))

print(f"Current total mass : {total_mass:.6f} kg")
print(f"Target total mass  : {TARGET_MASS:.6f} kg")
k = TARGET_MASS / total_mass
print(f"Scale factor k     : {k:.8f}\n")

# ── Step 2: print new per-link values ─────────────────────────────────────────
print(f"{'Link':<45} | {'Old mass':>10} | {'New mass':>10}")
print("-" * 72)
for link in root.findall("link"):
    inertial = link.find("inertial")
    if inertial is None:
        continue
    mass_el = inertial.find("mass")
    if mass_el is None:
        continue
    name  = link.get("name")
    m_old = float(mass_el.get("value"))
    m_new = m_old * k

    inertia_el = inertial.find("inertia")
    ixx_old = float(inertia_el.get("ixx")) if inertia_el is not None else 0
    ixy_old = float(inertia_el.get("ixy")) if inertia_el is not None else 0
    ixz_old = float(inertia_el.get("ixz")) if inertia_el is not None else 0
    iyy_old = float(inertia_el.get("iyy")) if inertia_el is not None else 0
    iyz_old = float(inertia_el.get("iyz")) if inertia_el is not None else 0
    izz_old = float(inertia_el.get("izz")) if inertia_el is not None else 0

    print(f"{name:<45} | {m_old:>10.6f} | {m_new:>10.6f}")
    print(f"  inertia: ixx={ixx_old*k:.6e}  ixy={ixy_old*k:.6e}  ixz={ixz_old*k:.6e}")
    print(f"           iyy={iyy_old*k:.6e}  iyz={iyz_old*k:.6e}  izz={izz_old*k:.6e}")

print(f"\nVerification — new total mass: {total_mass * k:.6f} kg")
