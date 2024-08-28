HF_TOKEN=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
vllm serve models/Llama-3.1-Storm-8B.Q8_0.gguf --gpu_memory_utilization 0.9 --max_model_len 48000 --enforce-eager