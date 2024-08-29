from typing import Optional
from config import DATA_LIMIT_EVAL
from langfuse_config import langfuse
from llm import llm
from graph import graph
import dotenv
from utils import format_prompt, typed_dict_to_dict
from langchain_core.messages import HumanMessage
from llm import MODEL_NAME

from datetime import datetime
import csv

import pandas as pd
from nodes import CHEATING_RETRIEVAL, DISABLE_GENERATION
from prompts import eval_prompt_template
from config import GraphConfig, LANGFUSE_DATASET_NAME

from tqdm.auto import tqdm
import time

dotenv.load_dotenv()


dataset = langfuse.get_dataset(LANGFUSE_DATASET_NAME)
HIGH_CORRECTNESS_THRESHOLD = 0.9

def get_doc_selection_display(retrieved_doc_ids: list[str], expected_doc_id: str) -> str:
    doc_selection_display = ""
    for doc in retrieved_doc_ids:
        if doc == expected_doc_id:
            doc_selection_display += '+' + doc
        else:
            doc_selection_display += doc
        doc_selection_display += ", "
    if expected_doc_id not in retrieved_doc_ids:
        doc_selection_display = '-' + doc
    return doc_selection_display

def relative_score(a, b, power=2) -> float:
    """
    Relative difference between two numbers
    
    We also apply a power penalty to penalize larger differences more.
    """
    if a == b:
        return 1.0
    else:
        return 1 - ((abs(a - b) / max(abs(a), abs(b))) ** power)
    
def retrieval_precision_score(predicted: list[str], expected: str) -> float:
    """
    Number of relevant documents retrieved / number of documents retrieved    
    In case of ConvFinQA, we only have 1 expected document. 
    """

    try:
        return float(expected in predicted) / len(predicted)
    except ZeroDivisionError:
        return 0

def retrieval_recall_score(predicted: list[str], expected: str) -> float:
    """
    Number of relevant documents retrieved / number of relevant documents
    
    In case of ConvFinQA, we only have 1 expected document. 
    So if the document is in the predicted set, we get a recall of 1
    Otherwise, we get a recall of 0
    """
    return float(expected in predicted)


def correctness_score(input: str, predicted: str, expected: str) -> Optional[float]:
    if DISABLE_GENERATION:
        return None
    
    predicted = predicted.lower().strip()
    expected = expected.lower().strip()

    # Base cases, we don't need to use LLM for that 
    if predicted == "" and expected != "":
        return 0
    if predicted != "" and expected == "":
        return None
    if predicted == expected:
        return 1
    
    # Compare numbers, allow for percentages, dollars signs
    try:
        expected_parsed = float(expected.replace('%', 'e-2').replace("$", "").replace(",", "").replace(" ", ""))
        expected_parsed_2 = float(expected.replace('%', '').replace("$", "").replace(",", "").replace(" ", ""))
        predicted_parsed = float(predicted.replace('%', 'e-2').replace("$", "").replace(",", "").replace(" ", ""))
        predicted_parsed_2 = float(predicted.replace('%', '').replace("$", "").replace(",", "").replace(" ", ""))
        return abs(max(
            relative_score(predicted_parsed, expected_parsed),
            relative_score(predicted_parsed_2, expected_parsed_2),
            relative_score(predicted_parsed, expected_parsed_2),
            relative_score(predicted_parsed_2, expected_parsed),
        ))
    except Exception:
        pass

    # Otherwise, use LLM
    print("Using LLM for score generation...")
    prompt = eval_prompt_template.format(question=input, actual_answer=predicted, expected_answer=expected)
    out = llm.completions.create(model=MODEL_NAME, prompt=format_prompt(prompt), max_tokens=10, temperature=0)
    out_text = out.choices[0].text
    out_text = out_text.replace("<OUTPUT>", "").replace("</OUTPUT>", "")
    try:
        float_out = abs(float(out_text))
    except Exception:
        float_out = None # Error
        print(f"Error generating score (generated: {out_text})")
    return float_out

def run_eval():
    answer_correctness_scores = []
    retrieval_precision_scores = []
    retrieval_recall_scores = []
    reranker_precision_scores = []
    reranker_recall_scores = []
    latencies = []
    out = []

    run_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    for item in tqdm(dataset.items[:DATA_LIMIT_EVAL]):
        handler = item.get_langchain_handler(
            run_name=run_name,
            run_description="RAG evaluation with ground-truth documents",
            run_metadata={"model": MODEL_NAME, "cheating_retrieval": CHEATING_RETRIEVAL, "disable_generation": DISABLE_GENERATION},
        )

        inputs = {
            "messages": [
                HumanMessage(item.input),
            ]
        }

        start = time.time()
        output = graph.invoke(inputs, config={"callbacks": [handler], "configurable": typed_dict_to_dict(GraphConfig)})
        latency = time.time() - start
        latencies.append(latency)
        
        question = output['question']
        answer = output['answer']
        generation = output['generation']

        retrieved_doc_ids = [doc.metadata['id'] for doc in output['documents']]
        assert all(retrieved_doc_ids), "Invalid document IDs"
        expected_doc_id = item.metadata['document']['id']

        retrieval_precision = retrieval_precision_score(retrieved_doc_ids, expected_doc_id)
        retrieval_recall = retrieval_recall_score(retrieved_doc_ids, expected_doc_id)

        reranked_doc_ids = [doc.metadata['id'] for doc in output['reranked_documents']]

        reranker_precision = retrieval_precision_score(reranked_doc_ids, expected_doc_id)
        reranker_recall = retrieval_recall_score(reranked_doc_ids, expected_doc_id)

        retrieval_precision_scores.append(retrieval_precision)
        retrieval_recall_scores.append(retrieval_recall)

        reranker_precision_scores.append(reranker_precision)
        reranker_recall_scores.append(reranker_recall)

        # Evaluate the output to compare different runs more easily
        correctness = correctness_score(item.input, answer, item.expected_output)

        # Print input, answer, expected output, and the score in a more readable format
        print(f"Input: {item.input}")
        print(f"Predicted Answer: {answer}")
        print(f"Expected Answer: {item.expected_output}")
        print(f"Retrieved Documents: {retrieved_doc_ids}")
        print(f"Expected Document: {expected_doc_id}")
        print(f"Retrieval Precision: {retrieval_precision:.2%}")
        print(f"Retrieval Recall: {retrieval_recall:.2%}")
        print(f"Reranker Precision: {reranker_precision:.2%} ({reranker_precision - retrieval_precision:+.2%})")
        print(f"Reranker Recall: {reranker_recall:.2%} ({reranker_recall - retrieval_recall:+.2%})")
        print(f"Correctness: {correctness:.2%}") if correctness else print(f"Correctness: {correctness}")
        print(f"Latency: {latency:.2f}s")
        # Show generation for debugging, when retrieval was correct but answer was not
        if not correctness or ((correctness < .5) and (retrieval_recall > 0)):
            print(f"Generation: {generation}")

        print("-"*50)

        handler.trace.update(name="eval", 
                            input=question,
                            output=answer,
                            metadata={"generation": generation,
                                        "documents": output["documents"]})
        if correctness is not None:
            handler.trace.score(
                name="correctness",
                data_type="NUMERIC",
                value=correctness,
                comment=generation,  # reasoning
            )

        # make list of retrieved docs
        # add '+' prefix if the doc was the correct one
        # add no prefix if it was incorrect
        # if no correct docs identfied, add the correct one at the end with '-' prefix 
        retrieval_doc_selection = get_doc_selection_display(retrieved_doc_ids=retrieved_doc_ids, expected_doc_id=expected_doc_id)

        handler.trace.score(
            name="retrieval_precision",
            data_type="NUMERIC",
            value=retrieval_precision,
            comment=retrieval_doc_selection,
        )

        handler.trace.score(
            name="retrieval_recall",
            data_type="BOOLEAN",
            value=retrieval_recall,
            comment=retrieval_doc_selection,
        )

        reranking_doc_selection = get_doc_selection_display(retrieved_doc_ids=retrieved_doc_ids, expected_doc_id=expected_doc_id)

        handler.trace.score(
            name="reranker_precision",
            data_type="NUMERIC",
            value=reranker_precision,
            comment=reranking_doc_selection,
        )

        handler.trace.score(
            name="reranker_recall",
            data_type="BOOLEAN",
            value=reranker_recall,
            comment=reranking_doc_selection,
        )

        answer_correctness_scores.append(correctness)
        retrieval_precision_scores.append(retrieval_precision)
        retrieval_recall_scores.append(retrieval_recall)    

        out.append({"question": question, 
                    "answer": answer, 
                    "generation": generation,
                    "expected_answer": item.expected_output,
                    "correctness": correctness,
                    "retrieval_precision": retrieval_precision,
                    "retrieval_recall": retrieval_recall,
                    "reranker_precision": reranker_precision,
                    "reranker_recall": reranker_recall,
                    "prompt": output["prompt"],
                    "latency": latency,
                    })

        out_df = pd.DataFrame.from_records(out)
        out_df.to_csv("eval.csv", quoting=csv.QUOTE_NONNUMERIC)
        
        print(f"{'='*50}")

        # Print the final average score in a formatted way
        answer_correctness_scores_non_none = [c for c in answer_correctness_scores if c is not None]
        if len(answer_correctness_scores_non_none) > 0:
            mean_correctness_score = sum(answer_correctness_scores_non_none) / len(answer_correctness_scores_non_none)
            print(f"Average Correctness: {mean_correctness_score:.2%}")
            high_correctness_rate = sum(c > HIGH_CORRECTNESS_THRESHOLD for c in answer_correctness_scores_non_none) / len(answer_correctness_scores_non_none)
            print(f"High Correctness Rate: {high_correctness_rate:.2%}")
            
        mean_retrieval_precision_score = sum(retrieval_precision_scores) / len(retrieval_precision_scores)
        mean_retrieval_recall_score = sum(retrieval_recall_scores) / len(retrieval_recall_scores)
        mean_reranker_precision_score = sum(reranker_precision_scores) / len(reranker_precision_scores)
        mean_reranker_recall_score = sum(reranker_recall_scores) / len(reranker_recall_scores)

        print(f"Mean Retrieval Precision: {mean_retrieval_precision_score:.2%}")
        print(f"Mean Retrieval Recall: {mean_retrieval_recall_score:.2%}")
        print(f"Mean Reranker Precision: {mean_reranker_precision_score:.2%} ({mean_reranker_precision_score - mean_retrieval_precision_score:+.2%})")
        print(f"Mean Reranker Recall: {mean_reranker_recall_score:.2%} ({mean_reranker_recall_score - mean_retrieval_recall_score:+.2%})")
        print(f"Mean Latency: {sum(latencies) / len(latencies):.2f}s")
        print(f"{'='*50}")

    # Flush the langfuse client to ensure all data is sent to the server at the end of the experiment run
    langfuse.flush()

if __name__=="__main__":
    run_eval()    


