import requests
from requests.structures import CaseInsensitiveDict
from requests.exceptions import Timeout
import os
from dotenv import load_dotenv


def get_lat_lon(location):

    load_dotenv()

    GEOCODE_API_KEY = os.getenv('GEOCODE_API')
    location_query = location

    url = f"https://api.geoapify.com/v1/geocode/search?text={location_query}&apiKey={GEOCODE_API_KEY}"
    print(url)

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    resp = requests.get(url, headers=headers)

    response = resp.json()
    lat = response['features'][0]['properties']['lat']
    lon = response['features'][0]['properties']['lon']

    return lat, lon

def get_soil_from_api(lat, lon):
    """
    Retrieves the soil type at a given latitude and longitude using the ISRIC SoilGrids API.

    Parameters:
    lat (float): The latitude of the location.
    lon (float): The longitude of the location.

    Returns:
    str: The name of the World Reference Base (WRB) soil class at the given location.
    """
    try:
        url = f"https://rest.isric.org/soilgrids/v2.0/classification/query?lon={lon}&lat={lat}&number_classes=5"
        response = requests.get(url, timeout=3)  # Set timeout to 2 seconds
        data = response.json()
        return data["wrb_class_name"]
    except Timeout:
        return "not found"