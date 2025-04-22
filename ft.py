import os
import yaml
import torch
import argparse
import random
import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
from peft import get_peft_model, LoraConfig, TaskType


def seed_everything(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def prepare_model_and_tokenizer(cfg):
    tokenizer = AutoTokenizer.from_pretrained(cfg['model_name_or_path'], trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(cfg['model_name_or_path'], trust_remote_code=True)

    if cfg.get('use_lora', True):
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=cfg['lora_rank'],
            lora_alpha=cfg['lora_alpha'],
            lora_dropout=cfg['lora_dropout'],
            bias="none"
        )
        model = get_peft_model(model, peft_config)

    return model, tokenizer


def preprocess(example, tokenizer):
    prompt = f"Question: {example['question']}\nContext: {example['context']}\n\nReasoning: {example['reasoning']}\nAnswer: {example['answer']}"
    return tokenizer(prompt, truncation=True, padding='max_length', max_length=512)


def load_and_tokenize_data(cfg, tokenizer):
    dataset = load_dataset("json", data_files=cfg['dataset_path'])['train']
    tokenized_dataset = dataset.map(lambda x: preprocess(x, tokenizer), batched=False)
    return tokenized_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config_finetune.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    seed_everything(42)

    model, tokenizer = prepare_model_and_tokenizer(cfg)
    tokenized_dataset = load_and_tokenize_data(cfg, tokenizer)

    training_args = TrainingArguments(
        output_dir=cfg['output_dir'],
        per_device_train_batch_size=cfg['per_device_train_batch_size'],
        gradient_accumulation_steps=cfg['gradient_accumulation_steps'],
        num_train_epochs=cfg['num_train_epochs'],
        learning_rate=cfg['learning_rate'],
        lr_scheduler_type=cfg['lr_scheduler_type'],
        warmup_ratio=cfg['warmup_ratio'],
        fp16=True,
        logging_dir=os.path.join(cfg['output_dir'], "logs"),
        logging_steps=10,
        save_total_limit=1,
        save_strategy="epoch",
        report_to="none",
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    trainer.train()
    model.save_pretrained(cfg['output_dir'])
    tokenizer.save_pretrained(cfg['output_dir'])


if __name__ == "__main__":
    main()
