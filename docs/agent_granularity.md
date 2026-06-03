# PPT Agent 颗粒度拆分

## 核心原则

第一版不要拆成多个独立 agent，而是拆成一个 LangGraph 里的多个节点。

原因：

- 节点比多 agent 更容易调试。
- 每个节点都有明确输入和输出。
- 可以先跑通工作流，再把稳定节点升级成子 agent。
- `ppt-master` 本身是严格串行流水线，过早并行会破坏上下文一致性。

## 产品级流程

```text
聊天收集需求
  -> 需求完整性检查
  -> 生成 PPT Brief
  -> 生成页面大纲
  -> 创建 ppt-master 项目
  -> 写入 sources / design_spec / spec_lock
  -> 生成 SVG 页面
  -> 质量检查
  -> PPTX 导出
```

## 第一阶段 LangGraph 节点

```text
START
  -> collect_requirement_node
  -> check_requirement_node
  -> 条件分支
       -> 信息不足: ask_followup_node -> END
       -> 信息足够: freeze_brief_node
  -> plan_deck_node
  -> create_project_node
  -> END
```

## 节点职责

### collect_requirement_node

从用户自然语言中提取 PPT 需求字段。

输出字段：

- topic
- use_case
- audience
- page_count
- style
- language
- source_files
- key_points

### check_requirement_node

检查最小必填字段是否齐全。

必填字段：

- topic
- use_case
- audience
- page_count
- style

输出字段：

- requirement_complete
- missing_fields

### ask_followup_node

当信息不足时，生成追问。

示例：

```text
我还需要确认两个信息：
1. 这份 PPT 是给谁看的？
2. 你希望大概多少页？
```

### freeze_brief_node

把聊天内容冻结成结构化 PPT Brief。

Brief 是后续所有节点的稳定输入，不再依赖松散聊天文本。

### plan_deck_node

根据 Brief 生成页面大纲。

输出示例：

```json
[
  {"page": 1, "title": "封面", "purpose": "展示题目、学生、导师"},
  {"page": 2, "title": "目录", "purpose": "说明汇报结构"},
  {"page": 3, "title": "研究背景", "purpose": "说明项目必要性"}
]
```

### create_project_node

调用 `ppt-master` 的项目初始化脚本。

命令：

```powershell
python skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
```

## 后续可升级的子 agent

等第一版跑稳后，可以拆出这些角色：

- Requirement Agent: 需求收集。
- Strategist Agent: 页面规划、风格确认、设计规格。
- PptMaster Tool Agent: 调用本地脚本。
- Slide Executor Agent: 逐页 SVG 生成。
- Quality Agent: SVG 检查和错误定位。
- Delivery Agent: 汇总输出和交付。

## 不要一开始做的事

- 不要直接一句话生成完整 PPT。
- 不要一开始做多个并行子 agent。
- 不要先接 FastAPI，再写 LangGraph。
- 不要第一版就处理 PDF/DOCX/URL 全格式。
- 不要第一版就做 SVG 自动修复。
