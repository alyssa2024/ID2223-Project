import json

class IntentRouter:
    def __init__(self, llm):
        self.llm = llm

    def route(self, query: str) -> str:
        """
        Determine the intent of the user query.
        Returns one of: 'GREETING', 'RAG_SEARCH', 'GENERAL_KNOWLEDGE'
        """
        
        prompt = f"""
You are a query classifier for a Medical Research Agent.
Classify the following user query into exactly one of these categories:

1. **GREETING**: Simple hellos, goodbyes, or polite chitchat (e.g., "hi", "how are you", "thanks").
2. **SELF_INFO**: Questions about who you are or your capabilities (e.g., "what can you do?", "who created you?").
3. **RAG_SEARCH**: Specific questions regarding medical research, papers, physiological signals, ECG, PCG, or data analysis. This requires retrieving documents.
4. **GENERAL_KNOWLEDGE**: Questions that don't need papers but need general knowledge (e.g. "What is Python?", "Write a poem").

User Query: "{query}"

Output ONLY the category name (e.g., RAG_SEARCH). Do not output explanation.
""".strip()

        response = self.llm(prompt).strip().upper()

        valid_intents = {"GREETING", "SELF_INFO", "RAG_SEARCH", "GENERAL_KNOWLEDGE"}
        
        cleaned_response = response.replace('"', '').replace("'", "").replace(".", "")
        
        if cleaned_response in valid_intents:
            return cleaned_response
        
        return "RAG_SEARCH"