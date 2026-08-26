## Update Log
### Guideline document:
[SDoH guideline](https://docs.google.com/document/d/1s9TIPULfy8k63ELmHUbQrI85llH2OCQyy92W8kmOqPQ/edit?tab=t.0#heading=h.rbme9t4jfh8u)

### 04/03/26
#### Model Performance Evaluation

| Model | Strict Precision | Strict Recall | Strict F1 | Relax Precision | Relax Recall | Relax F1 | Sentence-level Precision | Sentence-level Recall | Sentence-level F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BERT** | 0.528 | 0.267 | 0.353 | 0.758 | 0.385 | 0.509 | 0.834 | 0.399 | 0.538 |
| **BioBERT** | 0.714 | 0.718 | 0.716 | 0.857 | 0.868 | 0.862 | 0.903 | 0.887 | 0.894 |
| **RoBERTa** | 0.777 | 0.775 | 0.775 | 0.884 | 0.893 | 0.888 | 0.914 | 0.909 | 0.911 |
| **BiLSTM-CRF** | 0.232 | 0.062 | 0.097 | 0.534 | 0.133 | 0.209 | 0.582 | 0.147 | 0.231 |
| **Ctran** | 0.467 | 0.438 | 0.452 | 0.648 | 0.615 | 0.630 | 0.719 | 0.664 | 0.689 |
| **GPT-4o** | N/A | N/A | N/A | N/A | N/A | N/A | 0.506 | 0.686 | 0.582 |

#### RoBERTa performance

| Tag | Strict Precision | Strict Recall | Strict F1 | Relax Precision | Relax Recall | Relax F1 | Sentence-level Precision | Sentence-level Recall | Sentence-level F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Adherence** | 0.643 | 0.592 | 0.614 | 0.879 | 0.814 | 0.841 | 0.94 | 0.858 | 0.894 |
| **Concern** | 0.655 | 0.518 | 0.577 | 0.755 | 0.595 | 0.664 | 0.803 | 0.627 | 0.703 |
| **Education** | 0.874 | 0.871 | 0.872 | 0.936 | 0.935 | 0.935 | 0.948 | 0.941 | 0.943 |
| **Employment** | 0.876 | 0.913 | 0.892 | 0.91 | 0.946 | 0.926 | 0.935 | 0.961 | 0.948 |
| **Financial** | 0.783 | 0.841 | 0.81 | 0.884 | 0.947 | 0.914 | 0.916 | 0.948 | 0.931 |
| **Healthcare** | 0.78 | 0.688 | 0.726 | 0.879 | 0.79 | 0.826 | 0.917 | 0.819 | 0.86 |
| **Insurance** | 0.859 | 0.808 | 0.83 | 0.967 | 0.904 | 0.932 | 0.988 | 0.916 | 0.947 |
| **Literacy** | 0.672 | 0.754 | 0.71 | 0.812 | 0.916 | 0.859 | 0.861 | 0.931 | 0.893 |
| **Living** | 0.871 | 0.895 | 0.881 | 0.888 | 0.914 | 0.899 | 0.903 | 0.923 | 0.911 |
| **MentalHealth** | 0.662 | 0.73 | 0.691 | 0.777 | 0.933 | 0.846 | 0.802 | 0.967 | 0.876 |
| **Recommendation** | 0.576 | 0.562 | 0.568 | 0.95 | 0.934 | 0.941 | 0.974 | 0.964 | 0.969 |
| **Smoke** | 0.96 | 0.944 | 0.952 | 1.0 | 0.983 | 0.991 | 1.0 | 0.982 | 0.99 |
| **Social** | 0.801 | 0.796 | 0.798 | 0.891 | 0.886 | 0.888 | 0.911 | 0.897 | 0.903 |
| **SubstanceUse** | 0.814 | 0.83 | 0.82 | 0.926 | 0.967 | 0.944 | 0.975 | 0.979 | 0.977 |
| **Transportation** | 0.795 | 0.838 | 0.815 | 0.89 | 0.949 | 0.917 | 0.906 | 0.958 | 0.93 |
| **Trauma** | 0.874 | 0.903 | 0.886 | 0.926 | 0.985 | 0.953 | 0.946 | 0.989 | 0.965 |
| **Overall** | 0.777 | 0.775 | 0.775 | 0.884 | 0.893 | 0.888 | 0.914 | 0.909 | 0.911 |



### 04/28/25
After tuning parameters and using different transformered-based models, here is the results table:

#### 1. Overall Model Comparison

| Model            | strict_precision | strict_recall | strict_f1 | relax_precision | relax_recall | relax_f1 | sentence-level_precision | sentence-level_recall | sentence-level_f1 |
|------------------|-------------------|---------------|-----------|-----------------|--------------|----------|---------------------------|------------------------|-------------------|
| **BERT**         | 0.656             | 0.680         | 0.667     | 0.766           | 0.795        | 0.779    | 0.808                     | 0.803                  | **0.805**         |
| **BioBERT**      | 0.687             | 0.681         | **0.684** | 0.786           | 0.778        | **0.782**| 0.807                     | 0.790                  | 0.799             |
| **RoBERTa-large**| 0.667             | 0.609         | 0.636     | **0.791**       | 0.724        | 0.756    | **0.845**                 | 0.728                  | 0.781             |

#### 2. Sentence-level Performance by Category

| Category         | Precision | Recall | F1-score |
|------------------|-----------|--------|----------|
| **Adherence**     | 0.85      | 0.86   | 0.83     |
| **Alcohol**       | 0.40      | 0.40   | 0.40     |
| **Concern**       | 0.70      | 0.52   | 0.55     |
| **Drug**          | 0.00      | 0.00   | 0.00     |
| **Education**     | 0.67      | 0.64   | 0.62     |
| **Employment**    | 0.80      | 0.84   | 0.82     |
| **Financial**     | 0.80      | 0.85   | 0.82     |
| **Healthcare**    | 0.58      | 0.63   | 0.59     |
| **Insurance**     | 0.94      | 0.94   | 0.94     |
| **Literacy**      | 0.07      | 0.20   | 0.10     |
| **Living**        | 0.79      | 0.82   | 0.80     |
| **Mental Health** | 0.97      | 0.92   | 0.94     |
| **Recommendation**| 0.89      | 0.89   | 0.88     |
| **Smoke**         | 0.98      | 1.00   | **0.99** |
| **Social**        | 0.79      | 0.75   | 0.77     |
| **Substance Use** | 0.93      | 0.94   | 0.93     |
| **Transportation**| 0.68      | 0.73   | 0.67     |
| **Trauma**        | 0.72      | 0.77   | 0.73     |
| **Overall**       | 0.79      | 0.78   | 0.78     |


### 12/09/24
1. Generate a unzip.py script for unzip all the zip files inside the folder and extract the json files out.
   - The default folder for zipped files are `../data/annotation_data_zip`
   - The default folder for json files are `../data/annotation_data`
2. Fix a small issue in transform_data.py
   - The default input folder is `../data/annotation_data`
   - The default output folder is `../data/train_data`

### 11/25/24
1. Add sub-levels for adherence, recommendation, literacy
2. Add category of transportation and concerns
3. Several cases to be discussed:
   - 102: 76
   - 101: 42
   - 100: 16, 17, 18, 19
   - 103: 15, 16, 24

### 11/18/24
1. Students finished the annotation of 20 EHRs last Friday.
2. Curation process almost done, but several of the EHRs need to be reviewed together.
   a. PTO 113: , 96: 35
   b. WIC (115)  Family wic means huge poverty
   c. expense 96: 32
3. Add potentially important categories:
   a. Recommendation - Increasing literacy, increase social support, increase financial support,
   b. Adherence
   c. Literacy 
   
### 10/29/24
1. Discuss the annotated documents within team.
2. Refine the guidelines.
3. Add tagsets and apply change to the layers.

### 10/25/24
1. Finish the first 10 curated datasets.
2. Assign 5 more documents to each of the student.


### 10/14/24
1. Add updates to the annotation guidelines. Add insurance, substance use. Add more labels for experiencers, employment status.
2. Leave instructions to the students so they can follow the latest guidelines.
Plans:
1. The INCEpTION will have two layers, one layer (yellow) for first-level TAG, and the other (green) for labels. For example, <img src="samples.png" alt="Annotation Sample"/>
2. We will ask students to fininsh the annotations for 10-15 EHRs first, so that we can start to use transformer-based models to make predictions. At the meantime, students can go back to annotate the second-level labels.
3. We will use transformer models to predict the first layer, and ask LLM to give labels using JSON format.


### 10/11/24
Meet with UF package annotator. Several improvements:
1. Add insurance category. Insurance should not be put into financial
2. Plan to use transformer-based models to predict level 1 category only.
3. Use LLM to predict labels.
4. Put all the related labels on the same span.

### 09/27/24
1. Make changes to the annotation tagset inside Inception server
2. Write code to convert annotation json file into txt file  (../util/transform_data.py)
3. Write code to further convert txt file into json file. Or directly output json file.

### 09/22/24 
1. Add annotation tagset into our Inception server.
2. Check the output file from Inception server.
3. Find what data format do we need.
