from openai import OpenAI
import re
import time

class Boss:
    # Initialization module
    def __init__(self, api_key: str, model: str ):   
        self.model = model  # Model
        self.client = OpenAI(api_key=api_key, base_url="https://api.chatanywhere.tech/v1")
        
    def determine_task_type(self, user_input):
        """
        Call the large model to determine the task type
        Return: "dialogue" or "task"
        """
        sys_prompt = f"""You are an expert in semantic scene judgment,
        Please determine whether the following user input is intended for general conversation with the robot or requires the robot to assist the user in performing a specific task.
        User input: {user_input}
        
        Return only one word:
        - If it is general conversation or question answering, return "dialogue"
        - If it requires the execution of a specific operation or task, return "task"
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3
            )
            decision = response.choices[0].message.content.lower().strip()
            cleaned_response = re.sub(r'<think>.*?</think>', '', decision, flags=re.DOTALL)
            decision = cleaned_response.strip()
            return "task" if "task" in decision else "dialogue"
        except Exception as e:
            print(f"Large model call error: {e}")
            return "dialogue"  # Default to dialogue mode
