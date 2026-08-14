import numpy as np

# Gearbox+basebottom <1> properties
m_gearbox = 53.54507630620746
c_gearbox_local = np.array([0.0380621089200134, 0.013880277551266054, -0.036283265361809244])
I_gearbox_local = np.array([
    [1.800918471081113, -0.04554095181470766, -0.0904782164793688],
    [-0.04554095181470766, 1.4616510968501655, 0.2896286386850842],
    [-0.09047821647936881, 0.2896286386850842, 2.619285356726074]
])
# Transform translation from root assembly occurrences
t_gearbox = np.array([0.008511724783650573, -0.0034115864586085065, 0.009621370568228177])
c_gearbox_global = c_gearbox_local + t_gearbox

# Assembly 1 <1> properties (transform is Identity)
m_asm1 = 11.3398
c_asm1_global = np.array([0.06601857164000612, -0.09998410506794123, 0.289188159456609])
I_asm1_local = np.array([
    [0.61338575, 0.0, 0.0],
    [0.0, 0.58917711, 0.0],
    [0.0, 0.0, 0.23190283]
]) # simplified/approximate or let's query the actual inertia tensor from the previous output if we can.
# Wait! In get_all_root_masses.py we only queried mass and centroid.
# Let's query the actual inertia tensors of Assembly 1 and Assembly 12 from Onshape as well, to be 100% precise!
