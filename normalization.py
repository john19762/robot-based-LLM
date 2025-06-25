from openai import OpenAI
import re
import time

class Boss:
    # Initialization module
    def __init__(self, api_key: str, model: str ):   
        self.model = model  # Model
        self.client = OpenAI(api_key=api_key, base_url="https://api.chatanywhere.tech/v1")       
    def task_normalization(self, task_description):
        """
        Use the large model to break down complex tasks
        """
        print("Task--->\n")
        sys_prompt = f"""
        You are a senior language analysis expert, especially skilled in synonym and near-synonym normalization. 
        **Please convert the following input text:
        {task_description} 
        into a unified format and semantic executable task description, and perform context disambiguation(Remember the keywords from the last 3 rounds of conversation ,automatically extract entity nouns.Perform coreference resolution)
        Finally, output only the result directly, without any explanation, thought process, or additional text. The answer format must be: Task: [content]**
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": task_description}
            ],
            temperature=0.3
        )
        tasktext = response.choices[0].message.content
        cleaned_response = re.sub(r'<think>.*?</think>', '', tasktext, flags=re.DOTALL)
        tasktext = cleaned_response.strip()
        print(f"{tasktext}")  
