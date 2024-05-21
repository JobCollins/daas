import yaml
import os

import streamlit as st
from streamlit_folium import st_folium
import folium


from cds_api_call import load_hist_proj, load_seasonal_forecast
from climate_functions import calculate_season_anomalies_location, extract_climate_data, extract_seasonal_data
from geo_loc import get_lat_lon, get_soil_from_api
# from postgres_query import read_data_db
# from event_prox_functions import filter_events_within_square

from langchain.callbacks.base import BaseCallbackHandler
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import ChatOpenAI, ChatOllama
from langchain.chains import LLMChain


config_path = os.getenv('CONFIG_PATH', 'config.yaml')
# print(config_path)
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

data_dir = config['data_dir']
db_engine_url = config['db_engine_url']
tables = config['table_names']
distance_from_event = config['distance_from_event']
seasons_ke = config['seasons_ke']
system_role = config['system_role']

content_message = "{user_message} \n \
      Location: latitude = {lat}, longitude = {lon} \
      Current soil type: {soil} \
      Current mean monthly temperature for each month: {hist_temp_str} \
      Future monthly temperatures for each month at the location: {future_temp_str}\
      Current precipitation flux (mm/month): {hist_pr_str} \
      Future precipitation flux (mm/month): {future_pr_str} \
      Current seasonal precipitation anomaly: {current_season_pr_anomaly}\
      "

class StreamHandler(BaseCallbackHandler):
    """
    Taken from here: https://discuss.streamlit.io/t/langchain-stream/43782
    """

    def __init__(self, container, initial_text="", display_method="markdown"):
        self.container = container
        self.text = initial_text
        self.display_method = display_method

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        display_function = getattr(self.container, self.display_method, None)
        if display_function is not None:
            display_function(self.text)
        else:
            raise ValueError(f"Invalid display_method: {self.display_method}")


historical, projection = load_hist_proj(data_dir=data_dir)
forecast, hindcast = load_seasonal_forecast(data_dir=data_dir)

st.title(
    ":earth_africa: daas-Climate"
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
    show_add_info = st.toggle("Provide additional information", value=True, help="""If this is activated you will see all the variables
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
            }], zoom=12
        )

        try:
            soil_type = get_soil_from_api(lat, lon)
        except:
            soil_type = "Not known"
        
        # define Kenya 
        sub = (5.5, 33, -5.5, 43) #North, West, South, East

        df, data_dict = extract_climate_data(lat, lon, historical, projection)
        seasonal_anomalies = calculate_season_anomalies_location(forecast, hindcast, sub)
        current_season_anomaly = extract_seasonal_data(lat, lon, seasonal_anomalies, seasons_ke)


    with st.spinner("Generating..."):
        chat_box = st.empty()
        stream_handler = StreamHandler(chat_box, display_method="write")
        llm = ChatOllama(
            model_name="llama3"
        )
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_role)
        human_message_prompt = HumanMessagePromptTemplate.from_template(content_message)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        chain = LLMChain(
            llm=llm,
            prompt=chat_prompt,
            verbose=True,
        ) 
        output = chain.run(
            user_message=user_message,
            lat=str(lat),
            lon=str(lon),
            soil=soil_type,
            hist_temp_str=data_dict["hist_temp"],
            future_temp_str=data_dict["future_temp"],
            hist_pr_str=data_dict["hist_pr"],
            future_pr_str=data_dict["future_pr"],
            current_season_pr_anomaly = current_season_anomaly,
            verbose=True,
        )

        st.subheader("Here is what you need to know", divider='rainbow')
        st.markdown(output)

        # print(output)

    # PLOTTING ADDITIONAL INFORMATION
    if show_add_info: 
        st.subheader("Additional information", divider='rainbow')
        st.markdown(f"**Coordinates:** {round(lat, 4)}, {round(lon, 4)}")
        st.markdown(f"**Soil type:** {soil_type}")
        
        # Climate Data
        st.markdown("**Climate data:**")
        st.markdown(
            "Near surface temperature",
        )
        st.line_chart(
            df,
            x="Month",
            y=["Present Day Temperature", "Future Temperature"],
            color=["#d62728", "#2ca02c"],
        )
        st.markdown(
            "Precipitation",
        )
        st.line_chart(
            df,
            x="Month",
            y=["Present Day Precipitation", "Future Precipitation"],
            color=["#d62728", "#2ca02c"],
        )


    

