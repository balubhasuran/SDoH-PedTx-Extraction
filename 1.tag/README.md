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
   pip install -r ./ner_code/requirements.txt
   ```

3. Run the .sh script to process and split the data
   ```bash
   ./copy_and_process_data.sh
   ./split.sh
   ```

4. Train the model (feel free to test on other models and modify the configurations in the .sh file.)
   ```bash
   ./train_bert.sh
   ./train_robertal.sh
   ```

5. Evaluation
   under developing ...
   Plans:
   1. Strict match criterion (Overall F-1, precision, recall, and individual F-1, precision, recall for each SDoH)
   2. Relax match criterion, which allows overlapping (Overall F-1, precision, recall, and individual F-1, precision, recall for each SDoH)
   3. Sentence level match (Overall F-1, precision, recall, and individual F-1, precision, recall for each SDoH)
        For example: She lives in a house and owns a car. If the model labels "house" as living, "own" as a transportation, the previous two criterion will count them as                incorrect. But since both living and transportation are mentioned in the prediction, we count this as a correct case.
      
6. Potential next step
   Since the NER task is a supporting step so that we can know which sentences contain information about SDoH, so we only require a high sentence level match score. In this        way, I think it is possible to use LLMs to do this task as well. We can try a combination of encoder and decoder, as well as decoder only.
   
      
