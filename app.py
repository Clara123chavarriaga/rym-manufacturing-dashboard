import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

from data_connector import (
    get_environment_data, get_vibration_data, get_gyro_data,
    get_environment_stats, get_vibration_stats,
)
from analytics import (
    descriptive_stats, simple_moving_average,
    zscore_anomaly_detection, iqr_anomaly_detection,
    linear_trend, operational_status,
)

st.set_page_config(
    page_title="RYM Manufacturing — Tablero Industrial",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
.rym-header {
    background: linear-gradient(135deg, #0A0E1A 0%, #0D1B2A 50%, #0A0E1A 100%);
    border: 1px solid #00D4FF22; border-left: 4px solid #00D4FF;
    padding: 1.5rem 2rem; margin-bottom: 1.5rem; border-radius: 4px;
}
.rym-header h1 { font-family: 'Share Tech Mono', monospace; color: #00D4FF; font-size: 1.8rem; margin: 0; letter-spacing: 2px; }
.rym-header p  { color: #64748B; font-size: 0.9rem; margin: 0.3rem 0 0 0; font-family: 'Share Tech Mono', monospace; }
.status-ok   { background: #064E3B; border-left: 4px solid #10B981; }
.status-alert{ background: #451A03; border-left: 4px solid #F59E0B; }
.status-fail { background: #450A0A; border-left: 4px solid #EF4444; }
.status-box  { padding: 0.8rem 1.2rem; border-radius: 4px; margin-bottom: 1rem; }
.status-box p{ margin: 0.2rem 0; font-size: 0.9rem; }
.section-title {
    font-family: 'Share Tech Mono', monospace; color: #00D4FF; font-size: 1rem;
    letter-spacing: 2px; text-transform: uppercase;
    border-bottom: 1px solid #1E293B; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 RYM Manufacturing")
    st.markdown("---")
    st.markdown("### ⏱ Rango de Tiempo")
    time_option = st.selectbox(
        "Período de análisis",
        ["Últimos 15 min", "Últimos 30 min", "Última hora",
         "Últimas 2 horas", "Últimas 6 horas", "Últimas 24 horas"],
        index=2,
    )
    time_map = {
        "Últimos 15 min": "-15m", "Últimos 30 min": "-30m",
        "Última hora": "-1h", "Últimas 2 horas": "-2h",
        "Últimas 6 horas": "-6h", "Últimas 24 horas": "-24h",
    }
    time_range = time_map[time_option]
    st.markdown("---")
    st.markdown("### 🔬 Parámetros de Análisis")
    sma_window       = st.slider("Ventana Promedio Móvil", 3, 50, 10)
    zscore_threshold = st.slider("Umbral Z-Score", 1.5, 4.0, 2.5, step=0.1)
    vib_threshold    = st.slider("Umbral vibración (m/s²)", 5.0, 20.0, 12.0, step=0.5)
    st.markdown("---")
    st.markdown("### 📡 Sensores")
    show_temp = st.checkbox("Temperatura (DHT22)",  value=True)
    show_hum  = st.checkbox("Humedad (DHT22)",      value=True)
    show_vib  = st.checkbox("Vibración (MPU6050)",  value=True)
    show_gyro = st.checkbox("Giroscopio (MPU6050)", value=False)
    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto-refresco (30s)", value=False)

if auto_refresh:
    time.sleep(30)
    st.rerun()

# ── HEADER ───────────────────────────────────
st.markdown(f"""
<div class="rym-header">
    <h1>🏭 RYM MANUFACTURING — TABLERO INDUSTRIAL</h1>
    <p>Monitoreo Celda de Secado | {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')} | {time_option}</p>
</div>
""", unsafe_allow_html=True)

# ── CARGA DE DATOS ───────────────────────────
with st.spinner("Consultando InfluxDB..."):
    df_env = get_environment_data(time_range) if (show_temp or show_hum) else pd.DataFrame()
    df_vib = get_vibration_data(time_range)   if show_vib  else pd.DataFrame()
    df_gyr = get_gyro_data(time_range)        if show_gyro else pd.DataFrame()
    env_stats = get_environment_stats(time_range)
    vib_stats = get_vibration_stats(time_range)

# ── ESTADO OPERATIVO ─────────────────────────
temp_c = env_stats.get("temperature", {}).get("current")
hum_c  = env_stats.get("humidity",    {}).get("current")
vib_c  = vib_stats.get("magnitude",   {}).get("current")
op = operational_status(temp_c, hum_c, vib_c, vib_threshold=vib_threshold)
sc = {"OK": "status-ok", "ALERTA": "status-alert", "FALLA": "status-fail"}[op["status"]]
se = {"OK": "🟢", "ALERTA": "🟡", "FALLA": "🔴"}[op["status"]]
msgs_html = "".join(f"<p>{m}</p>" for m in op["messages"])
st.markdown(f'<div class="status-box {sc}"><strong>{se} Estado: {op["status"]}</strong>{msgs_html}</div>', unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    v = env_stats.get("temperature", {})
    st.metric("🌡 Temperatura", f"{v.get('current','N/D')} °C", delta=f"±{v.get('std','?')} std")
with c2:
    v = env_stats.get("temperature", {})
    st.metric("↑ Temp. Máx", f"{v.get('max','N/D')} °C")
with c3:
    v = env_stats.get("humidity", {})
    st.metric("💧 Humedad", f"{v.get('current','N/D')} %", delta=f"±{v.get('std','?')} std")
with c4:
    v = env_stats.get("humidity", {})
    st.metric("↑ Hum. Máx", f"{v.get('max','N/D')} %")
with c5:
    v = vib_stats.get("magnitude", {})
    st.metric("📳 Vibración", f"{v.get('current','N/D')} m/s²", delta=f"±{v.get('std','?')} std")
with c6:
    v = vib_stats.get("magnitude", {})
    st.metric("↑ Vib. Máx", f"{v.get('max','N/D')} m/s²")

st.markdown("---")

# ══ SECCIÓN 1: TEMPERATURA Y HUMEDAD ════════
if show_temp or show_hum:
    st.markdown('<p class="section-title">01 / Temperatura y Humedad — DHT22</p>', unsafe_allow_html=True)
    if df_env.empty:
        st.warning("Sin datos de ambiente en el rango seleccionado.")
    else:
        fig_env = make_subplots(rows=2, cols=1, shared_xaxes=True,
            subplot_titles=("Temperatura (°C)", "Humedad Relativa (%)"),
            vertical_spacing=0.08)
        if show_temp and "temperature" in df_env.columns:
            df_t = simple_moving_average(df_env, "temperature", windows=[sma_window])
            fig_env.add_trace(go.Scatter(x=df_t["_time"], y=df_t["temperature"],
                name="Temperatura", line=dict(color="#F97316", width=1.5)), row=1, col=1)
            fig_env.add_trace(go.Scatter(x=df_t["_time"], y=df_t[f"SMA_{sma_window}"],
                name=f"SMA-{sma_window}", line=dict(color="#FCD34D", width=2, dash="dash")), row=1, col=1)
        if show_hum and "humidity" in df_env.columns:
            df_h = simple_moving_average(df_env, "humidity", windows=[sma_window])
            fig_env.add_trace(go.Scatter(x=df_h["_time"], y=df_h["humidity"],
                name="Humedad", line=dict(color="#38BDF8", width=1.5)), row=2, col=1)
            fig_env.add_trace(go.Scatter(x=df_h["_time"], y=df_h[f"SMA_{sma_window}"],
                name=f"SMA-{sma_window}", line=dict(color="#7DD3FC", width=2, dash="dash")), row=2, col=1)
        fig_env.update_layout(height=480, paper_bgcolor="#0A0E1A", plot_bgcolor="#111827",
            font=dict(color="#94A3B8", family="Share Tech Mono"),
            legend=dict(bgcolor="#111827", bordercolor="#1E293B"),
            margin=dict(l=10, r=10, t=40, b=10))
        fig_env.update_xaxes(gridcolor="#1E293B", zeroline=False)
        fig_env.update_yaxes(gridcolor="#1E293B", zeroline=False)
        st.plotly_chart(fig_env, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if show_temp and "temperature" in df_env.columns:
                st.markdown("**Anomalías de Temperatura (Z-Score)**")
                df_az = zscore_anomaly_detection(df_env, "temperature", threshold=zscore_threshold)
                anom = df_az[df_az["is_anomaly"]]
                if anom.empty:
                    st.success("✅ Sin anomalías detectadas")
                else:
                    st.warning(f"⚠️ {len(anom)} anomalías detectadas")
                    st.dataframe(anom[["_time", "temperature", "z_score"]].tail(10), use_container_width=True)
        with col_b:
            if show_hum and "humidity" in df_env.columns:
                st.markdown("**Anomalías de Humedad (Z-Score)**")
                df_ahz = zscore_anomaly_detection(df_env, "humidity", threshold=zscore_threshold)
                anom_h = df_ahz[df_ahz["is_anomaly"]]
                if anom_h.empty:
                    st.success("✅ Sin anomalías detectadas")
                else:
                    st.warning(f"⚠️ {len(anom_h)} anomalías detectadas")
                    st.dataframe(anom_h[["_time", "humidity", "z_score"]].tail(10), use_container_width=True)

        if show_temp and "temperature" in df_env.columns and len(df_env) > 5:
            st.markdown('<p class="section-title">📈 Tendencia Predictiva — Temperatura</p>', unsafe_allow_html=True)
            df_fitted, df_forecast, metrics = linear_trend(df_env, "temperature", forecast_steps=30)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df_fitted["_time"], y=df_fitted["temperature"],
                name="Mediciones", line=dict(color="#F97316", width=1.5)))
            fig_trend.add_trace(go.Scatter(x=df_fitted["_time"], y=df_fitted["trend"],
                name="Tendencia", line=dict(color="#FCD34D", width=2, dash="dot")))
            if not df_forecast.empty:
                fig_trend.add_trace(go.Scatter(x=df_forecast["_time"], y=df_forecast["trend"],
                    name="Proyección", line=dict(color="#EF4444", width=2, dash="dash"), opacity=0.8))
                fig_trend.add_vrect(x0=df_forecast["_time"].min(), x1=df_forecast["_time"].max(),
                    fillcolor="rgba(239,68,68,0.12)", line_width=0,
                    annotation_text="PROYECCIÓN", annotation_position="top left")
            fig_trend.update_layout(height=320, paper_bgcolor="#0A0E1A", plot_bgcolor="#111827",
                font=dict(color="#94A3B8", family="Share Tech Mono"),
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(bgcolor="#111827", bordercolor="#1E293B"))
            fig_trend.update_xaxes(gridcolor="#1E293B")
            fig_trend.update_yaxes(gridcolor="#1E293B")
            st.plotly_chart(fig_trend, use_container_width=True)
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("R²", metrics.get("R²", "N/D"))
            m2.metric("Pendiente", f"{metrics.get('Pendiente','N/D')} °C/s")
            m3.metric("Intercepto", metrics.get("Intercepto", "N/D"))
            m4.metric("p-valor", metrics.get("p-valor", "N/D"))
            m5.metric("Significativo", metrics.get("Significativo", "N/D"))

    st.markdown("---")

# ══ SECCIÓN 2: VIBRACIÓN ═════════════════════
if show_vib:
    st.markdown('<p class="section-title">02 / Vibración — MPU6050 (Acelerómetro)</p>', unsafe_allow_html=True)
    if df_vib.empty:
        st.warning("Sin datos de vibración en el rango seleccionado.")
    else:
        fig_vib = make_subplots(rows=2, cols=1, shared_xaxes=True,
            subplot_titles=("Aceleración por Eje (m/s²)", "Magnitud del Vector (m/s²)"),
            vertical_spacing=0.1)
        colors_ax = {"accel_x": "#EF4444", "accel_y": "#10B981", "accel_z": "#3B82F6"}
        for ax, color in colors_ax.items():
            if ax in df_vib.columns:
                fig_vib.add_trace(go.Scatter(x=df_vib["_time"], y=df_vib[ax],
                    name=ax.replace("accel_","Eje ").upper(),
                    line=dict(color=color, width=1.2)), row=1, col=1)
        df_mag = simple_moving_average(df_vib, "magnitude", windows=[sma_window])
        fig_vib.add_trace(go.Scatter(x=df_mag["_time"], y=df_mag["magnitude"],
            name="Magnitud", line=dict(color="#A78BFA", width=1.5)), row=2, col=1)
        fig_vib.add_trace(go.Scatter(x=df_mag["_time"], y=df_mag[f"SMA_{sma_window}"],
            name=f"SMA-{sma_window}", line=dict(color="#C4B5FD", width=2, dash="dash")), row=2, col=1)
        fig_vib.add_hline(y=vib_threshold, row=2, col=1, line_color="#EF4444", line_dash="dot",
            annotation_text=f"Umbral {vib_threshold} m/s²", annotation_font_color="#EF4444")
        fig_vib.update_layout(height=500, paper_bgcolor="#0A0E1A", plot_bgcolor="#111827",
            font=dict(color="#94A3B8", family="Share Tech Mono"),
            legend=dict(bgcolor="#111827", bordercolor="#1E293B"),
            margin=dict(l=10, r=10, t=40, b=10))
        fig_vib.update_xaxes(gridcolor="#1E293B", zeroline=False)
        fig_vib.update_yaxes(gridcolor="#1E293B", zeroline=False)
        st.plotly_chart(fig_vib, use_container_width=True)

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("**Detección por Z-Score**")
            df_vz = zscore_anomaly_detection(df_vib, "magnitude", threshold=zscore_threshold)
            anom_vz = df_vz[df_vz["is_anomaly"]]
            if anom_vz.empty:
                st.success(f"✅ Sin anomalías (Z={zscore_threshold})")
            else:
                st.warning(f"⚠️ {len(anom_vz)} eventos detectados")
                st.dataframe(anom_vz[["_time", "magnitude", "z_score"]].tail(10), use_container_width=True)
        with col_v2:
            st.markdown("**Detección por IQR**")
            df_vi = iqr_anomaly_detection(df_vib, "magnitude", factor=1.5)
            anom_vi = df_vi[df_vi["is_anomaly_iqr"]]
            if anom_vi.empty:
                st.success("✅ Sin outliers por IQR")
            else:
                st.warning(f"⚠️ {len(anom_vi)} outliers detectados")
                st.dataframe(anom_vi[["_time", "magnitude", "iqr_lower", "iqr_upper"]].tail(10), use_container_width=True)

        st.markdown("**Distribución de Magnitud**")
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(x=df_vib["magnitude"], nbinsx=40,
            marker_color="#A78BFA", opacity=0.85, name="Frecuencia"))
        fig_hist.add_vline(x=df_vib["magnitude"].mean(), line_color="#FCD34D", line_dash="dash",
            annotation_text="Media", annotation_font_color="#FCD34D")
        fig_hist.add_vline(x=vib_threshold, line_color="#EF4444", line_dash="dot",
            annotation_text="Umbral", annotation_font_color="#EF4444")
        fig_hist.update_layout(height=260, paper_bgcolor="#0A0E1A", plot_bgcolor="#111827",
            font=dict(color="#94A3B8", family="Share Tech Mono"),
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="Magnitud (m/s²)", yaxis_title="Frecuencia")
        fig_hist.update_xaxes(gridcolor="#1E293B")
        fig_hist.update_yaxes(gridcolor="#1E293B")
        st.plotly_chart(fig_hist, use_container_width=True)

        if all(c in df_vib.columns for c in ["accel_x", "accel_y", "accel_z"]):
            st.markdown("**Trayectoria 3D del Vector de Aceleración**")
            fig_3d = go.Figure(data=go.Scatter3d(
                x=df_vib["accel_x"], y=df_vib["accel_y"], z=df_vib["accel_z"],
                mode="lines+markers",
                marker=dict(size=2, color=df_vib["magnitude"],
                            colorscale="Plasma", showscale=True,
                            colorbar=dict(title="Magnitud")),
                line=dict(width=1, color="#A78BFA"),
            ))
            fig_3d.update_layout(height=450, paper_bgcolor="#0A0E1A",
                scene=dict(bgcolor="#111827",
                    xaxis=dict(title="Accel X (m/s²)", gridcolor="#1E293B"),
                    yaxis=dict(title="Accel Y (m/s²)", gridcolor="#1E293B"),
                    zaxis=dict(title="Accel Z (m/s²)", gridcolor="#1E293B")),
                font=dict(color="#94A3B8", family="Share Tech Mono"),
                margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_3d, use_container_width=True)

        if len(df_vib) > 5:
            st.markdown('<p class="section-title">📈 Tendencia Predictiva — Vibración</p>', unsafe_allow_html=True)
            df_vf, df_vfc, vmetrics = linear_trend(df_vib, "magnitude", forecast_steps=30)
            fig_vt = go.Figure()
            fig_vt.add_trace(go.Scatter(x=df_vf["_time"], y=df_vf["magnitude"],
                name="Magnitud", line=dict(color="#A78BFA", width=1.5)))
            fig_vt.add_trace(go.Scatter(x=df_vf["_time"], y=df_vf["trend"],
                name="Tendencia", line=dict(color="#C4B5FD", width=2, dash="dot")))
            if not df_vfc.empty:
                fig_vt.add_trace(go.Scatter(x=df_vfc["_time"], y=df_vfc["trend"],
                    name="Proyección", line=dict(color="#EF4444", width=2, dash="dash"), opacity=0.8))
                fig_vt.add_vrect(x0=df_vfc["_time"].min(), x1=df_vfc["_time"].max(),
                    fillcolor="rgba(239,68,68,0.12)", line_width=0,
                    annotation_text="PROYECCIÓN", annotation_position="top left")
            fig_vt.add_hline(y=vib_threshold, line_color="#EF4444", line_dash="dot",
                annotation_text=f"Umbral {vib_threshold}", annotation_font_color="#EF4444")
            fig_vt.update_layout(height=320, paper_bgcolor="#0A0E1A", plot_bgcolor="#111827",
                font=dict(color="#94A3B8", family="Share Tech Mono"),
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(bgcolor="#111827", bordercolor="#1E293B"))
            fig_vt.update_xaxes(gridcolor="#1E293B")
            fig_vt.update_yaxes(gridcolor="#1E293B")
            st.plotly_chart(fig_vt, use_container_width=True)
            mv1, mv2, mv3, mv4, mv5 = st.columns(5)
            mv1.metric("R²", vmetrics.get("R²","N/D"))
            mv2.metric("Pendiente", f"{vmetrics.get('Pendiente','N/D')} m/s²/s")
            mv3.metric("Intercepto", vmetrics.get("Intercepto","N/D"))
            mv4.metric("p-valor", vmetrics.get("p-valor","N/D"))
            mv5.metric("Significativo", vmetrics.get("Significativo","N/D"))

    st.markdown("---")

# ══ SECCIÓN 3: GIROSCOPIO ════════════════════
if show_gyro and not df_gyr.empty:
    st.markdown('<p class="section-title">03 / Giroscopio — MPU6050</p>', unsafe_allow_html=True)
    fig_gyr = go.Figure()
    for gx, color in {"gyro_x":"#F97316","gyro_y":"#10B981","gyro_z":"#3B82F6"}.items():
        if gx in df_gyr.columns:
            fig_gyr.add_trace(go.Scatter(x=df_gyr["_time"], y=df_gyr[gx],
                name=gx.replace("gyro_","Giro ").upper(), line=dict(color=color, width=1.2)))
    fig_gyr.update_layout(height=300, paper_bgcolor="#0A0E1A", plot_bgcolor="#111827",
        font=dict(color="#94A3B8", family="Share Tech Mono"),
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(bgcolor="#111827", bordercolor="#1E293B"),
        yaxis_title="Velocidad Angular (°/s)")
    fig_gyr.update_xaxes(gridcolor="#1E293B")
    fig_gyr.update_yaxes(gridcolor="#1E293B")
    st.plotly_chart(fig_gyr, use_container_width=True)
    st.markdown("---")

# ══ SECCIÓN 4: ESTADÍSTICA ═══════════════════
st.markdown('<p class="section-title">04 / Estadística Descriptiva</p>', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🌡 Ambiente (DHT22)", "📳 Vibración (MPU6050)"])
with tab1:
    if not df_env.empty:
        cols_env = [c for c in ["temperature","humidity"] if c in df_env.columns]
        if cols_env:
            st.dataframe(descriptive_stats(df_env, cols_env), use_container_width=True)
    else:
        st.info("Sin datos de ambiente.")
with tab2:
    if not df_vib.empty:
        cols_vib = [c for c in ["accel_x","accel_y","accel_z","magnitude"] if c in df_vib.columns]
        if cols_vib:
            st.dataframe(descriptive_stats(df_vib, cols_vib), use_container_width=True)
    else:
        st.info("Sin datos de vibración.")

# ══ DATOS CRUDOS ══════════════════════════════
with st.expander("🗃 Ver datos crudos (Raw Data)"):
    t1, t2, t3 = st.tabs(["Ambiente","Acelerómetro","Giroscopio"])
    with t1:
        st.dataframe(df_env.tail(100) if not df_env.empty else pd.DataFrame(), use_container_width=True)
    with t2:
        st.dataframe(df_vib.tail(100) if not df_vib.empty else pd.DataFrame(), use_container_width=True)
    with t3:
        st.dataframe(df_gyr.tail(100) if not df_gyr.empty else pd.DataFrame(), use_container_width=True)

st.markdown("---")
st.markdown(
    "<center style='color:#475569;font-family:monospace;font-size:0.8rem'>"
    "RYM Manufacturing © 2025 | Digitalización de Plantas Productivas | InfluxDB · Streamlit · Python"
    "</center>", unsafe_allow_html=True)
