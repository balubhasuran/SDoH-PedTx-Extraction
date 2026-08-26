# SDoH
The SDoH categories are annotated based on this [annotation guideline](https://docs.google.com/document/d/1s9TIPULfy8k63ELmHUbQrI85llH2OCQyy92W8kmOqPQ/edit?usp=sharing).
This repository provides the code for further process after curating the annotation data. We use the INCEpTION tool to annotate and export the whole project as json file. We stored the zipped JSON file inside /data/annotation_data_zip

To run the code, 
1. Clone this repo to your local disk
   ```bash
   git clone https://github.com/drizzle98/SDoH/tree/main
   ```
2. Install a conda environment and use that environment, and install the requirement at SDoH/ner_code/requirements.txt. Be sure to install the compatible [pytorch](https://pytorch.org/).
   ```bash
   cd SDoH
   conda create -n SDoH python=3.11
   conda activate SDoH
   pip install -r /ner_code/requirements.txt
   ```

3. Run the .sh script to process the data
   ```bash
   ./copy_and_process_data.sh
   ```


   
      
