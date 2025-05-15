import matplotlib.pyplot as plt
from collections import defaultdict

def read_jain_data(file_path):
    """
    Lê o arquivo contendo os índices de Jain e organiza os dados por algoritmo e delay.
    """
    data = defaultdict(list)
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith("Índice de Equidade de Jain"):
                # Extrai as informações do algoritmo, delay e índice de Jain
                parts = line.split(":")
                index_value = float(parts[1].strip())
                descriptor = parts[0].split("(")[1].split(")")[0]
                algorithm, delay = descriptor.split(", delay ")
                data[algorithm.strip()].append((int(delay.replace("ms", "")), index_value))
    return data

def plot_jain_index(data, output_file):
    """
    Plota o gráfico de variação do índice de Jain para diferentes algoritmos e delays,
    e salva o gráfico em um arquivo.
    """
    plt.figure(figsize=(10, 6))
    for algorithm, values in data.items():
        # Ordena os valores por delay para garantir que a linha do gráfico seja contínua
        values.sort(key=lambda x: x[0])
        delays, indices = zip(*values)
        plt.plot(delays, indices, marker='o', label=algorithm)

    plt.title("Variação do Índice de Jain por Algoritmo e Delay", fontsize=14)
    plt.xlabel("Delay (ms)", fontsize=12)
    plt.ylabel("Índice de Jain", fontsize=12)
    plt.legend(title="Algoritmo", fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    # Salva a figura no arquivo especificado
    plt.savefig(output_file, dpi=300)
    plt.close()

# Caminho do arquivo
file_path = "Jain_Fairness_index.txt"
output_file = "graf_Jain_fairness.png"

# Lê os dados e plota o gráfico
jain_data = read_jain_data(file_path)
plot_jain_index(jain_data, output_file)

print(f"Gráfico salvo como: {output_file}")

