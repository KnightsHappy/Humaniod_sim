# Let's write the coordinates and do the precise subtraction

# Link 1 (elbow_link_1)
# Old joint origin of bicep relative to shoulder_link_2: [0.02315, 0.0, -0.053]
# We want to shift the joint origin by dx = -0.089765, dy = -0.065012, dz = 0
# New joint origin: [0.02315 - 0.089765, 0.0 - 0.065012, -0.053] = [-0.066615, -0.065012, -0.053]

# Link 2 (elbow_link_2)
# Old joint origin of forearm relative to elbow_link_1: [0.021583, -0.0307, -0.2334]
# Since parent frame (elbow_link_1) shifted by [-0.089765, -0.065012, 0], to keep absolute forearm joint at the same CAD location,
# we need to adjust the forearm joint origin relative to new elbow_link_1 frame.
# Absolute parent frame shifted by dp = [-0.089765, -0.065012, 0].
# Absolute child joint target position in CAD is [-0.225819, 0.072677, 0.7404].
# New parent absolute position is [-0.211941, 0.048354, 0.9691].
# So new relative forearm joint origin is:
# [-0.225819 - (-0.211941), 0.072677 - 0.048354, 0.7404 - 0.9691] = [-0.013878, 0.024323, -0.2287]

print("Joint Origins:")
print(f"left_bicep new origin: xyz=\"-0.066615 -0.065012 -0.053\"")
print(f"left_forearm new origin: xyz=\"-0.013878 0.024323 -0.2287\"")

# For elbow_link_1 visuals:
# We subtract [-0.089765, -0.065012, 0] from the original visual origins
e1_visuals = [
    # (mesh, old_xyz, rpy)
    ("L_E1_motor_bracket.stl", [-0.089765, -0.065012, -0.119932], "-1.53655 -0.0823267 -3.06536"),
    ("L_E1_3dp_CHP.stl", [-0.089765, -0.065012, -0.119932], "-1.53655 -0.0823267 -3.06536"),
    ("L_E1_1_cover.stl", [-0.080647, -0.060304, -0.003884], "0.0823748 0.0341349 1.64985"),
    ("L_E1_2_cover.stl", [-0.080647, -0.060304, -0.003884], "0.0823748 0.0341349 1.64985")
]

print("\nelbow_link_1 Visuals:")
for mesh, old_xyz, rpy in e1_visuals:
    new_xyz = [old_xyz[0] - (-0.089765), old_xyz[1] - (-0.065012), old_xyz[2]]
    print(f"  Mesh: {mesh}")
    print(f"    New xyz: {new_xyz[0]:.6f} {new_xyz[1]:.6f} {new_xyz[2]:.6f}")

# For elbow_link_2 visuals:
# The new joint frame is at [-0.225819, 0.072677, 0.7404].
# Old joint frame was at [-0.100593, 0.082666, 0.7357].
# So the child joint frame shifted by [-0.125226, -0.009989, 0.0047].
# We subtract this shift from the original visual origins.
e2_visuals = [
    ("L_E1_motor_bearing_holder.stl", [-0.109185, -0.073748, 0.103204], "-2.11532 -0.0823267 -3.06536"),
    ("L_E2_3dp_CHP.stl (1)", [-0.124998, -0.024135, -0.005601], "0.631794 0.0823267 0.0762336"),
    ("L_E2_3dp_CHP.stl (2)", [-0.125226, -0.009989, 0.004700], "-0.631794 -0.0823267 -3.06536"),
    ("L_Wr_2_motorholding_bracket.stl", [-0.125337, -0.009405 	, 0.003896], "-0.631794 -0.0823267 -3.06536"),
    ("ID_Needle_AXK_3047.stl", [-0.136540, 0.051290, -0.075459], "-2.20259 -0.0823267 -3.06536"),
    ("L_E2_2_cover.stl", [-0.125226, -0.009989, 0.004700], "-0.631794 -0.0823267 -3.06536"),
    ("L_S2_M_motor_holder.stl", [-0.126249, -0.008293, -0.006092], "-0.544528 -0.0823267 -3.06536"),
    ("ID_DGBB_6200_dummy.stl", [-0.091930, -0.035284, 0.040176], "0.157961 1.0207 1.78199"),
    ("L_E2_motorholding_bracket.stl", [-0.125226, -0.009989, 0.004700], "-0.631794 -0.0823267 -3.06536"),
    ("ID_Thrust_51106_dummy.stl", [-0.135595, 0.046327, -0.068623], "0.939002 -0.0823267 -3.06536"),
    ("L_E2_1_cover.stl", [-0.125226, -0.009989, 0.004700], "-0.631794 -0.0823267 -3.06536"),
    ("L_Wr_motor_horn_adaptor.stl", [-0.134817, 0.042241, -0.062993], "0.939002 -0.0823267 -3.06536"),
    ("L_Wr_1_motorholding_bracket.stl", [-0.125226, -0.009989, 0.004700], "-0.631794 -0.0823267 -3.06536"),
    ("RS02.stl", [-0.123977, -0.037732, 0.042828], "-0.894002 1.46512 -2.38583"),
    ("L_Wr_3_motorholding_bracket.stl", [-0.125030, -0.009812, 0.004801], "-0.631794 -0.0823267 -3.06536")
]

print("\nelbow_link_2 Visuals:")
for mesh, old_xyz, rpy in e2_visuals:
    new_xyz = [old_xyz[0] - (-0.125226), old_xyz[1] - (-0.009989), old_xyz[2] - 0.004700]
    print(f"  Mesh: {mesh}")
    print(f"    New xyz: {new_xyz[0]:.6f} {new_xyz[1]:.6f} {new_xyz[2]:.6f}")
