import os, sys
import numpy as np
import datetime
import argparse

# API
from wq_sat import config
from wq_sat.download import sentinel

# ACOLITE
sys.path.append(os.path.join(config.base_dir(), 'acolite'))
import acolite as ac

def main():

    parser = argparse.ArgumentParser(description='Satellite Water Quality')

    # '--download' o '-d' file with details to download images
    parser.add_argument('--download', '-d', type=str, help='Download file path to process')
    # '--atcor' o '-at' file with details to apply atmospheric corrections
    parser.add_argument('--atcor', '-at', type=str, help='Atmospheric correction file path to process')
    # Parse command line arguments
    args = parser.parse_args()

    try:
        if args.download:
            print(f'Processing the file: {args.download}')
            download_args = process_download_file(args.download)
            print(download_args)

            #download sentinel files
            s2 = sentinel.download(**download_args)
            downloaded, pending = s2.download()
            print(f'downloaded images: {downloaded} \n')
            
        if args.atcor:
            print(f'Processing the file: {args.atcor}')
            if args.download:
                acolite_args = process_acolite_file(args.atcor, downloaded)
            else:
                acolite_args = process_acolite_file(args.atcor)
            #ac.acolite.acolite_run(settings=acolite_args)
            
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

def process_download_file(download):

    args = {'start_date': "",
            'end_date': "",
            'coordinates': "",
            'platform': "",
            'product_type': "",
            'cloud': ""}

    try:
        with open(download, 'r') as file:
            for line in file:
                words = line.split(' ')
                if words[0].startswith("#"):
                    continue
                elif not words[0] in list(args.keys()):
                    raise ValueError(f"{words[0]} is not a valid download setting")
                else:
                    if words[0] in ['start_date', 'end_date']:
                        try:
                            args[words[0]] = datetime.datetime.strptime(words[-1].strip(), "%Y-%m-%d")
                        except ValueError as e:
                            raise ValueError(f'The date {words[-1]} is not in the correct format. Please, use "Y-m-d"')
                    elif words[0] == 'coordinates':
                        W, N, E, S = process_coordinates(words[-1])
                        args[words[0]] = {"W": np.round(W,4), "N": np.round(N,4), "E": np.round(E,4), "S": np.round(S,4)}
                    elif words[0] == 'cloud':
                        args[words[0]] = np.uint(words[-1])
                    else:
                        args[words[0]] = words[-1].strip()
                        
    except FileNotFoundError as e:
        # Exception if file not found
        raise FileNotFoundError(f'The file {download} was not found...')

    if args['end_date'] <= args['start_date']:
        raise ValueError("The end date must be after the start date")
    if not args['platform'] in ['SENTINEL-2', 'SENTINEL-3']:
        raise ValueError(f"{args['platform']} is not valid platform. Please use SENTINEL-2 or SENTINEL-3")
    elif args['platform'] == 'SENTINEL-2':
        if not args['product_type'] in ['S2MSI1C', 'S2MSI2A']:
            raise ValueError(f"{args['product_type']} is not valid product type for Sentinel-2")
    elif args['platform'] == 'SENTINEL-3':
        if not args['product_type'] in ['OL_1_EFR___', 'OL_1_ERR___']:
            raise ValueError(f"{args['product_type']} is not valid product type for Sentinel-3")

    return args

def process_acolite_file(atcor, downloaded=None):
    args = acolite_settings()
    acolite_args = {}
    try:
        with open(atcor, 'r') as file:
            for line in file:
                words = line.split(' ')
                if words[0].startswith("#"):
                    continue
                elif not words[0] in args:
                    print(f"{words[0]} is not a valid ACOLITE setting. It will not be taken into account for preprocessing.")
                else:
                    acolite_args[words[0]] = words[-1].strip()
    except FileNotFoundError as e:
        # Exception if file not found
        raise FileNotFoundError(f'The file {atcor} was not found...')

    if downloaded:
        input_path = []
        output_path = []
        for tile in downloaded:
            scene = tile.split('.')[0]
            input_path.append(config.tile_path(scene))
            output_path.append(config.acolite_path(scene))
        print(input_path)
        print(output_path)
        acolite_args['inputfile'] = input_path
        acolite_args['output'] = output_path
    else:
        print('no downloaded')
        
    return acolite_args

def acolite_settings():
    args = []
    with open(os.path.join(config.base_dir(), 'acolite_settings.txt'), 'r') as file:
        for line in file:
            words = line.split('=')
            if words[0].startswith("#"):
                    continue
            else:
                args.append(words[0])
    return args

def process_coordinates(coord):
    
    coord = coord.split(',')
    W, N, E, S = np.float32(coord[0][1:]), np.float32(coord[1]), np.float32(coord[2]), np.float32(coord[-1][:-2])

    latitude_range = [-90, 90]  # Valid range for latitude
    longitude_range = [-180, 180]  # Valid range for longitude
    
    # test Norte > Sur
    if not N > S:
        raise ValueError("The north coordinate must be greater than the south coordinate")

    # test Oeste < Este
    if not W < E:
        raise ValueError("The west coordinate must be less than the east coordinate")

    # test of range
    if not (latitude_range[0] <= N <= latitude_range[1] and
            latitude_range[0] <= S <= latitude_range[1] and
            longitude_range[0] <= W <= longitude_range[1] and
            longitude_range[0] <= E <= longitude_range[1]):
        raise ValueError("Coordinates are out of valid range")

    return W, N, E, S
            
if __name__ == "__main__":
    main()