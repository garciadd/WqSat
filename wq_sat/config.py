import os
import numpy as np
from skimage import exposure
import yaml
from werkzeug.exceptions import BadRequest

homedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def base_dir():
    return homedir

def wqsat_path():
    return os.path.join(base_dir(), 'wq_sat')

def data_path():
    return os.path.join(base_dir(), 'data')

def load_credentials():
    cred_path = os.path.join(wqsat_path(), 'credentials.yaml')
    if not os.path.isfile(cred_path):
        raise BadRequest('You must create a credentials.yaml file to store your user/pass')
        
    with open(cred_path, 'r') as f:
        return yaml.safe_load(f)

def tile_path(tile):
    if tile.startswith('S2'):
#        wrs = (tile.split('_'))[5]
        if (tile.split('_'))[1] == 'MSIL1C':
            return os.path.join(data_path(), 'SENTINEL-2', 'S2MSI1C', '{}.SAFE'.format(tile))
        elif (tile.split('_'))[1] == 'MSIL2A':
            return os.path.join(data_path(), 'SENTINEL-2', 'S2MSI2A', '{}.SAFE'.format(tile))

def acolite_path(tile):
    if tile.startswith('S2'):
        return os.path.join(data_path(), 'SENTINEL-2', 'ACOLITE', tile)
            
# def get_regions():
#     if not os.path.isfile(os.path.join(base_dir(), 'regions.yaml')):
#         raise BadRequest('You must create a regions.yaml file to store the coordinates')
    
#     with open(os.path.join(base_dir(), 'regions.yaml'), 'r') as f:
#         regions = yaml.safe_load(f)
        
#     return regions 

# def load_coordinates(region):
   
#     regions = get_regions()
    
#     if region in regions.keys():
#         return regions[region]
#     else:
#         raise BadRequest('Invalid region name. Please review the Regions.yaml file')