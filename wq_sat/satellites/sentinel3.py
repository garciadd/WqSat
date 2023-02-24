import xarray as xr 
import rioxarray as rio
from netCDF4 import Dataset as NetCDFFile 
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap

def generate_geotiffs(folder, coordinates):
    print("Generating GeoTiff data: %s" % folder)
    variable = 'radiance'
    ds = xr.open_dataset(folder + 'Oa01_radiance.nc')
    ds = ds.rename_dims({'rows':'latitude', 'columns':'longitude'})
    for e in range(2,22,1):
        banda = ''
        if len(str(e)) == 1:
            banda = 'Oa0%i_%s' % (e, variable)
        else:
            banda = 'Oa%i_%s' % (e, variable)
        ds_temp = xr.open_dataset(folder + '%s.nc' % banda)
        ds_temp = ds_temp.rename_dims({'rows':'latitude', 'columns':'longitude'})
        ds['Oa0%i_%s' % (e, variable)] = ds_temp[banda]
        print('Loading %s band' % banda)

    print("Addign coordinates")
    olci_geo_coords = xr.open_dataset(folder + 'geo_coordinates.nc')
    olci_geo_coords = olci_geo_coords.rename_dims({'rows':'y', 'columns':'x'})


    # extracting coordinates
    lat = olci_geo_coords.latitude.data
    lon = olci_geo_coords.longitude.data
    
    lon_ds = [i[0] for i in olci_geo_coords['latitude'].data[:]]
    ds = ds.assign_coords({"latitude": lon_ds, "longitude": olci_geo_coords['longitude'].data[0]})
    
    print("Generating complete GEoTIFF")
    ds.rio.to_raster(raster_path=folder + "complete.tif", driver="GTiff")
    
    #Cortar 
    min_lat = coordinates['S']
    min_lon = coordinates['W']
    max_lat = coordinates['N']
    max_lon = coordinates['E']
    print("Generating clip box GEoTIFF")
    ds.rio.write_crs("epsg:4326", inplace=True)
    subset = ds.rio.clip_box(minx=min_lon, miny=min_lat, maxx=max_lon, maxy=max_lat,crs="EPSG:4326")
    subset.rio.to_raster(raster_path=folder + "clip.tif", driver="GTiff")