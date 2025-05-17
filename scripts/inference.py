import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


def load_model_and_tokenizer(checkpoint_dir):
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir)
    model = AutoModelForCausalLM.from_pretrained(
        checkpoint_dir, torch_dtype=torch.float16
    ).cuda()
    model.eval()
    return model, tokenizer


def generate_answer(model, tokenizer, prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=128)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Path to fine-tuned model directory",
    )
    parser.add_argument("--question", type=str, required=True)
    parser.add_argument("--context", type=str, required=True)
    args = parser.parse_args()

    model, tokenizer = load_model_and_tokenizer(args.checkpoint)
    prompt = f"Question: {args.question}\nContext: {args.context}\n\nReasoning:"
    response = generate_answer(model, tokenizer, prompt)
    print("\nGenerated Response:\n", response)


if __name__ == "__main__":
    main()
