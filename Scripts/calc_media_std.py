import os
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.patches import Patch

def read_data(file_path, start_time, end_time, interval=10):
    """
    Lê os dados de um arquivo .txt e retorna as taxas em Mbps dentro de um intervalo de tempo específico,
    agrupando em janelas de tempo definidas por 'interval'.
    """
    rates = defaultdict(list)
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            timestamp = int(float(row[6].split('-')[0]))  # Captura o início do intervalo em segundos
            if start_time <= timestamp < end_time:
                rates[timestamp // interval].append(float(row[8]) / 1e6)  # Converte bits/seg para Mbps

    # Calcula a média da taxa em cada intervalo
    avg_rates = [sum(values) / len(values) for values in rates.values() if values]
    return avg_rates

def jains_fairness_index(values):
    """
    Calcula o índice de equidade de Jain.
    """
    if not values:
        return 0
    numerator = sum(values) ** 2
    denominator = len(values) * sum(v ** 2 for v in values)
    return numerator / denominator

def calculate_statistics(values):
    """
    Calcula a média e o desvio padrão dos valores.
    """
    if not values:
        return 0, 0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    stddev = math.sqrt(variance)
    return mean, stddev

def get_file_groups(directory):
    """
    Agrupa arquivos por delay e algoritmo, diferenciando pares de hosts,
    mantendo a sequência desejada para os delays e algoritmos.
    """
    files = [f for f in os.listdir(directory) if f.endswith(".txt")]
    
    file_groups = defaultdict(lambda: {"h1-h2": None, "h3-h4": None})
    
    delay_order = ['75ms', '50ms', '10ms', '1ms']  
    algorithm_order = ['reno', 'bic', 'cubic', 'bbr']  

    ordered_file_groups = defaultdict(lambda: defaultdict(list))
    
    for file in files:
        parts = file.replace(".txt", "").split("_")
        
        if len(parts) == 4:
            algorithm = parts[1]
            hosts = parts[2]
            delay = parts[3]
            
            if algorithm in algorithm_order and delay in delay_order:
                ordered_file_groups[delay][algorithm].append((hosts, file))

    for delay in delay_order:
        for algorithm in algorithm_order:
            if ordered_file_groups[delay][algorithm]:
                for hosts, file in ordered_file_groups[delay][algorithm]:
                    file_groups[(algorithm, delay)][hosts] = file

    return file_groups

def plot_statistics(algorithms, means_h1_h2, stddevs_h1_h2, means_h3_h4, stddevs_h3_h4, jain_means, jain_stddevs):
    """
    Gera um gráfico bidirecional com faixas de fundo coloridas por delay.
    """
    y_pos = np.arange(len(algorithms))
    fig, ax1 = plt.subplots(figsize=(10, 8))

    # Definindo cores de fundo para cada grupo de delay
    delay_colors = {
        '1ms': (0.7, 0.8, 1.0),    # Azul mais saturado
        '10ms': (0.6, 1.0, 0.7),    # Verde limão
        '50ms': (0.9, 0.7, 0.9),    # Roxo mais forte
        '75ms': (1.0, 0.8, 0.6)     # Laranja mais vivo
    }
    
    # Mapeamento para o dobro do valor do delay
    delay_display_names = {
        '1ms': '2ms',
        '10ms': '20ms',
        '50ms': '100ms',
        '75ms': '150ms'
    }
    
    # Adicionando as faixas de fundo
    current_delay = None
    for i, algo in enumerate(algorithms):
        original_delay = algo.split('(')[1].split(')')[0]  # Extrai o delay original do texto
        if original_delay != current_delay:
            # Encontra todos os algoritmos com o mesmo delay
            start_idx = i
            end_idx = i + 4  # Assumindo 4 algoritmos por delay
            ax1.axhspan(start_idx-0.5, end_idx-0.5, facecolor=delay_colors[original_delay], alpha=0.5)
            current_delay = original_delay
    
    # Atualizando os rótulos para mostrar o dobro do delay
    updated_algorithms = []
    for algo in algorithms:
        parts = algo.split('(')
        original_delay = parts[1].split(')')[0]
        updated_algorithms.append(f"{parts[0]}({delay_display_names[original_delay]})")
    
    # Plotando as barras
    bars_h1_h2 = ax1.barh(y_pos, -np.array(means_h1_h2), xerr=stddevs_h1_h2, 
                         color="blue", label="h1-h2", align='center', capsize=5)
    bars_h3_h4 = ax1.barh(y_pos, means_h3_h4, xerr=stddevs_h3_h4, 
                         color="red", label="h3-h4", align='center', capsize=5)
    
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(updated_algorithms, fontsize=16)
    ax1.set_xlim(-100, 100)
    ax1.set_xlabel("Data transmission rate (Mbps)", fontsize=16)

    # ADIÇÃO: Configurar o tamanho da fonte dos ticks do eixo x
    ax1.tick_params(axis='x', labelsize=16)  # Esta é a linha que você precisa adicionar

    ax1.legend(loc='upper right')
    ax1.set_title("Average bitrate with Standard Deviation ", fontsize=20)
    
    # Legenda para as cores de fundo com os novos valores de delay
    legend_elements = [
        Patch(facecolor=delay_colors['1ms'], label=f"{delay_display_names['1ms']} delay"),
        Patch(facecolor=delay_colors['10ms'], label=f"{delay_display_names['10ms']} delay"),
        Patch(facecolor=delay_colors['50ms'], label=f"{delay_display_names['50ms']} delay"),
        Patch(facecolor=delay_colors['75ms'], label=f"{delay_display_names['75ms']} delay"),
    ]
    ax1.legend(handles=legend_elements, bbox_to_anchor=(1.15, 1), title="Delays")
    
    # Restaurando a legenda das barras
    ax1.legend([bars_h1_h2, bars_h3_h4], ['h1-h2', 'h3-h4'], loc='upper right', fontsize=16)

    # Eixo secundário para o índice de Jain
    ax2 = ax1.twinx()
    ax2.set_yticks(y_pos)
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_yticklabels([f"{mean:.4f} ± {stddev:.4f}" for mean, stddev in zip(jain_means, jain_stddevs)], 
                       fontsize=16, color='green')
    
    ax1.set_ylabel("Congestion Control Algorithm / RTT", fontsize=18)
    ax2.set_ylabel("Average Jain Index / Standard Deviation ", fontsize=18, color='green')

    plt.grid(True, linestyle='-.')
    plt.tight_layout()
    plt.savefig("grafico_bidirecional_com_jain_e_delays.png")
    plt.show()

def main(directory, start_time1, end_time1, start_time2, end_time2, interval=10):
    file_groups = get_file_groups(directory)
    algorithms = []
    means_h1_h2 = []
    stddevs_h1_h2 = []
    means_h3_h4 = []
    stddevs_h3_h4 = []
    jain_means = []
    jain_stddevs = []

    for (algorithm, delay), hosts_files in file_groups.items():
        if hosts_files["h1-h2"] and hosts_files["h3-h4"]:
            print(f"Analisando para algoritmo {algorithm}, delay {delay}:")

            rates_h1_h2 = read_data(os.path.join(directory, hosts_files["h1-h2"]), start_time1, end_time1, interval)
            rates_h3_h4 = read_data(os.path.join(directory, hosts_files["h3-h4"]), start_time2, end_time2, interval)

            mean_h1_h2, stddev_h1_h2 = calculate_statistics(rates_h1_h2)
            mean_h3_h4, stddev_h3_h4 = calculate_statistics(rates_h3_h4)
            
            print(f"  - h1-h2: Média = {mean_h1_h2:.2f} Mbps, Desvio Padrão = {stddev_h1_h2:.2f} Mbps")
            print(f"  - h3-h4: Média = {mean_h3_h4:.2f} Mbps, Desvio Padrão = {stddev_h3_h4:.2f} Mbps")

            algorithms.append(f"{algorithm} ({delay})")
            means_h1_h2.append(mean_h1_h2)
            stddevs_h1_h2.append(stddev_h1_h2)
            means_h3_h4.append(mean_h3_h4)
            stddevs_h3_h4.append(stddev_h3_h4)

            # Índice de Jain por intervalos de tempo
            jain_values = []
            for i in range(len(rates_h1_h2)):
                if i < len(rates_h3_h4):
                    jain_values.append(jains_fairness_index([rates_h1_h2[i], rates_h3_h4[i]]))

            mean_jain, stddev_jain = calculate_statistics(jain_values)
            print(f"  Índice de Equidade de Jain: {mean_jain:.4f} ± {stddev_jain:.4f}\n")
            
            jain_means.append(mean_jain)
            jain_stddevs.append(stddev_jain)

    plot_statistics(algorithms, means_h1_h2, stddevs_h1_h2, means_h3_h4, stddevs_h3_h4, jain_means, jain_stddevs)

directory = "."  
start_time1 = 200
end_time1 = 1000
start_time2 = 0
end_time2 = 800

main(directory, start_time1, end_time1, start_time2, end_time2)
