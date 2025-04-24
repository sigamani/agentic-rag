from peft import PeftModel

# Load model + adapter
model = PeftModel.from_pretrained(base_model, "outputs")
model = model.merge_and_unload()

# Save full merged model
model.save_pretrained("outputs-merged")
tokenizer.save_pretrained("outputs-merged")
