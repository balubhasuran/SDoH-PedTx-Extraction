import json
import argparse
from glob import glob
import os
from tqdm import tqdm

def process_data(file_path):
    json_file = json.load(open(file_path,'r'))
    # --- Get the sentence, article, tags, and labels information through the JSON format ---
    sentences = json_file['_views']['_InitialView']['Sentence']
    article = json_file['_referenced_fss']['1']['sofaString']
    tags = json_file['_views']['_InitialView']['SDoHLevel1']
    labels = json_file['_views']['_InitialView']['SDoHlevel2']
    
    data_dict = {}
    span_dict = {}
    for idx in range(len(sentences)):
        data_dict[idx] = {}
        try:
            begin = sentences[idx]['begin']
        except:
            begin = 0
        end = sentences[idx]['end']
        span_dict[(begin, end)] = idx
        data_dict[idx]['sentence'] = article[begin:end].replace('\xa0',' ').strip()
        data_dict[idx]['begin'], data_dict[idx]['end'] = begin, end
    
    keys_to_del = ['sofa','begin','end']
    for tag, label in zip(tags, labels):
    # ---- Since tags and labels are on the same trigger words, the spans should be the same ----
        begin = tag['begin']
        end = tag['end']
        for spans, idx in span_dict.items():
            if begin >= spans[0] and end <= spans[1]:
                # Find the corresponding sentence ID
                s_id = idx
                break
        for k in keys_to_del:
            label.pop(k, None)
        added_info = {tag['SDoHlv1']: label}
        try:
            data_dict[s_id]['SDoH'].append(added_info)
        except:
            data_dict[s_id]['SDoH'] = [added_info]
    # --- Delete the unnecessary keys ---
    for k,v in data_dict.items():
        v.pop('begin', None)
        v.pop('end', None)
    return data_dict
    
def file_dump(target, output_file):
    with open(output_file,'w', encoding="utf-8") as f:
        json.dump(target, f, indent=3, ensure_ascii=False)
    print(f"Saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Convert annotation data into second level SDoH extraction JSON format for multiple documents")
    parser.add_argument("-i", "--input_folder", default="../data/annotation_data", help="Input data folder")
    parser.add_argument("-o", "--output_folder", default="../data/processed_data", help="Output data folder")
    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder
    if not input_folder.endswith('/'):
        input_folder += '/'
    if not output_folder.endswith('/'):
        output_folder += '/'
    os.makedirs(output_folder, exist_ok=True)
    file_paths = glob(f'{input_folder}*.json')
    for file_path in tqdm(file_paths):
        data_dict = process_data(file_path)
        file_path = file_path.replace("\\","/")
        file_name = file_path.split('/')[-1].split('.')[0]
        output_file = f'{output_folder}{file_name}.json'
        file_dump(data_dict, output_file)

if __name__ == "__main__":
    main()