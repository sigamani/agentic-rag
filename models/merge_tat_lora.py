from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import os

BASE_MODEL = "NousResearch/Llama-2-7b-hf"           # Requires HF auth
LORA_ADAPTER = "next-tat/tat-llm-7b-lora"
MERGED_SAVE_PATH = "./merged_tat_llm_fp16"

os.makedirs(MERGED_SAVE_PATH, exist_ok=True)

# Load base model
print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Load and merge LoRA
print("Loading and merging LoRA adapter...")
merged_model = PeftModel.from_pretrained(base_model, LORA_ADAPTER)
merged_model = merged_model.merge_and_unload()

print(f"Saving merged model to: {MERGED_SAVE_PATH}")
merged_model.save_pretrained(MERGED_SAVE_PATH)

# Save tokenizer
print("Saving tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.save_pretrained(MERGED_SAVE_PATH)

print("✅ Merge complete.")
