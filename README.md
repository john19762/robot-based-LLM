# robot-based-LLM
Social Robot Control System Based on Large Language Models
Welcome to the GitHub repository of this project! This system is designed to build a multi-layered control architecture for social robots powered by large language models (LLMs), enhancing natural, accurate, and robust human-robot interactions. It integrates advanced speech recognition, semantic understanding, task planning, and execution monitoring technologies to enable robots to communicate more intelligently and naturally.

Project Overview
With the rapid advancement of AI technology, LLMs such as GPT-4 and ChatGPT have achieved unprecedented milestones in natural language processing (NLP), bringing revolutionary improvements to social robots. This project introduces a hierarchical, multi-role interaction framework that leverages LLMs to achieve high reliability and precision in understanding and planning.
Experimental results demonstrate that this system outperforms traditional approaches in multiple real-world scenarios, showing significant improvements in task accuracy, robustness, and conversation naturalness.
Project Structure

├── adapter.py              # Interface for task and API adaptation
├── dialogue_mode.py        # Dialogue management strategies
├── normalization.py        # Semantic normalization tools
├── pepper_controller.py    # Pepper robot control interface
├── determine_task_type.py  # Task type recognition
├── PepperPromptEngine.py   # Multi-stage prompt design
├── taskplan.py             # Task decomposition and scheduling
├── navigation_params.json  # Navigation-related parameters
├── available_examples_short.json  # Sample commands/examples
├── Experiment result.xlsx  # Experimental results and analysis
└── *** (Additional configuration and data files) ***
Usage Instructions
1. Environment Setup
    • Python 3.8 or higher
    • Install dependencies:
    • Configure speech recognition models (Whisper, PaddleSpeech) and robot APIs
2. Running the Demo
    1. Record speech commands; system converts to text via ASR 
    2. System automatically performs semantic correction and intent detection 
    3. Instruction normalization maps diverse expressions to standardized formats 
    4. Hierarchical task decomposition generates structured tasks 
    5. Scheduler calculates optimal execution order considering dependencies/resources 
    6. Action commands are dispatched to the robot; feedback is monitored 
    7. System dynamically adjusts plans as needed 
3. Customizing Tasks
    • Modify navigation_params.json or define new templates
    • Adjust prompt strategies for specific scenarios
    • Extend adapter.py for custom device API interactions

Experimental Evaluation
    • Tested in diverse scenarios: navigation, multi-step tasks, dialogues
        • Key metrics include:
        ◦ Accuracy of intent and template matching
        ◦ Task scheduling success rate
        ◦ Resource conflict reduction
        ◦ Dialogue naturalness and user satisfaction
See Experiment result.xlsx for detailed analysis.

Ongoing Development and Licensing
This project is under continuous development. The current release is a demo version intended for evaluation and exploration purposes. The full, detailed version—including additional features and datasets—is available upon request.
For access to the complete version and data, please contact me. zhoulijun1976@126.com.
Future Plans
    • Incorporate multimodal perception (vision, tactile sensing)
    • Support cross-lingual natural language understanding
    • Enable multi-robot coordination and collaboration
    • Long-term deployment in social environments
    • User feedback integration for continuous learning
Contributions and Collaboration
Contributions are welcome! Please fork the repository or submit issues if you have suggestions. For detailed contribution guidelines, see CONTRIBUTING.md.
Contact
    • Project Lead: Zhuo Lijun (zhoulijun1976@126.com)
    • Related Paper: [Research title, authors, publication details]
    • Project URL: https://github.com/john19762/robot-based-LLM

License
This project is licensed under the MIT License. Feel free to use and adapt it.
