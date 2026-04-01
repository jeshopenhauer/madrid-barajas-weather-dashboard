"""
Optimización del Funcional de Energía Potencial Total
Placa cuadrada (L=2000mm) con agujero circular (R=250mm)
Tracción uniaxial σ_xx = 1 MPa
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
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
    
    # Ensure r and theta are numpy arrays
    r = np.atleast_1d(r)
    theta = np.atleast_1d(theta)
    
    u_r = np.zeros_like(r, dtype=float)
    
    # Polinomio radial (cúbico) que anula en r=R
    rad_factor = ((r - R) / (r + R)) ** 2  # Asegura u_r(R) = 0
    
    for n in range(N_fourier):
        A_n = coeff_r[2*n]
        B_n = coeff_r[2*n + 1]
        u_r = u_r + (A_n * np.cos(n*theta) + B_n * np.sin(n*theta)) * rad_factor
    
    return u_r.squeeze() if u_r.size > 1 else float(u_r)

def evaluar_utheta(r, theta, coeff_r, coeff_theta):
    """Aproximación de u_θ mediante Series de Fourier."""
    N_fourier = len(coeff_theta) // 2
    
    # Ensure r and theta are numpy arrays
    r = np.atleast_1d(r)
    theta = np.atleast_1d(theta)
    
    u_theta = np.zeros_like(r, dtype=float)
    
    # Polinomio radial que anula en r=R
    rad_factor = ((r - R) / (r + R)) ** 2
    
    for n in range(1, N_fourier + 1):  # Comienza en n=1
        C_n = coeff_theta[2*(n-1)]
        D_n = coeff_theta[2*(n-1) + 1]
        u_theta = u_theta + (C_n * np.cos(n*theta) + D_n * np.sin(n*theta)) * rad_factor
    
    return u_theta.squeeze() if u_theta.size > 1 else float(u_theta)

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

# Crear figura con 8 subplots
fig = plt.figure(figsize=(22, 10))

# Plot 1: Desplazamiento radial u_r
ax1 = plt.subplot(2, 4, 1)
theta_slice = np.linspace(0, 2*np.pi, 60)
r_slice = np.linspace(R + 10, 1000, 30)
R_s, Theta_s = np.meshgrid(r_slice, theta_slice)
U_r_s = evaluar_ur(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo)
contour1 = ax1.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_r_s, levels=20, cmap='RdBu_r')
ax1.set_xlabel('x (mm)', fontsize=10)
ax1.set_ylabel('y (mm)', fontsize=10)
ax1.set_title('Desplazamiento Radial $u_r$ (mm)', fontsize=11, fontweight='bold')
ax1.axis('equal')
circle1 = Circle((0, 0), R, fill=False, color='black', linewidth=2)
ax1.add_patch(circle1)
plt.colorbar(contour1, ax=ax1, label='$u_r$ (mm)')

# Plot 2: Desplazamiento tangencial u_θ
ax2 = plt.subplot(2, 4, 2)
U_theta_s = evaluar_utheta(R_s, Theta_s, coeff_r_optimo, coeff_theta_optimo)
contour2 = ax2.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_theta_s, levels=20, cmap='RdBu_r')
ax2.set_xlabel('x (mm)', fontsize=10)
ax2.set_ylabel('y (mm)', fontsize=10)
ax2.set_title('Desplazamiento Tangencial $u_\\theta$ (mm)', fontsize=11, fontweight='bold')
ax2.axis('equal')
circle2 = Circle((0, 0), R, fill=False, color='black', linewidth=2)
ax2.add_patch(circle2)
plt.colorbar(contour2, ax=ax2, label='$u_\\theta$ (mm)')

# Plot 3: Magnitud del desplazamiento
ax3 = plt.subplot(2, 4, 3)
U_x_s = U_r_s * np.cos(Theta_s) - U_theta_s * np.sin(Theta_s)
U_y_s = U_r_s * np.sin(Theta_s) + U_theta_s * np.cos(Theta_s)
U_mag_s = np.sqrt(U_x_s**2 + U_y_s**2)
contour3 = ax3.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_mag_s, levels=20, cmap='viridis')
ax3.set_xlabel('x (mm)', fontsize=10)
ax3.set_ylabel('y (mm)', fontsize=10)
ax3.set_title('Magnitud $|\\mathbf{u}|$ (mm)', fontsize=11, fontweight='bold')
ax3.axis('equal')
circle3 = Circle((0, 0), R, fill=False, color='red', linewidth=2)
ax3.add_patch(circle3)
plt.colorbar(contour3, ax=ax3, label='$|\\mathbf{u}|$ (mm)')

# Plot 4: Configuración inicial
ax4 = plt.subplot(2, 4, 4)
rect_init = Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='blue', linewidth=3, label='Placa')
ax4.add_patch(rect_init)
circle_init = Circle((0, 0), R, fill=False, edgecolor='red', linewidth=3, label='Agujero')
ax4.add_patch(circle_init)

# Flechas de carga
arrow_left = plt.Arrow(-L/2 - 150, 0, -200, 0, width=100, color='darkred', alpha=0.7)
arrow_right = plt.Arrow(L/2 + 150, 0, 200, 0, width=100, color='darkred', alpha=0.7)
ax4.add_patch(arrow_left)
ax4.add_patch(arrow_right)

ax4.set_xlim(-L/2 - 300, L/2 + 300)
ax4.set_ylim(-L/2 - 300, L/2 + 300)
ax4.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax4.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax4.set_title('INICIAL\n(Sin Deformación)', fontsize=11, fontweight='bold', color='blue')
ax4.axis('equal')
ax4.grid(True, alpha=0.3)
ax4.legend(loc='upper right', fontsize=10)
ax4.text(0, -L/2 - 180, f'σ_xx = {sigma_inf} MPa', ha='center', fontsize=10, 
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7, pad=0.5), fontweight='bold')

# Plot 5: COMPARATIVA ANTES Y DESPUÉS (CON AMPLIFICACIÓN)
ax5 = plt.subplot(2, 4, 5)
amplification_factor = 50  # Factor de amplificación para visualizar mejor

# Placa original (transparente)
rect_orig = Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='blue', linewidth=2.5, 
                       linestyle='--', label='Original', alpha=0.6)
ax5.add_patch(rect_orig)
circle_orig = Circle((0, 0), R, fill=False, edgecolor='blue', linewidth=2.5, linestyle='--', alpha=0.6)
ax5.add_patch(circle_orig)

# Borde derecho deformado (amplificado)
y_vals_edge = np.linspace(-L/2, L/2, 40)
x_vals_edge = np.ones_like(y_vals_edge) * (L/2)
theta_edge = np.arctan2(y_vals_edge, x_vals_edge)
r_edge = np.sqrt(x_vals_edge**2 + y_vals_edge**2)

u_r_edge = evaluar_ur(r_edge, theta_edge, coeff_r_optimo, coeff_theta_optimo)
u_theta_edge = evaluar_utheta(r_edge, theta_edge, coeff_r_optimo, coeff_theta_optimo)
u_x_edge = u_r_edge * np.cos(theta_edge) - u_theta_edge * np.sin(theta_edge)
u_y_edge = u_r_edge * np.sin(theta_edge) + u_theta_edge * np.cos(theta_edge)

x_def_edge = x_vals_edge + amplification_factor * u_x_edge
y_def_edge = y_vals_edge + amplification_factor * u_y_edge

ax5.plot(x_def_edge, y_def_edge, 'g-', linewidth=3, label=f'Borde deformado x=L/2 (×{amplification_factor})')

# Borde izquierdo deformado (amplificado)
x_vals_left = np.ones_like(y_vals_edge) * (-L/2)
theta_left = np.arctan2(y_vals_edge, x_vals_left)
r_left = np.sqrt(x_vals_left**2 + y_vals_edge**2)

u_r_left = evaluar_ur(r_left, theta_left, coeff_r_optimo, coeff_theta_optimo)
u_theta_left = evaluar_utheta(r_left, theta_left, coeff_r_optimo, coeff_theta_optimo)
u_x_left = u_r_left * np.cos(theta_left) - u_theta_left * np.sin(theta_left)
u_y_left = u_r_left * np.sin(theta_left) + u_theta_left * np.cos(theta_left)

x_def_left = x_vals_left + amplification_factor * u_x_left
y_def_left = y_vals_edge + amplification_factor * u_y_left

ax5.plot(x_def_left, y_def_left, 'g-', linewidth=3, label=f'Borde deformado x=-L/2 (×{amplification_factor})')

# Borde superior deformado (amplificado)
x_vals_top = np.linspace(-L/2, L/2, 40)
y_vals_top = np.ones_like(x_vals_top) * (L/2)
theta_top = np.arctan2(y_vals_top, x_vals_top)
r_top = np.sqrt(x_vals_top**2 + y_vals_top**2)

u_r_top = evaluar_ur(r_top, theta_top, coeff_r_optimo, coeff_theta_optimo)
u_theta_top = evaluar_utheta(r_top, theta_top, coeff_r_optimo, coeff_theta_optimo)
u_x_top = u_r_top * np.cos(theta_top) - u_theta_top * np.sin(theta_top)
u_y_top = u_r_top * np.sin(theta_top) + u_theta_top * np.cos(theta_top)

x_def_top = x_vals_top + amplification_factor * u_x_top
y_def_top = y_vals_top + amplification_factor * u_y_top

ax5.plot(x_def_top, y_def_top, 'orange', linewidth=3, label=f'Borde deformado y=L/2 (×{amplification_factor})')

# Agujero deformado (amplificado)
theta_hole = np.linspace(0, 2*np.pi, 100)
u_r_hole = evaluar_ur(R, theta_hole, coeff_r_optimo, coeff_theta_optimo)
u_theta_hole = evaluar_utheta(R, theta_hole, coeff_r_optimo, coeff_theta_optimo)
u_x_hole = u_r_hole * np.cos(theta_hole) - u_theta_hole * np.sin(theta_hole)
u_y_hole = u_r_hole * np.sin(theta_hole) + u_theta_hole * np.cos(theta_hole)

x_hole_def = R * np.cos(theta_hole) + amplification_factor * u_x_hole
y_hole_def = R * np.sin(theta_hole) + amplification_factor * u_y_hole

ax5.plot(x_hole_def, y_hole_def, 'purple', linewidth=3.5, label=f'Agujero deformado (×{amplification_factor})')
ax5.fill(x_hole_def, y_hole_def, 'lightyellow', alpha=0.4)

ax5.set_xlim(-L/2 - 200, L/2 + 200)
ax5.set_ylim(-L/2 - 200, L/2 + 200)
ax5.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax5.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax5.set_title(f'COMPARATIVA (Amplificado ×{amplification_factor})\n(Antes - Azul Punteado | Después - Verde)', fontsize=11, fontweight='bold', color='green')
ax5.axis('equal')
ax5.grid(True, alpha=0.3)
ax5.legend(loc='upper right', fontsize=8)

# Plot 6: Zoom en el agujero (CON AMPLIFICACIÓN)
ax6 = plt.subplot(2, 4, 6)

# Original
circle_zoom_orig = Circle((0, 0), R, fill=False, edgecolor='blue', linewidth=2.5, linestyle='--', alpha=0.6, label='Original')
ax6.add_patch(circle_zoom_orig)

# Deformado (CON AMPLIFICACIÓN)
theta_zoom = np.linspace(0, 2*np.pi, 200)
u_r_zoom = evaluar_ur(R, theta_zoom, coeff_r_optimo, coeff_theta_optimo)
u_theta_zoom = evaluar_utheta(R, theta_zoom, coeff_r_optimo, coeff_theta_optimo)
u_x_zoom = u_r_zoom * np.cos(theta_zoom) - u_theta_zoom * np.sin(theta_zoom)
u_y_zoom = u_r_zoom * np.sin(theta_zoom) + u_theta_zoom * np.cos(theta_zoom)

x_zoom_def_amp = R * np.cos(theta_zoom) + amplification_factor * u_x_zoom
y_zoom_def_amp = R * np.sin(theta_zoom) + amplification_factor * u_y_zoom

ax6.plot(x_zoom_def_amp, y_zoom_def_amp, 'purple', linewidth=3.5, label=f'Deformado (×{amplification_factor})')
ax6.fill(x_zoom_def_amp, y_zoom_def_amp, 'plum', alpha=0.4)

# Calcular proporciones de la elipse
u_r_theta_0 = evaluar_ur(R, 0, coeff_r_optimo, coeff_theta_optimo)
u_theta_theta_0 = evaluar_utheta(R, 0, coeff_r_optimo, coeff_theta_optimo)

u_r_theta_pi2 = evaluar_ur(R, np.pi/2, coeff_r_optimo, coeff_theta_optimo)
u_theta_theta_pi2 = evaluar_utheta(R, np.pi/2, coeff_r_optimo, coeff_theta_optimo)

# Radio en dirección x (θ=0)
r_x = R + u_r_theta_0
# Radio en dirección y (θ=π/2)
r_y = R + u_r_theta_pi2

zoom_range_amp = R * 1.8

ax6.set_xlim(-zoom_range_amp, zoom_range_amp)
ax6.set_ylim(-zoom_range_amp, zoom_range_amp)
ax6.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax6.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax6.set_title(f'ZOOM: Agujero (×{amplification_factor})\nRatio: Rx/Ry = {r_x/r_y:.6f}', 
              fontsize=11, fontweight='bold', color='purple')
ax6.axis('equal')
ax6.grid(True, alpha=0.3)
ax6.legend(loc='upper right', fontsize=10)

# Plot 7: Campo de desplazamientos
ax7 = plt.subplot(2, 4, 7)
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
            
            ax7.arrow(x_pos, y_pos, dx*2, dy*2, head_width=30, head_length=20, 
                     fc='blue', ec='blue', alpha=0.6, length_includes_head=True)

ax7.add_patch(Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='black', linewidth=2))
ax7.add_patch(Circle((0, 0), R, fill=True, facecolor='lightgray', edgecolor='red', linewidth=2))
ax7.set_xlim(-L/2 - 100, L/2 + 100)
ax7.set_ylim(-L/2 - 100, L/2 + 100)
ax7.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax7.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax7.set_title('Campo de Desplazamientos\n(Vectores)', fontsize=11, fontweight='bold', color='darkblue')
ax7.axis('equal')
ax7.grid(True, alpha=0.3)

# Plot 8: Información de resultados
ax8 = plt.subplot(2, 4, 8)
ax8.axis('off')
info_text = f"""
RESULTADOS OPTIMIZACIÓN
{'='*42}

ENERGÍA MÍNIMA: {result.fun:.6e} MJ

PARÁMETROS:
  • L = {L} mm
  • R = {R} mm
  • E = {E} MPa
  • ν = {nu}
  • σ_∞ = {sigma_inf} MPa

OPTIMIZACIÓN:
  • Método: BFGS
  • Términos Fourier: {N_fourier}
  • Iteraciones: {result.nit}
  • Convergencia: {'Sí' if result.success else 'No'}

DESPLAZAMIENTOS:
  • u_r,max: {np.max(np.abs(u_r_zoom)):.6e} mm
  • u_θ,max: {np.max(np.abs(u_theta_zoom)):.6e} mm
  
COEF. ÓPTIMOS (u_r):
  {np.array2string(coeff_r_optimo, precision=4)}

COEF. ÓPTIMOS (u_θ):
  {np.array2string(coeff_theta_optimo, precision=4)}
"""
ax8.text(0.05, 0.95, info_text, transform=ax8.transAxes, fontsize=7.5,
        verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.85, pad=0.5))

plt.suptitle('OPTIMIZACIÓN DE PLACA CON AGUJERO BAJO TRACCIÓN UNIAXIAL\nComparación Antes-Después', 
             fontsize=14, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('/home/almo/Desktop/forecast_bot/plate_deformation.png', dpi=150, bbox_inches='tight')
print("✓ Gráfico guardado: plate_deformation.png")

plt.show()

print("\n✓ Optimización completada exitosamente!")
