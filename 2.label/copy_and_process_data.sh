#!/bin/bash

SOURCE_DIR="data/curation"
DEST_FOLDER="data/annotation_data_zip"

# Create the destination folder if it doesn't exist
mkdir -p "$DEST_FOLDER"

# Find and copy ZIP files safely, handling spaces in filenames
find "$SOURCE_DIR" -type f -name "*.zip" -print0 | while IFS= read -r -d '' file; do
    # Extract the parent directory name
    parent_folder=$(basename "$(dirname "$file")")
    
    # Extract the original ZIP filename
    original_filename=$(basename "$file")
    
    # Construct new filename with parent folder name
    new_filename="${parent_folder}.zip"
    
    # Copy and rename the ZIP file
    cp "$file" "$DEST_FOLDER/$new_filename"
    
    echo "Copied and renamed: $file → $DEST_FOLDER/$new_filename"
done

echo "All ZIP files have been copied and renamed in $DEST_FOLDER."

cd util
python unzip.py -i ../data/annotation_data_zip/ -o ../data/annotation_data/

python transform_data.py