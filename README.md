# growing_agent

`growing_agent` 是一个用 Python + LangGraph 搭建的聊天式 PPT 制作 Agent。

它不重新实现 PPT 生成器，而是把用户聊天需求整理成结构化任务，再调用本地 `ppt-master` 的工作流完成 PPT 项目创建、设计规格生成、SVG 页面生成和 PPTX 导出。

## 先读这个

真正用于开发的主文档是：

[docs/WORK_MATERIALS.md](docs/WORK_MATERIALS.md)

这份文档写清楚了：

- 我们要做的 agent 到底是什么。
- 工作时需要用到哪些资料。
- 哪些 `ppt-master` 文件必须参考。
- 第一版要实现哪些 LangGraph 节点。
- 每个节点的输入、输出和验收标准。
- 需要调用哪些本地命令。

## 当前目标

第一版只做最小闭环：

```text
用户输入 PPT 需求
  -> 提取结构化需求
  -> 检查缺失字段
  -> 信息不足时追问
  -> 信息完整时生成 PPT Brief
  -> 生成页面大纲
  -> 调用 ppt-master 创建项目目录
```

第一版暂时不做：

- PDF / DOCX / URL 自动解析
- 自动生成 `design_spec.md`
- 自动逐页生成 SVG
- 自动导出 PPTX

这些放到后续阶段。


## 计划代码结构

```text
ppt_agent/
  app.py
  graph.py
  state.py
  nodes/
    collect_requirement.py
    check_requirement.py
    ask_followup.py
    freeze_brief.py
    plan_deck.py
    create_project.py
  services/
    ppt_master_runner.py
    project_naming.py
  prompts/
    requirement_extract.md
    deck_planner.md
```

## 第一版运行目标

```powershell
python -m ppt_agent.app "我要做一个毕业答辩PPT，题目是基于Java的多类型网络攻击检测系统，20页，科技蓝风格，给答辩老师看，重点讲系统架构、检测规则和实验结果"
```

期望输出：

```text
需求完整
Brief 已生成
Outline 已生成
Project 已创建
项目路径: F:\Make_money\基于java的多类型网络攻击检测系统\ppt-master\projects\<project_name>
```
