# ConvFinQA

## Introduction
ConvFinQA is a financial question-answering task that involves answering questions based on financial documents. The challenge is to accurately retrieve relevant information from a large corpus of documents and generate correct answers. This document outlines the steps to implement and evaluate a model for this task, including both easy and hard variants.

## Problem
The task is to answer questions using the full corpus of the ConvFinQA `train.json` dataset.

See [Explanation of Metrics](#explanation-of-metrics) for a guide on how to interpret the metrics.

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

# Model

The model is based on a RAG architecture, with some elements of "advanced RAG" such as query rewriting, reranking, answer extraction. In high-level:

## Description

![Model graph](./graph.png)

1. **Start Node (`__start__`)**:
   - This is the entry point of the workflow, marking where the process begins.

2. **Extract Question (`extract_question`)**:
   - This node extracts the user's question from the input messages. The extracted question is stored in the state for further processing.

3. **Generate Queries (`generate_queries`)**:
   - This node generates multiple queries based on the extracted question. These queries are used to retrieve relevant documents from a database or knowledge base.

4. **Retriever (`retriever`)**:
   - This node retrieves documents that are potentially relevant to the generated queries from a database or vector store. It returns these documents for further processing.

5. **Reranker (`reranker`)**:
   - After retrieving the documents, this node reranks them based on their relevance to the user's question. The reranking is done to prioritize the most relevant documents for the next steps.

6. **Generator (`generator`)**:
   - This node generates a response based on the reranked documents. It may use a language model to produce an answer that combines information from the top-ranked documents.

7. **Extract Answer (`extract_answer`)**:
   - This node extracts the final answer from the generated response. It parses the generated text to find the specific answer to the user's question.

8. **End Node (`__end__`)**:
   - This is the final point of the workflow, marking the completion of the process. The final answer is provided as the output.

## Findings & Shortcomings
One of the biggest flaws of the model is the retrieval system. as we are only getting 24.14% recall which is the limiting factor for getting high correctness answers downstream. So this should be the main focus on [further improvements](#todo).

More experiments with larger LLMs are needed to make any assessments of the post-retrieval part of the pipeline. For the easy variant of the problem, With a Llama3.1-8B-Storm model we can achieve ~61.86% high correctness rate which roughly aligns with the expectations given the model size.

### Evaluation Results
#### Easy variant

From the first 120 `train.json` examples:

| Metric                    | Value          |
|---------------------------|----------------|
| **Average Correctness**    | 71.09%         |
| **High Correctness Rate**  | 61.86%         |
| **Mean Latency (RTX 3090)**| 14.64s         |

You can find row-wise evaluation details in [experiments/eval_easy.csv](experiments/eval_easy.csv)

#### Hard Variant

From the first 120 `train.json` examples:

| Metric                    | Value          |
|---------------------------|----------------|
| **Average Correctness**    | 39.36%         |
| **High Correctness Rate**  | 25.89%         |
| **Mean Retrieval Precision** | 2.10%       |
| **Mean Retrieval Recall**  | 26.45%         |
| **Mean Reranker Precision**| 7.71%          |
| **Mean Reranker Recall**   | 23.14%         |
| **Mean Latency (RTX 3090)**| 23.17s         |

You can find row-wise evaluation details in [experiments/eval_hard.csv](experiments/eval_hard.csv)

### Context extraction experiment
- **Context Extraction**: Using a context extraction step resulted in a significant recall loss without sufficient gains in precision. **Decision:** Removed the context extraction step.
- **Reranking Step**: The reranking step significantly reduces the amount of context while barely sacrificing recall, making it a valuable addition. **Decision:** Keeping the reranking step.

#### Results
Below are some results with an older version of the model on the first 100 samples from `train.json`, vector db also only had the same 100 samples. Change is calculated relative to the previous step: retrieval -> reranker -> context extraction.

| Metric                               | Value (%) | Change (%)        |
|--------------------------------------|-----------|-------------------|
| Mean Retrieval Precision             | 2.58      | -                 |
| Mean Retrieval Recall                | 31.15     | -                 |
| Mean Reranking Precision             | 9.84      | +7.25             |
| Mean Reranking Recall                | 29.51     | -1.64             |
| Mean Context Extraction Precision    | 12.84     | +3.01             |
| Mean Context Extraction Recall       | 19.67     | -9.84             |


## Prerequisites
- Python 3.12
- [Poetry](https://python-poetry.org/docs/#installation)
- OpenAI (or OpenAI compatible) API access. I have used vLLM with [Llama-3.1-8B-Storm (Q8_0 GGUF)](https://huggingface.co/akjindal53244/Llama-3.1-Storm-8B-GGUF?show_file_info=Llama-3.1-Storm-8B.Q8_0.gguf).
- Cohere API Access. You can get free trial keys from [cohere.com](https://cohere.com)
- Langfuse. You can either get free access from [cloud.langfuse.com](https://cloud.langfuse.com) or you can self-host it.
  
## Installation
1. Install dependencies: `poetry install`
2. Download data: `sh get_data.sh`
3. Set your `.env` with the correct urls/keys for LLM, Cohere, Langfuse. See [.env.example](.env.example) for reference.

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
- **Code Refactor**: Improve code structure and readability through refactoring, comments, dockerization, reorganization of project structure, addition of unit tests, logging.
- **Fine-Tuning Models**: Experiment with fine-tuning language models specifically on financial documents to improve performance.

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

## Observability
Langfuse was used to add an LLM observability platform, with experiment tracking. It was not necessary but I wanted to try it. See Langfuse documentation on how to use it. They have both free cloud and self-hosted offerings.
