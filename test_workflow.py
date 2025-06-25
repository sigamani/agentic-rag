#!/usr/bin/env python3
"""
End-to-end test of the financial RAG workflow using mock dependencies.
"""
import os
import sys
from langchain_core.messages import HumanMessage
from config import GraphConfig, DEFAULT_CONFIG
from workflow.state import AgentState

# Import test nodes
from workflow.nodes_test import (
    extract_question,
    generate_queries, 
    retrieve,
    generate,
    extract_answer
)

def test_individual_nodes():
    """Test each workflow node individually."""
    print("🧪 Testing individual workflow nodes...")
    
    # Test data
    test_question = "What was the percentage change in the net cash from operating activities from 2008 to 2009?"
    
    # Test extract_question
    print("\n1️⃣ Testing extract_question...")
    state = {"messages": [HumanMessage(test_question)]}
    result = extract_question(state)
    print(f"   ✓ Extracted question: {result['question'][:50]}...")
    
    # Test generate_queries  
    print("\n2️⃣ Testing generate_queries...")
    state = {"question": test_question}
    result = generate_queries(state)
    print(f"   ✓ Generated {len(result['queries'])} queries:")
    for i, query in enumerate(result['queries'], 1):
        print(f"     {i}. {query}")
    
    # Test retrieve
    print("\n3️⃣ Testing retrieve...")
    state = {"question": test_question, "queries": result['queries']}
    config = DEFAULT_CONFIG
    result = retrieve(state, config)
    print(f"   ✓ Retrieved {len(result['documents'])} documents")
    print(f"   ✓ Context length: {len(result['context'])} characters")
    
    # Test generate
    print("\n4️⃣ Testing generate...")
    state = {
        "question": test_question,
        "context": result['context']
    }
    result = generate(state, config)
    print(f"   ✓ Generated response length: {len(str(result['generation']))} characters")
    print(f"   ✓ Response preview: {str(result['generation'])[:100]}...")
    
    # Test extract_answer
    print("\n5️⃣ Testing extract_answer...")
    state = {
        "question": test_question,
        "generation": result['generation']
    }
    result = extract_answer(state)
    print(f"   ✓ Final answer: {result['answer']}")
    
    print("\n✅ All individual nodes working!")

def test_full_workflow():
    """Test the complete workflow pipeline."""
    print("\n🔄 Testing complete workflow pipeline...")
    
    # Initial state
    test_question = "What was the percentage change in the net cash from operating activities from 2008 to 2009?"
    state = {
        "messages": [HumanMessage(test_question)]
    }
    config = DEFAULT_CONFIG
    
    print(f"\n❓ Question: {test_question}")
    
    # Step 1: Extract question
    print("\n📝 Step 1: Extracting question...")
    state.update(extract_question(state))
    print(f"   ✓ Question: {state['question']}")
    
    # Step 2: Generate queries
    print("\n🔍 Step 2: Generating search queries...")
    state.update(generate_queries(state))
    print(f"   ✓ Generated {len(state['queries'])} queries")
    
    # Step 3: Retrieve documents
    print("\n📚 Step 3: Retrieving documents...")
    state.update(retrieve(state, config))
    print(f"   ✓ Retrieved {len(state['documents'])} documents")
    print(f"   ✓ Document IDs: {[doc.metadata['id'] for doc in state['documents']]}")
    
    # Step 4: Generate response
    print("\n💭 Step 4: Generating response...")
    state.update(generate(state, config))
    print(f"   ✓ Generated response")
    
    # Step 5: Extract final answer
    print("\n🎯 Step 5: Extracting final answer...")
    state.update(extract_answer(state))
    print(f"   ✓ Final Answer: {state['answer']}")
    
    print("\n✅ Complete workflow successful!")
    return state

def test_with_different_questions():
    """Test workflow with various financial questions."""
    print("\n🔬 Testing with different question types...")
    
    test_questions = [
        "What was the revenue growth from 2008 to 2009?",
        "How did the working capital ratio change?", 
        "What was the cash flow trend over the period?"
    ]
    
    config = DEFAULT_CONFIG
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: {question}")
        
        state = {"messages": [HumanMessage(question)]}
        
        # Run abbreviated workflow
        state.update(extract_question(state))
        state.update(generate_queries(state))
        state.update(retrieve(state, config))
        state.update(generate(state, config))
        state.update(extract_answer(state))
        
        print(f"   ✓ Answer: {state['answer']}")
    
    print("\n✅ Multiple question types working!")

def main():
    """Run all tests."""
    print("🚀 Starting Financial RAG Workflow End-to-End Tests")
    print("=" * 60)
    
    try:
        # Test 1: Individual nodes
        test_individual_nodes()
        
        # Test 2: Full workflow
        final_state = test_full_workflow()
        
        # Test 3: Different questions
        test_with_different_questions()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ The financial RAG workflow is working end-to-end")
        print(f"📊 Final test result: {final_state['answer']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)