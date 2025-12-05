import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

load_dotenv()

APP_TITLE = "Weather Dashboard"
SCHEMA = "weather"
TABLE = "weather_data"


def get_env_variable(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


@st.cache_resource(show_spinner=False)
def get_engine():
    host = get_env_variable("DB_HOST")
    user = get_env_variable("DB_USER")
    password = get_env_variable("DB_PASSWORD")
    db = get_env_variable("DB_DBNAME")
    port = get_env_variable("DB_PORT")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(url, pool_pre_ping=True)
    return engine


@st.cache_data(show_spinner=False)
def list_cities() -> list[str]:
    engine = get_engine()
    q = text(
        f"""
        SELECT DISTINCT city
        FROM {SCHEMA}.{TABLE}
        WHERE city IS NOT NULL
        ORDER BY city
        """
    )
    with engine.connect() as conn:
        cities = [row[0] for row in conn.execute(q).fetchall()]
    return cities


@st.cache_data(show_spinner=False)
def load_data(city: str | None, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    engine = get_engine()
    params = {"start": start_dt, "end": end_dt}
    filters = ["collection_timestamp BETWEEN :start AND :end"]
    if city:
        filters.append("city = :city")
        params["city"] = city

    where_sql = " AND ".join(filters)
    q = text(
        f"""
        SELECT *
        FROM {SCHEMA}.{TABLE}
        WHERE {where_sql}
        ORDER BY collection_timestamp ASC
        """
    )
    
    with engine.connect() as conn:
        result = conn.execute(q, params)
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        # Normalize column names to lowercase for consistent usage
        df.columns = [c.lower() for c in df.columns]
        # Ensure datetime type
        df["collection_timestamp"] = pd.to_datetime(df["collection_timestamp"])
    return df

def c_to_f(value_c: float) -> float:
    return value_c * 9.0 / 5.0 + 32.0

def render_hero(df: pd.DataFrame, latest: pd.Series, use_fahrenheit: bool) -> None:
    temp_c = float(latest.get("temperature_c", float("nan")))
    feels_c = float(latest.get("thermal_sensation_c", float("nan")))
    temp_display = c_to_f(temp_c) if use_fahrenheit else temp_c
    feels_display = c_to_f(feels_c) if use_fahrenheit else feels_c
    unit = "°F" if use_fahrenheit else "°C"

    col_left, col_right = st.columns([2, 5], gap="large")

    with col_left:
        #st.markdown(f"<h1 style='text-align: center; color: black; font-size: 92px;margin-top: 2rem;'>{temp_display:.0f}{unit}</h1>", unsafe_allow_html=True)
        #st.markdown(f"<p style='text-align: center; color: black; font-size: 16px;'>{latest.get('weather_main', '')}</p>", unsafe_allow_html=True)
        icon_url = latest.get("weather_icon", None)
        if isinstance(icon_url, str) and icon_url:     
            st.markdown(f"""
            <style>
                @media (max-width: 768px) {{
                    .weather-card {{
                        padding: 1rem !important;
                        width: 100% !important;
                    }}
                    .city-name {{
                        font-size: 18px !important;
                        margin-left: 1rem !important;
                    }}
                    .country-name {{
                        font-size: 14px !important;
                        margin-left: 1rem !important;
                    }}
                    .temperature {{
                        font-size: 48px !important;
                        margin-left: 1rem !important;
                    }}
                    .weather-icon {{
                        width: 80px !important;
                    }}
                    .weather-description {{
                        font-size: 16px !important;
                    }}
                    .weather-content {{
                        flex-direction: column !important;
                        text-align: center !important;
                    }}
                }}
                @media (min-width: 769px) and (max-width: 1024px) {{
                    .city-name {{
                        font-size: 20px !important;
                    }}
                    .country-name {{
                        font-size: 15px !important;
                    }}
                    .temperature {{
                        font-size: 52px !important;
                    }}
                    .weather-icon {{
                        width: 100px !important;
                    }}
                    .weather-description {{
                        font-size: 20px !important;
                    }}
                }}
            </style>
            <div style='background-color: rgba(28, 131, 225, 0.2); border-radius: 1rem; display: flex;flex-direction: column;' class='weather-card'>
                <h1 style='text-align: left; color: black; font-size: 24px;margin-left: 2rem;' class='city-name'>{latest.get('city', '')}</h1>
                <h2 style='text-align: left; color: grey; font-size: 16px;margin-left: 2rem;margin-top: -2rem;' class='country-name'>{latest.get('sys_country', '')}</h2>
                <div style='display: flex;flex-direction: row;align-items: center;justify-content: space-between;' class='weather-content'> 
                    <h1 style='text-align: center; color: black;font-size: 92px; margin-left: 2rem;' class='temperature'>{temp_display:.0f}{unit}</h1>
                    <div style='display: flex;flex-direction: column;align-items: center;justify-content: center; margin-right: 2rem;'>
                        <img src='{icon_url}' width='120' style='display: block; margin: 0 auto;' class='weather-icon'>
                        <p style='text-align: center; color: grey; font-size: 24px;' class='weather-description'>{latest.get('weather_main', '')}</p>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    with col_right:
        sub = st.container(border=True)
        with sub:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Humidity", f"{latest.get('humidity', 'N/A')}%")
            c2.metric("Wind", f"{latest.get('wind_speed', 'N/A')} km/h")
            c3.metric("Pressure", f"{latest.get('pressure', 'N/A')} hPa")
            c4.metric("Feels like", f"{feels_display:.0f}{unit}")
        with sub:
            # Hourly Weather Forecast Chart
            if not df.empty:
                # Resample data to hourly averages
                hourly_data = df.set_index("collection_timestamp").resample("1H").agg({
                    "humidity": "mean",
                    "temperature_c": "mean",
                    "weather_main": "first",
                    "weather_icon": "first"
                }).dropna().reset_index()
                
                if not hourly_data.empty:
                    # Limit to next 8 hours for better visibility
                    hourly_data = hourly_data.head(8)
                    
                    # Convert temperature if needed
                    temp_data = hourly_data["temperature_c"].apply(c_to_f) if use_fahrenheit else hourly_data["temperature_c"]
                    temp_unit = "°F" if use_fahrenheit else "°C"
                    
                    # Create the chart
                    fig = go.Figure()
                    
                    # Add area chart for precipitation/humidity
                    fig.add_trace(go.Scatter(
                        x=hourly_data["collection_timestamp"],
                        y=hourly_data["humidity"],
                        mode='lines',
                        fill='tonexty',
                        fillcolor='rgba(74, 144, 226, 0.3)',
                        line=dict(color='rgba(74, 144, 226, 0.8)', width=2),
                        name='Rain precipitation %',
                        showlegend=False
                    ))
                    
                    # Add temperature points and labels
                    for i, row in hourly_data.iterrows():
                        temp_val = temp_data.iloc[hourly_data.index.get_loc(i)]
                        time_str = row["collection_timestamp"].strftime("%H:%M")
                        
                        # Add temperature text above the chart
                        fig.add_annotation(
                            x=row["collection_timestamp"],
                            y=100,  # Position above the humidity area
                            text=f"{temp_val:.0f}°",
                            showarrow=False,
                            font=dict(size=14, color="black"),
                            yshift=20
                        )
                        
                        # Add time labels at the bottom
                        fig.add_annotation(
                            x=row["collection_timestamp"],
                            y=0,
                            text=time_str,
                            showarrow=False,
                            font=dict(size=12, color="gray"),
                            yshift=-20
                        )
                    
                    # Update layout to match the reference design
                    fig.update_layout(
                        title="Upcoming hours",
                        title_font=dict(size=16, color="black"),
                        xaxis=dict(
                            showgrid=False,
                            showticklabels=False,
                            zeroline=False,
                            range=[hourly_data["collection_timestamp"].min(), hourly_data["collection_timestamp"].max()]
                        ),
                        yaxis=dict(
                            showgrid=False,
                            showticklabels=False,
                            zeroline=False,
                            range=[0, 100]
                        ),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10, r=10, t=60, b=40),
                        height=200
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not enough data to display hourly forecast.")

def render_hourly_chart(df: pd.DataFrame, use_fahrenheit: bool) -> None:
    if df.empty:
        st.info("No data available for the selected range.")
        return
    hourly = (
        df.set_index("collection_timestamp")["temperature_c"]
        .resample("1H")
        .mean()
        .dropna()
        .reset_index()
    )
    if hourly.empty:
        st.info("Not enough data to draw an hourly chart.")
        return

    if use_fahrenheit:
        hourly["temperature"] = hourly["temperature_c"].apply(c_to_f)
        y_title = "Temperature (°F)"
    else:
        hourly["temperature"] = hourly["temperature_c"]
        y_title = "Temperature (°C)"

    fig = px.area(
        hourly,
        x="collection_timestamp",
        y="temperature",
        title="Upcoming hours",
    )
    fig.update_traces(line_color="#4A90E2")
    fig.update_layout(yaxis_title=y_title, xaxis_title="Time", margin=dict(l=10, r=10, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

def render_extra_timeseries(df: pd.DataFrame) -> None:
    if df.empty:
        return
    cols = st.columns(3)
    series_map = [
        ("Humidity (%)", "humidity"),
        ("Pressure (hPa)", "pressure"),
        ("Wind speed (km/h)", "wind_speed"),
    ]
    for col, (title, key) in zip(cols, series_map):
        with col:
            s = (
                df.set_index("collection_timestamp")[key]
                .resample("1H")
                .mean()
                .dropna()
                .reset_index()
            )
            if s.empty:
                st.info(f"No {key} data")
                continue
            fig = px.line(s, x="collection_timestamp", y=key, title=title)
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

def render_detail_cards(latest: pd.Series, use_fahrenheit: bool) -> None:
    cols = st.columns(6)
    values = {
        "Humidity": f"{latest.get('humidity', 'N/A')}%",
        "Wind": f"{latest.get('wind_speed', 'N/A')} km/h",
        "Pressure": f"{latest.get('pressure', 'N/A')} hPa",
        "Feels like": f"{c_to_f(float(latest.get('thermal_sensation_c', 0))) if use_fahrenheit else float(latest.get('thermal_sensation_c', 0)):.0f}{'°F' if use_fahrenheit else '°C'}",
        "Temp min": f"{c_to_f(float(latest.get('temp_min_c', 0))) if use_fahrenheit else float(latest.get('temp_min_c', 0)):.0f}{'°F' if use_fahrenheit else '°C'}",
        "Temp max": f"{c_to_f(float(latest.get('temp_max_c', 0))) if use_fahrenheit else float(latest.get('temp_max_c', 0)):.0f}{'°F' if use_fahrenheit else '°C'}",
    }
    for col, (label, value) in zip(cols, values.items()):
        with col:
            st.metric(label, value)

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.markdown('<style> #MainMenu {visibility:hidden;} footer {visibility: hidden;} .stAppHeader {visibility: hidden;}</style>', unsafe_allow_html=True)
    
    st.title(APP_TITLE)

    # --- Auto refresh every 2 minutes: clear cache then rerun ---
    now = datetime.now()
    last_refresh = st.session_state.get("_last_auto_refresh_at")
    if last_refresh is None:
        st.session_state["_last_auto_refresh_at"] = now
    else:
        if (now - last_refresh).total_seconds() >= 120:
            st.cache_data.clear()
            st.session_state["_last_auto_refresh_at"] = now
            st.rerun()

    # ---------- Top toolbar (no sidebar) ----------
    cities = list_cities()
    default_city = cities[0] if cities else None
    today = datetime.now().date()
    default_start = datetime.combine(today - timedelta(days=1), datetime.min.time())
    default_end = datetime.combine(today, datetime.max.time())

    t1, t2, t3, t4 = st.columns([2, 3, 1, 1])
    with t1:
        city = st.selectbox("City", options=cities, index=0 if default_city in cities else None, placeholder="Select a city")
    with t2:
        date_range = (default_start.date(), default_end.date())
        #date_range = st.date_input("Date range", (default_start.date(), default_end.date()))
    with t4:
        unit_f = st.toggle("°F", value=False, help="Toggle temperature unit")
    

    # Normalize date range
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_dt = datetime.combine(date_range[0], datetime.min.time())
        end_dt = datetime.combine(date_range[1], datetime.max.time())
    else:
        start_dt, end_dt = default_start, default_end

    df = load_data(city, start_dt, end_dt)

    if df.empty:
        st.warning("No weather data found. Ensure the ETL has loaded data into the database.")
        return

    latest_row = df.sort_values("collection_timestamp").iloc[-1]

    # ---------- Hero section ----------
    st.divider()
    render_hero(df, latest_row, unit_f)
    st.divider()
    st.info("Weather forecast is provided by the OpenWeatherMap API.", icon=":material/water_drop:")

if __name__ == "__main__":
    main()