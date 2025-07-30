import requests
import logging
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import folium_static

stations = requests.get("https://api.gios.gov.pl/pjp-api/v1/rest/station/findAll")
logging.info(stations)
cities = stations.json()


def get_city():
    city_list = [element["Identyfikator miasta"]["Nazwa miasta"] for element in data["data"]]
    city_list = sorted(city_list)
    return list(dict.fromkeys(city_list))


def get_stations(city, arg):
    station_list = [(element['Nazwa stacji']) for index, element in enumerate(arg) if element['Identyfikator miasta']['Nazwa miasta'] == city]
    return station_list


def get_id(station, arg):
    for i in range(len(arg)):
        if arg[i]['Nazwa stacji'] == station:
            return arg[i]['id']


def get_sensors(wrt):
    url = 'https://api.gios.gov.pl/pjp-api/v1/rest/metadata/sensors' + str(wrt)
    response = requests.get(url)
    return response.json()


def param_list(sensors):
    return [value['Wskaźnik - kod']['Wskaźnik'] for index, value in enumerate(sensors)]


def get_params(sensors, param):
    for i in range(len(sensors)):
        if sensors[i]['Wskaźnik - kod']['Wskaźnik'] == param:
            return sensors[i]['id']


def get_data(p_id):
    url = 'https://api.gios.gov.pl/pjp-api/v1/rest/data/getData/' + str(p_id)
    data = requests.get(url)
    return data.json()


city = get_city()
st.title(' **Jakość powietrza w Polsce**')
st.write('\n')
selectcity = st.selectbox('Wybierz miasto', city)
selectstation = st.selectbox('Wybierz stację', get_stations(selectcity, cities))
id = get_id(selectstation, cities)
s = get_sensors(id)
param_list = param_list(s)

for i in range(len(cities)):
    if cities[i]['id'] == id:
        lats = cities[i]['WGS84 λ E']
        longs = cities[i]['WGS84 φ N']
        name = cities[i]['Nazwa stacji']


def plot_map(stations):
    f = folium.Figure(width=100, height=50)
    map = folium.Map(location=[lats, longs], control_scale=True, zoom_start=15)

    for station in stations:
        iframe = folium.IFrame(f" {station['stationName']} ")
        popup = folium.Popup(iframe, min_width=300, max_width=300)

        folium.Marker(location=[float(station['gegrLat']), float(station['gegrLon'])],
                      popup=popup,
                      icon=folium.Icon(color='blue', icon='')).add_to(map)

    iframe = folium.IFrame(name)
    popup = folium.Popup(iframe, min_width=300, max_width=300)
    folium.Marker(location=[float(lats), float(longs)],
                  popup=popup,
                  icon=folium.Icon(color='red', icon='')).add_to(map)
    return map


chart = folium_static(plot_map(cities), width=700)

param = st.selectbox('Wybierz parameter', param_list)
data = get_data(get_params(s, param))

fig = px.line(data['values'], x='date', y="value", title=param)
chart1 = st.plotly_chart(fig)
st.caption("Github page: https://github.com/placeholder2")
