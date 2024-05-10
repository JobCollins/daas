from postgres_query import read_data_db
import numpy as np


def filter_events_within_square(lat, lon, table_name, distance_from_event):
    """
    Filter events within a square of given distance from the center point.

    Args:
    - lat (float): Latitude of the center point (rounded to 3 decimal places)
    - lon (float): Longitude of the center point (rounded to 3 decimal places)
    - haz_dat (pandas.DataFrame): Original dataset.
    - distance_from_event (float): Distance in kilometers to form a square.

    Returns:
    - pandas.DataFrame: Reduced dataset containing only events within the square.
    """

    data = read_data_db(table_name)

    # Calculate the boundaries of the square
    lat_min, lat_max = lat - (distance_from_event / 111), lat + (distance_from_event / 111)
    lon_min, lon_max = lon - (distance_from_event / (111 * np.cos(np.radians(lat)))), lon + (distance_from_event / (111 * np.cos(np.radians(lat))))

    # Filter events within the square
    filtered_data = data[
        (data['latitude'] >= lat_min) & (data['latitude'] <= lat_max) &
        (data['longitude'] >= lon_min) & (data['longitude'] <= lon_max)
    ]

    prompt_haz_data = filtered_data.drop(columns=['country', 'geolocation', 'latitude', 'longitude'])

    return filtered_data, prompt_haz_data