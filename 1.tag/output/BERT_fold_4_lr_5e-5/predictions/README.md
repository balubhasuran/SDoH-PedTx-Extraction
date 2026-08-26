---
library_name: transformers
base_model: output/BERT_fold_4_lr_5e-5
tags:
- generated_from_trainer
model-index:
- name: predictions
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# predictions

This model is a fine-tuned version of [output/BERT_fold_4_lr_5e-5](https://huggingface.co/output/BERT_fold_4_lr_5e-5) on an unknown dataset.

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 5e-05
- train_batch_size: 8
- eval_batch_size: 8
- seed: 42
- optimizer: Use OptimizerNames.ADAMW_TORCH_FUSED with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: linear
- num_epochs: 3.0

### Framework versions

- Transformers 4.57.1
- Pytorch 2.9.0+cu126
- Datasets 4.3.0
- Tokenizers 0.22.1
