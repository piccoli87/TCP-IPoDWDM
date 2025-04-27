import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np

# Função para ler o arquivo e extrair os dados
def read_jain_fairness(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    data = []
    for line in lines:
        # Extrair as informações usando regex corrigida
        match = re.match(r"^\s*Índice de Equidade de Jain \(algoritmo (\w+), delay (\d+)ms\):\s+(\d+\.\d+)", line)
        if match:
            algorithm = match.group(1)
            delay = int(match.group(2))
            fairness_index = float(match.group(3))
            data.append((algorithm, 2*delay, fairness_index))
    print(data)
    return data

# Caminho do arquivo
file_path = 'Jain_Fairness_index.txt'

# Ler os dados
data = read_jain_fairness(file_path)

# Organizar os dados em um DataFrame
df = pd.DataFrame(data, columns=['Algorithm', 'Delay', 'Fairness Index'])

# Pivotar os dados para ter os algoritmos como colunas e os delays como linhas
df_pivot = df.pivot(index='Delay', columns='Algorithm', values='Fairness Index')

# Criando o gráfico de heatmap com matplotlib
fig, ax = plt.subplots(figsize=(10, 8))

# Definir a colormap
cmap = plt.get_cmap("YlGnBu")

# Plotando a matriz de dados com a colormap
cax = ax.matshow(df_pivot, cmap=cmap)

# Adicionando uma barra de cores
fig.colorbar(cax)

# Definir os rótulos dos eixos
ax.set_xticks(np.arange(len(df_pivot.columns)))
ax.set_xticklabels(df_pivot.columns, rotation=45, ha="right")
ax.set_yticks(np.arange(len(df_pivot.index)))
ax.set_yticklabels(df_pivot.index)

# Adicionando anotações nas células
for i in range(len(df_pivot.index)):
    for j in range(len(df_pivot.columns)):
        ax.text(j, i, f"{df_pivot.iloc[i, j]:.4f}", ha="center", va="center", color="black")

# Títulos e rótulos
plt.title("Jain's Fairness Index")
plt.xlabel("Algoritmos")
plt.ylabel("RTT (ms)")

# Exibindo o gráfico
plt.tight_layout()
output_file = "Jain_heatmap_RTT.png"
plt.savefig(output_file, dpi=300)
plt.show()
