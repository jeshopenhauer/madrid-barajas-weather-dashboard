"""
Optimización del Funcional de Energía Potencial Total
Placa cuadrada (L=2000mm) con agujero circular (R=250mm)
Tracción uniaxial σ_xx = 1 MPa

UNIDADES:
- Longitudes: mm
- Fuerzas: N
- Esfuerzos: MPa
- Energía: N·mm = mJ
"""

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import warnings
warnings.filterwarnings('ignore')

# ==================== PARÁMETROS ====================
L = 2000.0      # mm - lado de la placa cuadrada
R = 250.0       # mm - radio del agujero circular
E = 70000.0     # MPa - módulo de Young (acero ~210 GPa, aluminio ~70 GPa)
nu = 0.3        # adimensional - coeficiente de Poisson
sigma_inf = 1.0 # MPa - tracción aplicada en los bordes
t = 10.0        # mm - espesor de la placa (10 mm para tener desplazamientos visibles)

# ==================== FUNCIONES AUXILIARES ====================

def r_ext(theta):
    """Radio externo de la placa cuadrada en función del ángulo."""
    return (L/2) / np.maximum(np.abs(np.cos(theta)), np.abs(np.sin(theta)))

def evaluar_ur(r, theta, coeff_r):
    """Aproximación de u_r mediante Series de Fourier con funciones radiales."""
    N_fourier = len(coeff_r) // 2
    
    # Ensure r and theta are numpy arrays
    r = np.atleast_1d(r)
    theta = np.atleast_1d(theta)
    
    u_r = np.zeros_like(r, dtype=float)
    
    # Polinomio radial (cúbico) que anula en r=R
    rad_factor = ((r - R) / (1.0*r_ext(0) - R)) ** 2  # Normalización correcta
    
    for n in range(N_fourier):
        A_n = coeff_r[2*n]
        B_n = coeff_r[2*n + 1]
        u_r = u_r + (A_n * np.cos(n*theta) + B_n * np.sin(n*theta)) * rad_factor
    
    return u_r.squeeze() if u_r.size > 1 else float(u_r)

def evaluar_utheta(r, theta, coeff_theta):
    """Aproximación de u_θ mediante Series de Fourier."""
    N_fourier = len(coeff_theta) // 2
    
    # Ensure r and theta are numpy arrays
    r = np.atleast_1d(r)
    theta = np.atleast_1d(theta)
    
    u_theta = np.zeros_like(r, dtype=float)
    
    # Polinomio radial que anula en r=R
    rad_factor = ((r - R) / (1.0*r_ext(0) - R)) ** 2
    
    for n in range(1, N_fourier + 1):  # Comienza en n=1
        C_n = coeff_theta[2*(n-1)]
        D_n = coeff_theta[2*(n-1) + 1]
        u_theta = u_theta + (C_n * np.cos(n*theta) + D_n * np.sin(n*theta)) * rad_factor
    
    return u_theta.squeeze() if u_theta.size > 1 else float(u_theta)

def integrando_energia(r, theta, coeff_r, coeff_theta, dr=1.0, dtheta=0.01):
    """Integrando para la energía potencial interna (densidad de energía * r)."""
    
    u_r = evaluar_ur(r, theta, coeff_r)
    u_theta = evaluar_utheta(r, theta, coeff_theta)
    
    # Derivadas numéricas
    if r > R + dr:
        dur_dr = (evaluar_ur(r + dr, theta, coeff_r) - evaluar_ur(r - dr, theta, coeff_r)) / (2*dr)
    else:
        dur_dr = 0
    
    dur_dtheta = (evaluar_ur(r, theta + dtheta, coeff_r) - evaluar_ur(r, theta - dtheta, coeff_r)) / (2*dtheta)
    dutheta_dr = (evaluar_utheta(r + dr, theta, coeff_theta) - evaluar_utheta(r - dr, theta, coeff_theta)) / (2*dr) if r > R + dr else 0
    
    # Deformaciones en coordenadas polares
    eps_rr = dur_dr
    eps_theta = (1.0/r) * dur_dtheta + u_r / r if r > 0 else 0
    eps_r_theta = 0.5 * ((1.0/r) * dur_dtheta + dutheta_dr - u_theta / r) if r > 0 else 0
    
    # Densidad de energía de deformación (Energía/Volumen)
    # W = (E/[2(1-ν²)]) * [ε_rr² + ε_θθ² + 2ν*ε_rr*ε_θθ] + (E/[2(1+ν)]) * ε_rθ²
    term1 = eps_rr**2
    term2 = eps_theta**2
    term3 = 2 * nu * eps_rr * eps_theta
    term4 = eps_r_theta**2
    
    W = (E / (2 * (1 - nu**2))) * (term1 + term2 + term3) + (E / (2 * (1 + nu))) * term4
    
    # El integrando es W * r (para coordenadas polares en 2D)
    return W * r

def funcional_energia(coeff):
    """
    Funcional de energía potencial total a minimizar.
    Π = U - W
    donde U es la energía interna y W es el trabajo de las fuerzas externas
    """
    N_coeff = len(coeff)
    N_fourier = N_coeff // 2
    
    coeff_r = coeff[:N_fourier]
    coeff_theta = coeff[N_fourier:]
    
    # ENERGÍA INTERNA: U = t ∫∫ W(u_r, u_θ) r dr dθ
    def integrar_energia(theta):
        r_vals = np.linspace(R + 1, min(r_ext(theta), R + 1000), 30)  # Limitar el rango
        energia_vals = np.array([integrando_energia(r, theta, coeff_r, coeff_theta) for r in r_vals])
        energia_theta = np.trapz(energia_vals, r_vals)
        return energia_theta
    
    # Integración en θ
    thetas = np.linspace(0, 2*np.pi, 50)
    energias = np.array([integrar_energia(t) for t in thetas])
    energia_total = np.trapz(energias, thetas) * t
    
    # TRABAJO EXTERNO: W = ∫ σ_xx * u_x dS
    # En los bordes x = ±L/2
    trabajo = 0.0
    
    # Borde derecho (x = L/2, θ ∈ [π/4, -π/4])
    for theta in np.linspace(-np.pi/4, np.pi/4, 20):
        r_borde = r_ext(theta)
        u_r_val = evaluar_ur(r_borde, theta, coeff_r)
        u_theta_val = evaluar_utheta(r_borde, theta, coeff_theta)
        # u_x = u_r * cos(θ) - u_θ * sin(θ)
        u_x = u_r_val * np.cos(theta) - u_theta_val * np.sin(theta)
        # Contribución del trabajo: σ_∞ * u_x * dy
        # dy = r_borde * dθ
        trabajo += sigma_inf * u_x * r_borde * (np.pi / 20)
    
    # Borde izquierdo (x = -L/2, θ ∈ [3π/4, 5π/4])
    for theta in np.linspace(3*np.pi/4, 5*np.pi/4, 20):
        r_borde = r_ext(theta)
        u_r_val = evaluar_ur(r_borde, theta, coeff_r)
        u_theta_val = evaluar_utheta(r_borde, theta, coeff_theta)
        u_x = u_r_val * np.cos(theta) - u_theta_val * np.sin(theta)
        # Contribución del trabajo (fuerza en dirección opuesta)
        trabajo += sigma_inf * u_x * r_borde * (np.pi / 20)
    
    trabajo *= t  # Multiplicar por espesor
    
    # Funcional de energía potencial total
    funcional = energia_total - trabajo
    
    return funcional

# ==================== OPTIMIZACIÓN ====================

print("\n" + "="*70)
print("OPTIMIZACIÓN DEL FUNCIONAL DE ENERGÍA POTENCIAL TOTAL")
print("="*70)
print(f"\nPARÁMETROS DEL PROBLEMA:")
print(f"  • Lado de placa:        L = {L} mm")
print(f"  • Radio del agujero:    R = {R} mm")
print(f"  • Módulo de Young:      E = {E} MPa")
print(f"  • Coef. Poisson:        ν = {nu}")
print(f"  • Tracción aplicada:    σ_xx = {sigma_inf} MPa")
print(f"  • Espesor:              t = {t} mm")
print("="*70)

# Inicialización de coeficientes
N_fourier = 3  # Número de términos de Fourier (reducido para convergencia más rápida)
coeff_inicial = np.random.randn(2 * N_fourier) * 0.01

print(f"\nPARÁMETROS DE OPTIMIZACIÓN:")
print(f"  • Número de términos Fourier: {N_fourier}")
print(f"  • Número de coeficientes: {len(coeff_inicial)}")

# Calcular energía inicial
E_init = funcional_energia(coeff_inicial)
print(f"  • Energía inicial: {E_init:.6e} N·mm")

# Minimización
print(f"\nIniciando optimización con BFGS...")
print("-"*70)

result = minimize(
    funcional_energia,
    coeff_inicial,
    method='BFGS',
    options={'maxiter': 50, 'disp': True},
)

print("-"*70)
print("\n" + "="*70)
print("RESULTADOS DE LA OPTIMIZACIÓN")
print("="*70)
print(f"  • Convergencia:  {result.success}")
print(f"  • Iteraciones:   {result.nit}")
print(f"  • Energía final: {result.fun:.6e} N·mm")
print(f"  • Reducción:     {100*(E_init - result.fun)/abs(E_init):.2f}%")
print("="*70)

coeff_optimo = result.x
coeff_r_optimo = coeff_optimo[:N_fourier]
coeff_theta_optimo = coeff_optimo[N_fourier:]

# ==================== VISUALIZACIÓN ====================

print("\nGenerando visualización...")

fig = plt.figure(figsize=(22, 14))

# PLOT 1: Desplazamiento radial
ax1 = plt.subplot(2, 4, 1)
theta_slice = np.linspace(0, 2*np.pi, 80)
r_slice = np.linspace(R + 10, min(r_ext(0), 1200), 40)
R_s, Theta_s = np.meshgrid(r_slice, theta_slice)
U_r_s = evaluar_ur(R_s, Theta_s, coeff_r_optimo)
contour1 = ax1.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_r_s, levels=25, cmap='RdBu_r')
ax1.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax1.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax1.set_title('Desplazamiento Radial $u_r$ (mm)', fontsize=11, fontweight='bold')
ax1.axis('equal')
circle1 = Circle((0, 0), R, fill=False, color='black', linewidth=2.5)
ax1.add_patch(circle1)
cbar1 = plt.colorbar(contour1, ax=ax1)
cbar1.set_label('$u_r$ (mm)', fontsize=9)

# PLOT 2: Desplazamiento tangencial
ax2 = plt.subplot(2, 4, 2)
U_theta_s = evaluar_utheta(R_s, Theta_s, coeff_theta_optimo)
contour2 = ax2.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_theta_s, levels=25, cmap='RdBu_r')
ax2.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax2.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax2.set_title('Desplazamiento Tangencial $u_\\theta$ (mm)', fontsize=11, fontweight='bold')
ax2.axis('equal')
circle2 = Circle((0, 0), R, fill=False, color='black', linewidth=2.5)
ax2.add_patch(circle2)
cbar2 = plt.colorbar(contour2, ax=ax2)
cbar2.set_label('$u_\\theta$ (mm)', fontsize=9)

# PLOT 3: Magnitud del desplazamiento
ax3 = plt.subplot(2, 4, 3)
U_x_s = U_r_s * np.cos(Theta_s) - U_theta_s * np.sin(Theta_s)
U_y_s = U_r_s * np.sin(Theta_s) + U_theta_s * np.cos(Theta_s)
U_mag_s = np.sqrt(U_x_s**2 + U_y_s**2)
contour3 = ax3.contourf(R_s * np.cos(Theta_s), R_s * np.sin(Theta_s), U_mag_s, levels=25, cmap='viridis')
ax3.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax3.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax3.set_title('Magnitud $|\\mathbf{u}|$ (mm)', fontsize=11, fontweight='bold')
ax3.axis('equal')
circle3 = Circle((0, 0), R, fill=False, color='red', linewidth=2.5)
ax3.add_patch(circle3)
cbar3 = plt.colorbar(contour3, ax=ax3)
cbar3.set_label('$|\\mathbf{u}|$ (mm)', fontsize=9)

# PLOT 4: Configuración inicial
ax4 = plt.subplot(2, 4, 4)
rect_init = Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='blue', linewidth=3.5, label='Placa')
ax4.add_patch(rect_init)
circle_init = Circle((0, 0), R, fill=False, edgecolor='red', linewidth=3.5, label='Agujero')
ax4.add_patch(circle_init)

# Flechas de carga
ax4.arrow(-L/2 - 200, 0, -200, 0, head_width=100, head_length=80, fc='darkred', ec='darkred', alpha=0.8, linewidth=3)
ax4.arrow(L/2 + 200, 0, 200, 0, head_width=100, head_length=80, fc='darkred', ec='darkred', alpha=0.8, linewidth=3)

ax4.set_xlim(-L/2 - 400, L/2 + 400)
ax4.set_ylim(-L/2 - 300, L/2 + 300)
ax4.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax4.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax4.set_title('INICIAL (Sin Deformación)', fontsize=12, fontweight='bold', color='blue')
ax4.axis('equal')
ax4.grid(True, alpha=0.3)
ax4.legend(loc='upper right', fontsize=11, framealpha=0.9)
ax4.text(0, -L/2 - 230, f'σ_xx = {sigma_inf} MPa', ha='center', fontsize=11, 
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8, pad=0.7), fontweight='bold')

# PLOT 5: COMPARATIVA ANTES Y DESPUÉS (con amplificación visual)
ax5 = plt.subplot(2, 4, 5)
amplificacion = 50  # Factor de amplificación para ver los desplazamientos

# Placa original (punteada)
rect_orig = Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='blue', linewidth=2, 
                       linestyle='--', label='Original', alpha=0.6)
ax5.add_patch(rect_orig)
circle_orig = Circle((0, 0), R, fill=False, edgecolor='blue', linewidth=2, linestyle='--', alpha=0.6)
ax5.add_patch(circle_orig)

# Bordes deformados
y_vals = np.linspace(-L/2, L/2, 50)

# Borde derecho
x_vals_right = np.ones_like(y_vals) * (L/2)
theta_right = np.arctan2(y_vals, x_vals_right)
r_right = np.sqrt(x_vals_right**2 + y_vals**2)
u_r_right = evaluar_ur(r_right, theta_right, coeff_r_optimo)
u_theta_right = evaluar_utheta(r_right, theta_right, coeff_theta_optimo)
u_x_right = u_r_right * np.cos(theta_right) - u_theta_right * np.sin(theta_right)
u_y_right = u_r_right * np.sin(theta_right) + u_theta_right * np.cos(theta_right)
x_def_right = x_vals_right + amplificacion * u_x_right
y_def_right = y_vals + amplificacion * u_y_right
ax5.plot(x_def_right, y_def_right, 'g-', linewidth=3, label=f'Borde deformado x×{amplificacion}')

# Borde izquierdo
x_vals_left = np.ones_like(y_vals) * (-L/2)
theta_left = np.arctan2(y_vals, x_vals_left)
r_left = np.sqrt(x_vals_left**2 + y_vals**2)
u_r_left = evaluar_ur(r_left, theta_left, coeff_r_optimo)
u_theta_left = evaluar_utheta(r_left, theta_left, coeff_theta_optimo)
u_x_left = u_r_left * np.cos(theta_left) - u_theta_left * np.sin(theta_left)
u_y_left = u_r_left * np.sin(theta_left) + u_theta_left * np.cos(theta_left)
x_def_left = x_vals_left + amplificacion * u_x_left
y_def_left = y_vals + amplificacion * u_y_left
ax5.plot(x_def_left, y_def_left, 'g-', linewidth=3)

# Agujero deformado con amplificación
theta_hole = np.linspace(0, 2*np.pi, 150)
u_r_hole = evaluar_ur(R, theta_hole, coeff_r_optimo)
u_theta_hole = evaluar_utheta(R, theta_hole, coeff_theta_optimo)
u_x_hole = u_r_hole * np.cos(theta_hole) - u_theta_hole * np.sin(theta_hole)
u_y_hole = u_r_hole * np.sin(theta_hole) + u_theta_hole * np.cos(theta_hole)
x_hole_def = R * np.cos(theta_hole) + amplificacion * u_x_hole
y_hole_def = R * np.sin(theta_hole) + amplificacion * u_y_hole
ax5.plot(x_hole_def, y_hole_def, 'purple', linewidth=3.5, label='Agujero deformado')
ax5.fill(x_hole_def, y_hole_def, 'plum', alpha=0.3)

ax5.set_xlim(-L/2 - 300, L/2 + 300)
ax5.set_ylim(-L/2 - 300, L/2 + 300)
ax5.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax5.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax5.set_title(f'COMPARATIVA (Deformación x{amplificacion})\nAzul Punteado=Original | Verde=Deformado', 
              fontsize=11, fontweight='bold', color='green')
ax5.axis('equal')
ax5.grid(True, alpha=0.3)
ax5.legend(loc='upper right', fontsize=10, framealpha=0.9)

# PLOT 6: Zoom del agujero con amplificación
ax6 = plt.subplot(2, 4, 6)
zoom_range = R * 2.5

# Original
circle_zoom_orig = Circle((0, 0), R, fill=False, edgecolor='blue', linewidth=2.5, linestyle='--', alpha=0.7, label='Original')
ax6.add_patch(circle_zoom_orig)

# Deformado
theta_zoom = np.linspace(0, 2*np.pi, 200)
u_r_zoom = evaluar_ur(R, theta_zoom, coeff_r_optimo)
u_theta_zoom = evaluar_utheta(R, theta_zoom, coeff_theta_optimo)
u_x_zoom = u_r_zoom * np.cos(theta_zoom) - u_theta_zoom * np.sin(theta_zoom)
u_y_zoom = u_r_zoom * np.sin(theta_zoom) + u_theta_zoom * np.cos(theta_zoom)
x_zoom_def = R * np.cos(theta_zoom) + amplificacion * u_x_zoom
y_zoom_def = R * np.sin(theta_zoom) + amplificacion * u_y_zoom

ax6.plot(x_zoom_def, y_zoom_def, 'g-', linewidth=3.5, label=f'Deformado (x{amplificacion})')
ax6.fill(x_zoom_def, y_zoom_def, 'lightgreen', alpha=0.4)

# Calcular razón de ejes
r_x = np.max(np.abs(x_zoom_def - R*np.cos(theta_zoom))) + R
r_y = np.max(np.abs(y_zoom_def - R*np.sin(theta_zoom))) + R
ratio = r_x / r_y if r_y > 0 else 1

ax6.set_xlim(-zoom_range, zoom_range)
ax6.set_ylim(-zoom_range, zoom_range)
ax6.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax6.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax6.set_title(f'ZOOM: Agujero (x{amplificacion})\nRatio Rx/Ry = {ratio:.6f}', 
              fontsize=11, fontweight='bold', color='darkgreen')
ax6.axis('equal')
ax6.grid(True, alpha=0.3)
ax6.legend(loc='upper right', fontsize=10, framealpha=0.9)

# PLOT 7: Campo de desplazamientos (vectores)
ax7 = plt.subplot(2, 4, 7)
theta_vec = np.linspace(0, 2*np.pi, 14)
r_max = min(r_ext(0), 1000)
r_vec = np.linspace(R + 50, r_max - 50, 5)

for theta_v in theta_vec:
    for r_v in r_vec:
        if r_v < r_ext(theta_v):
            x_pos = r_v * np.cos(theta_v)
            y_pos = r_v * np.sin(theta_v)
            u_r_v = evaluar_ur(r_v, theta_v, coeff_r_optimo)
            u_theta_v = evaluar_utheta(r_v, theta_v, coeff_theta_optimo)
            dx = (u_r_v * np.cos(theta_v) - u_theta_v * np.sin(theta_v)) * amplificacion * 2
            dy = (u_r_v * np.sin(theta_v) + u_theta_v * np.cos(theta_v)) * amplificacion * 2
            
            ax7.arrow(x_pos, y_pos, dx, dy, head_width=40, head_length=30, 
                     fc='blue', ec='blue', alpha=0.7, length_includes_head=True, linewidth=1.5)

ax7.add_patch(Rectangle((-L/2, -L/2), L, L, fill=False, edgecolor='black', linewidth=2))
ax7.add_patch(Circle((0, 0), R, fill=True, facecolor='lightyellow', edgecolor='red', linewidth=2.5))
ax7.set_xlim(-L/2 - 200, L/2 + 200)
ax7.set_ylim(-L/2 - 200, L/2 + 200)
ax7.set_xlabel('x (mm)', fontsize=10, fontweight='bold')
ax7.set_ylabel('y (mm)', fontsize=10, fontweight='bold')
ax7.set_title(f'Campo de Desplazamientos\n(Vectores x{amplificacion})', fontsize=11, fontweight='bold', color='darkblue')
ax7.axis('equal')
ax7.grid(True, alpha=0.3)

# PLOT 8: Información de resultados
ax8 = plt.subplot(2, 4, 8)
ax8.axis('off')

info_text = f"""
RESULTADOS DE LA OPTIMIZACIÓN
{'='*50}

ENERGÍA MÍNIMA: {result.fun:.8e} N·mm

PARÁMETROS:
  Geometría:
    • Lado placa:      L = {L} mm
    • Radio agujero:   R = {R} mm
    • Relación L/R:    {L/R:.2f}
  Material:
    • Módulo Young:    E = {E} MPa
    • Coef. Poisson:   ν = {nu}
    • Espesor:         t = {t} mm
  Carga:
    • Tracción:        σ_∞ = {sigma_inf} MPa

OPTIMIZACIÓN:
  • Método:           BFGS
  • Términos Fourier: {N_fourier}
  • Coeficientes:     {len(coeff_optimo)}
  • Iteraciones:      {result.nit}
  • Convergencia:     {'✓ Sí' if result.success else '✗ No'}
  • Energía inicial:  {E_init:.6e} N·mm
  • Reducción:        {100*(E_init-result.fun)/abs(E_init) if E_init != 0 else 0:.2f}%

COEFICIENTES ÓPTIMOS (u_r):
  {np.array2string(coeff_r_optimo, precision=5, max_line_width=45)}

COEFICIENTES ÓPTIMOS (u_θ):
  {np.array2string(coeff_theta_optimo, precision=5, max_line_width=45)}

FACTOR AMPLIFICACIÓN VISUAL: {amplificacion}x
"""

ax8.text(0.02, 0.98, info_text, transform=ax8.transAxes, fontsize=8.5,
        verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, pad=1, edgecolor='black', linewidth=1.5))

plt.suptitle('OPTIMIZACIÓN DE PLACA CON AGUJERO BAJO TRACCIÓN UNIAXIAL\nComparación Antes-Después (Deformación Amplificada)', 
             fontsize=15, fontweight='bold', y=0.998)
plt.tight_layout(rect=[0, 0, 1, 0.995])
plt.savefig('/home/almo/Desktop/forecast_bot/plate_deformation.png', dpi=150, bbox_inches='tight', facecolor='white')
print("✓ Gráfico guardado: plate_deformation.png")

plt.show()

print("\n✓ Optimización completada exitosamente!")
