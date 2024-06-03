import json
import yaml
import os

import streamlit as st
from streamlit_folium import st_folium
import folium

from cds_api_call import load_hist_proj, load_seasonal_forecast
from climate_functions import calculate_season_anomalies_location, extract_cordex_climate_data, extract_seasonal_data
from geo_loc import get_lat_lon, get_soil_from_api

from langchain.callbacks.base import BaseCallbackHandler
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_community.chat_models.ollama import ChatOllama
from langchain_openai import ChatOpenAI
from ollama_functions import OllamaFunctions
from langchain.chains import LLMChain
from langchain_core.pydantic_v1 import BaseModel

config_path = os.getenv('CONFIG_PATH', 'config.yaml')

print(config_path)
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

class AnswerWithJustification(BaseModel):
    '''An answer to the user question along with justification for the answer.'''
    answer: str
    justification: str

placeholder = st.empty()


splash_css = """
<style>
#splash-screen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: #000000;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-size: 1.5em;
    z-index: 1000;
    flex-direction: column;
    text-align: center;
}



@keyframes fade {
    0%, 20%, 100% { opacity: 0; }
    10%, 90% { opacity: 1; }
}

#spinner {
    width: 150px;
    height: 150px;
    background-color: #4CAF50;
    border-radius: 50%;
    position: relative;
    box-shadow: 0 0 30px 4px rgba(0, 0, 0, 0.5) inset,
      0 5px 12px rgba(0, 0, 0, 0.15);
    overflow: hidden;
  }
  #spinner:before,
  #spinner:after {
    content: "";
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 45%;
    top: -40%;
    background-color: #fff;
    animation: wave 5s linear infinite;
  }
  #spinner:before {
    border-radius: 30%;
    background: rgba(255, 255, 255, 0.4);
    animation: wave 5s linear infinite;
  }
  @keyframes wave {
    0% {
      transform: rotate(0);
    }
    100% {
      transform: rotate(360deg);
    }
  }

.message {
    opacity: 0;
    animation: fade 9s infinite;
}

.message:nth-child(1) { animation-delay: 0s; }
.message:nth-child(2) { animation-delay: 3s; }
.message:nth-child(3) { animation-delay: 6s; }
</style>
"""

# Custom HTML for the splash screen
splash_html = """
<div id="splash-screen">
    <div id="spinner"></div>
    <div class="message">Downscaling climate data for a custom response</div>
    <div class="message">Your on demand agricultural extension service AI</div>
    <div class="message">Thank you for your patience</div>
</div>
"""

# Injecting CSS and HTML into the placeholder
placeholder.markdown(splash_css + splash_html, unsafe_allow_html=True)

historical, projection = load_hist_proj()
forecast, hindcast = load_seasonal_forecast()

placeholder.empty()

forecast, hindcast = load_seasonal_forecast(data_dir=data_dir)


# Custom CSS for styling and mobile responsiveness
custom_css = """
<style>
[data-testid="stAppViewContainer"]{
background-color: #000000;
opacity: 0.8;
background-image:  radial-gradient(#4caf50 0.5px, transparent 0.5px), radial-gradient(#4caf50 0.5px, #000000 0.5px);
background-size: 20px 20px;
background-position: 0 0,10px 10px;
}
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
body {
    font-family: 'Roboto', sans-serif;
    background-color: #f9f9f9;
    color: #333333;
}

h1, h2, h3, h4, h5, h6 {
    color: #4CAF50;
}

p, ul, li{
    color: #ffffff
}

.stButton button, .stFormSubmitButton button {
    background-color: #4CAF50 !important;
    color: white !important;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s ease;
}

.stButton button:hover, .stFormSubmitButton button:hover {
    background-color: #45A049 !important;
}

.stButton button:active, .stFormSubmitButton button:active {
    background-color: #3E8E41 !important;
}

.stButton button:focus, .stFormSubmitButton button:focus {
    outline: none !important;
}

.stTextInput input {
    border-bottom: 1px solid #4CAF50 !important;
    border-radius: 5px;
    padding: 10px;
    font-size: 16px;
}

.stTextInput input:focus {
    border-color: #45A049 !important;
    outline: none;
    box-shadow: 0 0 5px rgba(71, 179, 76, 0.5);
}

.stMarkdown {
    max-width: 100%;
    word-wrap: break-word;
    font-size: 16px;
}

.stSpinner > div {
    border-top-color: #4CAF50 !important;
}

@media (max-width: 768px) {
    .stForm {
        width: 100% !important;
        padding: 10px !important;
    }

    .stTextInput, .stNumberInput {
        width: 100% !important;
    }

    .stButton, .stFormSubmitButton {
        width: 100% !important;
        text-align: center;
    }

    .stMarkdown {
        font-size: 14px;
    }
}

.container {
    padding: 0 20px;
}
</style>
"""

# Embed CSS in Streamlit
st.markdown(custom_css, unsafe_allow_html=True)


# Title and Description
st.markdown("""
    <div style="text-align: center;">
        <h1>daas-agrex</h1>
    </div>
    <div style="text-align: center; margin-bottom: 20px;">
        <p>AI agricultural extension consultant for your farming activity at a location of your choice.</p>
    </div>
""", unsafe_allow_html=True)

# Carousel

with st.form(key='my_form', border=False):
    user_message = st.text_input(
        "Describe the venture that you would like to consult for: "
    )
    location = st.text_input(
        "Please enter your location of interest: "
    )

    submit_button = st.form_submit_button(label='Consult')

if submit_button and user_message and location:
    lat, lon = get_lat_lon(location)

    # col1, col2 = st.columns(2)
    # lat = col1.number_input("Latitude", value=lat, format="%.4f")
    # lon = col2.number_input("Longitude", value=lon, format="%.4f")
    show_add_info = st.checkbox("Provide additional information", value=True, help="""If this is activated you will see all the variables
                            that were taken into account for the analysis as well as some plots.""")

    with st.spinner("Analyzing location information...."):
        st.markdown(f"**Coordinates:** {round(lat, 4)}, {round(lon, 4)}")

        # Define map 
        st.map(
            [{
                'latitude': lat,
                'longitude': lon
            }], color='#4CAF50', zoom=12
        )

        try:
            soil_type = get_soil_from_api(lat, lon)
        except:
            soil_type = "Not known"

        # define Kenya 
        sub = (5.5, 33, -5.5, 43) #North, West, South, East

        df_temp, df_pr, data_dict = extract_cordex_climate_data(lat, lon, historical, projection)
        seasonal_anomalies = calculate_season_anomalies_location(forecast, hindcast, sub)
        current_season_anomaly = extract_seasonal_data(lat, lon, seasonal_anomalies, seasons_ke)

    with st.spinner("Generating..."):
        chat_box = st.empty()
        stream_handler = StreamHandler(chat_box, display_method="write")
        # llm = ChatOpenAI(
        #     model="gpt-4o",
        #     temperature=0 
        # )
        llm = ChatOpenAI(
            openai_api_base = "http://localhost:11434/v1",
            api_key= "ollama",
            model="llama3",
            temperature=0
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

        st.subheader("Here is what you need to know")
        st.markdown(output)

    if show_add_info:
        st.subheader("Additional information")
        st.markdown(f"**Coordinates:** {round(lat, 4)}, {round(lon, 4)}")
        st.markdown(f"**Soil type:** {soil_type}")
        # Climate Data
        st.markdown("**Climate data:**")
        st.markdown(
            "Near surface temperature",
        )
        st.line_chart(
            df_temp,
            x="Month",
            y=["Present Day Temperature", "Future Temperature"],
            color=["#4CAF50", "#2E7D32"],
        )
        st.markdown(
            "Precipitation",
        )
        st.line_chart(
            df_pr,
            x="Month",
            y=["Present Day Precipitation", "Future Precipitation"],
            color=["#4CAF50", "#2E7D32"],
        )
