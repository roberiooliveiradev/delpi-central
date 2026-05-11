class KnowledgeError(Exception):
    code = "knowledge.error"
    message = "Knowledge error"


class InvalidKnowledgeDocumentInputError(KnowledgeError):
    code = "knowledge.invalid_input"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class KnowledgeDocumentNotFoundError(KnowledgeError):
    code = "knowledge.document_not_found"

    def __init__(self, message: str = "Knowledge document not found"):
        self.message = message
        super().__init__(message)
