import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from randomWalk import RandomWalkModel, State

st.set_page_config(page_title="Simulador de Pandemia", layout="wide")

st.title("🦠 Simulador de Pandemia - Random Walk")
st.markdown("""
Esta aplicação simula a propagação de um vírus em uma população usando um modelo de Passeio Aleatório (Random Walk).
Configure os parâmetros abaixo e execute a simulação para visualizar os resultados.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configurações da Simulação")
    
    numberOfRuns = st.number_input(
        "Número de Execuções", 
        min_value=1, 
        max_value=100,
        value=1,
        help="Quantas vezes a simulação será rodada para calcular estatísticas."
    )
    
    gridSize = st.number_input(
        "Tamanho do Grid", 
        min_value=10, 
        max_value=500,
        value=100,
        help="O tamanho da matriz quadrada que representa a população."
    )
    
    numberOfGenerations = st.number_input(
        "Número de Gerações (Semanas)", 
        min_value=1, 
        max_value=1000,
        value=52,
        help="Duração da simulação em gerações."
    )

    simulation_speed = st.slider(
        "Velocidade da Animação (segundos)",
        min_value=0.01,
        max_value=1.0,
        value=0.1,
        help="Tempo de espera entre cada semana para visualização."
    )
    
    visualize_all = st.checkbox(
        "Animar todas as execuções (Lento)", 
        value=False,
        help="Se marcado, mostra a animação semana a semana para TODAS as execuções. Se desmarcado, anima apenas a primeira e mostra apenas o resultado final das outras para agilizar."
    )
    
    st.markdown("---")
    
    run_button = st.button("🚀 Executar Simulação", type="primary")

def get_population_grid_data(model):
    """Converte a população para uma matriz numérica para o Plotly."""
    # Mapeia estados para valores numéricos: Healthy=0, Sick=1, Dead=2, Immune=3
    return [[individual.state.value for individual in row] for row in model.population]

# Cores personalizadas: 0:Verde, 1:Amarelo, 2:Vermelho, 3:Azul
colorscale = [
    [0.0, 'green'],   # 0
    [0.25, 'green'],
    [0.25, 'yellow'], # 1
    [0.5, 'yellow'],
    [0.5, 'red'],     # 2
    [0.75, 'red'],
    [0.75, 'blue'],   # 3
    [1.0, 'blue']
]

if run_button:
    simulation_container = st.container()
    stats_container = st.container()
    
    with simulation_container:
        st.subheader("Simulação em Tempo Real")
        grid_placeholder = st.empty()
        status_text = st.empty()
    
    deaths_list = []
    last_run_history = []
    start_time = time.time()
    
    # Variável para armazenar a figura do Plotly e ser reutilizada
    fig = None

    for run in range(numberOfRuns):
        # Visualizamos a primeira execução OU todas se a opção estiver marcada
        is_visualizing = (run == 0) or visualize_all
        
        if is_visualizing:
            if run == 0:
                 status_text.text(f"Executando simulação {run + 1}...")
            else:
                 status_text.text(f"Animando simulação {run + 1}/{numberOfRuns}...")
        else:
            status_text.text(f"Simulando em background {run + 1}/{numberOfRuns} (Atualizando resultado final)...")
        
        # Create new model
        model = RandomWalkModel(gridSize)
        
        # Track history
        history = []
        history.append(model.report())
        
        # Configuração inicial do gráfico na primeira execução (ou na primeira visualizada)
        if fig is None: # Cria a figura apenas uma vez
            # Inicializa a visualização do grid
            data = get_population_grid_data(model)
            fig = go.Figure(data=go.Heatmap(
                z=data, 
                zmin=0, 
                zmax=3, 
                colorscale=colorscale, 
                showscale=False
            ))
            fig.update_layout(
                width=500, 
                height=500, 
                autosize=False,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False, autorange="reversed") # Y invertido para corresponder à matriz
            )
            grid_placeholder.plotly_chart(fig, use_container_width=True, key=f"grid_{run}_start")
        elif is_visualizing: 
            # Se já existe figura mas vamos animar o início de uma nova run
             data = get_population_grid_data(model)
             fig.data[0].z = data
             grid_placeholder.plotly_chart(fig, use_container_width=True, key=f"grid_{run}_start")

        # Run generations
        for gen in range(numberOfGenerations):
            model.nextGeneration()
            history.append(model.report())
            
            if is_visualizing:
                data = get_population_grid_data(model)
                
                # Atualiza o gráfico existente
                fig.data[0].z = data
                
                # Usamos unique key para cada frame para evitar StreamlitDuplicateElementKey
                grid_placeholder.plotly_chart(fig, use_container_width=True, key=f"grid_anim_{run}_{gen}")
                
                # Pausa para o usuário ver a mudança
                time.sleep(simulation_speed)
        
        # Se NÃO foi visualizado passo a passo, atualizamos o grid com o estado FINAL da simulação
        # para dar feedback de progresso ao usuário
        if not is_visualizing and fig is not None:
             data = get_population_grid_data(model)
             fig.data[0].z = data
             grid_placeholder.plotly_chart(fig, use_container_width=True, key=f"grid_end_run_{run}")
                
        # Store results
        deaths = model.numberOfDeaths()
        deaths_list.append(deaths)
        
        # Salva o histórico da simulação visualizada (ou da última, caso rode várias)
        if is_visualizing:
            last_run_history = history
        elif run == numberOfRuns - 1 and not last_run_history:
             last_run_history = history


    end_time = time.time()
    status_text.success(f"Simulação concluída em {end_time - start_time:.2f} segundos!")
    
    # --- Statistics Section ---
    with stats_container:
        st.header("📊 Resultados Gerais")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Média de Mortes", f"{sum(deaths_list) / numberOfRuns:.2f}")
        col2.metric("Mínimo de Mortes", min(deaths_list))
        col3.metric("Máximo de Mortes", max(deaths_list))

        # --- Detailed Visualization for First Run ---
        st.markdown("---")
        st.subheader(f"Evolução Temporal (Simulação Visualizada)")
        
        df_history = pd.DataFrame(last_run_history, columns=["Saudáveis", "Doentes", "Mortos", "Imunes"])
        st.line_chart(df_history, color=["#00FF00", "#FFFF00", "#FF0000", "#0000FF"])
        
        with st.expander("Ver dados brutos"):
            st.dataframe(df_history)

    # --- Statistics Chart if multiple runs ---
    if numberOfRuns > 1:
        st.markdown("---")
        st.subheader("Dispersão de Mortes por Execução")
        chart_data = pd.DataFrame({"Execução": range(1, numberOfRuns + 1), "Mortes": deaths_list})
        st.bar_chart(chart_data.set_index("Execução"))
