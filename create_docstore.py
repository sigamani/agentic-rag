import json
import logging
import time
import psutil
from pathlib import Path
from langchain_core.documents import Document
from document_ai_agents.document_parsing_agent import (
    DocumentLayoutParsingState,
    DocumentParsingAgent,
)
from document_ai_agents.document_utils import extract_images_from_pdf
from document_ai_agents.image_utils import pil_image_to_base64_jpeg

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to save images to disk
def save_image_to_disk(base64_image, output_directory, image_name):
    """Save a base64 image to the disk."""
    from PIL import Image
    import base64
    from io import BytesIO
    import os

    # Decode the base64 string to bytes
    image_data = base64.b64decode(base64_image)
    output_path = os.path.join(output_directory, f"{image_name}.jpg")
    
    # Write the image data to a file
    with open(output_path, 'wb') as f:
        f.write(image_data)

    logger.info(f"Image saved to {output_path}")
    return output_path

def export_documents_to_jsonl(documents: list[Document], output_path: str):
    """Exports documents to a JSONL file, including image metadata."""
    start_time = time.time()  # Track start time for export
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for doc in documents:
                # Save images if available
                if 'image' in doc.metadata:
                    image_path = save_image_to_disk(doc.metadata['image'], "documents/extract/images", doc.metadata["document_id"])
                    doc.metadata["image_path"] = image_path
                json.dump({"text": doc.page_content, "metadata": doc.metadata}, f)
                f.write("\n")
        elapsed_time = time.time() - start_time
        cpu_usage = psutil.cpu_percent(interval=1)
        logger.info(f"✅ Exported {len(documents)} documents to {output_path}")
        logger.info(f"Processing time: {elapsed_time:.2f} seconds")
        logger.info(f"CPU usage during export: {cpu_usage}%")
    except Exception as e:
        logger.error(f"Error exporting documents to {output_path}: {e}")
        logger.error(f"CPU usage during failure: {psutil.cpu_percent(interval=1)}%")
        raise

def process_pdf_document(document_path: str):
    """Processes the PDF document and returns the parsed document(s) including images."""
    start_time = time.time()  # Track start time for document processing
    state = DocumentLayoutParsingState(document_path=document_path)
    agent = DocumentParsingAgent()
    
    # Extract images from the PDF
    images = extract_images_from_pdf(pdf_path=document_path)
    images_base64 = [pil_image_to_base64_jpeg(img) for img in images]  # Assuming function converts image to base64
    
    # Add images to the state
    state.pages_as_base64_jpeg_images = images_base64

    result = agent.graph.invoke(state)

    elapsed_time = time.time() - start_time
    cpu_usage = psutil.cpu_percent(interval=1)
    logger.info(f"Document processing completed in {elapsed_time:.2f} seconds")
    logger.info(f"CPU usage during processing: {cpu_usage}%")

    return result["documents"]

def main():
    # Path to the document
    document_path = "documents/input/whirlpool_small.pdf"
    output_path = "documents/extract/whirlpool_chunks.jsonl"
    
    # Log the process start
    start_time = time.time()
    logger.info(f"Starting to process document: {document_path}")
    
    try:
        # Process the document with the DocumentParsingAgent, including images
        documents = process_pdf_document(document_path)
        
        # Export the documents to JSONL with images saved to disk
        export_documents_to_jsonl(documents, output_path)
        
        elapsed_time = time.time() - start_time
        cpu_usage = psutil.cpu_percent(interval=1)
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        logger.info(f"Total CPU usage during the entire process: {cpu_usage}%")
        
    except Exception as e:
        logger.error(f"Failed to process: {e}")
        logger.error(f"CPU usage during failure: {psutil.cpu_percent(interval=1)}%")

if __name__ == "__main__":
    main()
