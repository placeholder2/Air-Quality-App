import requests
import logging
import streamlit as st
import plotly.express as px

stations = requests.get("http://api.gios.gov.pl/pjp-api/rest/station/findAll")
logging.info(stations)
cities = stations.json()


def get_city(arg):
    city_list = [(element['city']['name']) for index, element in enumerate(cities)]
    city_list = sorted(city_list, key=lambda l: l[0])
    return list(dict.fromkeys(city_list))


def get_stations(city, arg):
    station_list = [(element['stationName']) for index, element in enumerate(arg) if element['city']['name'] == city]
    return station_list


def get_id(station, arg):
    for i in range(len(arg)):
        if arg[i]['stationName'] == station:
            return (arg[i]['id'])


def get_sensors(wrt):
    url = 'https://api.gios.gov.pl/pjp-api/rest/station/sensors/' + str(wrt)
    response = requests.get(url)
    return response.json()


def param_list(sensors):
    return [value['param']['paramName'] for index, value in enumerate(sensors)]


def get_params(sensors, param):
    for i in range(len(sensors)):
        if sensors[i]['param']['paramName'] == param:
            return sensors[i]['id']


def get_data(p_id):
    url = 'https://api.gios.gov.pl/pjp-api/rest/data/getData/' + str(p_id)
    data = requests.get(url)
    return data.json()


city = get_city(cities)
st.title(' **Air Quality in Poland**')
st.write('\n')
selectcity = st.selectbox('Choose city', city)
selectstation = st.selectbox('Choose station', get_stations(selectcity, cities))
id = get_id(selectstation, cities)
s = get_sensors(id)
param_list = param_list(s)

for i in range(len(cities)):
    if cities[i]['id'] == id:
        lats = cities[i]['gegrLat']
        longs = cities[i]['gegrLon']


def plot_map(stations):
    fig = px.scatter_geo(stations,
                         lat='gegrLat',
                         lon='gegrLon',
                         hover_name="stationName",
                         scope='europe',
                         )
    fig.update_layout(
        geo=dict(
            projection_scale=11,
            center=dict(lat=51.9189046, lon=19.1343786), showsubunits=True

        ))
    fig.update_layout(
        geo=dict(
            projection_scale=100,
            center=dict(lat=float(lats), lon=float(longs)),

        ))

    return fig


chart = st.plotly_chart(plot_map(cities), use_container_width=True)

param = st.selectbox('Choose parameter', param_list)
data = get_data(get_params(s, param))

fig = px.line(data['values'], x='date', y="value", title=param)
chart1 = st.plotly_chart(fig)

st.caption(Github page: https://github.com/placeholder2)
