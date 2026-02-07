from langchain_core.prompts import PromptTemplate

def get_anime_prompt():
    template = """
You are an expert anime recommender system. Your goal is to provide highly personalized suggestions based ONLY on the provided context.

### INSTRUCTIONS:
1. Suggest exactly 3 anime titles from the context that best match the user's request.
2. Your response MUST follow this exact structure:
   - First line: Title 1, Title 2, Title 3 (Just the names, separated by commas).
   - Then, provide a detailed breakdown for each:
     * **[Title]**
     * **Plot:** (2-3 concise sentences)
     * **Why it matches:** (A clear explanation based on the user's specific request)

### RULES:
- If the context doesn't contain enough information, say "I don't have enough data to make a recommendation."
- Do not use any introductory text like "Here are your recommendations."
- Start immediately with the comma-separated list of titles.

Context:
{context}

User's Query:
{question}

Your Structured Response:
"""

    return PromptTemplate(
        template=template.strip(), 
        input_variables=["context", "question"]
    )