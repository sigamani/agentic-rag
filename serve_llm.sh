HF_TOKEN=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
# vllm serve PRichardErkhov/Wengwengwhale_-_llama-3.1-8B-Instruct-finance-analyst-gguf
vllm serve meta-llama/Meta-Llama-3.1-8B-Instruct --gpu_memory_utilization 0.90 --max_model_len 16000