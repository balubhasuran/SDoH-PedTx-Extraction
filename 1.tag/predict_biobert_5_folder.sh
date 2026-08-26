#!/bin/bash

# Set GPU device (change if needed)
export CUDA_VISIBLE_DEVICES=0

# BioBERT model path (update if needed)
MODEL="dmis-lab/biobert-base-cased-v1.2"

# Path to 5-fold cross-validation data
DATA_DIR="data/splitted_data"
OUTPUT_BASE="output"

# Training parameters
LEARNING_RATE=5e-5
NUM_EPOCHS=5
BATCH_SIZE=16

# Loop over 5 folds
for fold in {1..5}; do
    echo "🔥 Predicting on Fold $fold..."
    
    # Define paths for this fold
    FOLD_DIR="$DATA_DIR/fold_$fold"

    OUTPUT_DIR="${OUTPUT_BASE}/BioBERT_fold_${fold}_lr_${LEARNING_RATE}/predictions"
    
    MODEL="${OUTPUT_BASE}/BioBERT_fold_${fold}_lr_${LEARNING_RATE}"
    # Ensure output directories exist
    mkdir -p "$OUTPUT_DIR"

    # Run training
    python ./ner_code/run_ner.py \
        --model_name_or_path $MODEL \
        --train_file "$FOLD_DIR/train.json" \
        --test_file "$FOLD_DIR/test.json" \
        --validation_file "$FOLD_DIR/test.json" \
        --output_dir "$OUTPUT_DIR" \
        --do_predict \

    echo "Fold $fold prediction complete. File saved to $OUTPUT_DIR"
done