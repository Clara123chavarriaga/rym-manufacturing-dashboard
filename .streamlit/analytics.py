import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from sklearn.linear_model import LinearRegression


def descriptive_stats(df, columns):
    result = {}
    for col in columns:
        if col not in df.columns:
            continue
        s = df[col].dropna()
        result[col] = {
            "N (muestras)":   int(s.count()),
            "Media":          round(s.mean(), 4),
            "Desv. Estándar": round(s.std(), 4),
            "Mínimo":         round(s.min(), 4),
            "Percentil 25%":  round(s.quantile(0.25), 4),
            "Mediana (50%)":  round(s.median(), 4),
            "Percentil 75%":  round(s.quantile(0.75), 4),
            "Máximo":         round(s.max(), 4),
            "CV (%)":         round((s.std() / s.mean()) * 100, 2) if s.mean() != 0 else None,
        }
    return pd.DataFrame(result)


def simple_moving_average(df, column, windows=[5, 10, 20]):
    df = df.copy()
    for w in windows:
        df[f"SMA_{w}"] = df[column].rolling(window=w, min_periods=1).mean()
    return df


def zscore_anomaly_detection(df, column, threshold=2.5):
    df = df.copy()
    s = df[column].dropna()
    mean, std = s.mean(), s.std()
    if std == 0:
        df["z_score"] = 0.0
        df["is_anomaly"] = False
        return df
    df["z_score"] = (df[column] - mean) / std
    df["is_anomaly"] = df["z_score"].abs() > threshold
    return df


def iqr_anomaly_detection(df, column, factor=1.5):
    df = df.copy()
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    df["iqr_lower"] = Q1 - factor * IQR
    df["iqr_upper"] = Q3 + factor * IQR
    df["is_anomaly_iqr"] = (df[column] < df["iqr_lower"]) | (df[column] > df["iqr_upper"])
    return df


def linear_trend(df, column, forecast_steps=20):
    df = df.dropna(subset=[column]).copy()
    if len(df) < 5:
        return df, pd.DataFrame(), {}
    t0 = df["_time"].min()
    df["t_sec"] = (df["_time"] - t0).dt.total_seconds()
    X = df["t_sec"].values.reshape(-1, 1)
    y = df[column].values
    model = LinearRegression()
    model.fit(X, y)
    df["trend"] = model.predict(X)
    r2 = model.score(X, y)
    slope = model.coef_[0]
    intercept = model.intercept_
    _, p_value = scipy_stats.pearsonr(df["t_sec"], y)
    metrics = {
        "R²": round(r2, 4),
        "Pendiente": round(slope, 6),
        "Intercepto": round(intercept, 4),
        "p-valor": round(p_value, 6),
        "Significativo": "Sí ✅" if p_value < 0.05 else "No ❌",
    }
    last_t = df["t_sec"].max()
    dt_mean = df["t_sec"].diff().median()
    future_t = np.array([last_t + dt_mean * i for i in range(1, forecast_steps + 1)])
    future_time = [t0 + pd.Timedelta(seconds=float(s)) for s in future_t]
    df_forecast = pd.DataFrame({
        "_time": future_time,
        "t_sec": future_t,
        "trend": model.predict(future_t.reshape(-1, 1)),
    })
    return df, df_forecast, metrics


def operational_status(temp, hum, vib_mag,
                        temp_range=(20, 80), hum_range=(20, 70), vib_threshold=12.0):
    messages = []
    level = "OK"
    if temp is not None:
        if temp < temp_range[0] or temp > temp_range[1]:
            messages.append(f"⚠️ Temperatura fuera de rango: {temp}°C")
            level = "ALERTA"
        if temp > temp_range[1] * 1.1:
            level = "FALLA"
            messages.append(f"🔴 Temperatura crítica: {temp}°C")
    if hum is not None:
        if hum < hum_range[0] or hum > hum_range[1]:
            messages.append(f"⚠️ Humedad fuera de rango: {hum}%")
            if level == "OK":
                level = "ALERTA"
    if vib_mag is not None:
        if vib_mag > vib_threshold:
            messages.append(f"⚠️ Vibración elevada: {vib_mag:.3f} m/s²")
            if level == "OK":
                level = "ALERTA"
        if vib_mag > vib_threshold * 1.5:
            level = "FALLA"
            messages.append(f"🔴 Vibración crítica: {vib_mag:.3f} m/s²")
    if not messages:
        messages.append("✅ Todos los parámetros dentro de rangos normales.")
    return {"status": level, "messages": messages}
