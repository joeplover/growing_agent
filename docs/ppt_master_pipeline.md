# ppt-master 流水线摘要

本项目复用 `ppt-master` 的 PPT 制作方法，但不会直接复制整个仓库。

## 核心路径

```text
用户输入
  -> source_to_md
  -> project_manager init
  -> import-sources
  -> Strategist
  -> design_spec.md
  -> spec_lock.md
  -> Image Acquisition
  -> Executor
  -> svg_output/
  -> svg_quality_checker.py
  -> total_md_split.py
  -> finalize_svg.py
  -> svg_to_pptx.py
  -> exports/*.pptx
```

## 关键脚本

### 内容转换

```powershell
python skills/ppt-master/scripts/source_to_md/pdf_to_md.py <file.pdf>
python skills/ppt-master/scripts/source_to_md/doc_to_md.py <file.docx>
python skills/ppt-master/scripts/source_to_md/excel_to_md.py <file.xlsx>
python skills/ppt-master/scripts/source_to_md/ppt_to_md.py <deck.pptx>
python skills/ppt-master/scripts/source_to_md/web_to_md.py <url>
```

### 项目管理

```powershell
python skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files...> --move
python skills/ppt-master/scripts/project_manager.py validate <project_path>
```

### 后处理和导出

```powershell
python skills/ppt-master/scripts/total_md_split.py <project_path>
python skills/ppt-master/scripts/finalize_svg.py <project_path>
python skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

### 质量检查

```powershell
python skills/ppt-master/scripts/svg_quality_checker.py <project_path>
```

## 第一版复用范围

第一版只复用：

- `project_manager.py init`
- 项目目录结构
- `design_spec.md` / `spec_lock.md` 的思想

暂不复用：

- PDF/DOCX 转换
- 图片生成
- 逐页 SVG 生成
- SVG 质量检查
- PPTX 导出

## 重要约束

`ppt-master` 的生成流程是严格串行的：

- 先有需求。
- 再有项目目录。
- 再有设计确认。
- 再有 `design_spec.md` 和 `spec_lock.md`。
- 再逐页生成 SVG。
- 再检查和导出。

不要在需求不完整时提前生成 PPT。
不要在没有 `spec_lock.md` 时生成页面。
不要让多个子 agent 并行生成不同页面。
