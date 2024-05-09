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
import cds_api_call

# Libraries for working with multidimensional arrays
import numpy as np
import xarray as xr

# Libraries for plotting and visualising data
import matplotlib.path as mpath
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfeature

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

URL = 'https://cds.climate.copernicus.eu/api/v2'
KEY = os.getenv('CDS_API_KEY')


def call_api(url=URL, key=KEY):
    client = cds_api_call.Client(url=url, key=key)
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
            'variable': '2m_air_temperature',
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
            'variable': '2m_air_temperature',
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

def load_hist_proj(data_dir):
    hist_data = xr.open_mfdataset(f'{data_dir}*CanESM2_historical*.nc')
    proj_data = xr.open_mfdataset(f'{data_dir}*CanESM2_rcp45*.nc')
    return hist_data, proj_data



