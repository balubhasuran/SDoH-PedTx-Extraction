#!/bin/bash

# Set GPU device (change if needed)
export CUDA_VISIBLE_DEVICES=0

# BioBERT model path (update if needed)
BERT_MODEL="google-bert/bert-large-uncased"

# Path to 5-fold cross-validation data
DATA_DIR="data/splitted_data"
OUTPUT_BASE="output"

# Training parameters
LEARNING_RATE=1e-5
NUM_EPOCHS=7
BATCH_SIZE=16

# Loop over 5 folds
for fold in {1..5}; do
    echo "🔥 Training on Fold $fold..."
    
    # Define paths for this fold
    FOLD_DIR="$DATA_DIR/fold_$fold"
    OUTPUT_DIR="$OUTPUT_BASE/BERTL_fold_$fold_lr_$LEARNING_RATE"

    # Ensure output directories exist
    mkdir -p "$OUTPUT_DIR"

    # Run training
    python ./ner_code/run_ner.py \
        --model_name_or_path $BERT_MODEL \
        --train_file "$FOLD_DIR/train.json" \
        --validation_file "$FOLD_DIR/test.json" \
        --output_dir "$OUTPUT_DIR" \
        --do_train \
        --do_eval \
        --learning_rate $LEARNING_RATE \
        --num_train_epochs $NUM_EPOCHS \
        --per_device_train_batch_size $BATCH_SIZE \
        --per_device_eval_batch_size $BATCH_SIZE \
        --overwrite_output_dir \
        --logging_steps 10 \
        --eval_strategy "epoch" \
        --save_strategy "epoch" \
        --logging_strategy "epoch" \
        --load_best_model_at_end True \
        --metric_for_best_model "eval_f1" \
        --greater_is_better True \
        --save_total_limit 2

    echo "Fold $fold training complete. Model saved to $OUTPUT_DIR"
done

echo "5-fold cross-validation training completed!"