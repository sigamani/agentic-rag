"""
Generate a visual data flow diagram for the Financial RAG Assistant pipeline.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_data_flow_diagram():
    """Create a comprehensive data flow diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    colors = {
        'input': '#E3F2FD',      # Light Blue
        'processing': '#FFF3E0',  # Light Orange
        'llm': '#F3E5F5',        # Light Purple
        'retrieval': '#E8F5E8',   # Light Green
        'output': '#FFEBEE',      # Light Red
        'state': '#F9F9F9',      # Light Gray
        'arrow': '#666666'        # Gray
    }
    
    # Helper function to create boxes
    def create_box(x, y, width, height, text, color, ax):
        box = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(box)
        ax.text(x + width/2, y + height/2, text, 
                ha='center', va='center', fontsize=10, fontweight='bold')
        return box
    
    # Helper function to create arrows
    def create_arrow(start_x, start_y, end_x, end_y, label="", ax=ax):
        arrow = ConnectionPatch(
            (start_x, start_y), (end_x, end_y), 
            "data", "data",
            arrowstyle="->", 
            shrinkA=5, shrinkB=5,
            mutation_scale=20,
            fc=colors['arrow'],
            ec=colors['arrow'],
            linewidth=2
        )
        ax.add_patch(arrow)
        if label:
            mid_x, mid_y = (start_x + end_x) / 2, (start_y + end_y) / 2
            ax.text(mid_x, mid_y + 0.15, label, ha='center', va='center', 
                   fontsize=8, style='italic', color=colors['arrow'])
    
    # Title
    ax.text(5, 9.5, 'Financial RAG Assistant - Data Flow Architecture', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    # === INPUT LAYER ===
    user_input = create_box(0.5, 8, 2, 0.8, "User Question\n(Financial Query)", colors['input'], ax)
    
    # === PYDANTIC STATE MANAGEMENT ===
    state_box = create_box(8, 8, 1.5, 0.8, "AgentState\n(Pydantic v2)", colors['state'], ax)
    
    # === WORKFLOW NODES ===
    
    # 1. Extract Question
    extract_q = create_box(0.5, 6.5, 2, 0.8, "1. Extract Question\n(HumanMessage → str)", colors['processing'], ax)
    
    # 2. Generate Queries  
    gen_queries = create_box(0.5, 5, 2, 0.8, "2. Generate Queries\n(LLM → 3 search terms)", colors['llm'], ax)
    
    # 3. Retrieval System
    retrieval_box = create_box(3.5, 5, 2.5, 0.8, "3. Document Retrieval\n(Vector Search)", colors['retrieval'], ax)
    
    # 4. Reranking (Optional)
    rerank_box = create_box(6.5, 5, 2, 0.8, "4. Reranking\n(Cohere/Mock)", colors['retrieval'], ax)
    
    # 5. Context Generation
    context_gen = create_box(3.5, 3.5, 2.5, 0.8, "5. Context Assembly\n(format_docs)", colors['processing'], ax)
    
    # 6. LLM Generation
    llm_gen = create_box(0.5, 2, 2, 0.8, "6. Generate Response\n(Financial Reasoning)", colors['llm'], ax)
    
    # 7. Answer Extraction
    extract_ans = create_box(0.5, 0.5, 2, 0.8, "7. Extract Answer\n(<ANSWER> tags)", colors['output'], ax)
    
    # === DATA STORES ===
    
    # Mock LLM
    mock_llm = create_box(3.5, 0.5, 2, 0.8, "Mock LLM\n(Financial Responses)", colors['llm'], ax)
    
    # Mock Vector Store
    mock_vector = create_box(6.5, 2, 2, 1.5, "Mock Vector Store\n\n• Financial docs\n• Cash flow data\n• Revenue analysis", colors['retrieval'], ax)
    
    # === ARROWS AND DATA FLOW ===
    
    # Main flow
    create_arrow(1.5, 8, 1.5, 7.3, "question", ax)
    create_arrow(1.5, 6.5, 1.5, 5.8, "extracted_q", ax)
    create_arrow(2.5, 5.4, 3.5, 5.4, "queries[]", ax)
    create_arrow(6, 5.4, 6.5, 5.4, "docs[]", ax)
    create_arrow(5, 4.6, 5, 4.3, "ranked_docs", ax)
    create_arrow(3.5, 3.9, 2.5, 2.4, "context", ax)
    create_arrow(1.5, 2, 1.5, 1.3, "generation", ax)
    
    # LLM connections
    create_arrow(1.5, 5, 3.5, 1.3, "query_prompt", ax)
    create_arrow(1.5, 2, 3.5, 1.3, "reasoning_prompt", ax)
    
    # Vector store connection
    create_arrow(4.5, 5, 6.5, 3.5, "similarity_search", ax)
    
    # State management arrows
    create_arrow(2.5, 8.4, 8, 8.4, "state updates", ax)
    
    # === LEGEND ===
    legend_elements = [
        mpatches.Patch(color=colors['input'], label='Input/Output'),
        mpatches.Patch(color=colors['processing'], label='Processing'),
        mpatches.Patch(color=colors['llm'], label='LLM Operations'),
        mpatches.Patch(color=colors['retrieval'], label='Retrieval System'),
        mpatches.Patch(color=colors['state'], label='State Management')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 0.95))
    
    # === ANNOTATIONS ===
    
    # Add flow annotations
    ax.text(0.2, 4, "WORKFLOW\nPIPELINE", rotation=90, ha='center', va='center', 
           fontsize=12, fontweight='bold', color='navy')
    
    ax.text(9.5, 4, "EXTERNAL\nSYSTEMS", rotation=90, ha='center', va='center', 
           fontsize=12, fontweight='bold', color='darkgreen')
    
    # Add technical details
    tech_details = """
    Technical Stack:
    • LangGraph: Workflow orchestration
    • Pydantic v2: Type-safe state management  
    • uv: Package management
    • Mock system: Testing without dependencies
    • PyTorch: ML backend (macOS Metal)
    """
    
    ax.text(7.5, 0.5, tech_details, ha='left', va='bottom', fontsize=9, 
           bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('financial_rag_dataflow.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

def create_state_diagram():
    """Create a detailed AgentState data structure diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'AgentState (Pydantic v2) - Data Structure', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    # State fields
    fields = [
        ("messages", "Sequence[BaseMessage]", "Chat conversation history"),
        ("steps", "List[str]", "Processing step log"),
        ("question", "str", "User's financial question"),
        ("queries", "List[str]", "Generated search queries"),
        ("documents", "List[Document]", "Retrieved documents"),
        ("reranked_documents", "List[Document]", "Relevance-ranked docs"),
        ("context", "str", "Assembled context text"),
        ("prompt", "str", "LLM input prompt"),
        ("generation", "str", "LLM response"),
        ("answer", "str", "Final extracted answer"),
        ("sources", "List[str]", "Source document IDs")
    ]
    
    # Create state box
    state_box = FancyBboxPatch(
        (1, 1), 8, 7.5,
        boxstyle="round,pad=0.2",
        facecolor='#F0F8FF',
        edgecolor='black',
        linewidth=2
    )
    ax.add_patch(state_box)
    
    # Add fields
    y_pos = 8
    for field_name, field_type, description in fields:
        ax.text(1.5, y_pos, f"• {field_name}:", fontweight='bold', fontsize=11)
        ax.text(3.5, y_pos, f"{field_type}", fontfamily='monospace', fontsize=10, color='blue')
        ax.text(1.7, y_pos - 0.2, f"  └─ {description}", fontsize=9, style='italic', color='gray')
        y_pos -= 0.65
    
    # Add validation features
    validation_text = """
    Pydantic v2 Features:
    ✓ Runtime type validation
    ✓ Field constraints & descriptions  
    ✓ Serialization/deserialization
    ✓ IDE autocompletion support
    """
    ax.text(1.5, 0.5, validation_text, fontsize=10, 
           bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('agent_state_structure.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return fig

if __name__ == "__main__":
    print("🎨 Generating Financial RAG Data Flow Diagrams...")
    
    # Create main data flow diagram
    print("📊 Creating main data flow diagram...")
    fig1 = create_data_flow_diagram()
    
    # Create state structure diagram  
    print("🏗️ Creating AgentState structure diagram...")
    fig2 = create_state_diagram()
    
    print("✅ Diagrams saved as:")
    print("   • financial_rag_dataflow.png")
    print("   • agent_state_structure.png")