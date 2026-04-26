# Requisitos: pandas, matplotlib, seaborn
# pip install pandas matplotlib seaborn

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Datos con días añadidos explícitamente (abril)
entries = [
    {'day': 21, 'volume': 108_883},
    {'day': 20, 'volume': 113_828},
    {'day': 19, 'volume': 98_229},
    {'day': 18, 'volume': 115_158},
    {'day': 17, 'volume': 117_951},
    {'day': 16, 'volume': 132_833},
    {'day': 15, 'volume': 118_380},
    {'day': 14, 'volume': 116_881},
    {'day': 13, 'volume': 116_286},
    {'day': 12, 'volume': 151_655},
    {'day': 11, 'volume': 133_497},
    {'day': 10, 'volume': 133_950},
    {'day': 9,  'volume': 117_347},
    {'day': 8,  'volume': 63_643},
    {'day': 7,  'volume': 165_718},
]

df = pd.DataFrame(entries)

# Formato para ejes (miles y signo $)
def thousands(x, pos):
    if x >= 1_000:
        return f'${int(x):,}'
    return f'${int(x)}'
fmt = FuncFormatter(thousands)

sns.set(style="whitegrid")

# Histograma: entradas individuales
plt.figure(figsize=(8,5))
sns.histplot(df['volume'], bins=8, kde=False, color='C0')
plt.gca().xaxis.set_major_formatter(fmt)
plt.title('Volumen de mercado - Abril 2026')
plt.xlabel('Volumen ($)')
plt.ylabel('Frecuencia')
plt.tight_layout()
plt.savefig('hist_individuales_abril.png', dpi=200)
plt.show()

# Volumen agregado por día (suma)
daily = df.groupby('day', as_index=False).volume.sum().sort_values('day', ascending=True)

print("Volumen total por día (suma):")
print(daily.to_string(index=False))

# Histograma: volúmenes diarios (agregados)
plt.figure(figsize=(8,5))
sns.histplot(daily['volume'], bins=6, kde=False, color='C1')
plt.gca().xaxis.set_major_formatter(fmt)
plt.title('Histograma de volúmenes diarios (suma por día) - Abril')
plt.xlabel('Volumen diario total ($)')
plt.ylabel('Frecuencia')
plt.tight_layout()
plt.savefig('hist_diarios_abril.png', dpi=200)
plt.show()

# Barra: volumen total por día (visual claro por día)
plt.figure(figsize=(9,5))
sns.barplot(data=daily, x='day', y='volume')
plt.gca().yaxis.set_major_formatter(fmt)
plt.title('Volumen total por día - Abril')
plt.xlabel('Día de abril')
plt.ylabel('Volumen total ($)')
plt.tight_layout()
plt.savefig('bar_diaria_abril.png', dpi=200)
plt.show()