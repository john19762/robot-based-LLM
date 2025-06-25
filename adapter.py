from openai import OpenAI
import json
from PepperPromptEngine import PepperPromptEngine

class DeepSeekAdapter:
    def __init__(self, api_key: str, model: str ):
        self.model = model    
        self.client = OpenAI(api_key=api_key, base_url="https://api.chatanywhere.tech/v1")
        self.system_prompt = """You are the control center for a Pepper robot. Please convert user commands into a JSON format that strictly follows the rules below:
        **Pepper Robot Control Hub Instruction Conversion Rules**
        **1. Action Mapping Rules:**
        - Detect movement-related verbs (e.g., "walk," "move," "turn") → Map to `move` action
        - Detect location-related nouns or navigation verbs (e.g., "take me to", "go to","directions to") → Map to `navigate` action
        - Detect exploration-related verbs (e.g., "explore," "check") → Map to `explore` action
        - Detect volume adjustment verbs (e.g., "increase volume," "decrease volume") → Map to `set_volume` action
        - Detect lighting adjustment verbs (e.g., "light up," "turn off lights") → Map to `set_led` action
        - Detect gesture-related verbs (e.g., "wave," "bow") → Map to `perform_gesture` action
        - If the action cannot be clearly parsed → Default to `answer` action

        **2. Parameter Parsing Rules:**
        - **move Action:**
          - Must include and only include three parameters: `x` (meters), `y` (meters), `theta` (radians, 0 indicates forward direction)
          - Default value: `y=0` (if no lateral displacement is specified by the user)
          - Example: `Move forward 1 meter` → `{"action": "move", "params": {"x": 1, "y": 0, "theta": 0}}`
        - **perform_gesture Action:**
          - Must include and only include one parameter: `name` (limited to: "wave", "bow", "reset")
          - Example: `Wave` → `{"action": "perform_gesture", "params": {"name": "wave"}}`
        - **Other Action Parameters:**
          - `navigate` → Must include `location` (string)
          - `explore` → Must include `radius` (float)
          - `set_volume` → Must include `level` (float between 0.0 and 1.0)
          - `set_led` → Must include `color` (limited to: "red", "green", "blue", "yellow", "white")

        **3. Format Requirements:**
        - Strictly follow the single JSON object format; arrays are prohibited
        - No extra parameters or missing required parameters
        - Parameter types must comply with constraints (e.g., `theta` must be a float, `level` must be a float between 0.0 and 1.0)
        - The `move` action must not include the `name` parameter

        **4. Error Example Correction:**
        - ❌ Incorrect: `Move forward` → `{"action": "move", "params": {"x": 1, "name": "forward"}}`
        - ✅ Correct: `Move forward` → `{"action": "move", "params": {"x": 1, "y": 0, "theta": 0}}`

        **5. Default Value Supplement Rules:**
        - When the user does not explicitly specify certain parameters, default values are automatically filled based on the action type:
          - `move` action: `y=0` (no lateral displacement)
          - `navigate` action: `location="current position"` (if no location is specified)
          - `set_volume` action: `level=0.5` (default medium volume)
          - `set_led` action: `color="white"` (default color)

        **6. Special Case Handling:**
        - If the user instruction cannot be fully parsed, return the `answer` action and include the unparsed part as the `response` parameter
          - Example: `I don't know how to operate` → `{"action": "answer", "params": {"response": "Please provide a clearer instruction"}}`

        **7. Output Template:**
        {
          "action": "move|answer|navigate|explore|set_volume|set_led|perform_gesture",
          "params": {
            "x": float, 
            "y": float,
            "theta": float,
            "radius": float,
            "response": "natural language response",
            "location": "location name",
            "level": float(0.0-1.0),
            "color": "red|green|blue|yellow|white",
            "name": "wave|bow|reset"
          }
        }

        **8. Examples:**
        - User Instruction: `Take me to the meeting room`
          - Output: `{"action": "navigate", "params": {"location": "meeting room"}}`
        - User Instruction: `Increase the volume to maximum`
          - Output: `{"action": "set_volume", "params": {"level": 1.0}}`
        - User Instruction: `Light up the red light`
          - Output: `{"action": "set_led", "params": {"color": "red"}}`
        """  
    def parse_command(self, text):
        # Call the API only once
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        engine=PepperPromptEngine()
        raw_content=engine.extract_json_from_text(response.choices[0].message.content) 

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as e:
            return self._error_response(f"JSON parsing failed: {str(e)}")

        # Handle array responses (should not occur)
        if isinstance(parsed, list):
            if len(parsed) == 0:
                return self._error_response("Received empty array response")
            parsed = parsed[0]

        return self._validate_output(parsed)

    def _error_response(self, message):
        return {
            "action": "answer",
            "params": {"response": f"System error: {message}"}
        }


    def _validate_output(self, command):
        # Parameter range validation
        if command["action"] == "set_volume":
            level = command["params"].get("level", 0.5)
            command["params"]["level"] = max(0.0, min(1.0, level))
        return command
