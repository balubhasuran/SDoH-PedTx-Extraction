## Update Log
### 04/03/26
Finished first round prediction process. The gold stardard tags and the sentences together with 2 previous sentences are fed into the GPT-4o API.

Sample output 1:
```json
{
  "sentence": "100\tPt, Tanecia, is a 4 year old female who is diagnosed with hypoplastic left heart syndrome s/p norwood, Glenn, and fenestrated fontan with a personal history of ECMO and seizure disorder who is now being referred for heart transplant psychosocial assessment.",
  "categories": [
    "Healthcare"
  ],
  "extracted_predictions": {
    "Healthcare": {
      "extracted_conditions": [
        {
          "category": "Healthcare",
          "Experiencer": "patients",
          "healthcare_type": "surgeries/procedures"
        },
        {
          "category": "Healthcare",
          "Experiencer": "patients",
          "healthcare_type": "surgeries/procedures"
        },
        {
          "category": "Healthcare",
          "Experiencer": "patients",
          "healthcare_type": "surgeries/procedures"
        },
        {
          "category": "Healthcare",
          "Experiencer": "patients",
          "healthcare_type": "hospital stay"
        },
        {
          "category": "Healthcare",
          "Experiencer": "patients",
          "healthcare_type": "clinical visits"
        }
      ]
    }
  }
}
```

Sample Output 2:
```json
    {
        "sentence": "There is no smoking in the home, although dad had been smoking outside.",
        "categories": [
            "Smoke",
            "Smoke"
        ],
        "extracted_predictions": {
            "Smoke": {
                "extracted_conditions": [
                    {
                        "category": "Smoke",
                        "Experiencer": "Father",
                        "smoke_status": "past"
                    },
                    {
                        "category": "Smoke",
                        "Experiencer": "Family",
                        "smoke_status": "none"
                    }
                ]
            }
        }
```
### 05/15/25
1. Build a [schema for LLM tool calling](../config/llm_category_schema.json). 
2. Complete a [sample code](../notebooks/LLM_label_prediction.ipynb) for tool calling.

### 04/28/25
Build the pipeline for data pre-processing

### 04/21/25
Finish curating the second level SDoH. 
