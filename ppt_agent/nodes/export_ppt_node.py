import subprocess
import sys
from pathlib import Path

from ppt_agent.nodes.create_project import PPT_MASTER_ROOT
from ppt_agent.state import State


def export_p_node(state: State) -> dict:
    """调用 ppt-master 导出 PPTX。"""
    project_path = state.get("project_path")

    if not project_path:
        return {
            "status": "failed",
            "error": "缺少 project_path，无法导出 PPT。",
        }

    project_dir = Path(project_path)

    try:
        print("Agent：正在后处理 SVG...")

        subprocess.run(
            [
                sys.executable,
                "skills/ppt-master/scripts/finalize_svg.py",
                str(project_dir),
            ],
            cwd=PPT_MASTER_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )

        print("Agent：正在导出 PPTX...")

        subprocess.run(
            [
                sys.executable,
                "skills/ppt-master/scripts/svg_to_pptx.py",
                str(project_dir),
            ],
            cwd=PPT_MASTER_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )

        exports_dir = project_dir / "exports"
        pptx_files = sorted(
            exports_dir.glob("*.pptx"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if not pptx_files:
            return {
                "status": "failed",
                "error": "导出命令执行完成，但没有找到 PPTX 文件。",
            }

        pptx_path = str(pptx_files[0])

        print(f"Agent：PPTX 已导出：{pptx_path}")

        return {
            "status": "ppt_exported",
            "pptx_path": pptx_path,
            "assistant_reply": f"PPT 已生成：{pptx_path}",
        }

    except subprocess.CalledProcessError as exc:
        return {
            "status": "failed",
            "error": exc.stderr or exc.stdout or str(exc),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": f"PPT 导出失败：{exc}",
        }
