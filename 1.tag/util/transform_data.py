import json
import argparse
import glob
import os
from tqdm import tqdm

# Your existing BIO conversion logic
def create_bio_format(tokens, token_offsets, token_labels, labeled_offsets):
    labeled_spans = []
    for label, offsets in zip(token_labels, labeled_offsets):
        for offset in offsets:
            labeled_spans.append((offset[0], offset[1], label))

    prev_entity = None
    prev_span = None
    labels = []

    for i, (token, offset) in enumerate(zip(tokens, token_offsets)):
        if token == " ":
            continue
        
        matched_labels = [label for start, end, label in labeled_spans if start <= offset[0] < end]

        if matched_labels:
            # Standardizing label format (removing spaces for consistency in B-TAG/I-TAG)
            label = matched_labels[0].replace(' ', '')
            current_span = [(start, end) for start, end, lbl in labeled_spans if lbl == label and start <= offset[0] < end]

            if prev_entity != label or (prev_span and current_span and prev_span != current_span[0]):
                labels.append(f"B-{label}")
            else:
                labels.append(f"I-{label}")

            prev_entity = label
            prev_span = current_span[0] if current_span else None
        else:
            labels.append("O")
            prev_entity = None
            prev_span = None

    return tokens, labels

def get_labels_and_offsets(view_data, method, mapping):
    """
    Extracts labels and offsets based on the chosen method.
    """
    token_labels = []
    label_offsets = []
    
    if method == "tag":
        # Original logic: Look for SDoHLevel1 tags directly
        sdoh_list = view_data.get("SDoHLevel1", [])
        for s in sdoh_list:
            if "SDoHlv1" in s and "begin" in s:
                token_labels.append(s["SDoHlv1"])
                label_offsets.append([(s["begin"], s["end"])])
                
    elif method == "label":
        # New logic: Look at SDoHLevel2 keys and map them to Level 1 names
        sdoh_list = view_data.get("SDoHlevel2", [])
        for s in sdoh_list:
            # Find which key in the JSON object matches our Level 2 keyword list
            found_mapped_labels = [mapping[k] for k in s if k in mapping]
            if found_mapped_labels and "begin" in s:
                # Take the first matched keyword mapping
                token_labels.append(found_mapped_labels[0])
                label_offsets.append([(s["begin"], s["end"])])
                
    return token_labels, label_offsets

def main():
    parser = argparse.ArgumentParser(description="Convert annotation data into token-based JSON format")
    parser.add_argument("-i", "--input_folder", default="../data/annotation_data/", help="Input folder")
    parser.add_argument("-o", "--output_folder", default="../data/train_data", help="Output folder")
    parser.add_argument("-m", "--method", choices=["tag", "label"], default="label", 
                        help="tag: use SDoHLevel1 tags; label: map SDoHLevel2 keys to Level 1 tags")
    args = parser.parse_args()

    # Mapping Level 2 keys -> Level 1 labels
    mapping = {
        'AdherenceLevel': 'Adherence', 'AdherenceType': 'Adherence',
        'ConcernLevel': 'Concern', 'EducationStatus': 'Education', 
        'EducationType': 'Education', 'EmploymentStatus': 'Employment',
        'FinancialStatus': 'Financial', 'HealthcareType': 'Healthcare',
        'InsuranceType': 'Insurance', 'LiteracyLevel': 'Literacy', 
        'LiteracyType': 'Literacy', 'LivingStatus': 'Living', 
        'LivingType': 'Living', 'ResidentType': 'Living',
        'MentalHealthStatus': 'Mental Health', 'MentalHealthType': 'Mental Health',
        'RecommendationType': 'Recommendation', 'SmokeStatus': 'Smoke',
        'SocialActivity': 'Social', 'SocialType': 'Social',
        'SubstanceUseStatus': 'Substance Use', 'TransportationType': 'Transportation',
        'TransportationConvenienceLevel': 'Transportation', 'TraumaStatus': 'Trauma', 
        'TraumaType': 'Trauma'
    }

    os.makedirs(args.output_folder, exist_ok=True)
    files = glob.glob(os.path.join(args.input_folder, "*.json"))

    for json_file in tqdm(files):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        view = data["_views"]["_InitialView"]
        context = data["_referenced_fss"]["1"]["sofaString"].replace("\u807D"," ")
        
        # Prepare basic tokens
        token_spans = view["Token"]
        spans = [(t.get("begin", 0), t["end"]) for t in token_spans]
        tokens, token_offsets = zip(*[(context[s[0]:s[1]], s) for s in spans if context[s[0]:s[1]].strip()])

        # Get Labels based on argument
        token_labels, label_offsets = get_labels_and_offsets(view, args.method, mapping)

        # Process into sentences
        sentence_start = 0
        document_sentences = []
        sentence_id = 1

        for i, token in enumerate(tokens):
            if token in {".", "!", "?"} or i == len(tokens) - 1:
                s_tokens = tokens[sentence_start : i + 1]
                s_spans = token_offsets[sentence_start : i + 1]
                
                _, s_labels = create_bio_format(s_tokens, s_spans, token_labels, label_offsets)

                document_sentences.append({
                    "id": sentence_id,
                    "tokens": list(s_tokens),
                    "ner_tags": s_labels
                })
                sentence_id += 1
                sentence_start = i + 1

        output_path = os.path.join(args.output_folder, os.path.basename(json_file))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(document_sentences, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()