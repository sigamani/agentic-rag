# ConvFinQA

TODO:
- Improve retrieval (Hybrid Search, finance embedding models, HyDe, embedding models)
- langfuse dataset run does not show input/output, also each input has its own empty col?
- Replace XML in prompts with something better (YAML?)


## Observations
Using context extraction step is not worth the recall loses. **Decision:** Took it out.
Using reranking step, significantly reduces the amount of context while barely sacrificing recall. **Decision:** Keeping it in.

See eval results below:

Mean Retrieval Precision: 2.58%
Mean Retrieval Recall: 31.15%
Mean Reranker Precision: 9.84% (+7.25%)
Mean Reranker Recall: 29.51% (-1.64%)
Mean Context Precision: 12.84% (+3.01%)
Mean Context Recall: 19.67% (-9.84%)