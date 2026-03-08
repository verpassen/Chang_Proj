import numpy as np
import matplotlib.pyplot as plt
import matplotlib

print(matplotlib.matplotlib_fname())
# Parameters
L = 10.0  # Length of the domain
T0 = 300  # Initial temperature (K)
T_laser = 2000  # Laser temperature (K)
alpha = 1e-5  # Thermal diffusivity (m^2/s)
dx = 0.1  # Spatial step
dt = 0.01  # Time step
nt = 1000  # Number of time steps

# Grid
nx = int(L / dx)
x = np.linspace(0, L, nx)
T = np.ones(nx) * T0

# Laser position
laser_pos = int(nx / 2)

# Simulation loop
for t in range(nt):
    T[laser_pos] = T_laser  # Apply laser heat source
    T[1:-1] += alpha * dt / dx**2 * (T[2:] - 2*T[1:-1] + T[:-2])  # Heat equation

# Plot results
plt.plot(x, T)
plt.xlabel('Position (mm)')
plt.ylabel('Temperature (K)')
plt.title('Temperature Distribution in DED Process')
plt.show()