from openai import OpenAI
import json
from typing import List, Dict, Tuple
import heapq
from PepperPromptEngine import PepperPromptEngine

class TaskPlanner:
    def __init__(self, api_key: str, model: str ):
        """
        Integrated Task Planner
        :param api_key: SiliconFlow API key
        :param model: Model name to use
        """
        self.model = model  # Model
        self.client = OpenAI(api_key=api_key, base_url="https://api.chatanywhere.tech/v1")
        self.tasks = []          # Original task list
        self.optimized_plan = [] # Optimized execution sequence
        self.resource_map = {}   # Resource timeline
        self.executed_tasks = [] # Record of executed tasks
        with open('available_examples_short.json', 'r') as f:
            action_list = json.load(f)
        self.demonstration_set = []
        for key, value in action_list.items():
            self.demonstration_set.append((key, value))

    class TaskNode:
        """A* Algorithm Node Inner Class"""
        __slots__ = ['task_id', 'g', 'h', 'path', 'resources']
        
        def __init__(self, task_id: int, g: float, h: float, path: list, resources: dict):
            self.task_id = task_id
            self.g = g      # Cost so far
            self.h = h      # Heuristic estimate
            self.path = path
            self.resources = resources

        @property
        def f(self):
            return self.g + self.h

        def __lt__(self, other):
            return self.f < other.f

    def generate_tasks(self, instruction: str) -> List[Dict]:
        """
        Generate initial task sequence
        :param instruction: Natural language instruction
        :return: Structured task list
        """
        #sys_prompt = """You are an expert in correcting text, specializing in fixing homophone errors. The types of errors include:
        #    Homophones with different tones; Homophones with the same tone.
        #Requirements:
        #    Correct only homophones that cause semantic inconsistency with the context.
        #    Keep other content unchanged.
        #    Output the sentence with only the erroneous homophones modified.
        #    The number of characters in the output must match the original sentence."""
        
        #response = self.client.chat.completions.create(
        #    model=self.model,
        #    messages=[
        #        {"role": "system", "content": sys_prompt},
        #        {"role": "user", "content": instruction}
        #    ],
        #    temperature=0.3,
        #)
        #instruction = response.choices[0].message.content
        #print("Corrected text:", instruction)
        example = self._select_most_similar_example(instruction)
        sys_prompt = """You are a professional task decomposition expert skilled in breaking down semantic tasks into core steps. When decomposing tasks, refer to the following example steps:"""+f"{example}"+"""
        Then decompose each core step into multiple independent atomic tasks (atomic task types can be: movement|dialogue|navigation|exploration|volume setting | LED setting |gesture). Each atomic task should be indivisible, considering task dependencies, priority levels, and resource requirements.
        The output should be an array where each element represents an atomic task. Prioritize urgent tasks.
        **When the user input is a question or dialogue, do not answer the question, but generate a task with the "name" value as the user's input text.**
        **Requirements for JSON Generation**:
        1. **Format Requirements**:
           - The output must be in a compact, pure JSON format with no additional markup or explanatory text.
           - The JSON structure must strictly adhere to the following template:
             {
               "tasks": [
                 {
                   "id": integer,
                   "name": "string",
                   "duration": float,  # Unit: seconds
                   "depends": [optional],
                   "resources": [optional]
                 }
               ]
             }
           - The `tasks` field must be present, and its value must be an array.
        2. **Content Requirements**:
           - **No Empty Objects Allowed**: If no atomic tasks are found, the following task must be returned:
             {
               "id": 0,
               "name": "Sorry, I cannot complete the task",
               "duration": 0.0
             }
           - **Array Format**:
             - Use English square brackets `[]` to enclose the entire task array.
             - Separate tasks within the array with English commas `,`.
             - Multiple JSON objects outside the array are prohibited.
        3. **Example Structure**:        
           {
             "tasks": [
               {
                 "id": 1,
                 "name": "Move to the podium",
                 "duration": 5.0,
                 "depends": [],
                 "resources": []
               },
               {
                 "id": 2,
                 "name": "Raise left hand",
                 "duration": 3.0,
                 "depends": [],
                 "resources": []
               }
             ]
           }

        **Note**:
        - `id` must be an integer.
        - `duration` must be a float (unit: seconds).
        - `depends` and `resources` are optional fields; if present, they must be arrays.
        - The generated JSON must strictly match the template and example structure, ensuring field names, data types, and formats are identical.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": instruction}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        engine=PepperPromptEngine()
        raw_content=engine.extract_json_from_text(response.choices[0].message.content)         
        self.tasks = json.loads(raw_content)["tasks"]
        self._preprocess_tasks()
        # Modification point 3: Enforce completion of the duration field
        for task in self.tasks:
            if 'duration' not in task:
                task['duration'] = 0.0
                print(f"Warning: Task {task['id']} lacks duration, set to 0")
            else:
                # Ensure correct type
                task['duration'] = float(task['duration'])
        return self.tasks

    def _preprocess_tasks(self):
        """Task preprocessing: Build dependency graph"""
        #self.dep_graph = {t['id']: set(t['depends']) for t in self.tasks}
        self.dep_graph = {t['id']: set(t.get('depends', [])) for t in self.tasks}
        self.task_dict = {t['id']: t for t in self.tasks}
    def _heuristic(self, remaining: List[int]) -> float:
        """Heuristic function: Estimate shortest time for remaining tasks"""
        return sum(self.task_dict[tid].get('duration', 0) for tid in remaining)  # Add default value 0

    def _validate_resources(self, task_id: int, resources: dict) -> bool:
        """Resource conflict detection"""
        task = self.task_dict[task_id]
        # Modify this line, add empty list by default
        for res in task.get('resources', []):  # <--- Key modification
            if resources.get(res, 0) > 0:
                return False
        return True

    def optimize_taskplan(self, tasks) -> List[Dict]:
        """Perform A* algorithm optimization"""
        open_heap = []
        start_node = self.TaskNode(
            task_id=None,
            g=0,
            h=self._heuristic([t['id'] for t in tasks]),
            path=[],
            resources={}
        )
        heapq.heappush(open_heap, start_node)
        while open_heap:
            current = heapq.heappop(open_heap)
            if len(current.path) == len(tasks):
                self.optimized_plan = [self.task_dict[tid] for tid in current.path]
                return self.optimized_plan

            # Generate successor nodes
            for task in tasks:
                if task['id'] in current.path:
                    continue
                if all(dep in current.path for dep in task.get('depends', [])):
                    # Insert resource validation --------------------------------------------------
                    if not self._validate_resources(task['id'], current.resources):
                        continue  # Skip task due to resource conflict
                    # ------------------------------------------------------------
                    new_resources = current.resources.copy()
                    valid = True
                    # Simulate resource usage
                    for res in task.get('resources', []):  # <--- Similarly modified
                        if new_resources.get(res, 0) > 0:
                            valid = False
                            break
                        new_resources[res] = task.get('duration', 0.0)  # Safe assignment                                           
                    if valid:
                        new_path = current.path + [task['id']]
                        remaining = [t['id'] for t in tasks if t['id'] not in new_path]
                        new_node = self.TaskNode(
                            task_id=task['id'],
                            g=current.g + task.get('duration', 0.0),  # Add default value
                            h=self._heuristic(remaining),
                            path=new_path,
                            resources=new_resources
                        )
                        heapq.heappush(open_heap, new_node)

        return tasks

    def optimize_plan(self) -> List[Dict]:
        """Perform A* algorithm optimization"""
        open_heap = []
        start_node = self.TaskNode(
            task_id=None,
            g=0,
            h=self._heuristic([t['id'] for t in self.tasks]),
            path=[],
            resources={}
        )
        heapq.heappush(open_heap, start_node)

        while open_heap:
            current = heapq.heappop(open_heap)
            
            if len(current.path) == len(self.tasks):
                self.optimized_plan = [self.task_dict[tid] for tid in current.path]
                return self.optimized_plan

            # Generate successor nodes
            for task in self.tasks:
                if task['id'] in current.path:
                    continue
                if all(dep in current.path for dep in task.get('depends', [])):           
                    # Insert resource validation --------------------------------------------------
                    if not self._validate_resources(task['id'], current.resources):
                        continue  # Skip task due to resource conflict
                    # ------------------------------------------------------------
                    new_resources = current.resources.copy()
                    valid = True
                    
                    # Simulate resource usage
                    for res in task.get('resources', []):  # <--- Similarly modified
                        if new_resources.get(res, 0) > 0:
                            valid = False
                            break
                        new_resources[res] = task.get('duration', 0.0)  # Safe assignment            
                    if valid:
                        new_path = current.path + [task['id']]
                        remaining = [t['id'] for t in self.tasks if t['id'] not in new_path]
                        new_node = self.TaskNode(
                            task_id=task['id'],
                            g=current.g + task.get('duration', 0.0),  # Add default value
                            h=self._heuristic(remaining),
                            path=new_path,
                            resources=new_resources
                        )
                        heapq.heappush(open_heap, new_node)

        return tasks

    def execute(self, max_retries: int = 3) -> Dict:
        """
        Execute the optimized task sequence
        :param max_retries: Maximum number of retries
        :return: Execution result report
        """
        report = {"success": [], "failed": []}
        current_plan = self.optimized_plan.copy()
        retry_count = 0

        while current_plan and retry_count < max_retries:
            task = current_plan[0]
            try:
                # Simulate task execution (should actually connect to executor interface)
                print(f"Executing {task['name']}...")
                self._update_resources(task, acquire=True)
                
                # Record successful task
                report["success"].append(task)
                self.executed_tasks.append(task['id'])
                current_plan.pop(0)
                retry_count = 0  # Reset retry counter
            except Exception as e:
                print(f"Task failed: {str(e)}")
                report["failed"].append(task)
                retry_count += 1
                
                if retry_count >= max_retries:
                    print("Triggering replanning...")
                    self._replan(current_plan)
                    retry_count = 0

        return report

    def _update_resources(self, task: Dict, acquire: bool):
        """Update resource usage status"""
        factor = 1 if acquire else -1
        for res in task['resources']:
            self.resource_map[res] = self.resource_map.get(res, 0) + factor * task['duration']

    def _replan(self, remaining_tasks: List[Dict]):
        """Dynamic replanning"""
        self.tasks = [t for t in self.tasks if t['id'] not in self.executed_tasks]
        self._preprocess_tasks()
        new_plan = self.optimize_plan()
        remaining_tasks.clear()
        remaining_tasks.extend(new_plan)
    def _select_most_similar_example(self, query_task: str) -> Tuple[str, List[str]]:
        # 1. Construct LLM semantic matching prompt
        prompt = self._build_semantic_match_prompt(query_task)
        #print(f"Constructing LLM semantic matching prompt--->{prompt}")
        
        # 2. Invoke LLM for response generation
        response = self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
            temperature=0.3
        )
    
        engine = PepperPromptEngine()
        #print(f"LLM response--->{response}")
        llm_response = engine.extract_json_from_text(response.choices[0].message.content)
        
        # 3. Parse response and extract optimal match
        best_example = self._parse_llm_response(llm_response)
        print(f"Identified best example: {best_example}")
        return best_example
    
    def _build_semantic_match_prompt(self, query_task: str) -> str:
        system_msg = {
            "role": "system",
            "content": """You are a semantic matching expert. Select the candidate example most semantically similar to the user query by strictly following these rules:
    1. Analyze core intent and contextual scenario of the query
    2. Compare descriptive keywords and contextual relevance of candidates
    3. Prioritize matching on three dimensions: task objective, operation target, constraints
    4. Output must be JSON format containing the highest-scoring task name and plan in JSON format"""
        }
        
        candidate_examples = "\n".join([
            f"Candidate {i+1}: Task Name '{task}'" 
            for i, (task, plan) in enumerate(self.demonstration_set)
        ])
        
        user_msg = {
            "role": "user",
            "content": f"""Query Task: {query_task}
    
    Candidate Pool:
    {candidate_examples}
    
    Return the highest-scoring task name and plan in JSON format, sorted by descending score."""
        }
        
        return [system_msg, user_msg]
    
    def _parse_llm_response(self, response: str) -> Tuple[str, List[str]]:
        try:
            # Extract and validate JSON content
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            result = json.loads(response[json_start:json_end])
            
            # Match result with candidate set
            for task, plan in self.demonstration_set:
                if task == result["task_name"]:
                    return (task, plan)
                    
        except (json.JSONDecodeError, KeyError):
            # Fallback to alternative similarity algorithm
            return response 
