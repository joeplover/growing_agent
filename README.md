# growing_agent

`growing_agent` 是一个基于 Python、LangGraph 和 FastAPI 的聊天式 PPT 制作 Agent。用户用自然语言描述 PPT 需求，系统会逐步整理需求、补充资料、生成制作方案，并调用内置的 `ppt-master` 工作流创建 PPT 项目、生成页面 SVG、导出 PPTX。

这个仓库不重新实现底层 PPT 渲染器，而是在 `ppt_creator/skills/ppt-master` 前面增加一个对话式控制层，让 PPT 制作流程可以通过聊天和 Web 页面驱动。

## 当前能力

- 从用户聊天中提取结构化 PPT 需求。
- 检查必要字段，不完整时自动追问。
- 支持上传 `.txt`、`.md`、`.markdown` 资料文件。
- 根据需求和资料生成 PPT Brief 与页面大纲。
- 调用本地 `ppt-master` 创建项目目录。
- 将 Brief、大纲和资料写入项目资料区。
- 在生成前要求用户确认制作方案。
- 确认后生成 `design_spec.md`、`spec_lock.md`、页面 SVG，并导出 PPTX。
- Web 端隐藏本地绝对路径，只暴露下载入口。

## 技术栈

- Python 3.11+
- LangGraph
- LangChain OpenAI adapter
- DeepSeek Chat API
- FastAPI
- Uvicorn
- pytest
- 内置 `ppt-master` 脚本与模板资源

## 目录结构

```text
growing_agent/
  ppt_agent/
    app.py                  # 命令行聊天入口
    graph.py                # LangGraph 流程编排
    state.py                # 全局 State 定义
    nodes/                  # Agent 节点
    prompt/                 # 需求提取、页面规划等提示词
    services/               # LLM 等服务封装
    web/
      server.py             # FastAPI 服务
      materials.py          # 上传资料解析
      sessions.py           # Web 会话状态
      static/               # Web 前端页面
  ppt_creator/
    skills/ppt-master/      # 本地 PPT 生成工作流、脚本、模板
  docs/
    WORK_MATERIALS.md       # 项目背景与开发资料
    GRAPH_FLOW.md           # 流程说明
    roadmap.md              # 后续规划
    reference/              # ppt-master 参考资料
  tests/
    test_web_api.py         # Web API 测试
  requirements.txt
  start_web.bat
```

## 快速开始

### 1. 安装依赖

建议在虚拟环境中安装：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果只想快速启动 Web 版，也可以直接运行：

```powershell
.\start_web.bat
```

`start_web.bat` 会检查 Web 运行依赖，缺失时自动安装 `requirements.txt`。

### 2. 配置 LLM Key

当前 LLM 服务使用 DeepSeek 兼容 OpenAI 的接口，需要配置：

```powershell
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
```

持久化配置可以写入系统环境变量，或者在每次启动服务前设置。

### 3. 启动 Web 工作台

```powershell
uvicorn ppt_agent.web.server:app --reload --host 127.0.0.1 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

Web 页面支持：

- 新建会话。
- 上传资料文件。
- 输入 PPT 需求。
- 查看 Agent 回复和当前状态。
- 在 PPTX 生成后下载文件。

### 4. 使用命令行入口

```powershell
python -m ppt_agent.app
```

启动后在终端中输入 PPT 需求，例如：

```text
我要做一个毕业答辩 PPT，题目是基于 Java 的多类型网络攻击检测系统，20 页，科技蓝风格，给答辩老师看，重点讲系统架构、检测规则和实验结果。
```

输入 `exit` 或 `quit` 退出。

## Agent 流程

当前 LangGraph 流程位于 `ppt_agent/graph.py`，核心路径如下：

```text
用户输入
  -> collect_requirement_node
  -> check_requirement_node
     -> ask_followup_node          # 需求不完整时追问
     -> ask_material_node          # 需求完整但缺少资料时请求资料
  -> collect_material_node
  -> freeze_brief_node
  -> plan_deck_node
  -> create_project_node
  -> write_project_materials_node
  -> confirm_plan_node
  -> check_user_confirm_node
  -> generate_design_spec_node
  -> generate_spec_lock_node
  -> generate_svg_node
  -> export_ppt_node
```

Web 会话会把上传资料、聊天消息、需求结构、页面大纲、项目状态和导出结果保存在内存中的 session state 里。服务重启后会话状态不会持久化。

## 上传资料限制

支持格式：

- `.txt`
- `.md`
- `.markdown`

限制：

- 单个文件最大 2MB。
- 内容必须是 UTF-8 或 GBK 可解码文本。
- 上传资料不会移动或覆盖用户原始文件，只会把解析后的文本保存到当前 Web 会话状态中。

## API 简表

FastAPI 服务提供以下主要接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/` | Web 页面 |
| `POST` | `/api/sessions` | 创建会话 |
| `POST` | `/api/materials` | 上传资料 |
| `POST` | `/api/chat` | 发送聊天消息并推进 Agent |
| `GET` | `/api/download/{session_id}/pptx` | 下载当前会话生成的 PPTX |

## 测试

运行测试：

```powershell
python -m pytest -q
```

当前测试重点覆盖 Web API：

- 上传文本资料写入会话。
- 拒绝不支持的文件类型。
- 聊天接口复用已有 session state。
- PPTX 生成后隐藏本地路径并返回下载状态。
- 下载接口返回生成文件。
- Web 响应隐藏本地项目路径。

## 关键实现说明

### LLM 服务

LLM 初始化位于 `ppt_agent/services/LLm.py`：

```python
llm = ChatOpenAI(
    model="deepseek-v4-flash",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)
```

如果没有配置 `DEEPSEEK_API_KEY`，Web 页面可以打开，但需要调用 LLM 的流程会失败。

### ppt-master 集成

`create_project_node` 会在本仓库内的 `ppt_creator` 目录下调用：

```powershell
python skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
```

后续导出节点会调用：

```powershell
python skills/ppt-master/scripts/finalize_svg.py <project_path>
python skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

生成的项目、SVG 和 PPTX 位于 `ppt_creator` 下的 `ppt-master` 项目目录中。

### Web 路径安全

Web API 不直接返回本地 `project_path` 和 `pptx_path`。前端只看到：

- `project_ready`
- `pptx_ready`
- `pptx_download_url`

这样可以避免把开发机绝对路径暴露给浏览器页面。

## 开发参考

优先阅读：

- `docs/WORK_MATERIALS.md`
- `docs/GRAPH_FLOW.md`
- `docs/ppt_master_pipeline.md`
- `docs/reference/ppt-master/SKILL.md`
- `docs/reference/ppt-master/scripts_README.md`

这些文档记录了项目目标、LangGraph 节点设计、`ppt-master` 的工作流和脚本约束。

## 当前注意事项

- Web session 当前只保存在内存中，不适合多进程部署或服务重启后恢复。
- 上传资料只支持文本和 Markdown，还不支持 PDF、DOCX、URL 自动解析。
- PPT 生成依赖本地 `ppt_creator/skills/ppt-master` 脚本和模板资源。
- 生成质量依赖用户需求、上传资料和 LLM 输出稳定性。
- 如果导出失败，优先检查 `DEEPSEEK_API_KEY`、项目目录、SVG 生成结果和 `ppt-master` 脚本依赖。
