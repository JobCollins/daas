"""
This script makes calls to the CORDEX API

Data: CORDEX regional climate model data on single levels - Experiment: Historical
Temporal coverage: 1 Jan 1971 to 31 Dec 2000
Spatial coverage: Domain: Africa
Format: NetCDF in zip archives

Data: CORDEX regional climate model data on single levels - Experiment: RCP4.5
Temporal coverage: 1 Jan 2071 to 31 Dec 2100
Spatial coverage: Domain: Africa
Format: NetCDF in zip archives

"""

# CDS API
import cdsapi

# Libraries for working with multidimensional arrays
import fsspec
import numpy as np
import xarray as xr

import boto3
import dask
import re
import s3fs
from dask.distributed import Client, progress

# Libraries for plotting and visualising data
import matplotlib.path as mpath
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap

import streamlit as st

# Other libraries (e.g. paths, filenames, zipfile extraction)
from glob import glob
from pathlib import Path
from os.path import basename
import zipfile
import yaml
import urllib3 
urllib3.disable_warnings() # Disable "InsecureRequestWarning" 
                           # for data download via API

import os
from dotenv import load_dotenv

load_dotenv()

# Fetch AWS credentials from environment variables
# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]

URL = 'https://cds.climate.copernicus.eu/api/v2'
KEY = os.getenv('CDS_API_KEY')


def call_api(url=URL, key=KEY):
    client = cdsapi.Client(url=url, key=key)
    return client

def retrieve_cordex_historical(client, data_dir):
    client.retrieve(
        'projections-cordex-domains-single-levels',
        {
            'format': 'zip',
            'domain': 'africa',
            'experiment': 'historical',
            'horizontal_resolution': '0_44_degree_x_0_44_degree',
            'temporal_resolution': 'daily_mean',
            'variable': ['2m_air_temperature', 'mean_precipitation_flux'],
            'gcm_model': 'cccma_canesm2',
            'rcm_model': 'cccma_canrcm4',
            'ensemble_member': 'r1i1p1',
            'start_year': ['1971', '1976', '1981', '1986', '1991', '1996'],
            'end_year': ['1975', '1980', '1985', '1990', '1995', '2000'],
        },
        f'{data_dir}1971-2000_cordex_historical_africa.zip')


def retrieve_cordex_projection(client, data_dir):
    client.retrieve(
        'projections-cordex-domains-single-levels',
        {
            'format': 'zip',
            'domain': 'africa',
            'experiment': 'rcp_4_5',
            'horizontal_resolution': '0_44_degree_x_0_44_degree',
            'temporal_resolution': 'daily_mean',
            'variable': ['2m_air_temperature', 'mean_precipitation_flux'],
            'gcm_model': 'cccma_canesm2',
            'rcm_model': 'cccma_canrcm4',
            'ensemble_member': 'r1i1p1',
            'start_year': ['2071', '2076', '2081', '2086', '2091', '2096'],
            'end_year': ['2075', '2080', '2085', '2090', '2095', '2100'],
        },
        f'{data_dir}2071-2100_cordex_rcp_4_5_africa.zip')

def unzip_files(data_dir):
    cordex_zip_paths = glob(f'{data_dir}*.zip')
    for j in cordex_zip_paths:
        with zipfile.ZipFile(j, 'r') as zip_ref:
            zip_ref.extractall(f'{data_dir}')

@st.cache_data
def load_hist_proj(data_dir):
#     # Initialize a boto3 session
#     session = boto3.Session(
#         aws_access_key_id=aws_access_key_id,
#         aws_secret_access_key=aws_secret_access_key
#     )

#     # Initialize S3 client
#     s3_client = session.client('s3')
#     bucket_name = 'agrexdata'
#     prefix = 'data/'

#     # Initialize a Dask client
#     # client = Client()  # This will start a local Dask cluster. For larger datasets, configure a distributed cluster.
#     # print(client)

#     try:
#         # List objects in the specified S3 bucket and prefix
#         response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
#         if 'Contents' not in response:
#             raise ValueError(f"No files found in the specified S3 path: s3://{bucket_name}/{prefix}")

#         # Filter files with the pattern CanESM2_historical
#         remote_hist_files = [item['Key'] for item in response['Contents']
#                         if re.search(r'CanESM2_historical.*\.nc', item['Key'])]
#         remote_proj_files = [item['Key'] for item in response['Contents']
#                         if re.search(r'CanESM2_rcp45.*\.nc', item['Key'])]

#         if not remote_hist_files:
#             raise ValueError("No files matching the pattern 'CanESM2_historical' found in the S3 bucket.")
        
#         if not remote_proj_files:
#             raise ValueError("No files matching the pattern 'CanESM2_rcp45' found in the S3 bucket.")

#         # Use s3fs to create a file system object
#         s3 = s3fs.S3FileSystem(key=aws_access_key_id, secret=aws_secret_access_key)

#         # Generate a list of opened files
#         hist_fileset = [s3.open(f's3://{bucket_name}/{file}') for file in remote_hist_files]
#         proj_fileset = [s3.open(f's3://{bucket_name}/{file}') for file in remote_proj_files]

#         # Enable dask for parallel processing
#         hist_data = xr.open_mfdataset(hist_fileset, combine='by_coords', parallel=True)
#         proj_data = xr.open_mfdataset(proj_fileset, combine='by_coords', parallel=True)

#         # # Persist data in memory to speed up further operations
#         # hist_data = hist_data.persist()
#         # proj_data = proj_data.persist()
#         # progress(data)

#         print("Datasets loaded successfully")

#     except boto3.exceptions.S3UploadFailedError as e:
#         print(f"Permission error: Check your AWS credentials and permissions for the specified S3 path. {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     # finally:
#     #     client.close()

    hist_data = xr.open_mfdataset(f'{data_dir}*CanESM2_historical*.nc')
    proj_data = xr.open_mfdataset(f'{data_dir}*CanESM2_rcp45*.nc')
    return hist_data, proj_data

def retrieve_seasonal_hist(client, data_dir):
    client.retrieve(
        'seasonal-monthly-single-levels',
        {
            'format': 'grib',
            'originating_centre': 'ecmwf',
            'system': '51',
            'variable': 'total_precipitation',
            'product_type': 'monthly_mean',
            'year': [
                '2002', '2003', '2004',
                '2005', '2006', '2007',
                '2008', '2009', '2010',
                '2011', '2012', '2013',
                '2014', '2015', '2016',
                '2017', '2018', '2019',
                '2020', '2021', '2022',
            ],
            'month': '03',
            'leadtime_month': [
                '1', '2', '3',
                '4', '5', '6',
            ],
        },
        f'{data_dir}seasonal/ecmwf_seas5_2002-2022_05_hindcast_monthly_tp.grib')
    
def retrieve_seasonal_proj(client, data_dir):
    # # Forecast data request
    client.retrieve(
        'seasonal-monthly-single-levels',
        {
            'format': 'grib',
            'originating_centre': 'ecmwf',
            'system': '51',
            'variable': 'total_precipitation',
            'product_type': 'monthly_mean',
            'year': '2024',
            'month': '05',
            'leadtime_month': [
                '1', '2', '3',
                '4', '5', '6',
            ],
        },
        f'{data_dir}seasonal/ecmwf_seas5_2024_03_forecast_monthly_tp.grib')

@st.cache_data
def load_seasonal_forecast(data_dir):

    # try:

    #     fore_aws_url = 'simplecache::s3://agrexdata/data/seasonal/ecmwf_seas5_2024_03_forecast_monthly_tp.grib'
    #     hind_aws_url = 'simplecache::s3://agrexdata/data/seasonal/ecmwf_seas5_2002-2022_05_hindcast_monthly_tp.grib'

    #     fore_file = fsspec.open_local(fore_aws_url, s3={'key': aws_access_key_id, 'secret': aws_secret_access_key}, filecache={'cache_storage':'/tmp/files'})
    #     hind_file = fsspec.open_local(hind_aws_url, s3={'key': aws_access_key_id, 'secret': aws_secret_access_key}, filecache={'cache_storage':'/tmp/files'})

    #     seas5_forecast = xr.open_dataset(fore_file, engine='cfgrib', backend_kwargs=dict(time_dims=('forecastMonth', 'time')))

    #     ds_hindcast = xr.open_dataset(hind_file, engine='cfgrib', backend_kwargs=dict(time_dims=('forecastMonth', 'time')))

    #     print("Datasets loaded successfully")

    # except boto3.exceptions.S3UploadFailedError as e:
    #     print(f"Permission error: Check your AWS credentials and permissions for the specified S3 path. {e}")
    # except Exception as e:
    #     print(f"An error occurred: {e}")

    seas5_forecast = xr.open_dataset(f'{data_dir}/seasonal/ecmwf_seas5_2024_03_forecast_monthly_tp.grib', engine='cfgrib', 
                                 backend_kwargs=dict(time_dims=('forecastMonth', 'time')))
    ds_hindcast = xr.open_dataset(f'{data_dir}/seasonal/ecmwf_seas5_2002-2022_05_hindcast_monthly_tp.grib', engine='cfgrib', backend_kwargs=dict(time_dims=('forecastMonth', 'time')))
    return seas5_forecast, ds_hindcast

if __name__ == "__main__":
    config_path = os.getenv('CONFIG_PATH', 'config.yml')
    # print(config_path)
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    data_dir = config['data_dir']

    client = call_api()
    retrieve_cordex_historical(client, data_dir)
    retrieve_cordex_projection(client, data_dir)
    retrieve_seasonal_hist(client, data_dir)
    retrieve_seasonal_proj(client, data_dir)
    # unzip_files(data_dir)


