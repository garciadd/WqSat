"""
Given two dates and the coordinates, download N Landsat Collections scenes from EarthExplorer.
The downloaded Landsat collection scenes are compatible with LANDSAT_8_C1

landsat_ot_c2_l2
-------------------------------------------------------------------------

Author: Daniel García Díaz
Email: garciad@ifca.unican.es
Institute of Physics of Cantabria (IFCA) (CSIC)
Advanced Computing and e-Science
Date: Sep 2018
"""

#APIs
import os, re
import shutil
import json
import requests

# Subfunctions
from wq_sat import config
from wq_sat.utils import sat_utils

class download:

    def __init__(self, inidate, enddate, coordinates=None, producttype='LANDSAT_8_C1', cloud=100):
        """
        Parameters
        ----------
        inidate : Initial date of the query in format: datetime.strptime "%Y-%m-%dT%H:%M:%SZ"
        enddate : Final date of the query in format: datetime.strptime "%Y-%m-%dT%H:%M:%SZ"
        coordinates : dict. Coordinates that delimit the region to be searched.
            Example: {"W": -2.830, "S": 41.820, "E": -2.690, "N": 41.910}}
        producttype : str
            Dataset type. A list of productypes can be found in https://mapbox.github.io/usgs/reference/catalog/ee.html
        cloud: int
            Cloud cover percentage to narrow your search
        
        Attention please!!
        ------------------
        This service works with the Machine-to-Machine (M2M) API os USGS/EROS.
        The Machine-to-Machine (M2M) API is a RESTful JSON API for accessing USGS/EROS data holdings for its supported data catalogs.
        Registration and login credentials are required to access all system features and download data from USGS EROS web services. 
        To register, please create a username and password.
        Once registered, the username and password must be added to the credentials.yaml file.
        Example: landsat: {password: password, user: username}
        """
        
        self.session = requests.Session()

        # Search parameters
        self.inidate = inidate.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.enddate = enddate.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.producttype = producttype
        self.satellite = 'landsat8'
        self.cloud = int(cloud)
        self.coord = coordinates

        #work path
        self.output_path = os.path.join(config.data_path(), self.satellite)        
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)

        # API
        self.api_url = "https://m2m.cr.usgs.gov/api/api/json/stable/"
        self.credentials = config.load_credentials()['landsat']

        # Fetching the API key
        data = {'username': self.credentials['user'],
                'password': self.credentials['password'],
                'catalogID': 'EE'}
        
        # Login
        response = self.session.post(self.api_url + 'login', json.dumps(data))
        json_feed = response.json()

        if json_feed['errorCode']:
            raise Exception('Failed to login: {}'.format(json_feed['errorMessage']))

        api_key = json_feed['data']
        self.headers = {'X-Auth-Token': api_key}
        
    def search(self):
        """
        Builds the query and get the scenes from the Landsat collection defined in the request 
        """

        # Post the query        
        query = {'datasetName': self.producttype,
                 'maxResults': 500,
                 'sceneFilter':{'spatialFilter': {'filterType': 'mbr',
                                                  'lowerLeft': {'latitude': self.coord['S'],
                                                                'longitude': self.coord['W']},
                                                  'upperRight': {'latitude': self.coord['N'],
                                                                 'longitude': self.coord['E']}
                                                 },
                                'acquisitionFilter': {'start': self.inidate,
                                                      'end': self.enddate},
                                'cloudCoverFilter':{'max': self.cloud,
                                                    'includeUnknown': False},
                               }
                }
        
        print("Searching scenes...\n")
        response = self.session.post(self.api_url + 'scene-search', json.dumps(query), headers = self.headers)
        json_feed = response.json()

        if json_feed['errorCode']:
            raise Exception('Error while searching: {}'.format(json_feed['errorMessage']))
        
        results = json_feed['data']
        print('Found {} results from Landsat ... \n'.format(results['recordsReturned']))
        
        sceneIds = []
        if results['recordsReturned'] > 0:
            sceneIds = []
            for result in results['results']:
                sceneIds.append(result['entityId'])
        
        return sceneIds

    def download(self):
        
        #results of the search
        tilesId = self.search()
        if not isinstance(tilesId, list):
            tilesId = [tilesId]
            
        for sceneIds in tilesId:
        
            data = {'datasetName' : self.producttype, 'entityIds' : sceneIds}
            response = self.session.post(self.api_url + "download-options", json.dumps(data), headers = self.headers)
            results = response.json()['data']

            downloads = []
            for product in results:
                # Make sure the product is available for this scene
                if product['available'] == True:
                    if product['productName'] == 'Level-1 GeoTIFF Data Product':
                        downloads.append({'entityId' : product['entityId'],
                                          'productId' : product['id']})

            if downloads:
                # set a label for the download request
                data = {'downloads' : downloads,
                        'label' : "download-sample"}

                # Call the download to get the direct download urls
                response = self.session.post(self.api_url + "download-request", json.dumps(data), headers = self.headers)
                results = response.json()['data']

            url = results['preparingDownloads'][-1]['url']
            print(url)

            wrs = sceneIds[3:9]
            save_dir = os.path.join(self.output_path, wrs, sceneIds)
            if not os.path.isdir(save_dir):
                os.makedirs(save_dir)
            else:
                print ('Tile {} Already downloaded \n'.format(sceneIds))
                continue
                
            tar_path = os.path.join(self.output_path, '{}.tar'.format(sceneIds))

            print('Downloading {} ...\n'.format(sceneIds))
            response = self.session.get(url, stream=True, allow_redirects=True)
            
            if response.status_code == 200:
                sat_utils.open_compressed(byte_stream=response.raw.read(),
                                          file_format='gz',
                                          output_folder= save_dir,
                                          file_path=tar_path)
                
        return tilesId