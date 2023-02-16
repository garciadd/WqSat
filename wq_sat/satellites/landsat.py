from __future__ import division
import os
import re
from functools import reduce
import operator
import json

import numpy as np
from osgeo import gdal, osr

# Subfunctions
from wq_sat.utils import gdal_utils

upscaling_factor = {15: 1,
                    30: 2}

# Bands per resolution (bands should be load always in the same order)
res_to_bands = {15: ['B8'],
                30: ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B9', 'B10', 'B11']}

input_shapes = {str(res): (len(band_list), None, None) for res, band_list in res_to_bands.items()}

band_desc = {'B1': 'B1 [435nm-451nm]',
             'B2': 'B2 [452nm-512nm]',
             'B3': 'B3 [533nm-590nm]',
             'B4': 'B4 [636nm-673nm]',
             'B5': 'B5 [851nm-879nm]',
             'B6': 'B6 [1566nm-1651nm]',
             'B7': 'B7 [2107/home/ubuntu/Dani/wq_satnm-2294nm]',
             'B8': 'B8 [503nm-676nm]',
             'B9': 'B9 [1363nm-1384nm]',
             'B10': 'B10 [1060nm-1119nm]',
             'B11': 'B11 [1150nm-1251nm]'}

# Define pixel values
max_val = 2**16
min_val = 1
fill_val = 0

def load_bands(tile_path, roi_x_y=None, roi_lon_lat=None, max_res=30):
    """
    Parameters
    ----------
    tile_path : str
    roi_x_y : list of ints
    roi_lon_lat : list of floats
    max_res : int
    Returns
    -------
    A dict where the keys are int of the resolutions and values are numpy arrays (H, W, N)
    """

    print('Loading {}'.format(tile_path))

    # Select bands
    resolutions = [res for res in res_to_bands.keys() if res <= max_res]
    selected_bands = []
    for res in resolutions:
        selected_bands.extend(res_to_bands[res])

    # Select ROIs
    if roi_lon_lat:
        roi_lon1, roi_lat1, roi_lon2, roi_lat2 = roi_lon_lat
    if roi_x_y:
        roi_x1, roi_y1, roi_x2, roi_y2 = roi_x_y

#     # Read config
#     r = re.compile("^(.*?)MTL.txt$")
#     matches = list(filter(r.match, os.listdir(tile_path)))
#     if matches:
#         mtl_path = os.path.join(tile_path, matches[0])
#     else:
#         raise ValueError('No MTL config file found.')
    mtl_path = get_mtl_path(tile_path)
    config = read_config_file(mtl_path)
    config = config['L1_METADATA_FILE']

    # Read dataset bands in GDAL
    ds_bands = {res: None for res in resolutions}
    for res in resolutions:
        print("Loading selected data from GDAL: {}m".format(res))
        ds_bands[res] = []
        for band_name in res_to_bands[res]:
            file_path = os.path.join(tile_path, '{}_{}.TIF'.format(config['METADATA_FILE_INFO']['LANDSAT_PRODUCT_ID'], band_name))
            tmp_ds = gdal.Open(file_path)
            ds_bands[res].append(tmp_ds)

    # Find the pixel coordinates
    ds = ds_bands[15][0]

    if roi_lon_lat:  # transform lonlat coordinates to pixels
        roi_x1, roi_y1 = gdal_utils.lonlat_to_xy(roi_lon1, roi_lat1, ds)
        roi_x2, roi_y2 = gdal_utils.lonlat_to_xy(roi_lon2, roi_lat2, ds)

    if roi_x_y or roi_lon_lat:
        tmxmin = max(min(roi_x1, roi_x2, ds.RasterXSize - 1), 0)
        tmxmax = min(max(roi_x1, roi_x2, 0), ds.RasterXSize - 1)
        tmymin = max(min(roi_y1, roi_y2, ds.RasterYSize - 1), 0)
        tmymax = min(max(roi_y1, roi_y2, 0), ds.RasterYSize - 1)

    else:  # if no user input, use all the image
        tmxmin = 0
        tmxmax = ds.RasterXSize - 1
        tmymin = 0
        tmymax = ds.RasterYSize - 1

    # Enlarge to the nearest 30 pixel boundary for the super-resolution
    mult = upscaling_factor[max_res]
    xmin = int(tmxmin / mult) * mult
    xmax = int((tmxmax + 1) / mult) * mult - 1
    ymin = int(tmymin / mult) * mult
    ymax = int((tmymax + 1) / mult) * mult - 1

    print("Selected pixel region: xmin=%d, ymin=%d, xmax=%d, ymax=%d:" % (xmin, ymin, xmax, ymax))
    print("Image size: width=%d x height=%d" % (xmax - xmin + 1, ymax - ymin + 1))

    # Reading dataset bands into an array
    data_bands = {res: None for res in resolutions}
    for res in resolutions:
        print("Loading arrays from: {}m".format(res))
        data_bands[res] = []
        uf = upscaling_factor[res]
        for i, tmp_ds in enumerate(ds_bands[res]):
            tmp_arr = tmp_ds.ReadAsArray(xoff=xmin // uf, yoff=ymin // uf,
                                         xsize=(xmax - xmin + 1) // uf, ysize=(ymax - ymin + 1) // uf,
                                         buf_xsize=(xmax - xmin + 1) // uf, buf_ysize=(ymax - ymin + 1) // uf)
#             tmp_arr = DN_to_reflectance(res_to_bands[res][i], tmp_arr, config)
            data_bands[res].append(tmp_arr)
        data_bands[res] = np.array(data_bands[res])
        data_bands[res] = np.moveaxis(data_bands[res], 0, -1)  # move to channels last
        
    if xmin == 0 and ymin == 0:
        
        geotransform = ds_bands[15][0].GetGeoTransform()
        geoprojection = ds_bands[15][0].GetProjection()

    else:
        
        geo = ds_bands[15][0].GetGeoTransform()
        geotransform = (geo[0] + xmin*geo[1], geo[1], geo[2], geo[3] + ymin*geo[5], geo[4], geo[5])
        geoprojection = ds_bands[15][0].GetProjection()

    # Get coordinates
    coord = {'xmin': xmin,
             'ymin': ymin,
             'width': xmax - xmin + 1,
             'height': ymax - ymin + 1,
             'geotransform': geotransform,
             'geoprojection': geoprojection}

    return data_bands, coord

def get_mtl_path(tile_path):
    
    # Read config
    r = re.compile("^(.*?)MTL.txt$")
    matches = list(filter(r.match, os.listdir(tile_path)))
    if matches:
        mtl_path = os.path.join(tile_path, matches[0])
    else:
        raise ValueError('No MTL config file found.')
        
    return mtl_path

def get_by_path(root, items):
    """
    Access a nested object in root by item sequence.
    ref: https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
    """
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """
    Set a value in a nested object in root by item sequence.
    ref: https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
    """
    get_by_path(root, items[:-1])[items[-1]] = value


def read_config_file(filepath):
    """
    Read a LandSat MTL config file to a Python dict
    """
    config = {}
    f = open(filepath)
    group_path = []
    for line in f:
        line = line.lstrip(' ').rstrip()  # remove leading whitespaces and trainling newlines

        if line.startswith('GROUP'):
            group_name = line.split(' = ')[1]
            group_path.append(group_name)
            set_by_path(root=config, items=group_path, value={})

        elif line.startswith('END_GROUP'):
            del group_path[-1]

        elif line.startswith('END'):
            continue

        else:
            key, value = line.split(' = ')
            try:
                set_by_path(root=config, items=group_path + [key], value=json.loads(value))
            except Exception:
                set_by_path(root=config, items=group_path + [key], value=value)
    f.close()
    return config

def DN_to_reflectance(band, arr, metadata):
    
    name = {'B1': 'BAND_1', 'B2': 'BAND_2', 'B3': 'BAND_3', 'B4': 'BAND_4', 'B5': 'BAND_5', 'B6': 'BAND_6', 
            'B7': 'BAND_7', 'B8': 'BAND_8', 'B9': 'BAND_9', 'B10': 'BAND_10', 'B11': 'BAND_11'}
    
    Ml = float(metadata['RADIOMETRIC_RESCALING']['RADIANCE_MULT_{}'.format(name[band])])
    Al = float(metadata['RADIOMETRIC_RESCALING']['RADIANCE_ADD_{}'.format(name[band])])
    
    L = Ml * arr + Al
    
    if band == 'B10' or band == 'B11':
        
        k1 = float(metadata['TIRS_THERMAL_CONSTANTS']['K1_CONSTANT_{}'.format(name[band])])
        k2 = float(metadata['TIRS_THERMAL_CONSTANTS']['K2_CONSTANT_{}'.format(name[band])])
        
        Tb = k2 / np.log((k1 / L) + 1)
        
        return L
        
    else:
        
        rad_max = float(metadata['MIN_MAX_RADIANCE']['RADIANCE_MAXIMUM_{}'.format(name[band])])
        ref_max = float(metadata['MIN_MAX_REFLECTANCE']['REFLECTANCE_MAXIMUM_{}'.format(name[band])])
        d = float(metadata['IMAGE_ATTRIBUTES']['EARTH_SUN_DISTANCE'])
        z = 90 - float(metadata['IMAGE_ATTRIBUTES']['SUN_ELEVATION'])
        Esun = (np.pi * d**2) * rad_max / ref_max

        sr = (np.pi * d**2 * L) / (Esun * np.cos(z * np.pi / 180.))
        
        return sr