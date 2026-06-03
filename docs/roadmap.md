# growing_agent 开发路线图

## Phase 1: 命令行版 LangGraph

目标：跑通最小 agent 工作流。

功能：

- 定义 `PPTAgentState`
- 实现需求提取节点
- 实现需求完整性检查节点
- 实现追问节点
- 实现 Brief 生成节点
- 实现页面大纲节点
- 实现 `ppt-master` 项目创建节点

成功标准：

```text
输入完整 PPT 需求
-> 输出 Brief
-> 输出 Outline
-> 创建 ppt-master 项目目录
```

## Phase 2: 加入用户确认

目标：学习 human-in-the-loop。

功能：

- 生成八项确认建议
- 等待用户确认
- 用户修改后重新生成 Brief / Outline
- 确认后继续创建项目

八项确认：

- 画布格式
- 页数范围
- 目标受众
- 风格目标
- 配色方案
- 图标使用
- 字体方案
- 图片使用

## Phase 3: 接入 FastAPI

目标：把命令行 agent 变成聊天 API。

接口：

```text
POST /chat
GET /sessions/{session_id}
POST /sessions/{session_id}/confirm
```

功能：

- session 隔离
- 保存会话 state
- 返回 agent 状态
- 支持等待用户补充信息

## Phase 4: 生成设计规格

目标：让 agent 生成 `design_spec.md` 和 `spec_lock.md`。

功能：

- 根据 Brief 生成设计说明
- 根据 Outline 生成页面列表
- 根据风格生成颜色、字体、图标规范
- 写入项目目录

## Phase 5: SVG 逐页生成

目标：进入真正 PPT 视觉生成阶段。

功能：

- 每页生成前读取 `spec_lock.md`
- 根据页面大纲生成 SVG
- 保存到 `svg_output/`
- 逐页执行，不并行

## Phase 6: 质量检查和导出

目标：输出最终 PPTX。

功能：

- 调用 `svg_quality_checker.py`
- 错误页重生成
- 调用 `finalize_svg.py`
- 调用 `svg_to_pptx.py`
- 返回 `exports/*.pptx`

## Phase 7: 完整聊天式 PPT Agent

目标：形成可用产品。

功能：

- 用户上传资料
- agent 追问需求
- agent 生成方案
- 用户确认
- 自动创建项目
- 自动生成 PPT
- 返回可编辑 PPTX
