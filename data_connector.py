from influxdb_client import InfluxDBClient
import pandas as pd
import numpy as np
import streamlit as st

INFLUX_URL    = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN  = "EJwrNIOrygCc52EJm-H0NVuHwUapDRTUdEiJ4rCwz3H_cwi_APdfpViMMc9bmzfzcfg9dub8uibJw0fpekAIVQ=="
INFLUX_ORG    = "miguelcmo"
INFLUX_BUCKET = "iot_telemetry_data"


@st.cache_resource
def get_client():
    return InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)


def _clean(df):
    df = df.drop(columns=["result", "table"], errors="ignore")
    if "_time" in df.columns:
        df["_time"] = pd.to_datetime(df["_time"])
        df = df.sort_values("_time").reset_index(drop=True)
    return df


def get_environment_data(range_start="-1h"):
    client = get_client()
    query_api = client.query_api()
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: {range_start})
  |> filter(fn: (r) => r._measurement == "environment")
  |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''
    try:
        df = query_api.query_data_frame(query)
        if isinstance(df, list):
            df = pd.concat(df, ignore_index=True)
        if df.empty:
            return pd.DataFrame(columns=["_time", "temperature", "humidity"])
        return _clean(df)
    except Exception as e:
        st.error(f"Error ambiente: {e}")
        return pd.DataFrame(columns=["_time", "temperature", "humidity"])


def get_vibration_data(range_start="-30m"):
    client = get_client()
    query_api = client.query_api()
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: {range_start})
  |> filter(fn: (r) => r._measurement == "mpu6050")
  |> filter(fn: (r) => r._field == "accel_x" or r._field == "accel_y" or r._field == "accel_z")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''
    try:
        df = query_api.query_data_frame(query)
        if isinstance(df, list):
            df = pd.concat(df, ignore_index=True)
        if df.empty:
            return pd.DataFrame(columns=["_time", "accel_x", "accel_y", "accel_z", "magnitude"])
        df = _clean(df)
        for ax in ["accel_x", "accel_y", "accel_z"]:
            if ax not in df.columns:
                df[ax] = 0.0
        df["magnitude"] = np.sqrt(df["accel_x"]**2 + df["accel_y"]**2 + df["accel_z"]**2)
        return df
    except Exception as e:
        st.error(f"Error vibración: {e}")
        return pd.DataFrame(columns=["_time", "accel_x", "accel_y", "accel_z", "magnitude"])


def get_gyro_data(range_start="-30m"):
    client = get_client()
    query_api = client.query_api()
    query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: {range_start})
  |> filter(fn: (r) => r._measurement == "mpu6050")
  |> filter(fn: (r) => r._field == "gyro_x" or r._field == "gyro_y" or r._field == "gyro_z")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''
    try:
        df = query_api.query_data_frame(query)
        if isinstance(df, list):
            df = pd.concat(df, ignore_index=True)
        if df.empty:
            return pd.DataFrame(columns=["_time", "gyro_x", "gyro_y", "gyro_z"])
        return _clean(df)
    except Exception as e:
        st.error(f"Error giroscopio: {e}")
        return pd.DataFrame(columns=["_time", "gyro_x", "gyro_y", "gyro_z"])


def get_environment_stats(range_start="-1h"):
    df = get_environment_data(range_start)
    stats = {}
    for col in ["temperature", "humidity"]:
        if col in df.columns and not df[col].dropna().empty:
            s = df[col].dropna()
            stats[col] = {
                "current": round(s.iloc[-1], 2),
                "mean": round(s.mean(), 2),
                "max": round(s.max(), 2),
                "min": round(s.min(), 2),
                "std": round(s.std(), 2),
            }
        else:
            stats[col] = {"current": None, "mean": None, "max": None, "min": None, "std": None}
    return stats


def get_vibration_stats(range_start="-30m"):
    df = get_vibration_data(range_start)
    if df.empty or "magnitude" not in df.columns:
        return {"magnitude": {"current": None, "mean": None, "max": None, "min": None, "std": None}}
    mag = df["magnitude"].dropna()
    return {
        "magnitude": {
            "current": round(mag.iloc[-1], 4) if not mag.empty else None,
            "mean": round(mag.mean(), 4),
            "max": round(mag.max(), 4),
            "min": round(mag.min(), 4),
            "std": round(mag.std(), 4),
        }
    }
