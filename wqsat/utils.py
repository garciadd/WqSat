import os
import yaml

def base_dir():
    """Returns the base directory where config.yaml is stored."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def config_path():
    """Returns the full path of the config.yaml file."""
    return os.path.join(base_dir(), 'config.yaml')

def regions_path():
    """Returns the full path of the regions.yaml file."""
    return os.path.join(base_dir(), 'regions.yaml')

def load_data_path():
    """
    Loads and returns the data path from the config.yaml file. Creates the directory if it doesn't exist.
    Raises an error if the directory cannot be created.
    """
    try:
        with open(config_path(), 'r') as file:
            data = yaml.safe_load(file)
            data_path = data.get('data_path', None)

            # Ensure the directory exists
            if data_path:
                if not os.path.exists(data_path):
                    try:
                        os.makedirs(data_path)
                        print(f"Directory '{data_path}' created.")
                    except Exception as e:
                        raise OSError(f"Failed to create the directory '{data_path}': {e}")

            return data_path
        
    except FileNotFoundError:
        print("Error: 'config.yaml' file not found.")
        return None
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")