"""Fetch 15-day weather forecast from Open-Meteo."""

import requests
import pandas as pd


def fetch_daily_forecast(lat, lon, days=15):
    """Fetch daily max temperature and precipitation sum from Open-Meteo.

    Args:
        lat: latitude
        lon: longitude
        days: forecast days (max 16 for free Open-Meteo API)

    Returns:
        DataFrame with columns: date, tmax, precip
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,precipitation_sum",
        "forecast_days": days,
        "timezone": "Asia/Shanghai",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(
        {
            "date": data["daily"]["time"],
            "tmax": data["daily"]["temperature_2m_max"],
            "precip": data["daily"]["precipitation_sum"],
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    return df
