from openai import OpenAI
import re
import time

class Boss:
    # Initialization module
    def __init__(self, api_key: str, model: str ):   
        self.model = model  # Model
        self.client = OpenAI(api_key=api_key, base_url="https://api.chatanywhere.tech/v1")
    def dialogue_mode(self, text):
        """
        Large model configuration
        """
        print("Dialogue--->\n")
        # Dialogue role setting
        sys_prompt = """
        You are now a knowledgeable and skilled conversationalist with the following characteristics:
        1. Broad knowledge base, capable of answering a variety of academic, technological, and cultural questions
        2. Friendly and natural language style, occasionally incorporating appropriate humor
        3. Concise and to the point, keeping responses within 3-5 sentences
        4. Honest about uncertainty, not fabricating answers for unknown questions
        5. Context continuity: Remember keywords from the last 3 rounds of conversation (automatically extract entity nouns)
        """            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        saytext = response.choices[0].message.content
        cleaned_response = re.sub(r'<think>.*?</think>', '', saytext, flags=re.DOTALL)
        saytext = cleaned_response.strip()
        chat_data = {
            "action": "answer",
            "params": {
                "response": saytext
            }
        }   
