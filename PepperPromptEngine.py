import json
import re

class PepperPromptEngine:
    def __init__(self):
        # Load domain terminology library
        with open("navigation_params.json") as f:
            self.domain_terms = json.load(f)
            
        # Initialize conversation memory
        self.context_buffer = []
    
    def _enhance_semantics(self, text):
        """Semantic enhancement processing"""
        # Term replacement
        for term in self.domain_terms:
            text = re.sub(term["pattern"], f"<{term['type']}>{term['std']}</{term['type']}>", text)
        return text
    def _generate_prompt(self, input_text):
        """Generate structured prompt"""
        enhanced_text = self._enhance_semantics(input_text)
        return f"""**Input Instruction**: {enhanced_text}
        **Return Format Requirements**: Must be compact pure JSON format. No explanatory text should be added before or after the JSON    structure, and code block markers (such as ```json or ```) are prohibited.
        - Do not return empty objects. When no atomic tasks are found, return the following content:
          {{"action": "answer", "params": {{"response": "Sorry, I cannot complete the task"}}}}
        """
    def _validate_command(self, command):
        """Command validation"""
        # JSON Schema validation
        required_params = {
            "move": ["x", "y", "theta"],
            "answer": ["response"]
        }
        action = command["action"]
        missing = [p for p in required_params.get(action, []) 
                  if p not in command["params"]]
        
        # Safety parameter check
        if action == "move" and command["params"].get("speed", 0) > 1.0:
            raise ValueError("Navigation speed exceeds safety threshold")
            
        return not missing
    def extract_json_from_text(self,text):
        # 去掉换行符和空格
        text = text.strip()
        # 找到JSON的开始位置（第一个 '{' 或 '['）
        start = 0
        for i, char in enumerate(text):
            if char in ['{', '[']:
                start = i
                print(f"{i}")
                break
        
        # 找到JSON的结束位置（最后一个 '}' 或 ']'）
        end = 0
        i=0
        stack = []
        for i, char in enumerate(text[start:]):
            if char in ['{', '[']:
                stack.append(char)
            elif char in ['}', ']']:
                if stack:
                    stack.pop()
                    end=i
                else:
                    
                    print(f"\n{i}")
                    break
        end = end + start
        # 提取JSON部分
        json_content = text[start:end+1]
        return json_content

    def _complete_parameters(self, command):
        """Parameter auto-completion"""
        # Coordinate completion logic
        if "x" not in command["params"]:
            last_pos = self.context_buffer[-1]["params"] if self.context_buffer else {"x": 0, "y": 0}
            return {**command["params"], "x": last_pos["x"] + 0.5}
            
        return command["params"]
