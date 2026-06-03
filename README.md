# growing_agent

聊天式 PPT 制作 Agent 学习项目。

本项目目标是用 Python + LangGraph 搭建一个小型 agent：它通过聊天收集用户需求，整理成结构化 PPT Brief，再调用 `ppt-master` 的项目创建、SVG 处理和 PPTX 导出能力，逐步完成一份可编辑的 PowerPoint。

## 当前阶段

第一阶段只做最小闭环：

1. 通过聊天收集 PPT 需求。
2. 检查需求是否完整。
3. 信息不足时追问用户。
4. 信息完整时生成结构化 Brief。
5. 生成页面大纲。
6. 调用 `ppt-master` 创建项目目录。

暂时不做完整 SVG 逐页生成和 PPTX 导出。那部分会在 graph、state、human-in-the-loop 跑稳之后再接入。

## 参考项目

本项目参考本地 `ppt-master` 工作流：

```text
F:\Make_money\基于java的多类型网络攻击检测系统\ppt-master
```

关键参考文件：

- `skills/ppt-master/SKILL.md`
- `skills/ppt-master/scripts/README.md`
- `docs/zh/technical-design.md`
- `projects/network_attack_detection_ppt169_20260519/design_spec.md`
- `projects/network_attack_detection_ppt169_20260519/spec_lock.md`

## 计划目录

```text
growing_agent/
  README.md
  docs/
    agent_granularity.md
    ppt_master_pipeline.md
    roadmap.md
  ppt_agent/
    state.py
    graph.py
    app.py
    nodes/
    services/
    prompts/
```

## 第一版成功标准

运行命令：

```powershell
python -m ppt_agent.app "我要做一个毕业答辩PPT，题目是基于Java的多类型网络攻击检测系统，20页，科技蓝风格，给答辩老师看"
```

期望结果：

```text
需求完整
Brief 已生成
Outline 已生成
Project 已创建
```

并返回 `ppt-master/projects/<project_name>` 的项目路径。
