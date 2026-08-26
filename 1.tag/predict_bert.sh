#!/bin/bash

# Set GPU device (change if needed)
export CUDA_VISIBLE_DEVICES=0

# Path to 5-fold cross-validation data
DATA_DIR="data/splitted_data/sentence_split"
OUTPUT_BASE="output"

# Training parameters
LEARNING_RATE=3e-5
NUM_EPOCHS=50
BATCH_SIZE=16


# Define paths for this fold
OUTPUT_DIR="${OUTPUT_BASE}/BERT_sentence_split_lr_${LEARNING_RATE}/predictions"
MODEL="${OUTPUT_BASE}/BERT_sentence_split_lr_${LEARNING_RATE}"
# Ensure output directories exist
mkdir -p "$OUTPUT_DIR"

# Run training
python ./ner_code/run_ner.py \
    --model_name_or_path $MODEL \
    --train_file "$DATA_DIR/train.json" \
    --test_file "$DATA_DIR/test.json" \
    --validation_file "$DATA_DIR/test.json" \
    --output_dir "$OUTPUT_DIR" \
    --do_predict \



echo "predict_bert.sh complete. File saved to $OUTPUT_DIR"