"""
Optimización del Funcional de Energía Potencial Total
Placa cuadrada (L=2000mm) con agujero circular (R=250mm)
Tracción uniaxial σ_xx = 1 MPa
"""

import numpy as np
from scipy.optimize import minimize
from scipy.integrate import dblquad
import matplotlib.pyplot as ax2 = plt.subplot(2, 4, 2)
U_theta_s = evaluar_utheta(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo)
contour2 = ax2.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_theta_s, levels=20, cmap='RdBu_r')
ax2.set_xlabel('x (mm)')
ax2.set_ylabel('y (mm)')
ax2.set_title('Desplazamiento Tangencial $u_\\theta$ (mm)')
ax2.axis('equal')
circle2 = Circle((0, 0), R, fill=False, color='black', linewidth=2)
ax2.add_patch(circle2)
plt.colorbar(contour2, ax=ax2)

# Plot 3: Magnitud del desplazamiento
ax3 = plt.subplot(2, 4, 3)lotlib.patches import Circle, Rectangle
import warnings
warnings.filterwarnings('ignore')

# ==================== PARÁMETROS ====================
L = 2000.0  # mm - lado de la placa
R = 250.0   # mm - radio del agujero
E = 70e3    # MPa - módulo de Young
nu = 0.3    # coeficiente de Poisson
sigma_inf = 1.0  # MPa - tracción aplicada
t = 1.0     # espesor (para cálculos, se normaliza)

# ==================== FUNCIONES AUXILIARES ====================

def r_ext(theta):
    """Radio externo de la placa cuadrada en función del ángulo."""
    return (L/2) / np.maximum(np.abs(np.cos(theta)), np.abs(np.sin(theta)))

def evaluar_ur(r, theta, coeff_r, coeff_theta):
    """Aproximación de u_r mediante Series de Fourier con funciones radiales."""
    N_fourier = len(coeff_r) // 2
    u_r = np.zeros_like(r, dtype=float)
    
    # Polinomio radial (cúbico) que anula en r=R
    rad_factor = ((r - R) / (r + R)) ** 2  # Asegura u_r(R) = 0
    
    for n in range(N_fourier):
        A_n = coeff_r[2*n]
        B_n = coeff_r[2*n + 1]
        u_r += (A_n * np.cos(n*theta) + B_n * np.sin(n*theta)) * rad_factor
    
    return u_r

def evaluar_utheta(r, theta, coeff_r, coeff_theta):
    """Aproximación de u_θ mediante Series de Fourier."""
    N_fourier = len(coeff_theta) // 2
    u_theta = np.zeros_like(r, dtype=float)
    
    # Polinomio radial que anula en r=R
    rad_factor = ((r - R) / (r + R)) ** 2
    
    for n in range(1, N_fourier + 1):  # Comienza en n=1
        C_n = coeff_theta[2*(n-1)]
        D_n = coeff_theta[2*(n-1) + 1]
        u_theta += (C_n * np.cos(n*theta) + D_n * np.sin(n*theta)) * rad_factor
    
    return u_theta

def derivada_ur_r(r, theta, dr, coeff_r, coeff_theta):
    """Aproximación de ∂u_r/∂r por diferencias finitas."""
    u_r_plus = evaluar_ur(r + dr, theta, coeff_r, coeff_theta)
    u_r_minus = evaluar_ur(r - dr, theta, coeff_r, coeff_theta)
    return (u_r_plus - u_r_minus) / (2 * dr)

def derivada_ur_theta(r, theta, dtheta, coeff_r, coeff_theta):
    """Aproximación de (1/r)∂u_r/∂θ."""
    u_r_plus = evaluar_ur(r, theta + dtheta, coeff_r, coeff_theta)
    u_r_minus = evaluar_ur(r, theta - dtheta, coeff_r, coeff_theta)
    return (u_r_plus - u_r_minus) / (2 * r * dtheta)

def derivada_utheta_r(r, theta, dr, coeff_r, coeff_theta):
    """Aproximación de ∂u_θ/∂r."""
    u_theta_plus = evaluar_utheta(r + dr, theta, coeff_r, coeff_theta)
    u_theta_minus = evaluar_utheta(r - dr, theta, coeff_r, coeff_theta)
    return (u_theta_plus - u_theta_minus) / (2 * dr)

def calcular_deformaciones(r, theta, dr, dtheta, coeff_r, coeff_theta):
    """Calcula las deformaciones en coordenadas polares."""
    u_r = evaluar_ur(r, theta, coeff_r, coeff_theta)
    u_theta = evaluar_utheta(r, theta, coeff_r, coeff_theta)
    
    dur_dr = derivada_ur_r(r, theta, dr, coeff_r, coeff_theta)
    dur_dtheta = derivada_ur_theta(r, theta, dtheta, coeff_r, coeff_theta)
    dutheta_dr = derivada_utheta_r(r, theta, dr, coeff_r, coeff_theta)
    
    eps_rr = dur_dr
    eps_theta_theta = (1/r) * (np.gradient(u_theta) if isinstance(u_theta, np.ndarray) else dtheta) + u_r / r
    eps_r_theta = 0.5 * (dur_dtheta + dutheta_dr - u_theta / r)
    
    return eps_rr, eps_theta_theta, eps_r_theta

def energía_densidad(r, theta, coeff_r, coeff_theta, dr=0.1, dtheta=0.01):
    """Calcula la densidad de energía de deformación."""
    u_r = evaluar_ur(r, theta, coeff_r, coeff_theta)
    u_theta = evaluar_utheta(r, theta, coeff_r, coeff_theta)
    
    dur_dr = derivada_ur_r(r, theta, dr, coeff_r, coeff_theta)
    dur_dtheta = derivada_ur_theta(r, theta, dtheta, coeff_r, coeff_theta)
    dutheta_dr = derivada_utheta_r(r, theta, dr, coeff_r, coeff_theta)
    
    eps_rr = dur_dr
    eps_theta = (1/r) * (du_theta/r) if np.isscalar(u_theta) else u_r/r
    eps_r_theta = 0.5 * (dur_dtheta + dutheta_dr - u_theta / r)
    
    # Densidad de energía en coordenadas polares
    term1 = eps_rr**2
    term2 = eps_theta**2
    term3 = 2 * nu * eps_rr * eps_theta
    term4 = eps_r_theta**2 * (2 * (1 + nu))
    
    L_dens = (E / (2 * (1 - nu**2))) * (term1 + term2 + term3) + (E / (2 * (1 + nu))) * term4
    
    return L_dens

def integrando_energia(r, theta, coeff_r, coeff_theta):
    """Integrando para la energía potencial interna."""
    dr = 0.5
    dtheta = 0.05
    
    u_r = evaluar_ur(r, theta, coeff_r, coeff_theta)
    u_theta = evaluar_utheta(r, theta, coeff_r, coeff_theta)
    
    # Derivadas numéricas
    if r > R + 1:
        dur_dr = (evaluar_ur(r + dr, theta, coeff_r, coeff_theta) - evaluar_ur(r - dr, theta, coeff_r, coeff_theta)) / (2*dr)
    else:
        dur_dr = 0
    
    dur_dtheta = (evaluar_ur(r, theta + dtheta, coeff_r, coeff_theta) - evaluar_ur(r, theta - dtheta, coeff_r, coeff_theta)) / (2*dtheta) / r
    dutheta_dr = (evaluar_utheta(r + dr, theta, coeff_r, coeff_theta) - evaluar_utheta(r - dr, theta, coeff_r, coeff_theta)) / (2*dr) if r > R + 1 else 0
    
    eps_rr = dur_dr
    eps_theta = dur_dtheta + u_r / r
    eps_r_theta = 0.5 * (dur_dtheta + dutheta_dr - u_theta / r)
    
    # Energía
    L_dens = (E / (2 * (1 - nu**2))) * (eps_rr**2 + eps_theta**2 + 2*nu*eps_rr*eps_theta) + (E / (2*(1+nu))) * eps_r_theta**2
    
    return L_dens * r

def funcional_energia(coeff):
    """Funcional de energía potencial total a minimizar."""
    N_coeff = len(coeff)
    N_fourier = N_coeff // 2
    
    coeff_r = coeff[:N_fourier]
    coeff_theta = coeff[N_fourier:]
    
    # Integración numérica de la energía interna
    def integrar_energia(theta):
        r_vals = np.linspace(R + 1, r_ext(theta), 20)
        energia_vals = np.array([integrando_energia(r, theta, coeff_r, coeff_theta) for r in r_vals])
        energia_theta = np.trapz(energia_vals, r_vals)
        return energia_theta
    
    # Integración en θ
    thetas = np.linspace(0, 2*np.pi, 40)
    energias = np.array([integrar_energia(t) for t in thetas])
    energia_total = np.trapz(energias, thetas) * t
    
    # Trabajo externo (aproximado)
    trabajo = 0
    for theta_borde in [np.pi/4, -np.pi/4, 3*np.pi/4, 5*np.pi/4]:
        for theta in np.linspace(theta_borde - np.pi/8, theta_borde + np.pi/8, 10):
            r_val = r_ext(theta)
            u_r_val = evaluar_ur(r_val, theta, coeff_r, coeff_theta)
            u_theta_val = evaluar_utheta(r_val, theta, coeff_r, coeff_theta)
            u_x = u_r_val * np.cos(theta) - u_theta_val * np.sin(theta)
            trabajo += sigma_inf * u_x * r_val
    
    trabajo *= t * (2*np.pi / 40)
    
    funcional = energia_total - trabajo
    
    return funcional

# ==================== OPTIMIZACIÓN ====================

print("=" * 60)
print("OPTIMIZACIÓN DEL FUNCIONAL DE ENERGÍA POTENCIAL TOTAL")
print("=" * 60)
print(f"Parámetros:")
print(f"  L = {L} mm")
print(f"  R = {R} mm")
print(f"  E = {E} MPa")
print(f"  ν = {nu}")
print(f"  σ_∞ = {sigma_inf} MPa")
print("=" * 60)

# Inicialización de coeficientes
N_fourier = 4  # Número de términos de Fourier
coeff_inicial = np.random.randn(2 * N_fourier) * 0.1

print(f"\nNúmero de términos Fourier: {N_fourier}")
print(f"Número de coeficientes: {len(coeff_inicial)}")
print(f"Energía inicial: {funcional_energia(coeff_inicial):.6e}")

# Minimización
print("\nIniciando optimización...")
result = minimize(
    funcional_energia,
    coeff_inicial,
    method='BFGS',
    options={'maxiter': 100, 'disp': True},
    callback=lambda x: print(f"  Iteración: Energía = {funcional_energia(x):.6e}")
)

print("\n" + "=" * 60)
print("RESULTADOS DE LA OPTIMIZACIÓN")
print("=" * 60)
print(f"Éxito: {result.success}")
print(f"Iteraciones: {result.nit}")
print(f"Energía mínima: {result.fun:.6e}")
print("=" * 60)

coeff_optimo = result.x
coeff_r_optimo = coeff_optimo[:N_fourier]
coeff_theta_optimo = coeff_optimo[N_fourier:]

# ==================== VISUALIZACIÓN ====================

print("\nGenerando visualización...")

# Crear malla
r_vals = np.linspace(R + 10, r_ext(0), 30)
theta_vals = np.linspace(0, 2*np.pi, 60)
R_grid, Theta_grid = np.meshgrid(r_vals, theta_vals)

# Calcular desplazamientos
U_r = np.zeros_like(R_grid)
U_theta = np.zeros_like(R_grid)

for i in range(len(theta_vals)):
    for j in range(len(r_vals)):
        U_r[i, j] = evaluar_ur(R_grid[i, j], Theta_grid[i, j], coeff_r_optimo, coeff_theta_optimo)
        U_theta[i, j] = evaluar_utheta(R_grid[i, j], Theta_grid[i, j], coeff_r_optimo, coeff_theta_optimo)

# Convertir a cartesianas para visualización
X_grid = R_grid * np.cos(Theta_grid)
Y_grid = R_grid * np.sin(Theta_grid)

U_x = U_r * np.cos(Theta_grid) - U_theta * np.sin(Theta_grid)
U_y = U_r * np.sin(Theta_grid) + U_theta * np.cos(Theta_grid)

# Posiciones deformadas
X_def = X_grid + U_x
Y_def = Y_grid + U_y

# Magnitud del desplazamiento
U_mag = np.sqrt(U_x**2 + U_y**2)

# Crear figura con subplots
fig = plt.figure(figsize=(18, 14))

# Plot 1: Desplazamiento radial u_r
ax1 = plt.subplot(2, 4, 1)
theta_slice = np.linspace(0, 2*np.pi, 60)
r_slice = np.linspace(R + 10, 1000, 30)
R_s, Theta_s = np.meshgrid(r_slice, theta_slice)
U_r_s = evaluar_ur(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo)
contour1 = ax1.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_r_s, levels=20, cmap='RdBu_r')
ax1.set_xlabel('x (mm)')
ax1.set_ylabel('y (mm)')
ax1.set_title('Desplazamiento Radial $u_r$ (mm)')
ax1.axis('equal')
circle1 = Circle((0, 0), R, fill=False, color='black', linewidth=2)
ax1.add_patch(circle1)
plt.colorbar(contour1, ax=ax1)

# Plot 2: Desplazamiento tangencial u_θ
ax2 = plt.subplot(2, 4, 2)
U_theta_s = evaluar_utheta(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo)
contour2 = ax2.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_theta_s, levels=20, cmap='RdBu_r')
ax2.set_xlabel('x (mm)')
ax2.set_ylabel('y (mm)')
ax2.set_title('Desplazamiento Tangencial $u_\\theta$ (mm)')
ax2.axis('equal')
circle2 = Circle((0, 0), R, fill=False, color='black', linewidth=2)
ax2.add_patch(circle2)
plt.colorbar(contour2, ax=ax2)

# Plot 3: Magnitud del desplazamiento
ax3 = plt.subplot(2, 3, 3)
U_mag_s = np.sqrt((R_s * np.cos(Theta_s) * (np.cos(Theta_s) * evaluar_ur(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo) - 
                                             np.sin(Theta_s) * evaluar_utheta(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo)))**2 +
                   (R_s * np.sin(Theta_s) * (np.sin(Theta_s) * evaluar_ur(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo) + 
                                             np.cos(Theta_s) * evaluar_utheta(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo)))**2)
contour3 = ax3.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_mag_s, levels=20, cmap='viridis')
ax3.set_xlabel('x (mm)')
ax3.set_ylabel('y (mm)')
ax3.set_title('Magnitud del Desplazamiento $|\\mathbf{u}|$ (mm)')
ax3.axis('equal')
circle3 = Circle((0, 0), R, fill=False, color='red', linewidth=2)
ax3.add_patch(circle3)
plt.colorbar(contour3, ax=ax3)

# Plot 4: Configuración inicial (sin deformación)
ax4 = plt.subplot(2, 3, 4)
ax4.add_patch(Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='blue', linewidth=2))
ax4.add_patch(Circle((0, 0), R, fill=False, edgecolor='red', linewidth=2))
ax4.arrow(-L/2 - 100, -L/2, -200, 0, head_width=50, head_length=50, fc='black', ec='black')
ax4.arrow(L/2 + 100, L/2, 200, 0, head_width=50, head_length=50, fc='black', ec='black')
ax4.set_xlim(-L/2 - 300, L/2 + 300)
ax4.set_ylim(-L/2 - 300, L/2 + 300)
ax4.set_xlabel('x (mm)')
ax4.set_ylabel('y (mm)')
ax4.set_title('Configuración Inicial')
ax4.axis('equal')
ax4.grid(True, alpha=0.3)
ax4.text(0, -L/2 - 200, f'σ_xx = {sigma_inf} MPa', ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

# Plot 5: Campo de desplazamientos (vectores)
ax5 = plt.subplot(2, 3, 5)
theta_vec = np.linspace(0, 2*np.pi, 12)
r_vec = np.linspace(R + 50, 800, 6)
for theta_v in theta_vec:
    for r_v in r_vec:
        if r_v < r_ext(theta_v):
            x_pos = r_v * np.cos(theta_v)
            y_pos = r_v * np.sin(theta_v)
            u_r_v = evaluar_ur(r_v, theta_v, coeff_r_optimo, coeff_theta_optimo)
            u_theta_v = evaluar_utheta(r_v, theta_v, coeff_r_optimo, coeff_theta_optimo)
            dx = u_r_v * np.cos(theta_v) - u_theta_v * np.sin(theta_v)
            dy = u_r_v * np.sin(theta_v) + u_theta_v * np.cos(theta_v)
            
            ax5.arrow(x_pos, y_pos, dx*2, dy*2, head_width=30, head_length=20, 
                     fc='blue', ec='blue', alpha=0.6, length_includes_head=True)

ax5.add_patch(Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='black', linewidth=2))
ax5.add_patch(Circle((0, 0), R, fill=True, facecolor='lightgray', edgecolor='red', linewidth=2))
ax5.set_xlim(-L/2 - 100, L/2 + 100)
ax5.set_ylim(-L/2 - 100, L/2 + 100)
ax5.set_xlabel('x (mm)')
ax5.set_ylabel('y (mm)')
ax5.set_title('Campo de Desplazamientos')
ax5.axis('equal')

# Plot 6: Información de convergencia
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')
info_text = f"""
RESULTADOS DE LA OPTIMIZACIÓN
{'='*40}

Energía Mínima: {result.fun:.6e} MJ

Parámetros del Problema:
  • L = {L} mm
  • R = {R} mm
  • E = {E} MPa
  • ν = {nu}
  • σ_∞ = {sigma_inf} MPa
  
Parámetros de Optimización:
  • Método: BFGS
  • Términos Fourier: {N_fourier}
  • Iteraciones: {result.nit}
  • Convergencia: {result.success}

Coeficientes Óptimos (u_r):
{np.array2string(coeff_r_optimo, precision=4, separator=', ')}

Coeficientes Óptimos (u_θ):
{np.array2string(coeff_theta_optimo, precision=4, separator=', ')}
"""
ax6.text(0.05, 0.95, info_text, transform=ax6.transAxes, fontsize=9,
        verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('/home/almo/Desktop/forecast_bot/plate_deformation.png', dpi=150, bbox_inches='tight')
print("✓ Gráfico guardado: plate_deformation.png")

plt.show()

print("\n✓ Optimización completada exitosamente!")
