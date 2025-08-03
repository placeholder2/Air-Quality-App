import requests
import logging
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import folium_static


# ---------------------- DATA FETCHING FUNCTIONS ----------------------

def fetch_all_stations():
    """Fetch and return all air quality monitoring stations in Poland."""
    response = requests.get("https://api.gios.gov.pl/pjp-api/v1/rest/station/findAll/?size=500")
    logging.info(response)
    return response.json().get('Lista stacji pomiarowych', [])


def fetch_sensors_by_station_id(station_id):
    """Get sensors for a given station ID."""
    url = f'https://api.gios.gov.pl/pjp-api/v1/rest/station/sensors/{station_id}'
    response = requests.get(url)
    return response.json()


def fetch_measurements_by_sensor_id(sensor_id):
    """Get measurement data for a given sensor (parameter) ID."""
    url = f'https://api.gios.gov.pl/pjp-api/v1/rest/data/getData/{sensor_id}/?size=500'
    response = requests.get(url)
    return response.json().get('Lista danych pomiarowych', [])


# ---------------------- HELPER FUNCTIONS ----------------------

def get_city_list(stations):
    """Return a sorted list of unique city names from station data."""
    return sorted({station['Nazwa miasta'] for station in stations})


def get_stations_by_city(stations, selected_city):
    """Filter stations by selected city."""
    return [station['Nazwa stacji'] for station in stations if station['Nazwa miasta'] == selected_city]


def get_station_id_by_name(stations, station_name):
    """Get station ID from station name."""
    for station in stations:
        if station['Nazwa stacji'] == station_name:
            return station['Identyfikator stacji']


def extract_station_coordinates(stations, station_id):
    """Get coordinates and name for a station with a given ID."""
    for station in stations:
        if station['Identyfikator stacji'] == station_id:
            return {
                'lat': float(station['WGS84 φ N']),
                'lon': float(station['WGS84 λ E']),
                'name': station['Nazwa stacji']
            }
    return None


def get_sensor_params(sensor_data):
    """Extract readable sensor parameters."""
    return [[sensor['Wskaźnik - kod'], sensor['Wskaźnik']]
            for sensor in sensor_data.get('Lista stanowisk pomiarowych dla podanej stacji', [])]

def get_sensor_id_by_param(sensor_data, selected_param):
    """Find sensor ID by selected parameter code."""
    for sensor in sensor_data.get('Lista stanowisk pomiarowych dla podanej stacji', []):
        if sensor['Wskaźnik - wzór'] == selected_param[0]:
            return sensor['Identyfikator stanowiska']


def display_station_map(stations, selected_station_coords):
    """Render a folium map with all stations and highlight the selected one."""
    m = folium.Map(location=[selected_station_coords['lat'], selected_station_coords['lon']],
                   zoom_start=15, control_scale=True)

    for station in stations:
        lat = float(station['WGS84 φ N'])
        lon = float(station['WGS84 λ E'])
        name = station['Nazwa stacji']
        html_string = name.replace(',', '<br>')
        html_content = f"""
        <div style="text-align:center;"
        background-color:#f9f9f9;
        border:1px solid #ccc;
        font-family: Arial, sans-serif;
        font-size: 35px;
        border-radius:6px;
        padding:10px;>
            <b>{html_string}</b>
        </div>
        """

        popup = folium.Popup(folium.IFrame(html_content, width=250, height=100), max_width=300)


        popup = folium.Popup(folium.IFrame(html_content, width=250, height=100), max_width=300)


        popup = folium.Popup(folium.IFrame(html_content, width=200, height=60), min_width=200, max_width=300,)

        color = 'red' if station['Identyfikator stacji'] == get_station_id_by_name(stations, name) else 'blue'
        folium.Marker(location=[lat, lon], popup=popup, icon=folium.Icon(color=color)).add_to(m)

    return m

st.title('**Jakość powietrza w Polsce**')


# Load station data
stations = fetch_all_stations()

# Step 1: City selection
city_list = get_city_list(stations)
selected_city = st.selectbox('Wybierz miasto', city_list)

# Step 2: Station selection
station_list = get_stations_by_city(stations, selected_city)
selected_station = st.selectbox('Wybierz stację', station_list)

# Step 3: Get station ID and sensor data
station_id = get_station_id_by_name(stations, selected_station)
sensor_data = fetch_sensors_by_station_id(station_id)
sensor_params = get_sensor_params(sensor_data)

# Step 4: Map view
station_coords = extract_station_coordinates(stations, station_id)
folium_static(display_station_map(stations, station_coords), width=700)

# Step 5: Parameter selection
param_labels = [' - '.join(p) for p in sensor_params]
param_map = dict(zip(param_labels, sensor_params))
selected_param_label = st.selectbox("Wybierz parametr", param_labels)
selected_param = param_map[selected_param_label]

# Step 6: Measurement chart
sensor_id = get_sensor_id_by_param(sensor_data, selected_param)
measurements = fetch_measurements_by_sensor_id(sensor_id)

if measurements:
    fig = px.line(measurements, x='Data', y='Wartość', title=selected_param[1])
    st.plotly_chart(fig)
else:
    st.warning("Brak danych pomiarowych dla wybranego parametru.")
    
st.markdown("""
---  
 **Źródło danych:** [Główny Inspektorat Ochrony Środowiska (GIOŚ)](https://api.gios.gov.pl)  
Dane pobierane bezpośrednio z publicznego API GIOŚ.
""")
st.caption("Github: https://github.com/placeholder2")


