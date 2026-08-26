import os
import glob
import json
import argparse
from sklearn.model_selection import KFold

def main():
    parser = argparse.ArgumentParser(description='Split JSON data into multiple folders for cross-validation')
    parser.add_argument('-i', '--input_folder', default='../data/train_data/', help='Input data folder, default: ../data/train_data/')
    parser.add_argument('-o', '--output_folder', default='../data/splitted_data/', help='Output data folder, default: ../data/splitted_data/')
    parser.add_argument('-f', '--folder_num', type=int, default=5, help='Number of folders for cross-validation, default: 5')
    args = parser.parse_args()

    data_dir = args.input_folder
    output_dir = args.output_folder
    folder_num = args.folder_num

    # Get all JSON files
    all_files = glob.glob(os.path.join(data_dir, "*.json"))
    
    if not all_files:
        print("No JSON files found in the input folder.")
        return

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Perform k-fold cross-validation
    kf = KFold(n_splits=folder_num, shuffle=True, random_state=42)

    for fold, (train_idx, test_idx) in enumerate(kf.split(all_files)):
        fold_dir = os.path.join(output_dir, f"fold_{fold+1}")
        os.makedirs(fold_dir, exist_ok=True)

        train_data = []
        test_data = []
        train_labels = set()  # Collect unique labels from training set
        
        # Process training files
        sentence_id_counter = 0  # Reset sentence ID counter for train files
        for idx in train_idx:
            with open(all_files[idx], 'r', encoding='utf-8') as infile:
                data = json.load(infile)
                for entry in data:
                    entry['sentence_id'] = sentence_id_counter
                    sentence_id_counter += 1
                    train_labels.update(entry["ner_tags"])  # Collect labels
                    train_data.append(entry)
        
        # Save merged training file
        train_merged_file = os.path.join(fold_dir, "train.json")
        with open(train_merged_file, 'w', encoding='utf-8') as outfile:
            json.dump(train_data, outfile, indent=2)
        
        # Process test files
        sentence_id_counter = 0  # Reset sentence ID counter for test files
        for idx in test_idx:
            with open(all_files[idx], 'r', encoding='utf-8') as infile:
                data = json.load(infile)
                for entry in data:
                    entry['sentence_id'] = sentence_id_counter
                    sentence_id_counter += 1
                    
                    # Ensure labels exist in train set; replace unknown labels
                    entry["ner_tags"] = [label if label in train_labels else "O" for label in entry["ner_tags"]]
                    
                    test_data.append(entry)
        
        # Save merged test file
        test_merged_file = os.path.join(fold_dir, "test.json")
        with open(test_merged_file, 'w', encoding='utf-8') as outfile:
            json.dump(test_data, outfile, indent=2)

        print(f"Fold {fold+1}: Merged train.json ({len(train_idx)} files) & test.json ({len(test_idx)} files)")
    
    print("\nCross-validation with label filtering completed!")

if __name__ == "__main__":
    main()
