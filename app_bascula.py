import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Configuración de página
st.set_page_config(page_title="Análisis de Báscula", page_icon="⚖️", layout="wide")

# Título de la App
st.title("⚖️ Dashboard de Análisis Corporal")
st.markdown("Visualización de métricas recolectadas de la báscula a lo largo del tiempo.")

# Ruta al archivo (fija como pidió el usuario)
# csv_file_path = "results_2.csv"

# leemos el archivo de configuración
with open("config/config.json", "r") as f:
    config = json.load(f)

# obtener la ruta del archivo desde el archivo de configuración
csv_file_path = config["csv_file_path"]

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
    delta_grasa = last_record['grasa_corporal'] - first_record['grasa_corporal']
    col2.metric("Grasa (kg)", f"{last_record['grasa_corporal']:.1f} kg", f"{delta_grasa:.1f} kg", delta_color="inverse")
    
    # 3. Masa Muscular Esquelética (Subir es bueno -> normal)
    delta_musculo = last_record['masa_muscular'] - first_record['masa_muscular']
    col3.metric("Masa Muscular (kg)", f"{last_record['masa_muscular']:.1f}", f"{delta_musculo:.1f} kg", delta_color="normal")
    
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
    
    # Métricas por defecto para la primera gráfica
    default_metrics_1 = ['grasa_corporal', 'masa_muscular']
    default_metrics_1 = [m for m in default_metrics_1 if m in numeric_columns]
    
    # Métricas por defecto para la segunda gráfica
    default_metrics_2 = ['porcentaje_musculo', 'porcentaje_grasa_corporal']
    default_metrics_2 = [m for m in default_metrics_2 if m in numeric_columns]

    # Métricas por defecto para la tercera gráfica
    #default_metrics_3 = ['porcentaje_musculo', 'porcentaje_grasa_corporal']
    default_metrics_3 = ['calificacion_grasa_visceral', 'edad_corporal']
    default_metrics_3 = [m for m in default_metrics_3 if m in numeric_columns]
    
    import datetime
    min_date = df['fecha'].min().date()
    max_date = df['fecha'].max().date()
    # Por defecto mostrar los últimos 7 días
    default_start_date = max(min_date, max_date - datetime.timedelta(days=7))
    
    col_date, _ = st.columns([1, 2])
    with col_date:
        date_range = st.date_input("Filtrar por rango de fechas:", (default_start_date, max_date), min_value=min_date, max_value=max_date)
    
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]
            
    # Filtro de fechas
    mask = (df['fecha'].dt.date >= start_date) & (df['fecha'].dt.date <= end_date)
    df_filtered = df.loc[mask]

    # --- Gráfico 1 ---
    selected_metrics_1 = st.multiselect(
        "Selecciona las métricas de la primera gráfica:",
        options=numeric_columns,
        default=default_metrics_1
    )
        
    if selected_metrics_1:
        # Reestructurar los datos filtrados para Plotly
        df_melted_1 = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics_1, 
                            var_name='Métrica', value_name='Valor')
        
        # Crear la gráfica interactiva
        fig_1 = px.line(df_melted_1, x='fecha', y='Valor', color='Métrica', markers=True,
                      title="Evolución de métricas absolutas en el tiempo",
                      labels={'fecha': 'Fecha', 'Valor': 'Valor'} )
        
        # Mejorar la interacción de la gráfica
        fig_1.update_layout(hovermode="x unified", xaxis_title="")
        
        # Mostrar la gráfica
        st.plotly_chart(fig_1, use_container_width=True)
    else:
        st.info("👆 Por favor, selecciona al menos una métrica para visualizar la primera gráfica.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Gráfico 2 ---
    selected_metrics_2 = st.multiselect(
        "Selecciona las métricas de la segunda gráfica (ej. Porcentajes):",
        options=numeric_columns,
        default=default_metrics_2
    )

    if selected_metrics_2:
        df_melted_2 = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics_2, 
                            var_name='Métrica', value_name='Valor')
        
        fig_2 = px.line(df_melted_2, x='fecha', y='Valor', color='Métrica', markers=True,
                      title="Evolución porcentual en el tiempo",
                      labels={'fecha': 'Fecha', 'Valor': '%'} )
        
        fig_2.update_layout(hovermode="x unified", xaxis_title="")
        st.plotly_chart(fig_2, use_container_width=True)
    else:
        st.info("👆 Por favor, selecciona al menos una métrica para visualizar la segunda gráfica.")

    # --- Utilidades de color dinámicas basadas en config.json ---
    # Construir un mapa de status -> hex_color invertido de la config "colors" (o "colores")
    mapa_colores = config.get("colors", config.get("colores", {}))
    status_to_hex = {v: k for k, v in mapa_colores.items()}
    
    def obtener_color_global(valor, config_dict, default_color="gray"):
        if not config_dict or pd.isna(valor): return default_color
        for status, rango_str in config_dict.items():
            try:
                partes = rango_str.split('-')
                if len(partes) == 2 and float(partes[0]) <= valor <= float(partes[1]):
                    c_hex = status_to_hex.get(status)
                    return c_hex if c_hex else default_color
            except Exception:
                pass
        return default_color

    # --- Gráfico 3 ---
    selected_metrics_3 = st.multiselect(
        "Selecciona las métricas de la tercera gráfica:",
        options=numeric_columns,
        default=default_metrics_3
    )

    if selected_metrics_3:
        df_melted_3 = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics_3, 
                            var_name='Métrica', value_name='Valor')
        
        fig_3 = px.bar(df_melted_3, x='fecha', y='Valor', color='Métrica', barmode='group',
                      title="Evolución temporal",
                      labels={'fecha': 'Fecha', 'Valor': 'Unidad'})
        
        # Lógica de colores condicionales basados en config
        for trace in fig_3.data:
            metric_name = trace.name
            colors = []
            
            if metric_name == 'edad_corporal':
                if "fecha_nacimiento" in config:
                    fecha_nac = pd.to_datetime(config["fecha_nacimiento"])
                    # Calcular edad real en años precisos
                    edad_real = (df_filtered['fecha'] - fecha_nac).dt.days / 365.25
                    
                    for y_v, e_v in zip(trace.y, edad_real):
                        if pd.isna(y_v):
                            colors.append("gray")
                        elif y_v < e_v:
                            colors.append("green")
                        else:
                            colors.append("red")
                    trace.marker.color = colors

            else:
                # Comprobar si existe configuración con "calificacion_" + nombre o el nombre directo
                nombres_posibles = [
                    f"calificacion_{metric_name}", 
                    metric_name
                ]
                # Mitigar redundancias o el typo 'viscera' del config
                if metric_name.startswith("calificacion_"):
                    nombres_posibles.append(metric_name.replace("calificacion_grasa_visceral", "calificacion_grasa_viscera"))
                else:
                    nombres_posibles.append(f"calificacion_{metric_name}".replace("calificacion_grasa_visceral", "calificacion_grasa_viscera"))
                    
                metric_config = None
                for key in nombres_posibles:
                    if config.get(key):
                        metric_config = config.get(key)
                        break
                        
                if metric_config:
                    for y_v in trace.y:
                        colors.append(obtener_color_global(y_v, metric_config, "gray"))
                    trace.marker.color = colors
        
        fig_3.update_layout(hovermode="x unified", xaxis_title="")
        st.plotly_chart(fig_3, use_container_width=True)
    else:
        st.info("👆 Por favor, selecciona al menos una métrica para visualizar la tercera gráfica.")
    st.markdown("---")
    
    # --- Gráfico 4: Composición de la última medición ---
    st.header("🥧 Composición Corporal (Última Medición)")
    
    # Tomamos el último registro disponible en el dataframe completo (o el filtrado)
    latest_record = df.iloc[-1]
    fecha_latest = latest_record['fecha'].strftime('%d/%m/%Y')
    peso_total = latest_record['peso']
    masa_musc = latest_record['masa_muscular']
    grasa_corp = latest_record['grasa_corporal']
    resto = peso_total - masa_musc - grasa_corp
    
    # Preparamos los datos para Plotly
    df_pie = pd.DataFrame({
        'Componente': ['Masa Muscular', 'Grasa Corporal', 'Resto (Hueso, Agua, etc.)'],
        'Valor': [masa_musc, grasa_corp, resto]
    })
    # Es mejor evaluar los porcentajes si existen (ya que la config suele ir en base al %)
    val_musc_eval = latest_record.get('porcentaje_musculo', masa_musc)
    val_grasa_eval = latest_record.get('porcentaje_grasa_corporal', grasa_corp)

    color_musc = obtener_color_global(val_musc_eval, config.get("calificacion_masa_muscular"), "green")
    color_grasa = obtener_color_global(val_grasa_eval, config.get("calificacion_grasa_corporal"), "red")

    fig_pie = px.pie(df_pie, values='Valor', names='Componente',
                     title=f"Distribución del peso actual ({peso_total} kg) - Fecha: {fecha_latest}",
                     color='Componente',
                     color_discrete_map={
                         'Masa Muscular': color_musc,
                         'Grasa Corporal': color_grasa,
                         'Resto (Hueso, Agua, etc.)': 'gray'
                     })
                     
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    
    col_pie, col_legend = st.columns([2, 1])
    
    with col_pie:
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_legend:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.subheader("Leyenda de Calificaciones")
        
        def dibujar_leyenda(titulo, dict_config):
            st.markdown(f"**{titulo}**")
            if dict_config:
                for status, rango in dict_config.items():
                    c_hex = status_to_hex.get(status, "gray")
                    st.markdown(f"<span style='color:{c_hex}; font-size:1.2em;'>■</span> {rango} ({status.title()})", unsafe_allow_html=True)
            else:
                st.markdown("*(No configurado en config.json)*")
                
        dibujar_leyenda("Masa Muscular", config.get("calificacion_masa_muscular", {}))
        st.markdown("<br>", unsafe_allow_html=True)
        dibujar_leyenda("Grasa Corporal", config.get("calificacion_grasa_corporal", {}))
        
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
    
