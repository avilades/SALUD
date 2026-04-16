import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Análisis de Báscula", page_icon="⚖️", layout="wide")

# leemos el archivo de configuración
with open("config/config.json", "r") as f:
    config = json.load(f)

# obtener la ruta del archivo desde config
csv_file_path = config.get("csv_file_path", "")
google_sheets_url = config.get("google_sheets_url", "")

# Utilidades de color (Moverlas arriba para disponibilidad global)
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

# Función para cargar y limpiar datos
@st.cache_data(ttl=600)  # Limpiar cache cada 10 mins (ideal para GSheets)
def load_data():
    try:
        # Priorizar Google Sheets si está configurado
        if google_sheets_url and "AQUI_TU_ID" not in google_sheets_url:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(spreadsheet=google_sheets_url)
            df = df.dropna(how='all') # Limpiar filas totalmente vacías
        else:
            # Leer el CSV local
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

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Controles")
    if st.button("🔄 Sincronizar Datos"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    
    if df is not None and not df.empty:
        st.subheader("📅 Filtro de Fecha")
        min_date = df['fecha'].min().date()
        max_date = df['fecha'].max().date()
        # Por defecto mostrar el último mes
        default_start_date = max(min_date, max_date - datetime.timedelta(days=30))

        start_date_7_day = max_date - datetime.timedelta(days=7)
        start_date_30_day = max_date - datetime.timedelta(days=30)
        
        date_range = st.date_input("Selecciona el rango:", (default_start_date, max_date), min_value=min_date, max_value=max_date)
        
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range[0]
            
        st.markdown("---")
        st.subheader("📊 Filtros de Gráficas")
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        default_metrics_1 = [m for m in ['masa_muscular', 'grasa_corporal'] if m in numeric_columns]
        selected_metrics_1 = st.multiselect("Gráfica 1 (Absolutos):", options=numeric_columns, default=default_metrics_1)
        
        default_metrics_2 = [m for m in ['porcentaje_musculo', 'porcentaje_grasa_corporal'] if m in numeric_columns]
        selected_metrics_2 = st.multiselect("Gráfica 2 (Porcentajes):", options=numeric_columns, default=default_metrics_2)

        default_metrics_3 = [m for m in ['calificacion_grasa_visceral', 'edad_corporal'] if m in numeric_columns]
        selected_metrics_3 = st.multiselect("Gráfica 3 (Evolución):", options=numeric_columns, default=default_metrics_3)
        
    else:
        st.warning("⚠️ No hay datos cargados.")

# --- TÍTULO PRINCIPAL ---
st.title("⚖️ Dashboard de Análisis Corporal")
st.markdown("Visualización e inteligencia de métricas recolectadas de tu báscula a lo largo del tiempo.")

if df is not None and not df.empty:
    
    # Filtro de fechas aplicado al DF
    mask = (df['fecha'].dt.date >= start_date) & (df['fecha'].dt.date <= end_date)
    df_filtered = df.loc[mask]

    # --- PESTAÑAS (TABS) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Resumen y Logros", "📈 Semanal","📈 Mensual", "🥧 Composición Actual", "📋 Histórico"])
    
    with tab1:
        st.header("Resumen del Periodo")
        st.caption(f"De {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
        
        if df_filtered.empty:
            st.info("No hay datos en el rango de fechas seleccionado.")
        else:
            first_record = df_filtered.iloc[0]
            last_record = df_filtered.iloc[-1]
            
            # --- Texto Inteligente ---
            dias_dif = (last_record['fecha'] - first_record['fecha']).days
            delta_peso = last_record['peso'] - first_record['peso']
            delta_grasa = last_record['grasa_corporal'] - first_record['grasa_corporal']
            delta_musculo = last_record['masa_muscular'] - first_record['masa_muscular']
            
            texto_resumen = f"En los últimos **{dias_dif} días** analizados, "
            if delta_peso < 0:
                texto_resumen += f"has perdido **{abs(delta_peso):.1f} kg** de peso. "
            elif delta_peso > 0:
                texto_resumen += f"has ganado **{delta_peso:.1f} kg** de peso. "
            else:
                 texto_resumen += "has mantenido tu peso estable. "
                
            if delta_grasa < 0:
                texto_resumen += f"Tu grasa corporal disminuyó en **{abs(delta_grasa):.1f} kg** y "
            elif delta_grasa > 0:
                texto_resumen += f"Tu grasa corporal aumentó en **{delta_grasa:.1f} kg** y "
            else:
                 texto_resumen += f"Tu grasa corporal se mantuvo estable y "
                
            if delta_musculo > 0:
                texto_resumen += f"te felicitamos porque tu masa muscular se incrementó en **{delta_musculo:.1f} kg**. ¡Sigue así! 💪"
            elif delta_musculo < 0:
                texto_resumen += f"perdiste **{abs(delta_musculo):.1f} kg** de masa muscular. ¡No descuides el deporte! 🥩🍗"
            else:
                texto_resumen += f"tu masa muscular se mantuvo."
                
            st.success(texto_resumen)
            
            # --- KPIs ---
            st.subheader("Métricas de Variación")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Peso (kg)", f"{last_record['peso']:.1f}", f"{delta_peso:.1f} kg", delta_color="inverse")
            col2.metric("Grasa (kg)", f"{last_record['grasa_corporal']:.1f} kg", f"{delta_grasa:.1f} kg", delta_color="inverse")
            col3.metric("Masa Muscular (kg)", f"{last_record['masa_muscular']:.1f}", f"{delta_musculo:.1f} kg", delta_color="normal")
            
            delta_edad = last_record['edad_corporal'] - first_record['edad_corporal']
            col4.metric("Edad Corporal", f"{last_record['edad_corporal']:.0f}", f"{delta_edad:.0f} años", delta_color="inverse")
            
            if 'calificacion_grasa_visceral' in df_filtered.columns:
                delta_visceral = last_record['calificacion_grasa_visceral'] - first_record['calificacion_grasa_visceral']
                col5.metric("Grasa Visceral", f"{last_record['calificacion_grasa_visceral']:.1f}", f"{delta_visceral:.1f}", delta_color="inverse")
                
            st.markdown("---")
            
            # --- Logros ---
            st.subheader("🏆 Récords Históricos (Wall of Fame)")
            st.caption("Estos son tus mejores hitos desde que tienes registros en la base de datos.")
            record_peso_min = df.loc[df['peso'].idxmin()]
            record_grasa_min = df.loc[df['grasa_corporal'].idxmin()]
            record_musculo_max = df.loc[df['masa_muscular'].idxmax()]
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.info(f"**Menor Peso Alcanzado**\n\n### {record_peso_min['peso']:.1f} kg\n*(Registrado el {record_peso_min['fecha'].strftime('%d/%m/%Y')})*")
            with col_b:
                st.info(f"**Mínima Grasa Corporal**\n\n### {record_grasa_min['grasa_corporal']:.1f} kg\n*(Registrado el {record_grasa_min['fecha'].strftime('%d/%m/%Y')})*")
            with col_c:
                st.info(f"**Máxima Masa Muscular**\n\n### {record_musculo_max['masa_muscular']:.1f} kg\n*(Registrado el {record_musculo_max['fecha'].strftime('%d/%m/%Y')})*")

    with tab2:
        st.header("📈 Evolución Temporal Semanal")
        if df_filtered.empty:
            st.warning("No hay datos en el rango seleccionado.")
        else:
            # --- Gráfico 1 ---
            if selected_metrics_1:
                # Calcular media móvil de 7 días al DF original pero filtrando luego
                df_ma = df.copy()
                for m in selected_metrics_1:
                    df_ma[f"{m}_MA7"] = df_ma[m].rolling(window=7, min_periods=1).mean()
                    
                # Aplicamos el filtro de fecha
                df_ma_filtered = df_ma.loc[mask]
                
                # Crear la gráfica con Plotly Graph Objects para mayor control multicapa
                fig_sem_1 = go.Figure()
                
                # Definimos paleta de colores nativa
                colors = px.colors.qualitative.Plotly
                
                for i, m in enumerate(selected_metrics_1):
                    color = colors[i % len(colors)]
                    # Puntos reales y linea tenue
                    fig_sem_1.add_trace(go.Scatter(x=df_ma_filtered['fecha'], y=df_ma_filtered[m],
                                            mode='lines+markers', name=m,
                                            line=dict(color=color, width=2, dash='dot'), opacity=0.4))
                    # Media Móvil (Tendencia)
                    fig_sem_1.add_trace(go.Scatter(x=df_ma_filtered['fecha'], y=df_ma_filtered[f"{m}_MA7"],
                                            mode='lines', name=f"{m} (Tendencia 7d)",
                                            line=dict(color=color, width=3)))

                fig_sem_1.update_layout(title="Evolución de métricas absolutas (Línea sólida = Tendencia de 7 días)",
                                  hovermode="x unified", xaxis_title="")
                
                st.plotly_chart(fig_sem_1, use_container_width=True,key="plot_for_week_data_1")
            else:
                st.info("👆 Selecciona métricas para el Gráfico 1 en el menú lateral.")

            # --- Gráfico 2 ---
            if selected_metrics_2:
                df_melted_2 = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics_2, 
                                    var_name='Métrica', value_name='Valor')
                fig_sem_2 = px.line(df_melted_2, x='fecha', y='Valor', color='Métrica', markers=True,
                              title="Evolución porcentual en el tiempo",
                              labels={'fecha': 'Fecha', 'Valor': '%'} )
                fig_sem_2.update_layout(hovermode="x unified", xaxis_title="")
                st.plotly_chart(fig_sem_2, use_container_width=True,key="plot_for_week_data_2")
            else:
                st.info("👆 Selecciona métricas para el Gráfico 2 en el menú lateral.")
                
            # --- Gráfico 3 ---
            if selected_metrics_3:
                df_melted_3 = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics_3, 
                                    var_name='Métrica', value_name='Valor')
                
                fig_sem_3 = px.bar(df_melted_3, x='fecha', y='Valor', color='Métrica', barmode='group',
                              title="Evolución temporal de Calificaciones Categóricas",
                              labels={'fecha': 'Fecha', 'Valor': 'Unidad'})
                
                for trace in fig_sem_3.data:    
                    metric_name = trace.name
                    colors_bar = []
                    
                    if metric_name == 'edad_corporal':
                        if "fecha_nacimiento" in config:
                            fecha_nac = pd.to_datetime(config["fecha_nacimiento"])
                            edad_real = (df_filtered['fecha'] - fecha_nac).dt.days / 365.25
                            for y_v, e_v in zip(trace.y, edad_real):
                                if pd.isna(y_v): colors_bar.append("gray")
                                elif y_v < e_v: colors_bar.append("green")
                                else: colors_bar.append("red")
                            trace.marker.color = colors_bar

                    else:
                        nombres_posibles = [f"calificacion_{metric_name}", metric_name]
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
                                colors_bar.append(obtener_color_global(y_v, metric_config, "gray"))
                            trace.marker.color = colors_bar
                
                fig_sem_3.update_layout(hovermode="x unified", xaxis_title="")
                st.plotly_chart(fig_sem_3, use_container_width=True,key="plot_for_week_data_3")
            else:
                st.info("👆 Selecciona métricas para el Gráfico 3 en el menú lateral.")


    with tab3:
        st.header("📈 Evolución Temporal Mensual")
        if df_filtered.empty:
            st.warning("No hay datos en el rango seleccionado.")
        else:
            # --- Gráfico 1 ---
            if selected_metrics_1:
                # Calcular media móvil de 30 días al DF original pero filtrando luego
                df_ma = df.copy()
                for m in selected_metrics_1:
                    df_ma[f"{m}_MA30"] = df_ma[m].rolling(window=30, min_periods=1).mean()
                    
                # Aplicamos el filtro de fecha
                df_ma_filtered = df_ma.loc[mask]
                
                # Crear la gráfica con Plotly Graph Objects para mayor control multicapa
                fig_mes_1 = go.Figure()
                
                # Definimos paleta de colores nativa
                colors = px.colors.qualitative.Plotly
                
                for i, m in enumerate(selected_metrics_1):
                    color = colors[i % len(colors)]
                    # Puntos reales y linea tenue
                    fig_mes_1.add_trace(go.Scatter(x=df_ma_filtered['fecha'], y=df_ma_filtered[m],
                                            mode='lines+markers', name=m,
                                            line=dict(color=color, width=2, dash='dot'), opacity=0.4))
                    # Media Móvil (Tendencia)
                    fig_mes_1.add_trace(go.Scatter(x=df_ma_filtered['fecha'], y=df_ma_filtered[f"{m}_MA30"],
                                            mode='lines', name=f"{m} (Tendencia 30d)",
                                            line=dict(color=color, width=3)))

                fig_mes_1.update_layout(title="Evolución de métricas absolutas (Línea sólida = Tendencia de 30 días)",
                                  hovermode="x unified", xaxis_title="")
                
                st.plotly_chart(fig_mes_1, use_container_width=True,key="plot_for_month_data_1")
            else:
                st.info("👆 Selecciona métricas para el Gráfico 1 en el menú lateral.")

            # --- Gráfico 2 ---
            if selected_metrics_2:
                df_melted_2 = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics_2, 
                                    var_name='Métrica', value_name='Valor')
                fig_mes_2 = px.line(df_melted_2, x='fecha', y='Valor', color='Métrica', markers=True,
                              title="Evolución porcentual en el tiempo",
                              labels={'fecha': 'Fecha', 'Valor': '%'} )
                fig_mes_2.update_layout(hovermode="x unified", xaxis_title="")
                st.plotly_chart(fig_mes_2, use_container_width=True,key="plot_for_month_data_2")
            else:
                st.info("👆 Selecciona métricas para el Gráfico 2 en el menú lateral.")
                
            # --- Gráfico 3 ---
            if selected_metrics_3:
                df_melted_3 = df_filtered.melt(id_vars=['fecha'], value_vars=selected_metrics_3, 
                                    var_name='Métrica', value_name='Valor')
                
                fig_mes_3 = px.bar(df_melted_3, x='fecha', y='Valor', color='Métrica', barmode='group',
                              title="Evolución temporal de Calificaciones Categóricas",
                              labels={'fecha': 'Fecha', 'Valor': 'Unidad'})
                
                for trace in fig_mes_3.data:
                    metric_name = trace.name
                    colors_bar = []
                    
                    if metric_name == 'edad_corporal':
                        if "fecha_nacimiento" in config:
                            fecha_nac = pd.to_datetime(config["fecha_nacimiento"])
                            edad_real = (df_filtered['fecha'] - fecha_nac).dt.days / 365.25
                            for y_v, e_v in zip(trace.y, edad_real):
                                if pd.isna(y_v): colors_bar.append("gray")
                                elif y_v < e_v: colors_bar.append("green")
                                else: colors_bar.append("red")
                            trace.marker.color = colors_bar

                    else:
                        nombres_posibles = [f"calificacion_{metric_name}", metric_name]
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
                                colors_bar.append(obtener_color_global(y_v, metric_config, "gray"))
                            trace.marker.color = colors_bar
                
                fig_mes_3.update_layout(hovermode="x unified", xaxis_title="")
                st.plotly_chart(fig_mes_3, use_container_width=True,key="plot_for_month_data_3")
            else:
                st.info("👆 Selecciona métricas para el Gráfico 3 en el menú lateral.")

    with tab4:
        st.header("🥧 Composición Corporal")
        
        if not df_filtered.empty:
            latest_record = df_filtered.iloc[-1]
            fecha_latest = latest_record['fecha'].strftime('%d/%m/%Y')
            peso_total = latest_record['peso']
            masa_musc = latest_record['masa_muscular']
            grasa_corp = latest_record['grasa_corporal']
            resto = peso_total - masa_musc - grasa_corp
            
            df_pie = pd.DataFrame({
                'Componente': ['Masa Muscular', 'Grasa Corporal', 'Resto (Hueso, Agua, etc.)'],
                'Valor': [masa_musc, grasa_corp, resto]
            })
            
            val_musc_eval = latest_record.get('porcentaje_musculo', masa_musc)
            val_grasa_eval = latest_record.get('porcentaje_grasa_corporal', grasa_corp)
                
            color_musc = obtener_color_global(val_musc_eval, config.get("calificacion_masa_muscular"), "green")
            color_grasa = obtener_color_global(val_grasa_eval, config.get("calificacion_grasa_corporal"), "red")

            fig_pie = px.pie(df_pie, values='Valor', names='Componente',
                             title=f"Distribución a fecha de {fecha_latest} (Peso Total: {peso_total} kg)",
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
                st.subheader("Leyenda")
                
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
        else:
             st.info("No hay datos para mostrar en la composición corporal.")
             
    with tab5:
        st.header("📋 Datos Completos")
        st.caption("Tabla con todos los registros disponibles, ordenados del más reciente al más antiguo.")
        st.caption("Nota: Los valores en **rojo** indican el máximo histórico y en **verde** el mínimo histórico de cada columna.")
        
        df_reversed = df.sort_values(by='fecha', ascending=False)
        
        # Identificar columnas numéricas para el estilo
        cols_numericas = df_reversed.select_dtypes(include=['float64', 'int64']).columns
        
        # Función personalizada para aplicar fondo y color de fuente negro (contraste)
        def estilo_extremos(col):
            is_max = col == col.max()
            is_min = col == col.min()
            return [
                'background-color: #ffcdd2; color: black; font-weight: bold' if v_max 
                else 'background-color: #c8e6c9; color: black; font-weight: bold' if v_min 
                else '' 
                for v_max, v_min in zip(is_max, is_min)
            ]
        
        # Aplicar estilos
        styled_df = df_reversed.style.format(subset=cols_numericas, formatter="{:.1f}") \
            .apply(estilo_extremos, subset=cols_numericas)
            
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
