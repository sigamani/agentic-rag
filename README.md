# Financial RAG Test Workflow

A streamlined ConvFinQA RAG (Retrieval-Augmented Generation) testing pipeline using mock dependencies for rapid development and validation. This refactored codebase focuses on testing workflow functionality with minimal external dependencies.

## 🏗️ Architecture Overview

![Data Flow Diagram](financial_rag_dataflow.png)

### Core Components

- **LangGraph Workflow**: Multi-node graph orchestrating the complete RAG pipeline
- **Pydantic v2 State**: Type-safe state management with validation and constraints  
- **Mock System**: Complete testing without external LLM/vector DB dependencies
- **Minimal Dependencies**: Only 4 essential packages for cross-platform compatibility

### Data Flow Pipeline

```
User Question → Extract Question → Generate Queries → Document Retrieval → 
Context Assembly → LLM Generation → Answer Extraction → Final Answer
```

1. **Question Extraction** → Extract user question from input messages
2. **Query Generation** → Generate 3 search queries using mock LLM
3. **Document Retrieval** → Mock vector similarity search with financial document stubs
4. **Context Assembly** → Format retrieved documents into structured context
5. **LLM Generation** → Mock financial reasoning with step-by-step analysis
6. **Answer Extraction** → Parse final answer from mock LLM response

![AgentState Structure](agent_state_structure.png)

## 📁 Project Structure

```
financial-rag-test/
├── test_workflow.py          # Main end-to-end test runner
├── config.py                # Pydantic v2 configuration schema
├── requirements.txt          # Minimal cross-platform dependencies
├── workflow/
│   ├── state.py             # Pydantic v2 AgentState model
│   └── nodes_test.py        # Test workflow nodes with mock dependencies
├── models/
│   └── llm_stub.py          # Mock LLM for testing
├── data/
│   └── retrieve_stub.py     # Mock document retrieval system
└── utils/
    ├── prompts.py           # Prompt templates
    └── utils.py             # Utility functions
```

## 📦 Installation

### Quick Setup with uv (Recommended)

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt
```

### Traditional Setup

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies (Only 4 packages!)

- **pydantic>=2.0.0** - Type-safe configuration and state management
- **langchain-core>=0.1.0** - Core LangChain components (messages, documents)
- **langgraph>=0.0.30** - Workflow orchestration framework
- **python-dotenv>=1.0.0** - Environment variable handling

## 🧪 Testing

### Run Complete End-to-End Test

```bash
python test_workflow.py
```

This comprehensive test validates:

- ✅ **Individual Node Testing** - Each workflow component in isolation
- ✅ **Full Pipeline Execution** - Complete end-to-end workflow
- ✅ **Multiple Question Types** - Various financial question formats
- ✅ **Mock System Integration** - No external dependencies required
- ✅ **Pydantic v2 State Management** - Type-safe state transitions

### Expected Output

```
🚀 Starting Financial RAG Workflow End-to-End Tests
============================================================
🧪 Testing individual workflow nodes...

1️⃣ Testing extract_question...
   ✓ Extracted question: What was the percentage change in the net cash fro...

2️⃣ Testing generate_queries...
   ✓ Generated 3 queries

3️⃣ Testing retrieve...
   ✓ Retrieved 5 documents
   ✓ Context length: 603 characters

4️⃣ Testing generate...
   ✓ Generated response

5️⃣ Testing extract_answer...
   ✓ Final answer: 29.31%

✅ All individual nodes working!

🔄 Testing complete workflow pipeline...
✅ Complete workflow successful!

🔬 Testing with different question types...
✅ Multiple question types working!

============================================================
🎉 ALL TESTS PASSED!
✅ The financial RAG workflow is working end-to-end
📊 Final test result: 29.31%
```

## 🔧 Configuration

The system uses Pydantic v2 for type-safe configuration in `config.py`:

```python
class GraphConfig(BaseModel):
    retrieval_k: int = 5          # Documents to retrieve
    rerank_k: int = 3             # Documents to rerank  
    max_tokens: int = 4096        # Max generation tokens
    temperature: float = 0.0      # Generation temperature
    top_p: float = 0.9           # Top-p sampling
```

## 🏷️ Mock System Details

### Mock LLM (`models/llm_stub.py`)
- Generates realistic financial reasoning responses
- Supports structured output with `<ANSWER>` tags
- No external API calls required

### Mock Retrieval (`data/retrieve_stub.py`)
- Returns relevant financial document stubs
- Simulates vector similarity search
- Provides consistent test data

## 🚀 Development Benefits

- **⚡ Fast Testing**: No external API calls or model downloads
- **🔄 Reproducible**: Consistent mock responses for reliable testing
- **🌐 Cross-Platform**: Works identically on macOS and Ubuntu
- **📦 Minimal**: Only 4 dependencies reduce installation complexity
- **🔒 Type-Safe**: Pydantic v2 ensures data validation throughout

## 🛠️ Use Cases

This streamlined codebase is perfect for:

- **Rapid Prototyping**: Test workflow logic without infrastructure setup
- **CI/CD Integration**: Fast, reliable automated testing
- **Development**: Iterate on workflow design with immediate feedback
- **Education**: Understand RAG pipeline architecture with clear examples

## 📚 Citation & Credits

- Built using **LangGraph** for workflow orchestration
- **Pydantic v2** for type-safe state management  
- **LangChain Core** for message and document handling
- Original ConvFinQA dataset concept for financial reasoning tasks

## 🛠️ Maintainer

**Michael Sigamani**  
[github.com/sigamani](https://github.com/sigamani)  
Licensed under Apache 2.0

---

*This is a refactored, test-focused version of a larger financial RAG system. The complete implementation with training, evaluation, and production components has been streamlined to focus on core workflow testing functionality.*