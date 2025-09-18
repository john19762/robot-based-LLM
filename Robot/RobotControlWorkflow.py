import json
from enum import Enum
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
import time

# ==================== 节点类型（保持原样，不新增机器人专用类型） ====================
class NodeType(Enum):
    START = "start"
    IF_ELSE = "if-else"
    LLM = "llm"
    ANSWER = "answer"
    PARAM_EXTRACTOR = "parameter-extractor"
    ASSIGNER = "assigner"

# ==================== 基类（完全保持你原来的） ====================
class Node:
    def __init__(self, node_id: str, node_type: NodeType, data: Dict):
        self.id = node_id
        self.type = node_type
        self.data = data
        self.next_nodes = {}  # key: edge_id, value: {"target": target_id, "condition": condition}

    def add_next_node(self, edge_id: str, target_id: str, condition: Optional[str] = None):
        self.next_nodes[edge_id] = {
            "target": target_id,
            "condition": condition
        }

    def get_next_node_targets(self) -> List[str]:
        return [node["target"] for node in self.next_nodes.values()]

    def execute(self, context: Dict) -> Tuple[Dict, List[str]]:
        print(f"执行基础节点 {self.id} ({self.type.value})")
        return context, []

# ==================== 所有节点类保持你原来的实现 ====================
# 👇 以下所有节点类均未做任何修改，完全复制你原来的代码

class StartNode(Node):
    def __init__(self, node_id: str, data: Dict):
        super().__init__(node_id, NodeType.START, data)
        self.variables = data.get("variables", [])

    def execute(self, context: Dict) -> Tuple[Dict, List[str]]:
        print(f"[执行节点] {self.id} (start)")
        for var in self.variables:
            var_name = var.get("name")
            var_selector = var.get("variable_selector", [])
            if not var_selector:
                continue
            if var_selector[0] == "sys":
                var_selector[0] = "conversation"
            if var_name and len(var_selector) >= 2:
                if "conversation" not in context:
                    context["conversation"] = {}
                context["conversation"][var_selector[1]] = ""
                print(f"  初始化变量: {var_selector[1]}")
        # 👉 改为机器人场景：等待语音输入（模拟）
        print("🤖 请说指令（模拟语音输入）...")
        user_input = input(">>> ").strip()
        context.setdefault("conversation", {})["user_speech"] = user_input
        context["conversation"]["dialogue_count"] = 1
        targets = self.get_next_node_targets()
        if not targets:
            print(f"[{self.id}] 警告：没有下一个节点，工作流结束")
            return context, []
        return context, [targets[0]]

class IfElseNode(Node):
    def __init__(self, node_id: str, data: Dict):
        super().__init__(node_id, NodeType.IF_ELSE, data)
        self.cases = data.get("cases", [])

    def evaluate_condition(self, condition: Dict, context: Dict) -> bool:
        selector = condition.get("variable_selector", [])
        if not selector:
            return False
        if selector[0] == "sys":
            selector[0] = "conversation"
        value = context
        for key in selector:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return False
        target_value = condition.get("value")
        op = condition.get("operator", "=")
        if isinstance(value, (int, float)) and isinstance(target_value, str) and target_value.isdigit():
            value = float(value)
            target_value = float(target_value)
            if op == "=":
                return value == target_value
            elif op == ">":
                return value > target_value
            elif op == "<":
                return value < target_value
        if op == "=":
            return str(value) == str(target_value)
        return False

    def execute(self, context: Dict) -> Tuple[Dict, List[str]]:
        print(f"[执行节点] {self.id} (if-else)")
        conv = context.get("conversation", {})
        target_nodes = []
        for node_id, node_info in self.next_nodes.items():
            condition_str = node_info.get("condition")
            if condition_str:
                eval_str = condition_str
                for var_name in conv:
                    eval_str = eval_str.replace(var_name, str(conv[var_name]))
                try:
                    if eval(eval_str):
                        target_nodes.append(node_info["target"])
                except:
                    pass
            else:
                target_nodes.append(node_info["target"])
        if not target_nodes:
            print(f"[{self.id}] 警告：无匹配目标，工作流结束")
        else:
            print(f"条件分支结果: -> 目标节点: {target_nodes}")
        return context, target_nodes

class LLMNode(Node):
    def __init__(self, node_id: str, data: Dict, api_key: str):
        super().__init__(node_id, NodeType.LLM, data)
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key, base_url="https://ai.gitee.com/v1")  # 修复空格

    def execute(self, context: Dict) -> Tuple[Dict, List[str]]:
        print(f"[执行节点] {self.id} (llm): {self.data.get('title')}")
        prompt_template = self.data.get("prompt_template", [])
        messages = []
        for item in prompt_template:
            role = item.get("role", "user")
            text = item.get("text", "")
            if "{{#" in text and "#}}" in text:
                start_idx = text.find("{{#") + 3
                end_idx = text.find("#}}")
                var_path_str = text[start_idx:end_idx]
                var_path = var_path_str.split(".")
                var_value = context
                try:
                    for key in var_path:
                        var_value = var_value[key.strip()]
                    text = text.replace(f"{{{{#{var_path_str}#}}}}", str(var_value))
                except KeyError:
                    print(f"警告: 变量 {var_path} 未找到")
            messages.append({"role": role, "content": text})
        model_config = self.data.get("model", {})
        model_name = model_config.get("name", "Qwen3-8B")
        temperature = model_config.get("temperature", 0.7)
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature
            )
            llm_output = response.choices[0].message.content.strip()
            print(f"  LLM输出: {llm_output[:100]}...")
            context.setdefault("node_outputs", {})[self.id] = llm_output
        except Exception as e:
            print(f"LLM调用错误: {str(e)}")
            llm_output = ""
        targets = self.get_next_node_targets()
        if not targets:
            print(f"[{self.id}] 警告：没有下一个节点，工作流结束")
            return context, []
        return context, [targets[0]]

class AnswerNode(Node):
    def __init__(self, node_id: str, data: Dict):
        super().__init__(node_id, NodeType.ANSWER, data)

    def execute(self, context: Dict) -> Tuple[Dict, List[str]]:
        print(f"[执行节点] {self.id} (answer): {self.data.get('title')}")
        answer_key = self.data.get("answer", "")
        question_var = "q1"
        if answer_key.startswith("{{#") and answer_key.endswith("#}}"):
            var_path_str = answer_key[3:-3]  # 修复：应为 -3
            var_path = var_path_str.split(".")
            question_var = var_path[-1]
        question = context.get("conversation", {}).get(question_var, "请回答：")
        user_answer = input(f"{question}: ")
        context.setdefault("conversation", {})["query" + str(context["conversation"].get("dialogue_count",1))] = user_answer
        context["conversation"]["dialogue_count"] = context["conversation"].get("dialogue_count",1) + 1
        targets = self.get_next_node_targets()
        if not targets:
            print(f"[{self.id}] 警告：没有下一个节点，工作流结束")
            return context, []
        return context, [targets[0]]

class ParameterExtractorNode(Node):
    def __init__(self, node_id: str, data: Dict):
        super().__init__(node_id, NodeType.PARAM_EXTRACTOR, data)

    def execute(self, context: Dict) -> Tuple[Dict, List[str]]:
        print(f"[执行节点] {self.id} (parameter-extractor): {self.data.get('title')}")
        parameters = self.data.get("parameters", [])
        if not parameters:
            print("  警告: 没有定义参数，跳过提取")
            targets = self.get_next_node_targets()
            return context, targets if targets else []
        for param in parameters:
            param_name = param.get("name")
            source_selector = param.get("source_selector", [])
            if not param_name or not source_selector:
                continue
            source_data = context
            try:
                for key in source_selector:
                    if isinstance(source_data, list) and key.isdigit():
                        key = int(key)
                    source_data = source_data[key]
            except (KeyError, IndexError, TypeError):
                source_data = None
            if source_data is not None:
                context.setdefault("extracted_params", {})[param_name] = source_data
                print(f"  提取参数: {param_name} = {str(source_data)[:50]}...")
        targets = self.get_next_node_targets()
        if not targets:
            print(f"[{self.id}] 警告：没有下一个节点，工作流结束")
            return context, []
        return context, [targets[0]]

class AssignerNode(Node):
    def __init__(self, node_id: str, data: Dict):
        super().__init__(node_id, NodeType.ASSIGNER, data)

    def execute(self, context: Dict) -> Tuple[Dict, List[str]]:
        print(f"[执行节点] {self.id} (assigner): {self.data.get('title')}")
        items = self.data.get("items", [])
        for item in items:
            var_selector = item.get("variable_selector", [])
            value_selector = item.get("value_selector", [])
            if not var_selector or not value_selector:
                continue
            if var_selector[0] == "sys":
                var_selector[0] = "conversation"
            value_data = context
            try:
                for key in value_selector:
                    if isinstance(value_data, list) and key.isdigit():
                        key = int(key)
                    value_data = value_data[key]
            except (KeyError, IndexError, TypeError):
                value_data = ""
            target = context
            for k in var_selector[:-1]:
                if k not in target or not isinstance(target[k], dict):
                    target[k] = {}
                target = target[k]
            target[var_selector[-1]] = value_data
            print(f"  赋值: {'.'.join(var_selector)} = {str(value_data)[:50]}...")
        targets = self.get_next_node_targets()
        if not targets:
            print(f"[{self.id}] 警告：没有下一个节点，工作流结束")
            return context, []
        return context, [targets[0]]

# ==================== Workflow 引擎（保持原样） ====================
class ResearchWorkflow:
    def __init__(self, workflow_data: Dict, api_key: str):
        self.nodes = {}
        self.api_key = api_key
        self.build_workflow(workflow_data)

    def build_workflow(self, workflow_data: Dict):
        for node_data in workflow_data["graph"]["nodes"]:
            node_id = node_data["id"]
            node_type_str = node_data["type"]
            try:
                node_type = NodeType(node_type_str)
            except ValueError:
                print(f"警告: 未知节点类型 {node_type_str}，节点ID: {node_id}")
                continue

            if node_type == NodeType.START:
                self.nodes[node_id] = StartNode(node_id, node_data["data"])
            elif node_type == NodeType.IF_ELSE:
                self.nodes[node_id] = IfElseNode(node_id, node_data["data"])
            elif node_type == NodeType.LLM:
                self.nodes[node_id] = LLMNode(node_id, node_data["data"], self.api_key)
            elif node_type == NodeType.ANSWER:
                self.nodes[node_id] = AnswerNode(node_id, node_data["data"])
            elif node_type == NodeType.ASSIGNER:
                self.nodes[node_id] = AssignerNode(node_id, node_data["data"])
            elif node_type == NodeType.PARAM_EXTRACTOR:
                self.nodes[node_id] = ParameterExtractorNode(node_id, node_data["data"])
            else:
                print(f"警告: 未实现的节点类型 {node_type}，节点ID: {node_id}")

        for edge in workflow_data["graph"]["edges"]:
            source_id = edge["source"]
            target_id = edge["target"]
            if source_id in self.nodes:
                source_node = self.nodes[source_id]
                condition = edge.get("data", {}).get("condition") or edge.get("sourceHandle")
                source_node.add_next_node(edge["id"], target_id, condition)
            else:
                print(f"警告: 找不到边的源节点 {source_id}")

        print("\n节点连接关系:")
        for nid, node in self.nodes.items():
            print(f"  节点 {nid}({node.type.value}) -> {node.get_next_node_targets()}")

    def execute(self, initial_context: Dict = None) -> Dict:
        context = initial_context or {}
        current_nodes = []
        for node_id, node in self.nodes.items():
            if node.type == NodeType.START:
                print(f"找到开始节点: {node_id}")
                current_nodes = [node_id]
                break

        MAX_STEPS = 50
        step = 0
        while current_nodes and step < MAX_STEPS:
            step += 1
            next_nodes = []
            print(f"\n=== 步骤 {step} ===")
            for node_id in current_nodes:
                if node_id not in self.nodes:
                    print(f"警告: 未找到节点 {node_id}")
                    continue
                node = self.nodes[node_id]
                try:
                    context, targets = node.execute(context)
                    for t in targets:
                        if t not in next_nodes:
                            next_nodes.append(t)
                except Exception as e:
                    print(f"节点执行错误: {str(e)}")
            current_nodes = next_nodes

        if step >= MAX_STEPS:
            print("警告: 达到最大步数，可能陷入循环")
        return context

# ==================== 主程序（加载 config.json） ====================
if __name__ == "__main__":
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            workflow_data = json.load(f)
    except FileNotFoundError:
        print("❌ 未找到 config.json，请创建配置文件")
        exit(1)

    api_key = "60YTTY3REN156NCBRO4S39C6L3JRHOGBBKAZGEAD"  # 替换为你的真实 API Key
    workflow = ResearchWorkflow(workflow_data, api_key)
    final_context = workflow.execute()

    print("\n" + "="*60)
    print("✅ 工作流执行完成")
    print("="*60)
    print(json.dumps(final_context, indent=2, ensure_ascii=False, default=str))
