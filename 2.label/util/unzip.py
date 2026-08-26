import zipfile
import glob
import json
import os
from tqdm import tqdm
import argparse


def main():
    def unzip_and_save_json(zip_file_path, output_folder):
        """Unzips a zip file and saves any JSON files to a new folder."""
    
        # Create the output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
    
        # Open the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Iterate over files in the zip
            for file_info in zip_ref.infolist():
                # Check if the file is a JSON file
                if file_info.filename.endswith('.json'):
                    # Extract the file
                    zip_ref.extract(file_info, output_folder)
        name = os.path.basename(zip_file_path).replace('.txt.zip', '')
        os.rename(f'{output_folder}CURATION_USER.json', f'{output_folder}{name}.json')


    parser = argparse.ArgumentParser(description='Unzip the zip files, and extract the json files inside.')
    parser.add_argument('-i','--input_folder', default = '../data/annotation_data_zip/', help='Input data folder, current default: ../data/annotation_data_zip/')
    parser.add_argument('-o','--output_folder', default='../data/annotation_data/',help = 'output data folder, current default: ../data/annotation_data/')
    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    
    
    if not input_folder.endswith('/'):
        input_folder += '/'
    if not output_folder.endswith('/'):
        output_folder += '/'
    
    for i in tqdm(glob.glob(f'{input_folder}*')):
        unzip_and_save_json(i, output_folder)

if __name__ == "__main__":
    main()
    
    