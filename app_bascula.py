import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Análisis de Báscula", page_icon="⚖️", layout="wide")

# Título de la App
st.title("⚖️ Dashboard de Análisis Corporal")
st.markdown("Visualización de métricas recolectadas de la báscula a lo largo del tiempo.")

# Ruta al archivo (fija como pidió el usuario)
csv_file_path = "results_2.csv"

# Función para cargar y limpiar datos
@st.cache_data
def load_data():
    try:
        # Leer el CSV
        df = pd.read_csv(csv_file_path)
        
        # Convertir la fecha. En el CSV está como dd/mm/yyyy
        df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
        
        # Ordenar por fecha cronológicamente
        df = df.sort_values(by='fecha')
        
        # Resetear el índice
        df = df.reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo de datos: {e}")
        return None

df = load_data()

if df is not None and not df.empty:
    # --- MÉTRICAS DESTACADAS (KPIs) ---
    st.header("Métricas Destacadas 🎯")
    st.caption("Comparación entre la primera y la última medición registrada.")
    
    # Obtener el primer y último registro (con datos numéricos)
    first_record = df.iloc[0]
    last_record = df.iloc[-1]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # 1. Peso (Bajar es bueno, delta inverso? En general, para perder peso es mejor delta_color="inverse")
    # Pero Streamlit "inverse" significa que negativo es verde y positivo es rojo.
    delta_peso = last_record['peso'] - first_record['peso']
    col1.metric("Peso (kg)", f"{last_record['peso']:.1f}", f"{delta_peso:.1f} kg", delta_color="inverse")
    
    # 2. % Grasa Corporal (Bajar es bueno -> inverse)
    delta_grasa = last_record['porcentaje_grasa_corporal'] - first_record['porcentaje_grasa_corporal']
    col2.metric("% Grasa", f"{last_record['porcentaje_grasa_corporal']:.1f}%", f"{delta_grasa:.1f} %", delta_color="inverse")
    
    # 3. Masa Muscular Esquelética (Subir es bueno -> normal)
    delta_musculo = last_record['masa_muscular_esqueletica'] - first_record['masa_muscular_esqueletica']
    col3.metric("Masa Muscular Esq. (kg)", f"{last_record['masa_muscular_esqueletica']:.1f}", f"{delta_musculo:.1f} kg", delta_color="normal")
    
    # 4. Edad Corporal (Bajar es bueno -> inverse)
    delta_edad = last_record['edad_corporal'] - first_record['edad_corporal']
    col4.metric("Edad Corporal", f"{last_record['edad_corporal']:.0f}", f"{delta_edad:.0f} años", delta_color="inverse")

    # 5. Grasa Visceral (Bajar es bueno -> inverse)
    if 'calificacion_grasa_visceral' in df.columns:
        delta_visceral = last_record['calificacion_grasa_visceral'] - first_record['calificacion_grasa_visceral']
        col5.metric("Grasa Visceral", f"{last_record['calificacion_grasa_visceral']:.1f}", f"{delta_visceral:.1f}", delta_color="inverse")
    
    st.markdown("---")
    
    # --- GRÁFICOS DE EVOLUCIÓN ---
    st.header("📈 Evolución Temporal")
    
    # Filtramos columnas que son numéricas para pintarlas
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Métricas por defecto para la gráfica
    default_metrics = ['peso', 'porcentaje_grasa_corporal', 'masa_muscular_esqueletica']
    default_metrics = [m for m in default_metrics if m in numeric_columns]
    
    min_date = df['fecha'].min().date()
    max_date = df['fecha'].max().date()
    
    col_sel, col_date = st.columns([2, 1])
    
    with col_sel:
        selected_metrics = st.multiselect(
            "Selecciona las métricas:",
            options=numeric_columns,
            default=default_metrics
        )
        
    with col_date:
        date_range = st.date_input("Filtrar por rango de fechas:", (min_date, max_date), min_value=min_date, max_value=max_date)
    
    if selected_metrics:
        # Asegurarnos de que el usuario ha seleccionado un mínimo de una fecha
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range[0]
            
        # Filtro de fechas
        mask = (df['fecha'].dt.date >= start_date) & (df['fecha'].dt.date <= end_date)
        df_filtered = df.loc[mask]

        # Reestructurar los datos filtrados para Plotly
        df_melted = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics, 
                            var_name='Métrica', value_name='Valor')
        
        # Crear la gráfica interactiva
        fig = px.line(df_melted, x='fecha', y='Valor', color='Métrica', markers=True,
                      title="Evolución de las métricas en el tiempo",
                      labels={'fecha': 'Fecha', 'Valor': 'Unidad de medida'})
        
        # Mejorar la interacción de la gráfica
        fig.update_layout(hovermode="x unified", xaxis_title="")
        
        # Mostrar la gráfica
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👆 Por favor, selecciona al menos una métrica para visualizar la gráfica.")
        
    st.markdown("---")
    
    # --- TABLA DE DATOS COMPLETOS ---
    st.header("📋 Datos Completos")
    st.caption("Aquí tienes tu base de datos completa. Puedes ordenarlos clicando en las columnas.")
    
    # Mostrar la tabla ordenada decrecientemente por fecha para ver los últimos registros primero
    df_reversed = df.sort_values(by='fecha', ascending=False)
    
    with st.expander("Ver tabla de todos los registros", expanded=False):
        st.dataframe(df_reversed, use_container_width=True, hide_index=True)

else:
    st.warning("⚠️ No se encontraron datos en el archivo 'results_2.csv' o el formato es incorrecto.")
