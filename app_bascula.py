import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import datetime
import numpy as np
from streamlit_gsheets import GSheetsConnection

# Page Configuration
st.set_page_config(page_title="Body Composition Analysis", page_icon="⚖️", layout="wide")

# Column Mapping (Spanish to English)
COL_MAPPING = {
    'fecha': 'date',
    'peso': 'weight',
    'imc': 'bmi',
    'porcentaje_grasa_corporal': 'body_fat_percentage',
    'masa_agua_corporal': 'body_water_mass',
    'grasa_corporal': 'body_fat_mass',
    'contenido_mineral_oseo': 'bone_mineral_content',
    'masa_proteica': 'protein_mass',
    'masa_muscular': 'muscle_mass',
    'porcentaje_musculo': 'muscle_percentage',
    'porcentaje_agua_corporal': 'body_water_percentage',
    'porcentaje_proteina': 'protein_percentage',
    'porcentaje_mineral_oseo': 'bone_mineral_percentage',
    'masa_muscular_esqueletica': 'skeletal_muscle_mass',
    'calificacion_grasa_visceral': 'visceral_fat_rating',
    'indice_metabolico_basal': 'basal_metabolic_rate',
    'estimacion_relacion_cintura_cadera': 'waist_hip_ratio_estimate',
    'edad_corporal': 'body_age',
    'peso_corporal_sin_grasa': 'fat_free_body_weight'
}

# Reading configuration files
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

with open("config/percentage_color.json", "r", encoding="utf-8") as f:
    metrics_config = json.load(f)

with open("config/units.json", "r", encoding="utf-8") as f:
    units_config = json.load(f)

# Get file path from config
csv_file_path = config.get("csv_file_path", "")
google_sheets_url = config.get("google_sheets_url", "")

def get_metric_style(metric, value):
    if pd.isna(value): return "gray", "N/A"
    
    # Normalize metric name to look up in config
    clean_metric = metric.lower().replace(" ", "_")
    for m_key in metrics_config["metrics"]:
        if m_key in clean_metric or clean_metric in m_key:
            bands = metrics_config["metrics"][m_key].get("color_bands", [])
            for band in bands:
                m_min = band.get("min")
                m_max = band.get("max")
                
                low_match = (m_min is None or value >= m_min)
                high_match = (m_max is None or value <= m_max)
                
                if low_match and high_match:
                    return band.get("color", "gray"), band.get("level", "Unknown")
    return "gray", "Unknown"

def create_gauge(value, title, metric_key):
    # Get metric configuration
    m_config = metrics_config["metrics"].get(metric_key, {})
    bands = m_config.get("color_bands", [])
    unit = m_config.get("unit", "")

    # Determine maximum range
    limit_values = []
    for b in bands:
        if b.get("min") is not None: limit_values.append(b["min"])
        if b.get("max") is not None: limit_values.append(b["max"])
    max_val = max(limit_values) * 1.1 if limit_values else 100

    # Create steps
    steps = []
    for b in bands:
        m_min = b.get("min") if b.get("min") is not None else 0
        m_max = b.get("max") if b.get("max") is not None else max_val
        steps.append({'range': [m_min, m_max], 'color': b.get("color", "gray")})

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title, 'font': {'size': 18}},
        number = {'suffix': f" {unit}", 'font': {'size': 24, 'color': "white"}},
        gauge = {
            'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "white", 'thickness': 0.2},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': steps,
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(height=230, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    return fig

def add_health_bands(fig, metric):
    m_config = metrics_config["metrics"].get(metric)
    if not m_config: return fig
    
    for band in m_config.get("color_bands", []):
        m_min = band.get("min")
        m_max = band.get("max")
        color = band.get("color")
        if color:
            # If min or max is None, we use extreme values for visualization
            y0 = m_min if m_min is not None else -1000
            y1 = m_max if m_max is not None else 1000
            fig.add_hrect(y0=y0, y1=y1, fillcolor=color, opacity=0.1, line_width=0, layer="below")
    return fig

# Function to load and clean data
@st.cache_data(ttl=600)  # Clear cache every 10 mins (ideal for GSheets)
def load_data():
    try:
        # Prioritize Google Sheets if configured
        if google_sheets_url and "YOUR_ID_HERE" not in google_sheets_url:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(spreadsheet=google_sheets_url)
            df = df.dropna(how='all') # Clean totally empty rows
        else:
            # Read local CSV
            df = pd.read_csv(csv_file_path, encoding="utf-8")
        
        # Rename columns to English
        df = df.rename(columns=COL_MAPPING)

        # Convert date. In the CSV it's as dd/mm/yyyy
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
        
        # Sort by date chronologically
        df = df.sort_values(by='date')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"Error loading data file: {e}")
        return None

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("🔄 Sync Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    
    if df is not None and not df.empty:
        st.subheader("📅 Date Filter")
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        # By default show the last month
        default_start_date = max(min_date, max_date - datetime.timedelta(days=30))

        start_date_7_day = max_date - datetime.timedelta(days=7)
        start_date_30_day = max_date - datetime.timedelta(days=15)
        
        date_range_7 = st.date_input("Select range:", (start_date_7_day, max_date), min_value=min_date, max_value=max_date)
        #date_range_30 = st.date_input("Selecciona el rango:", (start_date_30_day, max_date), min_value=min_date, max_value=max_date)
        
        if len(date_range_7) == 2:
            start_date_7, end_date_7 = date_range_7
        else:
            start_date_7 = end_date_7 = date_range_7[0]
            
        #if len(date_range_30) == 2:
        #    start_date_30, end_date_30 = date_range_30
        #else:
        #    start_date_30 = end_date_30 = date_range_30[0]
            
        st.markdown("---")
        st.subheader("📊 Chart Filters")
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        default_metrics_1 = [m for m in ['muscle_mass'] if m in numeric_columns]
        selected_metrics_1 = st.multiselect("Chart 1 (Absolute):", options=numeric_columns, default=default_metrics_1)

        default_metrics_fat = [m for m in ['body_fat_mass'] if m in numeric_columns]
        selected_metrics_fat = st.multiselect("Chart 2 (Absolute):", options=numeric_columns, default=default_metrics_fat)
        
        default_metrics_2 = [m for m in ['muscle_percentage', 'body_fat_percentage'] if m in numeric_columns]
        selected_metrics_2 = st.multiselect("Chart 2 (Percentages):", options=numeric_columns, default=default_metrics_2)

        default_metrics_3 = [m for m in ['visceral_fat_rating', 'body_age'] if m in numeric_columns]
        selected_metrics_3 = st.multiselect("Chart 3 (Evolution):", options=numeric_columns, default=default_metrics_3)
        
        st.markdown("---")
        st.subheader("💡 Period Comparison")
        comparison_mode = st.checkbox("Activate Comparison Period")
        if comparison_mode:
            min_c = min_date
            max_c = max_date
            comp_range = st.date_input("Period 2 (Comparative):", (start_date_7 - datetime.timedelta(days=7), start_date_7 - datetime.timedelta(days=1)), min_value=min_c, max_value=max_c)
            if len(comp_range) == 2:
                start_comp, end_comp = comp_range
            else:
                start_comp = end_comp = comp_range[0]
            
    else:
        st.warning("⚠️ No data loaded.")
    
    st.markdown("---")
    st.subheader("🎯 Objectives")
    default_target = config['weight_target']
    weight_target = st.number_input("Target Weight (kg):", value=float(default_target), step=0.1)

# --- MAIN TITLE ---
st.title("⚖️ Body Composition Analysis Dashboard")
st.markdown("Visualization and intelligence of metrics collected from your scale over time.")

if df is not None and not df.empty:
    
    # Date filter applied to DF
    mask = (df['date'].dt.date >= start_date_7) & (df['date'].dt.date <= end_date_7)
    df_filtered = df.loc[mask]

    if comparison_mode:
        mask_comp = (df['date'].dt.date >= start_comp) & (df['date'].dt.date <= end_comp)
        df_comp = df.loc[mask_comp]
    else:
        df_comp = pd.DataFrame()

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Summary & Achievements", "📈 Muscle Mass","📈 Body Fat", "🥧 Current Composition", "📋 History"])
    
    with tab1:
        st.header("Period Summary")
        st.caption(f"From {start_date_7.strftime('%d/%m/%Y')} to {end_date_7.strftime('%d/%m/%Y')}")
        
        if df_filtered.empty:
            st.info("No data in the selected date range.")
        else:
            first_record = df_filtered.iloc[0]
            last_record = df_filtered.iloc[-1]
            
            # --- Smart Summary Text ---
            days_diff = (last_record['date'] - first_record['date']).days
            delta_weight = last_record['weight'] - first_record['weight']
            delta_fat = last_record['body_fat_mass'] - first_record['body_fat_mass']
            delta_muscle = last_record['muscle_mass'] - first_record['muscle_mass']
            
            summary_text = f"In the last **{days_diff} days** analyzed, "
            if delta_weight < 0:
                summary_text += f"you have lost **{abs(delta_weight):.1f} kg** of weight. "
            elif delta_weight > 0:
                summary_text += f"you have gained **{delta_weight:.1f} kg** of weight. "
            else:
                 summary_text += "your weight has remained stable. "
                
            if delta_fat < 0:
                summary_text += f"Your body fat decreased by **{abs(delta_fat):.1f} kg** and "
            elif delta_fat > 0:
                summary_text += f"Your body fat increased by **{delta_fat:.1f} kg** and "
            else:
                 summary_text += f"Your body fat remained stable and "
                
            if delta_muscle > 0:
                summary_text += f"congratulations because your muscle mass increased by **{delta_muscle:.1f} kg**. Keep it up! 💪"
            elif delta_muscle < 0:
                summary_text += f"you lost **{abs(delta_muscle):.1f} kg** of muscle mass. Don't neglect your workout! 🥩🍗"
            else:
                summary_text += f"your muscle mass remained stable."
                
            st.success(summary_text)
            
            # --- KPIs ---
            st.subheader("Variation Metrics")
            
            def show_period_metrics(curr_df, label="Actual"):
                if curr_df.empty:
                    st.info(f"No data for {label}")
                    return
                first = curr_df.iloc[0]
                last = curr_df.iloc[-1]
                cols = st.columns(5)
                
                # Weight
                color_p, _ = get_metric_style("weight", last['weight'])
                cols[0].metric(f"Weight ({label})", f"{last['weight']:.1f}", f"{last['weight'] - first['weight']:.1f} kg", delta_color="inverse")
                
                # Fat
                color_g, _ = get_metric_style("body_fat_mass", last['body_fat_mass'])
                cols[1].metric(f"Fat ({label})", f"{last['body_fat_mass']:.1f} kg", f"{last['body_fat_mass'] - first['body_fat_mass']:.1f} kg", delta_color="inverse")
                
                # Muscle
                color_m, _ = get_metric_style("muscle_mass", last['muscle_mass'])
                cols[2].metric(f"Muscle ({label})", f"{last['muscle_mass']:.1f}", f"{last['muscle_mass'] - first['muscle_mass']:.1f} kg", delta_color="normal")
                
                # Age
                cols[3].metric("Body Age", f"{last['body_age']:.0f}", f"{last['body_age'] - first['body_age']:.0f} years", delta_color="inverse")
                
                # Visceral
                if 'visceral_fat_rating' in curr_df.columns:
                    cols[4].metric("V. Fat", f"{last['visceral_fat_rating']:.1f}", f"{last['visceral_fat_rating'] - first['visceral_fat_rating']:.1f}", delta_color="inverse")

            if comparison_mode and not df_comp.empty:
                st.markdown("**Main Period**")
                show_period_metrics(df_filtered)
                st.markdown("**Comparison Period**")
                show_period_metrics(df_comp, "Comp.")
            else:
                show_period_metrics(df_filtered)
                
            st.markdown("---")

            # --- Health Gauges ---
            st.subheader("🩺 Current Health Status (Gauges)")
            g_col1, g_col2, g_col3 = st.columns(3)
            
            with g_col1:
                height = config.get("height")
                bmi_val = last_record['weight'] / (height ** 2) if height else last_record.get('bmi', 0)
                st.plotly_chart(create_gauge(bmi_val, "BMI", "bmi"), width='stretch')
                
            with g_col2:
                visceral_val = last_record.get('visceral_fat_rating', 0)
                st.plotly_chart(create_gauge(visceral_val, "Visceral Fat", "visceral_fat_rating"), width='stretch')
                
            with g_col3:
                muscle_val = last_record.get('muscle_percentage', 0)
                st.plotly_chart(create_gauge(muscle_val, "Muscle Mass (%)", "muscle_percentage"), width='stretch')

            st.markdown("---")

            # --- Projections and Goals ---
            if weight_target > 0 and not df_filtered.empty:
                st.subheader("🎯 Progress Towards Goal")
                
                # Data for regression (dates as numbers)
                x = (df_filtered['date'] - df_filtered['date'].min()).dt.days.values
                y = df_filtered['weight'].values
                
                if len(x) > 1:
                    # Linear fit: y = mx + c
                    m, c = np.polyfit(x, y, 1)
                    
                    # When will we reach the target weight? weight_obj = m*x + c => x = (weight_obj - c) / m
                    if m != 0:
                        days_to_target = (weight_target - c) / m
                        if days_to_target > x[-1]: # If the goal is in the future
                            target_date = df_filtered['date'].min() + datetime.timedelta(days=days_to_target)
                            
                            col_goal1, col_goal2 = st.columns([2, 1])
                            with col_goal1:
                                days_left = (target_date - last_record['date']).days
                                if days_left > 0:
                                    st.info(f"📅 **Estimated Date:** {target_date.strftime('%d/%m/%Y')} (in approx. {days_left} days)")
                                else:
                                    st.success("🎉 Goal reached according to trend!")
                            
                            with col_goal2:
                                # Calculate progress
                                initial_weight_period = df_filtered.iloc[0]['weight']
                                total_to_lose = initial_weight_period - weight_target
                                already_lost = initial_weight_period - last_record['weight']
                                
                                if total_to_lose > 0:
                                    progress = min(max(already_lost / total_to_lose, 0.0), 1.0)
                                    st.write(f"Progress: {progress*100:.1f}%")
                                    st.progress(progress)
                        else:
                            if last_record['weight'] <= weight_target:
                                st.success(f"🏆 You have exceeded your goal of {weight_target} kg! (Current weight: {last_record['weight']:.1f} kg)")
                            else:
                                st.warning("📉 The current trend is not heading towards your goal. You can adjust it!")
                else:
                    st.info("You need at least two records in this period to calculate the projection.")

            st.markdown("---")

            # --- Data Insights: Perspectives and Patterns ---
            st.subheader("🧠 Data Insights")
            
            # 1. Alerts for Sudden Variations
            if len(df_filtered) >= 2:
                last_val = df_filtered.iloc[-1]
                prev_val = df_filtered.iloc[-2]
                
                # Alert: Significant muscle loss
                diff_musc_last = last_val['muscle_mass'] - prev_val['muscle_mass']
                if diff_musc_last < -0.5:
                    st.warning(f"⚠️ **Muscle Alert:** You have lost {abs(diff_musc_last):.1f} kg of muscle mass since the last record. Ensure you consume enough protein!")
                
                # Alert: Significant fat increase
                diff_fat_last = last_val['body_fat_mass'] - prev_val['body_fat_mass']
                if diff_fat_last > 0.5:
                    st.error(f"⚠️ **Fat Alert:** Increase of {diff_fat_last:.1f} kg of body fat. Review your physical activity!")

            # 2. Pattern Chart by Day of the Week
            st.markdown("**Weekly Patterns (Average per day)**")
            df_patterns = df_filtered.copy()
            df_patterns['day_of_week'] = df_patterns['date'].dt.day_name()
            # Sort days correctly
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df_patterns['day_of_week'] = pd.Categorical(df_patterns['day_of_week'], categories=days_order, ordered=True)
            
            daily_average = df_patterns.groupby('day_of_week', observed=True)[['weight', 'body_fat_mass']].mean().reset_index()
            
            fig_patterns = px.bar(daily_average, x='day_of_week', y='weight', 
                                title="Average Weight by Day of the Week",
                                color='weight', color_continuous_scale='Blues')
            fig_patterns.update_layout(height=350, xaxis_title="", coloraxis_showscale=False)
            st.plotly_chart(fig_patterns, width='stretch')
            
            st.markdown("---")
            
            # --- Achievements ---
            st.subheader("🏆 Comparative: First Record vs Current")
            initial_record = df.iloc[0]
            
            diff_weight_total = last_record['weight'] - initial_record['weight']
            diff_fat_total = last_record['body_fat_mass'] - initial_record['body_fat_mass']
            diff_muscle_total = last_record['muscle_mass'] - initial_record['muscle_mass']
            
            c_hist1, c_hist2, c_hist3 = st.columns(3)
            with c_hist1:
                st.metric("Total Weight Change", f"{last_record['weight']:.1f} kg", f"{diff_weight_total:.1f} kg (since start)", delta_color="inverse")
            with c_hist2:
                st.metric("Total Fat Change", f"{last_record['body_fat_mass']:.1f} kg", f"{diff_fat_total:.1f} kg (since start)", delta_color="inverse")
            with c_hist3:
                st.metric("Total Muscle Change", f"{last_record['muscle_mass']:.1f} kg", f"{diff_muscle_total:.1f} kg (since start)", delta_color="normal")

            st.markdown("---")
            st.subheader("🏆 Historical Records (Wall of Fame)")
            st.caption("These are your best milestones since you have records in the database.")
            record_weight_min = df.loc[df['weight'].idxmin()]
            record_fat_min = df.loc[df['body_fat_mass'].idxmin()]
            record_muscle_max = df.loc[df['muscle_mass'].idxmax()]
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.info(f"**Lowest Weight Reached**\n\n### {record_weight_min['weight']:.1f} kg\n*(Recorded on {record_weight_min['date'].strftime('%d/%m/%Y')})*")
            with col_b:
                st.info(f"**Minimum Body Fat**\n\n### {record_fat_min['body_fat_mass']:.1f} kg\n*(Recorded on {record_fat_min['date'].strftime('%d/%m/%Y')})*")
            with col_c:
                st.info(f"**Maximum Skeletal Muscle**\n\n### {record_muscle_max['skeletal_muscle_mass']:.1f} kg\n*(Recorded on {record_muscle_max['date'].strftime('%d/%m/%Y')})*")

            st.markdown("---")
            st.subheader("📊 Period Metrics")
            
            # Calculate period averages
            avg_weight = df_filtered['weight'].mean()
            avg_fat = df_filtered['body_fat_mass'].mean()
            avg_muscle = df_filtered['muscle_mass'].mean()
            avg_visceral = df_filtered['visceral_fat_rating'].mean()
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Average Weight", f"{avg_weight:.1f} kg")
            with c2:
                st.metric("Average Body Fat", f"{avg_fat:.1f} kg")
            with c3:
                st.metric("Average Muscle", f"{avg_muscle:.1f} kg")
    with tab2:
        st.header("📈 Muscle Mass Evolution")
        if df_filtered.empty:
            st.warning("No data in the selected range.")
        else:
            # Chart 1: Absolute evolution (Kg) with MA7 Trend
            # Calculate MA7
            df_plot = df_filtered.copy()
            df_plot['muscle_mass_MA7'] = df_plot['muscle_mass'].rolling(window=7, min_periods=1).mean()
            
            fig1 = go.Figure()
            # Real points
            fig1.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['muscle_mass'],
                                     mode='markers', name='Real Value',
                                     marker=dict(color='lightgray', size=8), opacity=0.6))
            # Trend
            fig1.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['muscle_mass_MA7'],
                                     mode='lines+markers', name='Trend (7d)',
                                     line=dict(color='#4CAF50', width=3)))
            
            fig1.update_layout(title="Muscle Mass Evolution (Kg) - 7-day Trend",
                               hovermode="x unified", height=400)
            st.plotly_chart(fig1, width='stretch')

            # Chart 2: Percentage and Color
            # Assign colors per point
            point_colors = [get_metric_style("muscle_percentage", v)[0] for v in df_plot['muscle_percentage']]
            
            fig2 = px.bar(df_plot, x='date', y='muscle_percentage',
                          title="Muscle Percentage Distribution (%)",
                          labels={'muscle_percentage': '% Muscle'})
            fig2.update_traces(marker_color=point_colors)
            fig2 = add_health_bands(fig2, "muscle_percentage")
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, width='stretch')

    with tab3:
        st.header("📈 Body Fat Evolution")
        if df_filtered.empty:
            st.warning("No data in the selected range.")
        else:
            # Chart 1: Absolute evolution (Kg) with MA7 Trend
            df_plot = df_filtered.copy()
            df_plot['body_fat_mass_MA7'] = df_plot['body_fat_mass'].rolling(window=7, min_periods=1).mean()
            
            figg1 = go.Figure()
            figg1.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['body_fat_mass'],
                                      mode='markers', name='Real Value',
                                      marker=dict(color='lightgray', size=8), opacity=0.6))
            figg1.add_trace(go.Scatter(x=df_plot['date'], y=df_plot['body_fat_mass_MA7'],
                                      mode='lines+markers', name='Trend (7d)',
                                      line=dict(color='#FF6B6B', width=3)))
            
            figg1.update_layout(title="Body Fat Evolution (Kg) - 7-day Trend",
                               hovermode="x unified", height=400)
            st.plotly_chart(figg1, width='stretch')

            # Chart 2: Percentage and Color
            point_colors_g = [get_metric_style("body_fat_percentage", v)[0] for v in df_plot['body_fat_percentage']]
            
            figg2 = px.bar(df_plot, x='date', y='body_fat_percentage',
                           title="Body Fat Percentage (%)",
                           labels={'body_fat_percentage': '% Fat'})
            figg2.update_traces(marker_color=point_colors_g)
            figg2 = add_health_bands(figg2, "body_fat_percentage")
            figg2.update_layout(height=400)
            st.plotly_chart(figg2, width='stretch')

    with tab4:
        st.header("🥧 Body Composition")
        
        if not df_filtered.empty:
            latest_record = df_filtered.iloc[-1]
            latest_date = latest_record['date'].strftime('%d/%m/%Y')
            total_weight = latest_record['weight']
            muscle_mass = latest_record['muscle_mass']
            body_fat_mass = latest_record['body_fat_mass']
            rest = total_weight - muscle_mass - body_fat_mass
            
            df_pie = pd.DataFrame({
                'Component': ['Muscle Mass', 'Body Fat', 'Rest (Bone, Water, etc.)'],
                'Value': [muscle_mass, body_fat_mass, rest]
            })
            
            muscle_eval_val = latest_record.get('muscle_percentage', muscle_mass)
            fat_eval_val = latest_record.get('body_fat_percentage', body_fat_mass)
                
            muscle_color, _ = get_metric_style("muscle_percentage", muscle_eval_val)
            fat_color, _ = get_metric_style("body_fat_percentage", fat_eval_val)

            fig_pie = px.pie(df_pie, values='Value', names='Component',
                             title=f"Distribution as of {latest_date} (Total Weight: {total_weight} kg)",
                             color='Component',
                             color_discrete_map={
                                 'Muscle Mass': muscle_color,
                                 'Body Fat': fat_color,
                                 'Rest (Bone, Water, etc.)': 'gray'
                             })
                             
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            
            col_pie, col_legend = st.columns([2, 1])
            
            with col_pie:
                st.plotly_chart(fig_pie, width='stretch')
                
            with col_legend:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.subheader("Legend")
                
                def draw_legend(metric_key):
                    m_info = metrics_config["metrics"].get(metric_key, {})
                    st.markdown(f"**{m_info.get('description', metric_key)}**")
                    bands = m_info.get("color_bands", [])
                    if bands:
                        for b in bands:
                            st.markdown(f"<span style='color:{b['color']}; font-size:1.2em;'>■</span> {b['min']}-{b['max'] if b['max'] else '∞'} ({b['level']})", unsafe_allow_html=True)
                        
                draw_legend("muscle_percentage")
                st.markdown("<br>", unsafe_allow_html=True)
                draw_legend("body_fat_percentage")
        else:
             st.info("No data to show in body composition.")
             
    with tab5:
        st.header("📋 Complete Data")
        st.caption("Table with all available records, sorted from most recent to oldest.")
        st.caption("Note: Values in **red** indicate the historical maximum and in **green** the historical minimum of each column.")

        new_custom_order = [
            'date', 'weight', 'muscle_mass', 'body_fat_mass', 'fat_free_body_weight',
            'protein_mass', 'skeletal_muscle_mass', 'visceral_fat_rating',
            'body_water_mass', 'muscle_percentage', 'body_fat_percentage',
            'protein_percentage', 'bmi', 'bone_mineral_content',
            'body_water_percentage', 'bone_mineral_percentage', 'basal_metabolic_rate',
            'waist_hip_ratio_estimate', 'body_age', 'filename'
        ]
        
        df = df[new_custom_order]
        df_reversed = df.sort_values(by='date', ascending=False)
        
        # Identify numeric columns for styling
        numeric_cols = df_reversed.select_dtypes(include=['float64', 'int64']).columns
        
        # Custom function to apply background and black font color (contrast)
        def extreme_styles(col):
            is_max = col == col.max()
            is_min = col == col.min()
            return [
                'background-color: #ffcdd2; color: black; font-weight: bold' if v_max 
                else 'background-color: #c8e6c9; color: black; font-weight: bold' if v_min 
                else '' 
                for v_max, v_min in zip(is_max, is_min)
            ]
        
        # Apply styles
        styled_df = df_reversed.style.format(subset=numeric_cols, formatter="{:.1f}") \
            .apply(extreme_styles, subset=numeric_cols)
            
        st.dataframe(styled_df, width='stretch', hide_index=True)

        # --- Export Button ---
        st.markdown("---")
        csv = df_reversed.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered History (CSV)",
            data=csv,
            file_name=f"scale_analysis_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
