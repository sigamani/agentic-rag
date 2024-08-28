# ConvFinQA

## Introduction
ConvFinQA is a financial question-answering task that involves answering questions based on financial documents. The challenge is to accurately retrieve relevant information from a large corpus of documents and generate correct answers. This document outlines the steps to implement and evaluate a model for this task, including both easy and hard variants.

## Problem
The task is to answer questions using the full corpus of the ConvFinQA `train.json` dataset.

### Easy Variant
The model has access to the correct document at inference time, so we are only working with a single document at a time.

**Inputs:**
- Question
- Document X

**Output:** Answer

To solve the easy problem, change `CHEATING_RETRIEVAL` to `True` in [config.py](config.py)

### Hard Variant
The model does not know which document contains the relevant information and must identify the correct document from the entire corpus (3,037 documents in `train.json`).

**Inputs:**
- Question
- Document 1
- Document 2
- ...
- Document 3,036
- Document 3,037

**Output:** Answer

To solve the hard problem, change `CHEATING_RETRIEVAL` to `False` in [config.py](config.py)

## Prerequisites
- Python 3.12
- [Poetry](https://python-poetry.org/docs/#installation)
- OpenAI (or OpenAI compatible) API access. I have used vLLM with [Llama-3.1-8B-Storm (Q8_0 GGUF)](https://huggingface.co/akjindal53244/Llama-3.1-Storm-8B-GGUF?show_file_info=Llama-3.1-Storm-8B.Q8_0.gguf).
- Cohere API Access. You can get free trial keys from [cohere.com](https://cohere.com)
- Langfuse. You can either get free access from [cloud.langfuse.com](https://cloud.langfuse.com) or you can self-host it.
  
## Installation
1. Install dependencies: `poetry install`
2. Download data: `sh get_data.sh`
3. Set your `.env` with the correct urls/keys for LLM, Cohere, Langfuse. See [.env.example](.env.example) for reference:
    - 

## Usage
### 1. Start the vLLM Server
   Skip this step if you have OpenAI (or OpenAI compatible) API access.

   1. Download a vLLM compatible model (I used [Llama-3.1-Storm-8B.Q8_0.gguf](https://huggingface.co/akjindal53244/Llama-3.1-Storm-8B-GGUF/blob/main/Llama-3.1-Storm-8B.Q8_0.gguf))
   
   2. Edit [run_serve.sh](run_serve.sh) to adjust it to your GPU capabilities (Currently it's set up for my RTX 3090)

   3. Start the vLLM server by running:
   ```sh
   sh run_serve.sh
   ```
   

### 2. Create the Vector Database
   Use the script to create a vector database with the data:
   ```sh
   python create_db.py
   ```
   This step will index the documents into a local vector database (ChromaDB).

### 3. Create the Evaluation Dataset
   Generate the evaluation dataset, which will be stored in Langfuse, using:
   ```sh
   python create_dataset.py
   ```
   This script prepares the dataset for evaluation by transforming it into a suitable format.

### 4. Run the Evaluation
   Run the evaluation of the model using:
   ```sh
   python eval.py
   ```
   This step will evaluate the model's performance and output the results in console and also row-wise in `eval.csv`

## Todo
- **Improve Retrieval**: Explore the following methods to enhance retrieval accuracy:
    - Hybrid search with multi-vector representations.
    - Fine-tune embedding models on financial data.
    - Experiment with [HyDe](https://docs.haystack.deepset.ai/docs/hypothetical-document-embeddings-hyde) and other querying techniques
- **Session Support**: Add support for multiple message conversations to handle context over several interactions.
- **Prompt Improvements**: Refine prompts for better model performance.
- **Reflection**: Implement LLM self-checks for correctness to improve answer accuracy.
- **Python Execution**: Integrate Python execution for more accurate math calculations, possibly using a chain of abstraction or alternatives.
- **Context Trimming**: Improve the process of trimming context to include only the most relevant parts. Previous attempts showed potential but need refinement.
- **Table Parsing**: Experiment with Chain of Tables ([Google Chain of Table](https://github.com/google-research/chain-of-table)) or other methods for more effective table parsing.
- **Optimization**: Run hyperparameter optimization for various parameters (e.g. k in retrieval)
- **Dependency Management**: Remove unnecessary dependencies to streamline the environment.
- **Code Refactor**: Improve code structure and readability through refactoring, dockerize, reorganize project structure, add logging.
- **Fine-Tuning Models**: Experiment with fine-tuning language models specifically on financial documents to improve performance.

## Observations


### Context extraction experiment
See
- **Context Extraction**: Using a context extraction step resulted in a significant recall loss without sufficient gains in precision. **Decision:** Removed the context extraction step.
- **Reranking Step**: The reranking step significantly reduces the amount of context while barely sacrificing recall, making it a valuable addition. **Decision:** Keeping the reranking step.

#### Results
Below are some results with an older version of the model on the first 100 samples from `train.json`. (Change is calculated relative to the previous step: retrieval -> reranker -> context extraction.)

| Metric                               | Value (%) | Change (%)        |
|--------------------------------------|-----------|-------------------|
| Mean Retrieval Precision             | 2.58      | -                 |
| Mean Retrieval Recall                | 31.15     | -                 |
| Mean Reranking Precision             | 9.84      | +7.25             |
| Mean Reranking Recall                | 29.51     | -1.64             |
| Mean Context Extraction Precision    | 12.84     | +3.01             |
| Mean Context Extraction Recall       | 19.67     | -9.84             |

### Explanation of Metrics

The code evaluates the performance of a system designed to answer questions using retrieved documents and generated answers. Below is an explanation of the metrics used in the evaluation:

- **Precision**: Precision is a measure of how many of the documents retrieved by the system are relevant to the query. In this context:
  - **Retrieval Precision**: It calculates the ratio of relevant documents retrieved (in this case, whether the expected document is in the retrieved list) to the total number of documents retrieved. If the expected document is among the retrieved documents, precision is calculated as 1 divided by the number of retrieved documents. Higher precision means fewer irrelevant documents (false positives) are included in the retrieval.
  - **Reranker Precision**: After reranking the retrieved documents, this metric measures how accurately the system has placed the relevant document at the top of the list. Similar to retrieval precision, it’s calculated as 1 divided by the number of reranked documents if the relevant document is present.

- **Recall**: Recall measures the ability of the system to find all relevant documents. In this case:
  - **Retrieval Recall**: It is defined as the proportion of relevant documents retrieved compared to the total number of relevant documents available. Since only one document is considered relevant for each query in ConvFinQA, recall is either 1 (if the relevant document is retrieved) or 0 (if it is not).
  - **Reranker Recall**: Similar to retrieval recall but applied after the documents have been reranked. It indicates whether the relevant document remains in the reranked list.

- **Correctness Score**: This metric assesses the accuracy of the generated answer compared to the expected answer. It’s calculated as follows:
  - If the predicted answer matches the expected answer exactly, the correctness score is 1.
  - If the answer is numeric or contains numeric information (e.g., percentages, dollar amounts), the score is calculated using a relative difference, with a power penalty applied to larger differences. The idea is to reward close approximations and penalize larger deviations.
  - In cases where the answer involves more complex comparisons or cannot be directly matched, the system may use a language model (LLM) to generate a score, although this is less common.

- **Relative Score**: This function calculates the relative difference between two numeric values. It applies a penalty to larger differences by raising the difference to a specified power. This ensures that smaller differences between predicted and expected values result in higher scores, while larger differences lead to lower scores.

- **High Correctness Threshold**: This is a predefined threshold (set at 0.9) used to categorize answers as having high correctness. If a correctness score exceeds this threshold, the answer is considered highly correct.

### Summary Statistics
At the end of the evaluation, the code calculates and prints average scores for each metric across all evaluated items:
- **Mean Correctness Score**: The average correctness score of the answers across all evaluated items.
- **High Correctness Rate**: The proportion of answers that exceed the high correctness threshold.
- **Mean Retrieval Precision Score**: The average retrieval precision score across all items.
- **Mean Retrieval Recall Score**: The average retrieval recall score across all items.
- **Mean Reranker Precision Score**: The average reranker precision score across all items, along with the difference from the mean retrieval precision score.
- **Mean Reranker Recall Score**: The average reranker recall score across all items, along with the difference from the mean retrieval recall score.

These metrics help evaluate both the retrieval effectiveness (how well relevant documents are retrieved) and the generation correctness (how accurately answers are generated based on those documents).
