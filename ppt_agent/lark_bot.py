"""
飞书机器人入口：通过 lark-cli 长轮询收消息，调用 LangGraph PPT Agent 回复。

用法：
    python -m ppt_agent.lark_bot

前提：
    - lark-cli 已安装并完成 config init
    - 飞书应用已开启「机器人」能力
    - 飞书应用已订阅 im.message.receive_v1 事件
"""

import json
import subprocess
import sys
import os
import shutil
import msvcrt
from pathlib import Path

from langchain_core.messages import HumanMessage

from ppt_agent.graph import app as graph_app


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

# 项目根目录（growing_agent）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# lark-cli 可执行文件
LARK_CLI = os.environ.get("LARK_CLI", "lark-cli.cmd")

# 每条消息处理超时（秒），PPT 生成可能较慢
INVOKE_TIMEOUT = 600

# 不可见字符清理（和 app.py 保持一致）
INVISIBLE_CHARS = {"\u200b", "\u200c", "\u200d", "\ufeff"}

# 用户临时资料目录。本目录会在每次任务完成或重置后清空。
MATERIALS_DIR = PROJECT_ROOT / "materials"
LOCK_PATH = PROJECT_ROOT / ".lark_bot.lock"


# ---------------------------------------------------------------------------
# 状态管理：每个 chat_id 独立维护一份 state
# ---------------------------------------------------------------------------

_chat_states: dict[str, dict] = {}
_processed_message_ids: set[str] = set()


def get_state(chat_id: str) -> dict:
    """获取或初始化某个聊天的 state。"""
    if chat_id not in _chat_states:
        _chat_states[chat_id] = {
            "messages": [],
            "requirement": {},
        }
    return _chat_states[chat_id]


def reset_state(chat_id: str) -> None:
    """重置某个聊天的 state（例如用户说 '重新开始'）。"""
    _chat_states[chat_id] = {
        "messages": [],
        "requirement": {},
    }
    clear_materials_dir()


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def clean_user_input(text: str) -> str:
    """清理用户输入中的不可见字符。"""
    return "".join(ch for ch in text if ch not in INVISIBLE_CHARS).strip()


def clear_materials_dir() -> None:
    """清空用户临时资料目录，保留 .gitkeep。"""
    MATERIALS_DIR.mkdir(parents=True, exist_ok=True)

    for path in MATERIALS_DIR.iterdir():
        if path.name == ".gitkeep":
            continue

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except Exception as exc:
            print(f"[WARN] 清理资料失败: {path} ({exc})", file=sys.stderr)


def extract_resource_key(message_type: str, content: str) -> str:
    """从 lark-cli 事件 content 中提取文件或图片资源 key。"""
    try:
        data = json.loads(content) if isinstance(content, str) else content
    except json.JSONDecodeError:
        data = {}

    if not isinstance(data, dict):
        return ""

    if message_type == "image":
        return data.get("image_key", "")

    return data.get("file_key", "")


def download_message_resource(event: dict) -> str:
    """下载飞书文件/图片消息到 materials/，返回本地路径。"""
    message_type = event.get("message_type", "")
    message_id = event.get("message_id", "")
    content = event.get("content", "")
    file_key = extract_resource_key(message_type, content)

    if not message_id or not file_key:
        return ""

    resource_type = "image" if message_type == "image" else "file"
    MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
    output_name = _safe_material_filename(event, file_key)
    output_path = MATERIALS_DIR / output_name

    result = subprocess.run(
        [
            LARK_CLI,
            "im",
            "+messages-resources-download",
            "--message-id",
            message_id,
            "--file-key",
            file_key,
            "--type",
            resource_type,
            "--output",
            f"./{output_name}",
            "--as",
            "bot",
        ],
        cwd=str(MATERIALS_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "资料下载失败")

    return str(output_path)


def _safe_material_filename(event: dict, file_key: str) -> str:
    try:
        data = json.loads(event.get("content", ""))
    except json.JSONDecodeError:
        data = {}

    raw_name = ""
    if isinstance(data, dict):
        raw_name = data.get("file_name") or data.get("name") or ""

    if not raw_name:
        suffix = ".png" if event.get("message_type") == "image" else ".bin"
        raw_name = f"{file_key}{suffix}"

    safe_name = "".join(ch if ch.isalnum() or ch in ".-_ " else "_" for ch in raw_name)
    safe_name = safe_name.strip(" .") or f"{file_key}.bin"

    return safe_name


def acquire_single_instance_lock():
    """获取单实例锁，避免多个 bot 进程重复消费同一事件。"""
    lock_file = LOCK_PATH.open("w", encoding="utf-8")
    try:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock_file.close()
        return None

    return lock_file


def find_other_bot_processes() -> list[dict]:
    """检测同机是否已有其它 ppt_agent.lark_bot 进程。"""
    current_pid = os.getpid()
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-CimInstance Win32_Process | "
                "Where-Object { "
                "$_.Name -like 'python*' -and "
                "$_.CommandLine -like '*ppt_agent.lark_bot*' "
                "} | "
                "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0 or not result.stdout.strip():
        return []

    try:
        processes = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    if isinstance(processes, dict):
        processes = [processes]

    matched_processes = []
    for process in processes:
        try:
            process_id = int(process.get("ProcessId"))
        except (TypeError, ValueError):
            continue

        if process_id != current_pid:
            matched_processes.append(process)

    return matched_processes


def is_probable_bot_event(event: dict) -> bool:
    """尽量识别机器人自己发出的消息事件，避免自触发。"""
    sender_type = str(event.get("sender_type") or event.get("sender", {}).get("sender_type") or "").lower()
    if sender_type == "bot":
        return True

    content = str(event.get("content", "")).strip()
    return content.startswith(
        (
            "我需要你补充这些信息：",
            "需求信息已经完整。",
            "请发送资料文本或上传资料文件。",
            "项目资料已创建，请确认 PPT 制作方案：",
            "PPT 已生成：",
            "文件已发送：",
            "运行失败：",
        )
    )


def send_reply(message_id: str, chat_id: str, text: str) -> None:
    """通过 lark-cli 回复消息。"""
    if not text:
        return
    try:
        payload = text.strip()
        result = subprocess.run(
            [
                LARK_CLI, "im", "+messages-reply",
                "--message-id", message_id,
                "--markdown", payload,
                "--as", "bot",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(
                f"[ERROR] 回复失败: code={result.returncode}, stderr={result.stderr.strip()}",
                file=sys.stderr,
            )
    except subprocess.TimeoutExpired:
        print(f"[WARN] 回复超时: {message_id}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] 回复失败: {e}", file=sys.stderr)


def send_file(chat_id: str, file_path: str) -> None:
    """通过 lark-cli 发送文件到聊天。"""
    if not file_path or not Path(file_path).exists():
        return
    # lark-cli 要求 cwd-relative 路径
    abs_path = Path(file_path).resolve()
    cwd = abs_path.parent
    rel_name = abs_path.name
    try:
        subprocess.run(
            [
                LARK_CLI, "im", "+messages-send",
                "--chat-id", chat_id,
                "--file", f"./{rel_name}",
                "--as", "bot",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(cwd),
        )
    except subprocess.TimeoutExpired:
        print(f"[WARN] 发送文件超时: {file_path}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] 发送文件失败: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 核心：处理一条用户消息
# ---------------------------------------------------------------------------

def handle_message(event: dict) -> None:
    """
    处理一条 im.message.receive_v1 事件。

    事件字段（flat schema，lark-cli 已预处理）：
        .message_type  - 消息类型 (text / image / file / ...)
        .content       - 已渲染为人类可读文本
        .chat_id       - 聊天 ID (oc_xxx)
        .chat_type     - p2p / group
        .sender_id     - 发送者 open_id (ou_xxx)
        .message_id    - 消息 ID (om_xxx)
    """
    msg_type = event.get("message_type", "")
    chat_id = event.get("chat_id", "")
    message_id = event.get("message_id", "")
    content = event.get("content", "")

    print(f"[EVENT_RAW] {json.dumps(event, ensure_ascii=False)[:1000]}")

    if is_probable_bot_event(event):
        print(f"[INFO] 跳过机器人自身消息: {message_id}")
        return

    if message_id in _processed_message_ids:
        print(f"[INFO] 跳过重复消息: {message_id}")
        return
    if message_id:
        _processed_message_ids.add(message_id)

    state = get_state(chat_id)

    if msg_type in {"file", "image"}:
        if state.get("status") != "waiting_material_upload":
            send_reply(message_id, chat_id, "已收到文件。请先在资料步骤回复“添加资料”，再上传资料文件。")
            return

        try:
            local_path = download_message_resource(event)
        except Exception as exc:
            send_reply(message_id, chat_id, f"资料下载失败：{exc}")
            return

        text = local_path
    elif msg_type == "text":
        text = clean_user_input(content)
    else:
        send_reply(message_id, chat_id, "暂时只支持文本、文件和图片消息。")
        return

    if not text:
        return

    # 特殊命令
    if text.lower() in {"exit", "quit", "/reset", "重新开始"}:
        reset_state(chat_id)
        send_reply(message_id, chat_id, "已重置对话，请输入新的 PPT 需求。")
        return

    # 追加用户消息
    state["messages"].append(HumanMessage(content=text))

    # 清除上次的 assistant_reply
    state.pop("assistant_reply", None)

    # 处理 waiting 状态
    if state.get("status") == "waiting_confirm":
        print(f"[INFO] 用户确认中: {text}")

    # 让飞书侧第一时间看到收到消息，避免后续链路慢时以为没响应
    # send_reply(message_id, chat_id, f"收到：{text}")

    try:
        print(f"[INFO] 调用 LangGraph Agent... (chat={chat_id})")
        state = graph_app.invoke(state)
        print(
            "[STATE] "
            f"status={state.get('status')} "
            f"requirement_complete={state.get('requirement_complete')} "
            f"missing_fields={state.get('missing_fields')} "
            f"requirement={state.get('requirement')}"
        )
        # 更新存储的 state
        _chat_states[chat_id] = state
    except Exception as e:
        error_msg = f"Agent 运行出错：{e}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        send_reply(message_id, chat_id, error_msg)
        return

    # 提取回复
    reply = state.get("assistant_reply", "")

    # 发送文本回复
    if reply:
        send_reply(message_id, chat_id, reply)

    # 检查状态：项目已创建
    if state.get("status") == "project_created":
        return

    # 检查状态：PPT 已导出
    if state.get("status") == "ppt_exported":
        pptx_path = state.get("pptx_path", "")
        if pptx_path:
            send_file(chat_id, pptx_path)
            send_reply(message_id, chat_id, f"文件已发送：{pptx_path}")
            reset_state(chat_id)
        else:
            send_reply(message_id, chat_id, "PPT 已生成，但未找到文件路径。")
            reset_state(chat_id)
        return

    # 检查状态：失败
    if state.get("status") == "failed":
        error = state.get("error", "未知错误")
        send_reply(message_id, chat_id, f"运行失败：{error}")
        reset_state(chat_id)
        return


# ---------------------------------------------------------------------------
# 主循环：启动 lark-cli event consume 并逐行读取 NDJSON
# ---------------------------------------------------------------------------

def main() -> None:
    other_processes = find_other_bot_processes()
    if other_processes:
        print(
            f"[WARN] 检测到疑似其它 bot 进程，但不会阻止启动: {other_processes}",
            file=sys.stderr,
        )

    lock_file = acquire_single_instance_lock()
    if lock_file is None:
        print("[ERROR] 已有一个飞书机器人实例在运行，请先关闭旧窗口。", file=sys.stderr)
        return

    try:
        print("=" * 60)
        print("  PPT Agent 飞书机器人启动中...")
        print(f"  项目根目录: {PROJECT_ROOT}")
        print("=" * 60)

        # 切换工作目录到项目根
        os.chdir(str(PROJECT_ROOT))

        # 构建 lark-cli event consume 命令
        cmd = [
            LARK_CLI, "event", "consume",
            "im.message.receive_v1",
            "--as", "bot",
        ]

        print(f"[INFO] 执行: {' '.join(cmd)}")
        print("[INFO] 等待飞书消息...")
        print("[INFO] 按 Ctrl+C 退出")
        print()

        # 启动子进程 — stdin 必须保持打开，否则 event consume 会立即退出
        # 用 PIPE 但不关闭它，模拟 tail -f /dev/null
        proc = subprocess.Popen(
            cmd,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,  # line-buffered
        )

        # 先读 stderr 等 ready marker
        import threading

        def read_stderr():
            """读 stderr 并打印日志。"""
            for line in proc.stderr:
                line = line.rstrip("\n")
                if line:
                    print(f"[lark-cli] {line}", file=sys.stderr)
                    # 检测到 ready marker 就打印提示
                    if "ready" in line and "event_key" in line:
                        print("\n✓ 飞书事件监听已就绪，等待用户发消息...\n")

        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stderr_thread.start()

        # 逐行读 stdout（NDJSON）
        try:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[WARN] 非 JSON 行: {line}", file=sys.stderr)
                    continue

                print(f"[EVENT] 收到消息: {event.get('message_type', '?')} "
                      f"from={event.get('sender_id', '?')} "
                      f"chat={event.get('chat_id', '?')}")
                print(f"[EVENT] 内容: {event.get('content', '')[:100]}")

                # 异步处理消息（避免阻塞事件流）
                try:
                    handle_message(event)
                except Exception as e:
                    print(f"[ERROR] 处理消息异常: {e}", file=sys.stderr)

        except KeyboardInterrupt:
            print("\n[INFO] 收到中断信号，正在停止...")
            proc.terminate()
            proc.wait(timeout=5)

        print("[INFO] 机器人已停止。")
    finally:
        lock_file.close()
        try:
            LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    main()
