from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import os
from huggingface_hub import HfApi, login

# --- Constants ---
BASE_MODEL = "NousResearch/Llama-2-7b-hf"            # Full base model
LORA_ADAPTER = "next-tat/tat-llm-7b-lora"             # LoRA adapter
MERGED_SAVE_PATH = "./merged-llama2-tat-fp16"         # Temp local save
HF_REPO_ID = "michael-sigamani/llama2-7b-tat-lora-fp16" # Final merged repo

PRIVATE = False  # Set True if you want the repo private

# --- Hugging Face Auth ---
login(token=os.environ.get("HF_TOKEN"))  # assumes HF_TOKEN is set in env

# --- Create local save dir ---
os.makedirs(MERGED_SAVE_PATH, exist_ok=True)

# --- Load base model ---
print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# --- Load and merge LoRA ---
print("Loading and merging LoRA adapter...")
merged_model = PeftModel.from_pretrained(
    base_model,
    LORA_ADAPTER,
    device_map="auto",
    torch_dtype=torch.float16
)
merged_model = merged_model.merge_and_unload()

# --- Save merged model locally ---
print(f"Saving merged model to: {MERGED_SAVE_PATH}")
merged_model.save_pretrained(MERGED_SAVE_PATH)

# --- Save tokenizer ---
print("Saving tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
tokenizer.save_pretrained(MERGED_SAVE_PATH)

# --- Push merged model to Hugging Face ---
print(f"Pushing merged model to Hugging Face Hub: {HF_REPO_ID}")
api = HfApi()
api.upload_folder(
    folder_path=MERGED_SAVE_PATH,
    repo_id=HF_REPO_ID,
    repo_type="model",
    commit_message="Upload merged NousResearch 7B + next-tat 7B LoRA merged model",
    private=PRIVATE,
)

print("✅ Merge and upload complete.")
