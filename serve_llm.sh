HF_TOKEN=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
# vllm serve PRichardErkhov/Wengwengwhale_-_llama-3.1-8B-Instruct-finance-analyst-gguf
# vllm serve meta-llama/Meta-Llama-3.1-8B-Instruct --gpu_memory_utilization 0.95 --max_model_len 64000 --enforce-eager
vllm serve models/Llama-3.1-Storm-8B.Q8_0.gguf --gpu_memory_utilization 0.95 --max_model_len 64000 --enforce-eager
# vllm serve akjindal53244/Llama-3.1-Storm-8B-GGUF/Llama-3.1-Storm-8B.Q4_K_M.gguf
# Load and run the model: