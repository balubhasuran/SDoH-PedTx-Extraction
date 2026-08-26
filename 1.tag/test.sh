#!/bin/bash

# Set GPU device (change if needed)
export CUDA_VISIBLE_DEVICES=0

# BioBERT model path (update if needed)
BIOBERT_MODEL="dmis-lab/biobert-base-cased-v1.2"

# Path to 5-fold cross-validation data
DATA_DIR="data/splitted_data"
OUTPUT_BASE="data/output"

# Training parameters
LEARNING_RATE=3e-5
NUM_EPOCHS=15
BATCH_SIZE=16

# Loop over 5 folds
for fold in {1..5}; do
    echo "🔥 Training on Fold $fold..."
    
    # Define paths for this fold
    FOLD_DIR="$DATA_DIR/fold_$fold"
    OUTPUT_DIR="$OUTPUT_BASE/fold_$fold"

    # Ensure output directories exist
    mkdir -p "$OUTPUT_DIR"

    # Run training
    python ./ner_code/run_ner.py \
        --model_name_or_path $BIOBERT_MODEL \
        --train_file "$FOLD_DIR/train.json" \
        --validation_file "$FOLD_DIR/test.json" \
        --output_dir "$OUTPUT_DIR" \
        --do_train \
        --do_eval \
        --learning_rate $LEARNING_RATE \
        --num_train_epochs $NUM_EPOCHS \
        --per_device_train_batch_size $BATCH_SIZE \
        --per_device_eval_batch_size $BATCH_SIZE \
        --overwrite_output_dir

    echo "Fold $fold training complete. Model saved to $OUTPUT_DIR"
done

echo "5-fold cross-validation training completed!"