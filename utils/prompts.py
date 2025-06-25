from langchain.prompts import PromptTemplate

# Main reasoning and answer prompt used in LangGraph
reason_and_answer_prompt_template = PromptTemplate(
    template="""You are an investment analyst. You will be given: 
    <INSTRUCTIONS>
        You will be provided:
        1. a QUESTION asked by the user
        2. CONTEXT provided by an automated context retrieval system
        
        Your task is to use the CONTEXT to provide a relevant ANSWER to the QUESTION.

        Only answer what the user is asking and nothing else.
        
        Explain your reasoning in a step-by-step manner. Ensure your reasoning and conclusion are correct.

        Avoid simply stating the correct answer at the outset.

        If there is no relevant context provided, state that at the outset.

        At the end of your calculations, provide a section for the final answer submission (must be in-between <ANSWER> and </ANSWER> tags).
    </INSTRUCTIONS>
    <EXAMPLE>
        <INPUT>
            <QUESTION>What is the percentage change in the net cash from operating activities from 2008 to 2009?</QUESTION>
            <CONTEXT>
            In 2008, the net cash from operating activities was $200,000.
            In 2009, the net cash from operating activities was $258,620.
            </CONTEXT>
        </INPUT>
        <OUTPUT>
            <REASONING>
                To calculate the percentage change, we can use the formula:


                Substituting the given values:

                old_value = 200000
                new_value = 258620

                percentage_change = ((258620 - 200000) / 200000) * 100

                percentage_change = (58620 / 200000) * 100

                percentage_change = 0.2931 * 100

                percentage_change = 29.31%

                Therefore, the percentage change in the net cash from operating activities from 2008 to 2009 is 29.31%.
            </REASONING>
            <ANSWER>29.31%</ANSWER>
        </OUTPUT>
    </EXAMPLE>
    <INPUT>
        <QUESTION>{question}</QUESTION>
        <CONTEXT>
        {context}
        </CONTEXT>
    </INPUT>
    """,
    input_variables=["question", "context"],
)

# Answer extraction prompt
extract_anwer_prompt_template = PromptTemplate(
    template="""
    <INSTRUCTIONS>
        You will be provided:
        1. QUESTION: question asked by the user
        2. LONG ANSWER: reasoning steps, followed by a final answer

        Your task is to extract the SHORT ANSWER from the LONG ANSWER

        The short answer should be as concise as possible, while still answering the question.

        Only return the SHORT ANSWER and nothing else.

        If answer is not provided, say "NO ANSWER"
    </INSTRUCTIONS>
    <INPUT>
        <QUESTION>{question}</QUESTION>
        <LONG ANSWER>{generation}</LONG ANSWER>
    </INPUT>
    """,
    input_variables=["question", "generation"],
)

# Context filtering prompt
filter_context_prompt_template = PromptTemplate(
    template="""
    <INSTRUCTIONS>
        You will be provided:
        1. QUESTION: question asked by the user
        2. DOCUMENTS: list of retrieved documents

        Your task is to:
         - pick the relevant DOCUMENTS that can be used to answer the question
         - discard irrelevant DOCUMENTS that provide no useful information to answer the question
         - trim the relevant DOCUMENTS to only include the relevant information needed to answer the question

        Only return the relevant information from the documents and the source douments, nothing else.
        Return in a YAML like format (see example).
        Do not try to produce the answer, only provide the relevant information that should be used to answer the question.
        
    </INSTRUCTIONS>
    <EXAMPLE>
        <INPUT>
            <QUESTION>What is the percentage change in the net cash from operating activities from 2008 to 2009?</QUESTION>
            <DOCS>
                <DOC ID="some-relevant-doc-1">
                The net cash from operating activities in 2008 was $10 million.
                </DOC>
                <DOC ID="some-relevant-doc-2">
                The net cash from operating activities increased by $2 million in 2009.
                </DOC>
                <DOC ID="some-irrelevant-doc-1">
                The company's net revenue from sales in 2009 was $50 million, compared to $45 million in 2008.
                </DOC>
            </DOCS>        
        </INPUT>
        <OUTPUT>
            The net cash from operating activities in 2008 was $10 million.
            The net cash from operating activities increased by $2 million in 2009.
            
            sources:
                - some-relevant-doc-1
                - some-relevant-doc-2
        </OUTPUT>
    </EXAMPLE>
    <INPUT>
        <QUESTION>{question}</QUESTION>
        <DOCS>
        {documents}
        </DOCS>
    </INPUT>
    """,
    input_variables=["question", "documents"],
)

# Query generation prompt
generate_queries_prompt_template = PromptTemplate.from_template(
    """Given this financial question, write 3 search queries that retrieve evidence to answer it.

Question: {question}

Queries:"""
)