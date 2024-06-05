from calendar import monthrange
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import streamlit as st

from geo_loc import ds_latlon_subset

def convert_to_mm_per_month(data):
    data_climatology = data.groupby('time.month').mean()
    numdays = [31,28,31,30,31,30,31,31,30,31,30,31]
    data_climatology = data_climatology.assign_coords(numdays=('month',numdays))
    # see https://www.researchgate.net/post/How-do-I-convert-ERA-Interim-precipitation-estimates-from-kg-m2-s-to-mm-day#:~:text=kg%2Fm2%2Fs%20is%20equivalent,of%20days%20in%20a%20month.
    data_climatology_mm_month = data_climatology * data_climatology.numdays *24 *60 * 60
    return data_climatology_mm_month

@st.cache_data
def extract_cordex_climate_data(lat, lon, _hist, _future):
    """
    Extracts climate data for a given latitude and longitude from historical and future datasets.

    Args:
    - lat (float): Latitude of the location to extract data for.
    - lon (float): Longitude of the location to extract data for.
    - hist (xarray.Dataset): Historical climate dataset.
    - future (xarray.Dataset): Future climate dataset.

    Returns:
    - df (pandas.DataFrame): DataFrame containing present day and future temperature, precipitation, and wind speed data for each month of the year.
    - data_dict (dict): Dictionary containing string representations of the extracted climate data.
    """
    hist_temp = _hist['tas']
    hist_temp = hist_temp.groupby('time.month').mean()
    hist_temp = hist_temp.sel(rlat=lat, rlon=lon, method="nearest") - 273.15
    hist_temp_str = np.array2string(hist_temp.ravel(), precision=3, max_line_width=100)[
        1:-1
    ]

    hist_pr = _hist['pr']
    hist_pr = convert_to_mm_per_month(hist_pr)
    hist_pr = hist_pr.sel(rlat=lat, rlon=lon, method="nearest").values

    hist_pr_str = np.array2string(hist_pr.ravel(), precision=3, max_line_width=100)[
        1:-1
    ]

    future_temp = _future['tas']
    future_temp = future_temp.groupby('time.month').mean()
    future_temp = future_temp.sel(rlat=lat, rlon=lon, method="nearest") - 273.15
    future_temp_str = np.array2string(
        future_temp.values.ravel(), precision=3, max_line_width=100
    )[1:-1]

    future_pr = _future['pr']
    future_pr = convert_to_mm_per_month(future_pr)
    future_pr = future_pr.sel(rlat=lat, rlon=lon, method="nearest").values
    future_pr_str = np.array2string(future_pr.ravel(), precision=3, max_line_width=100)[
        1:-1
    ]

    print("hist_temp: ", len(hist_temp))
    print("hist_temp: ", len(hist_pr))
    print("future pr: ", len(future_temp))
    print("future pr: ", len(future_pr))

    df_temp = pd.DataFrame(
        {
            "Present Day Temperature": hist_temp,
            "Future Temperature": future_temp,
            # "Present Day Precipitation": hist_pr,
            # "Future Precipitation": future_pr,
            "Month": range(1, 13),
        }
    )
    df_pr = pd.DataFrame(
        {
            
            "Present Day Precipitation": hist_pr,
            "Future Precipitation": future_pr,
            "Month": range(1, 13),
        }
    )
    data_dict = {
        "hist_temp": hist_temp_str,
        "hist_pr": hist_pr_str,
        "future_temp": future_temp_str,
        "future_pr": future_pr_str,
    }
    return df_temp, df_pr, data_dict

def convert_prate_mm(data):
    # Convert precipitation rate to accumulation in mm
    # Calculate number of days for each forecast month and add it as coordinate information to the data array
    vt = [ pd.to_datetime(data.time.values) + relativedelta(months=fcmonth-1) for fcmonth in data.forecastMonth]
    data = data.assign_coords(valid_time=('forecastMonth',vt))
    # seas5_anomalies_3m_202403_em ['month_year'] = seas5_anomalies_3m_202403_em['valid_time'].dt.strftime('%b, %Y')
    vts = [[thisvt+relativedelta(months=-mm) for mm in range(3)] for thisvt in vt]
    numdays = [np.sum([monthrange(dd.year,dd.month)[1] for dd in d3]) for d3 in vts]
    data = data.assign_coords(numdays=('forecastMonth',numdays))


    # Define names for the 3-month rolling archives, that give an indication over which months the average was built
    vts_names = ['{} {} {} {}'.format(d3[2].strftime('%b'),d3[1].strftime('%b'),d3[0].strftime('%b'), d3[0].strftime('%Y'))  for d3 in vts]
    data = data.assign_coords(valid_time=('forecastMonth',vts_names))
    data

    # Convert the precipitation accumulations based on the number of days
    data_tp = data * data.numdays * 24 * 60 * 60 * 1000

    # Add updated attributes
    data_tp.attrs['units'] = 'mm'
    data_tp.attrs['long_name'] = 'SEAS3 3-monthly total precipitation ensemble mean anomaly for 6 lead-time months, start date in May 2021.'
    return data_tp

def calculate_season_anomalies_location(forecast, hindcast, sub):
    # Compute 3-month rolling averages
    seas5_forecast_3m = forecast.rolling(forecastMonth=3).mean()
    ds_hindcast_3m = hindcast.rolling(forecastMonth=3).mean()

    # Calculate anomalies
    ds_hindcast_3m_hindcast_mean = ds_hindcast_3m.mean(['number','time'])
    seas5_anomalies_3m_202403 = seas5_forecast_3m.tprate - ds_hindcast_3m_hindcast_mean.tprate

    # Ensemble mean anomaly
    seas5_anomalies_3m_202403_em = seas5_anomalies_3m_202403.mean('number')
    seas5_anomalies_3m_202403_em

    seas5_anomalies_3m_202403_em_tp = convert_prate_mm(seas5_anomalies_3m_202403_em)
    # print("seas: ", seas5_anomalies_3m_202403_em_tp)
    
    # define Africa
    # sub = (40, -23, -35, 55) #North, West, South, East
    seas5_location_anomalies_3m_202403_em_tp = ds_latlon_subset(seas5_anomalies_3m_202403_em_tp, sub)

    return seas5_location_anomalies_3m_202403_em_tp

def extract_seasonal_data(lat, lon, seasonal_location_data, location_seasons):
    data = seasonal_location_data.sel(latitude=lat, longitude=lon, method="nearest")
    data = data.to_dataframe("anomaly_mm")

    def extract_season_str(value):
        return value[0:11]
    
    def filter_seasons_location(df, location_seasons):
        df['seasons'] = df.valid_time.apply(extract_season_str)
        filtered_df = df[df.seasons.isin(location_seasons)]
        # print("filter: ",filtered_df.head())
        return filtered_df
    
    data = filter_seasons_location(data, location_seasons)
    # print(data.head())

    def get_current_season_anomaly(df):
        
        today = date.today()
        current_month = calendar.month_abbr[today.month]
        for season in df.seasons:
            if current_month in season:
                anomaly = df.loc[df.seasons==season, 'anomaly_mm'].iloc[0]
        return anomaly

    return get_current_season_anomaly(data) 



