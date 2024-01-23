"""
Given two dates and the coordinates, download N Sentinel Collections scenes from ESA Sentinel dataHUB.
The downloaded Sentinel collection scenes are compatible with:

Sentinel-2:
    - S2MSI1C: Top-of-atmosphere reflectances in cartographic geometry
    - S2MSI2A: Bottom-of-atmosphere reflectance in cartographic geometry
    
Sentinel-3:
    - OL_1_EFR___: Full Resolution TOA Reflectance
    - OL_1_ERR___: Reduced Resolution TOA Reflectance
----------------------------------------------------------------------------------------------------------

Author: Daniel García Díaz
Email: garciad@ifca.unican.es
Spanish National Research Council (CSIC); Institute of Physics of Cantabria (IFCA)
Advanced Computing and e-Science
Date: Apr 2023
"""

#imports apis
import datetime
import requests
import os
import pandas as pd
from tqdm import tqdm

# Subfunctions
from wq_sat import config
from wq_sat.utils import sat_utils


class download:

    def __init__(self, start_date, end_date, coordinates, platform, product_type, cloud=100):
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
        Registration and login credentials are required to access all system features and download data.
        To register, please create a username and password.
        Once registered, the username and password must be added to the credentials.yaml file.
        Example: sentinel: {password: password, user: username}
        """
        
        # Open the request session
        self.session = requests.Session()
        
        #Search parameters
        self.start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        self.end_date = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        self.platform = platform.upper() #All caps
        self.producttype = product_type
        self.cloud = int(cloud)
        self.coord = coordinates

        #work path
        self.output_path = os.path.join(config.data_path(), self.platform, self.producttype)        
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)
        
        #ESA APIs
        self.api_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?'
        self.credentials = config.load_credentials()['sentinel']
        
        
    def get_keycloak(self):
        data = {
            "client_id": "cdse-public",
            "username": self.credentials['user'],
            "password": self.credentials['password'],
            "grant_type": "password",
            }
        try:
            r = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
            )
            r.raise_for_status()
        except Exception as e:
            raise Exception(
                f"Keycloak token creation failed. Reponse from the server was: {r.json()}"
                )
        return r.json()["access_token"]
    
    
    def search(self, omit_corners=True):

        # Post the query to Copernicus
        footprint = 'POLYGON(({0} {1},{2} {1},{2} {3},{0} {3},{0} {1}))'.format(self.coord['W'],
                                                                                self.coord['S'],
                                                                                self.coord['E'],
                                                                                self.coord['N'])
        if self.platform == 'SENTINEL-2':
            url_query = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.platform}' and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and ContentDate/Start gt {self.start_date} and ContentDate/Start lt {self.end_date} and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {self.cloud}) and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{self.producttype}')"
        elif self.platform == 'SENTINEL-3':
            url_query = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.platform}' and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and ContentDate/Start gt {self.start_date} and ContentDate/Start lt {self.end_date} and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{self.producttype}')"
        response = self.session.get(url_query)

        response.raise_for_status()

        # Parse the response
        json_feed = response.json()

        # # Remove results that are mainly corners
        # def keep(r):
        #     for item in r['str']:
        #         if item['name'] == 'size':
        #             units = item['content'].split(' ')[1]
        #             mult = {'KB': 1, 'MB': 1e3, 'GB': 1e6}[units]
        #             size = float(item['content'].split(' ')[0]) * mult
        #             break
        #     if size > 0.5e6:  # 500MB
        #         return True
        #     else:
        #         return False
        results = pd.DataFrame.from_dict(json_feed['value'])
        print('Retrieving {} results \n'.format(len(results)))

        return results
    
    def download(self):
        
        #results of the search
        results = self.search()
        downloaded, pending= [], []
        keycloak_token = self.get_keycloak()
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {keycloak_token}'})
        print("Authorized OK")
        for index, row in results.iterrows():
            print(f"Product online? {row['Online']}")            
            if row['Online'] and (self.producttype):
                url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products(%s)/$value" % row['Id']
                if self.platform == 'SENTINEL-2':
                    tile_path = os.path.join(self.output_path, row['Name'])
                elif self.platform == 'SENTINEL-3':
                    tile_path = os.path.join(self.output_path, row['Name'])
                if os.path.isdir(tile_path):
                    print ('Already downloaded \n')
                    break
                print(f"Downloading {url}")
                response = session.head(url, allow_redirects=False)
                print("After head")
                if response.status_code in (301, 302, 303, 307):
                    url = response.headers['Location']
                    print(url)
                    #response = session.get(url, allow_redirects=False)
                response = session.get(url, stream=True)

                print(f"Status code {response.status_code}")
                if response.status_code == 200:

                    total_size = int(response.headers.get('content-length', 0))
                    chunk_size = 1024  # Define the chunk size

                    # Initialize an empty byte array to hold the data
                    data = bytearray()

                    with tqdm(
                        desc="Downloading",
                        total=total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            # Update the byte array with the chunk
                            data.extend(chunk)
                            # Update the progress bar
                            bar.update(len(chunk))


                    downloaded.append(row['Name'])

                    print('Downloading {} ... \n'.format(row['Name']))
                    print(f"Saving in... {tile_path}")

                    sat_utils.open_compressed(byte_stream=data,
                                              file_format='zip',
                                              output_folder=self.output_path)
            
                else:
                    pending.append(row['Name'])
                    print ('The product is offline')
                    print ('Activating recovery mode ...')
                
            else:
                pending.append(row['Name'])
                print ('The product {} is offline'.format(row['Name']))
                print ('Activating recovery mode ... \n')
                
        return downloaded, pending