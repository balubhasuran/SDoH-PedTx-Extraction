import json
import argparse
import glob
import os
import random
from tqdm import tqdm
from collections import Counter

def get_sentence_strat_label(ner_tags, priority_list):
    present_entities = {t.split("-")[-1] for t in ner_tags if t != "O"}
    if not present_entities:
        return "O"
    for p_tag in priority_list:
        if p_tag in present_entities:
            return p_tag
    return list(present_entities)[0]

def main():
    parser = argparse.ArgumentParser(description="Auto-Priority Stratified Split")
    parser.add_argument("-i", "--input_folder", default="../data/train_data/")
    parser.add_argument("-o", "--output_folder", default="../data/splitted_data/sentence_split/")
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)
    json_files = glob.glob(os.path.join(args.input_folder, "*.json"))

    temp_sentences = []
    global_tag_counts = Counter()

    print("Step 1: Analyzing frequencies and tracking document names...")
    for file_path in tqdm(json_files):
        # Extract the filename (e.g., 'patient_01.json')
        doc_name = os.path.basename(file_path).split('.')[0]
        
        with open(file_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
            for sentence in doc_data:
                # Track unique entities for rarity logic
                entities_in_sent = {t.split("-")[-1] for t in sentence["ner_tags"] if t != "O"}
                for ent in entities_in_sent:
                    global_tag_counts[ent] += 1
                
                # ATTACH THE FILENAME HERE
                sentence["file_name"] = doc_name
                temp_sentences.append(sentence)

    # Generate priority (rarest first)
    dynamic_priority = [tag for tag, count in global_tag_counts.most_common()[::-1]]
    
    # Step 2: Binning
    bins = {}
    for s in temp_sentences:
        strat_label = get_sentence_strat_label(s["ner_tags"], dynamic_priority)
        s["_strat_key"] = strat_label
        bins.setdefault(strat_label, []).append(s)

    train_data, test_data = [], []
    random.seed(42)

    # Step 3: The 80/20 Split per Bin
    print("Step 2: Performing stratified split...")
    for label, sents in bins.items():
        random.shuffle(sents)
        split_idx = int(len(sents) * 0.8)
        
        # This is where the 80% and 20% are taken for each tag
        train_data.extend(sents[:split_idx])
        test_data.extend(sents[split_idx:])

    # Shuffle everything and rebuild final JSONs
    random.shuffle(train_data)
    random.shuffle(test_data)

    for name, dataset in [("train.json", train_data), ("test.json", test_data)]:
        final_list = []
        for i, s in enumerate(dataset, 1):
            # Include 'file_name' in the final dictionary
            final_list.append({
                "id": i,
                "file_name": s["file_name"], 
                "tokens": s["tokens"],
                "ner_tags": s["ner_tags"]
            })
        
        with open(os.path.join(args.output_folder, name), "w", encoding="utf-8") as f:
            json.dump(final_list, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Train and Test files created in {args.output_folder}")

if __name__ == "__main__":
    main()