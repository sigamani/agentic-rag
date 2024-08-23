from utils import create_question_to_document_map

class RelevantDocumentRetriever:
    def __init__(self, data_path: str, limit: int = None):
        self.q2d = create_question_to_document_map(data_path, limit=limit)

    def __call__(self, question):
        return self.q2d[question]
    
    def query(self, question):
        return self.q2d[question]