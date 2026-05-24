# 🏭 RYM Manufacturing — Tablero Industrial de Monitoreo

**Curso:** Digitalización de Plantas Productivas | Proyecto Final

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rym-manufacturing-dashboard-uyomnutmkxmpnraq7zxbz9.streamlit.app/)

## Descripción del Caso

RYM Manufacturing opera una celda de producción con proceso de secado asistido por agitación mecánica. El tablero monitorea en tiempo real:

| Variable | Sensor | Unidad |
|----------|--------|--------|
| Temperatura | DHT22 | °C |
| Humedad relativa | DHT22 | % RH |
| Vibración (3 ejes) | MPU6050 | m/s² |
| Velocidad angular | MPU6050 | °/s |

## Objetivos

1. Visualizar variables ambientales y mecánicas en tiempo real e histórico
2. Detectar desviaciones y anomalías automáticamente
3. Aplicar modelo predictivo (regresión lineal) para anticipar tendencias
4. Generar información para mantenimiento y control de calidad

## Instalación Local

```bash
git clone https://github.com/Clara123chavarriaga/rym-manufacturing-dashboard.git
cd rym-manufacturing-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Dependencias

| Librería | Versión | Uso |
|----------|---------|-----|
| streamlit | 1.35.0 | Tablero interactivo |
| influxdb-client | 1.43.0 | Conexión a InfluxDB |
| pandas | 2.2.2 | Procesamiento de datos |
| numpy | 1.26.4 | Cálculo numérico |
| plotly | 5.22.0 | Visualizaciones interactivas |
| scikit-learn | 1.5.0 | Regresión lineal |
| scipy | 1.13.1 | Estadística (p-valor) |

## Funcionalidades

- **Estado operativo** en tiempo real (OK / ALERTA / FALLA)
- **6 KPIs** con valores actuales y desviación estándar
- **Promedio Móvil Simple (SMA)** con ventana configurable
- **Detección de anomalías** por Z-Score e IQR
- **Regresión lineal** con proyección futura y métricas (R², p-valor)
- **Trayectoria 3D** del vector de aceleración
- **Estadística descriptiva** completa (N, media, std, percentiles, CV%)
- **Controles interactivos**: rango de tiempo, umbrales, auto-refresco

## Métodos Analíticos

- **SMA**: suaviza ruido de sensores
- **Z-Score**: anomalías estadísticas (|Z| > umbral configurable)
- **IQR**: outliers robustos no paramétricos
- **Regresión Lineal**: tendencia y proyección futura
- **Magnitud euclidiana**: `|a| = sqrt(ax² + ay² + az²)`

## Estructura del Proyecto
## Estructura del Proyecto

├── app.py               # Aplicación principal Streamlit
├── data_connector.py    # Conexión y consultas InfluxDB
├── analytics.py         # Módulo de analítica
├── requirements.txt     # Dependencias
└── .streamlit/
    └── config.toml      # Tema visual

## Equipo

## Equipo

| Nombre | Rol |
|--------|-----|
| María Clara Chavarriaga Álvarez | Diseño, desarrollo, análisis y documentación del proyecto |
| Sofía Montoya Mejía | Diseño, desarrollo, análisis y documentación del proyecto |
| Andrea Lopera Lopera | Diseño, desarrollo, análisis y documentación del proyecto |
| Jose Daniel Jaramillo Giraldo | Diseño, desarrollo, análisis y documentación del proyecto |

---
*Digitalización de Plantas Productivas — 2026-1*
