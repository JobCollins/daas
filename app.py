import yaml
import os

import streamlit as st
from streamlit_folium import st_folium
import folium


from cds_api_call import load_hist_proj
from climate_functions import extract_climate_data
from geo_loc import get_lat_lon, get_soil_from_api
from postgres_query import read_data_db
from event_prox_functions import filter_events_within_square



config_path = os.getenv('CONFIG_PATH', 'config.yml')
# print(config_path)
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

data_dir = config['data_dir']
db_engine_url = config['db_engine_url']
tables = config['table_names']
distance_from_event = config['distance_from_event']
lat_default = config['lat_default']
lon_default = config['lon_default']

historical, projection = load_hist_proj(data_dir=data_dir)

st.title(
    ":earth_africa: Daas-Climate"
)

# Wrap the input fields and the submit button in a form
with st.form(key='my_form'):
    user_message = st.text_input(
        "Describe the activity that you would like to evaluate for this location: "
    )
    location = st.text_input(
        "Please enter your location of interest: "
    )
    

    # # Include the API key input within the form only if it's not found in the environment
    # if not api_key:
    #     api_key_input = st.text_input(
    #         "OpenAI API key",
    #         placeholder="Enter your OpenAI API key here"
    #     )

    # Replace the st.button with st.form_submit_button
    submit_button = st.form_submit_button(label='Generate')


# lat, lon = get_lat_lon(location)

if submit_button and user_message and location:

    lat, lon = get_lat_lon(location)

    col1, col2 = st.columns(2)

    lat = col1.number_input("Latitude", value=lat, format="%.4f")
    lon = col2.number_input("Longitude", value=lon, format="%.4f")
    show_add_info = st.toggle("Provide additional information", value=False, help="""If this is activated you will see all the variables
                            that were taken into account for the analysis as well as some plots.""")
    
    
    # if map_data:
    #     clicked_coords = map_data["last_clicked"]
    #     if clicked_coords:
    #         lat_default = clicked_coords["lat"]
    #         lon_default = clicked_coords["lng"]
    
    with st.spinner("Loading location information...."):
        
        st.markdown(f"**Coordinates:** {round(lat, 4)}, {round(lon, 4)}")

        # Define map 
        st.map(
            [{
                'latitude': lat,
                'longitude': lon
            }], zoom=9
        )     

    

