export CUDA_VISIBLE_DEVICES=0

python ./ner_code/run_ner.py \
    --model_name_or_path roberta-base \
    --train_file "data/splitted_data/fold_1/train.json" \
    --validation_file "data/splitted_data/fold_1/test.json" \
    --output_dir "output/sample_output/predictions" \
    --do_train \
    --do_eval \
    --learning_rate 2e-5 \
    --num_train_epochs 4 \
    --per_device_train_batch_size 16 \
    --max_seq_length 512 \
    --overwrite_cache \
    --overwrite_output_dir