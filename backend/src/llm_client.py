from typing import List, Dict, Any, Optional
import ollama
import json

class LLMClient:
    """
    Client for interacting with Local LLM (Ollama) to generate code and insights.
    """
    def __init__(self, model_name: str = "llama3"):
        self.model = model_name
        self.system_prompt = """
        You are Opal, an expert Data Analyst and Visualization Architect.
        Your goal is to help users analyze their datasets by generating valid Vega-Lite JSON specifications or Python Pandas code snippets.
        
        You have access to the dataset schema (columns and types).
        
        RULES:
        1. When asked to PLOT/VISUALIZE: Output a JSON object with a "type" of "chart" and a "spec" containing the Vega-Lite V5 spec.
           - INFER the best chart type (Bar, Line, Scatter, etc.) based on the data.
           - HANDLE aggregations intelligently (e.g., if plotting Products (categorical) vs Date (time), you typically want COUNT of products).
           - Do NOT assume exact column names; try to match phonetically but use the EXACT codes provided in the schema.
        
        2. When asked for STATS/TRENDS: Output a JSON object with a "type" of "analysis" and a "content" string describing the answer.
        
        3. If you cannot fulfill the request: Output a JSON object with a "type" of "error" and a "message" explaining why.
        
        OUTPUT FORMAT must be pure JSON, no markdown fencing.
        """

    def query(self, user_query: str, schema_info: Dict[str, str], history: List[Dict] = []) -> Dict[str, Any]:
        """
        Sends query to Ollama and parses the JSON response.
        """
        schema_str = ", ".join([f"{k} ({v})" for k, v in schema_info.items()])
        
        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': f"Dataset Schema: [{schema_str}]"}
        ]
        
        # Append history
        for msg in history:
            role = 'assistant' if msg['type'] == 'bot' else 'user'
            messages.append({'role': role, 'content': msg['text']})
            
        messages.append({'role': 'user', 'content': f"Current Request: {user_query}. Remember to respond in JSON."})
        
        print(f"🧠 Opal (LLM): Sending query to {self.model}...")
        try:
            response = ollama.chat(model=self.model, messages=messages)
            content = response['message']['content']
            
            # Simple cleanup to remove potential markdown code blocks if the model ignores instruction
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
            
        except Exception as e:
            print(f"❌ Opal (LLM) Error: {e}")
            return {
                "type": "error", 
                "message": f"I tried to analyze that with my new brain, but something went wrong: {str(e)}"
            }

    def generate_tableau_metadata(self, schema_info: Dict[str, str]) -> str:
        """
        Ask LLM to generate XML content for .tds file based on schema? 
        Or just simple rule-based is better. Let's stick to rule-based for .tds 
        and use LLM only for analysis for now.
        """
        pass
