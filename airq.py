import requests
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import folium_static
import pandas as pd

# ---------------------- TRANSLATIONS ----------------------

TEXTS = {
    "pl": {
        "title": "Jakość powietrza w Polsce",
        "select_city": "Wybierz miasto",
        "select_station": "Wybierz stację",
        "select_param": "Wybierz parametr",
        "no_stations": "Brak danych o stacjach.",
        "no_data": "Brak danych pomiarowych dla wybranego parametru.",
        "raw_data": "Surowe dane pomiarowe dla sensora",
        "data_source": """
---
**Źródło danych:** [Główny Inspektorat Ochrony Środowiska (GIOŚ)](https://api.gios.gov.pl)  
Dane pobierane bezpośrednio z publicznego API GIOŚ.
""",
        "github": "GitHub: https://github.com/placeholder2"
    },
    "en": {
        "title": "Air Quality in Poland",
        "select_city": "Select city",
        "select_station": "Select station",
        "select_param": "Select parameter",
        "no_stations": "No station data available.",
        "no_data": "No measurement data for selected parameter.",
        "raw_data": "Raw measurement data for sensor",
        "data_source": """
---
**Data source:** [Chief Inspectorate of Environmental Protection (GIOŚ)](https://api.gios.gov.pl)  
Data fetched directly from public GIOŚ API.
""",
        "github": "GitHub: https://github.com/placeholder2"
    }
}

# ---------------------- DATA FETCHING ----------------------

def fetch_all_stations():
    """Fetch all monitoring stations in Poland (all pages)."""
    all_stations = []
    page = 0
    while True:
        url = f"https://api.gios.gov.pl/pjp-api/v1/rest/station/findAll?page={page}&size=20"
        response = requests.get(url)
        if response.status_code != 200:
            break
        data = response.json()
        stations = data.get('Lista stacji pomiarowych', [])
        if not stations:
            break
        all_stations.extend(stations)
        total_pages = data.get('totalPages', 1)
        page += 1
        if page >= total_pages:
            break
    return all_stations

def fetch_sensors_by_station_id(station_id):
    """Get list of sensors for a given station ID."""
    url = f'https://api.gios.gov.pl/pjp-api/v1/rest/station/sensors/{station_id}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('Lista stanowisk pomiarowych dla podanej stacji', [])
    return []

def fetch_measurements_by_sensor_id(sensor_id):
    """Get measurement data for a given sensor ID (all pages)."""
    all_measurements = []
    page = 0
    while True:
        url = f"https://api.gios.gov.pl/pjp-api/v1/rest/data/getData/{sensor_id}?page={page}&size=20"
        response = requests.get(url)
        if response.status_code != 200:
            st.warning(f"Nie udało się pobrać danych dla sensora {sensor_id}, strona {page}")
            break
        data = response.json()
        measurements = data.get("Lista danych pomiarowych", [])
        if not measurements:
            break
        all_measurements.extend(measurements)
        total_pages = data.get("totalPages", 1)
        page += 1
        if page >= total_pages:
            break
    return all_measurements

# ---------------------- HELPERS ----------------------

def get_city_list(stations):
    return sorted({station['Nazwa miasta'] for station in stations})

def get_stations_by_city(stations, selected_city):
    return [station for station in stations if station['Nazwa miasta'] == selected_city]

def get_station_coords(station):
    return float(station['WGS84 φ N']), float(station['WGS84 λ E'])

def get_sensor_options(sensors_list):
    options = []
    for sensor in sensors_list:
        sensor_id = sensor.get('Identyfikator stanowiska')
        param_name = sensor.get('Wskaźnik')
        if sensor_id and param_name:
            options.append((sensor_id, param_name))
    return options

def display_map(all_stations, selected_station):
    lat, lon = get_station_coords(selected_station)
    m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)
    for station in all_stations:
        s_lat, s_lon = get_station_coords(station)
        name = station['Nazwa stacji']
        color = 'red' if station['Identyfikator stacji'] == selected_station['Identyfikator stacji'] else 'blue'
        folium.Marker(
            location=[s_lat, s_lon],
            popup=name,
            icon=folium.Icon(color=color)
        ).add_to(m)
    return m

# ---------------------- STREAMLIT APP ----------------------

# Wybór języka
language = st.selectbox("Language / Język", ["pl", "en"], index=0)
t = TEXTS[language]

st.title(t["title"])

# 1 Pobranie stacji
stations = fetch_all_stations()
if not stations:
    st.warning(t["no_stations"])
    st.stop()

# 2 Wybór miasta
cities = get_city_list(stations)
selected_city = st.selectbox(t["select_city"], cities)

# 3 Wybór stacji
city_stations = get_stations_by_city(stations, selected_city)
station_names = [s['Nazwa stacji'] for s in city_stations]
selected_station_name = st.selectbox(t["select_station"], station_names)
selected_station = next(s for s in city_stations if s['Nazwa stacji'] == selected_station_name)

# 4 Wyświetlenie mapy
folium_static(display_map(stations, selected_station), width=700)

# 5 Pobranie sensorów i parametrów
sensors = fetch_sensors_by_station_id(selected_station['Identyfikator stacji'])
sensor_options = get_sensor_options(sensors)

if sensor_options:
    sensor_dict = dict(sensor_options)
    selected_param_name = st.selectbox(t["select_param"], [name for _, name in sensor_options])
    selected_sensor_id = next(sid for sid, name in sensor_options if name == selected_param_name)

    # 6 Pobranie danych pomiarowych i wykres
    measurements = fetch_measurements_by_sensor_id(selected_sensor_id)
    if measurements:
        df = pd.DataFrame({
            "date": [m['Data'] for m in measurements],
            "value": [m['Wartość'] for m in measurements]
        })
        df['date'] = pd.to_datetime(df['date'])
        fig = px.line(df, x='date', y='value', title=selected_param_name)
        st.plotly_chart(fig)
    else:
        st.warning(t["no_data"])

# 7 Źródło danych
st.markdown(t["data_source"])
st.caption(t["github"])

