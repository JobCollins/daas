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
    

# Define a geographical subset
def ds_latlon_subset(ds,area,latname='latitude',lonname='longitude'):
    """
     generates a geographical subset of an xarray data array. 
     The latitude and longitude values that are outside the defined area are dropped.
    """

    lon1 = area[1] % 360
    lon2 = area[3] % 360
    if lon2 >= lon1:
        masklon = ( (ds[lonname]<=lon2) & (ds[lonname]>=lon1) ) 
    else:
        masklon = ( (ds[lonname]<=lon2) | (ds[lonname]>=lon1) ) 
        
    mask = ((ds[latname]<=area[0]) & (ds[latname]>=area[2])) * masklon
    dsout = ds.where(mask,drop=True)
    
    if lon2 < lon1:
        dsout[lonname] = (dsout[lonname] + 180) % 360 - 180
        dsout = dsout.sortby(dsout[lonname])        
    
    return dsout