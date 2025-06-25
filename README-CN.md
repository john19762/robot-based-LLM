        ​ 项目简介
随着AI技术快速发展，LLMs如GPT-4和ChatGPT在自然语言处理（NLP）中达到了前所未有的水平，为社交机器人带来突破性的改进。本项目提出了一个层级式多角色交互框架，结合LLMs实现高可靠性与高精度的理解与规划.
实验显示，该系统在多种实际场景中表现优于传统方案，在任务精度、鲁棒性和对话自然性方面具有显著优势。

​ 文件结构
.
├── adapter.py              # 任务和API适配接口
├── dialogue_mode.py        # 对话控制策略
├── normalization.py        # 语义归一化工具
├── pepper_controller.py    # Pepper机器人的控制接口
├── determine_task_type.py  # 任务类型判定
├── PepperPromptEngine.py   # 多阶段Prompt设计
├── taskplan.py             # 任务分解与调度
├── navigation_params.json  # 导航相关参数
├── available_examples_short.json  # 可用示例
├── normalization.py        # 语义归一化核心
├── Experiment result.xlsx  # 实验结果分析
└── ***（其他配置文件与数据）***

​ 使用指南
​ 1. 环境准备
    • Python 3.8+ 
    • 安装必要依赖
    • 配置机器人API及语音识别模型（Whisper、PaddleSpeech）等 
2. 运行流程
    1. 录入语音指令，通过ASR系统转换为文本 
    2. 系统自动进行语义校正和意图识别 
    3. 指令归一化，将多样表达映射为规范结构 
    4. 任务分解，生成子任务树 
    5. 调度器根据依赖与资源状态制定执行计划 
    6. 执行层发出控制命令，监控反馈 
    7. 动态调整任务计划以应对环境变化 
3. 自定义任务
    • 修改navigation_params.json或定义新模板 
    • 调整Prompt策略以适应新的场景或需求 
    • 结合adapter.py进行扩展，实现自定义API调用或设备控制 

​ 实验与评估
    • 在多样化场景（公共空间、家庭服务）中测试 
    • 核心指标： 
        ◦ 任务识别准确率 
        ◦ 语义模板匹配精度 
        ◦ 调度成功率与资源冲突率 
        ◦ 对话自然性与用户满意度 
查看Experiment result.xlsx获取详细实验数据和分析。

​ 未来方向
    • 融合多模态感知（视觉、触觉） 
    • 跨语言多语理解 
    • 多机器人协作 
    • 长期适应与学习能力 
    • 用户反馈的持续优化 

持续开发与许可
本项目正在不断进行中。目前发布的版本为演示版，旨在供评估和探索使用。完整的、详细的版本，包括额外的功能和数据集，需另行申请。
如需获得完整版本和相关数据，请联系项目负责人：zhoulijun1976@126.com。
​ 贡献与合作
欢迎提交Pull Request或提交Issue以提出建议与改进！详细贡献指南请见CONTRIBUTING.md。

​ 联系方式
    • 论文地址：Corresponding author: iauthor@gmail.com 
    • 项目主页： https://github.com/john19762/robot-based-LLM 

​ 许可证
此项目遵循MIT协议，欢迎自由使用与修改。
