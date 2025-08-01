import os
import yaml

from wqsat import utils
from wqsat_get.manager import GetManager
from wqsat_format.manager import FormatManager

class WqSatManager:
    def __init__(self, config: dict = None, config_file: str = None):
        if config:
            self.config = config
        elif config_file:
            self.config = self.from_yaml(config_file)
        else:
            raise ValueError("Either config or config_path must be provided.")

        self.satellite = self.config.get('satellite')
        self.start_date = self.config.get('start_date')
        self.end_date = self.config.get('end_date')
        self.coordinates = self.config.get('coordinates')
        self.product_type = self.config.get('product_type')
        self.cloud = self.config.get('cloud', 100)
        self.dos = self.config.get('DOS', False)
        self.window = self.config.get('window', None)
        self.temporal_composite = self.config.get('temporal_composite', None)
        self.spatial_composite = self.config.get('spatial_composite', False)
        self.output_format = self.config.get('output_format', 'GeoTIFF')
        self.sr_method = self.config.get('sr_method', None)
        self.use_acolite = self.config.get('acolite', False)
        self.bands = self.config.get('bands', [])

        ## Define output path for downloads
        self.output_path = utils.load_data_path()

    def from_yaml(self, yaml_file: str) -> dict:
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)
    
    def workflow(self):

        get_settings = {
            'platform': self.satellite,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'coordinates': self.coordinates,
            'product_type': self.product_type,
            'cloud': self.cloud
        }

        get = GetManager(get_settings)
        downloaded, pending = get.download()
        if downloaded:
            print(f"Downloaded {len(downloaded)} files.")
            if pending:
                print(f"Pending files: {len(pending)}")
                for file in pending:
                    print(f"Pending file: {file}")
            else:
                print("All files downloaded successfully.")
        else:
            print("No files downloaded.")

        tile_path = [os.path.join(self.output_path, tile) for tile in downloaded]
        format_settings = {
            'satellite': self.satellite,
            'tile_path': tile_path,
            'bands': self.bands,
            'coordinates': self.coordinates,
            'use_acolite': self.use_acolite,
            'temporal_composite': self.temporal_composite,
            'spatial_composite': self.spatial_composite,
            'output_format': self.output_format
        }

        format = FormatManager(format_settings)
        format.workflow()
        
        return downloaded, pending