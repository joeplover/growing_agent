import unittest
from unittest.mock import patch

from ppt_agent.nodes.ask_followup import ask_f_node
from ppt_agent.nodes.ask_material_node import ask_m_node
from ppt_agent.nodes.check_requirement import check_r_node
from ppt_agent.nodes.collect_material_node import collect_m_node
from ppt_agent.nodes.collect_requirement import collect_r_node
from ppt_agent.nodes.plan_deck import _build_fallback_outline
from ppt_agent.lark_bot import extract_resource_key, is_probable_bot_event, send_reply


class AskFollowupTests(unittest.TestCase):
    def test_missing_fields_are_rendered_as_actionable_markdown(self):
        result = ask_f_node({"missing_fields": ["topic", "page_count", "style"]})

        self.assertEqual(result["status"], "waiting_user")
        first_line = result["assistant_reply"].splitlines()[0]
        self.assertEqual(first_line, "我需要你补充这些信息：题目、页数、风格。")
        self.assertIn("- **题目**：PPT 的具体题目是什么？", result["assistant_reply"])
        self.assertIn("- **页数**：你希望大概做多少页？", result["assistant_reply"])
        self.assertIn("- **风格**：你希望 PPT 是什么风格？", result["assistant_reply"])
        self.assertIn("你可以直接按下面格式回复：", result["assistant_reply"])


class LarkReplyTests(unittest.TestCase):
    @patch("ppt_agent.lark_bot.subprocess.run")
    def test_multiline_reply_is_sent_as_markdown(self, run):
        run.return_value.returncode = 0

        send_reply("om_test", "oc_test", "我需要你补充这些信息：\n- 题目\n- 页数")

        args = run.call_args.args[0]
        self.assertIn("--markdown", args)
        self.assertNotIn("--text", args)
        self.assertEqual(args[args.index("--markdown") + 1], "我需要你补充这些信息：\n- 题目\n- 页数")

    def test_extracts_file_key_from_event_content_json(self):
        self.assertEqual(
            extract_resource_key("file", '{"file_key":"file_v3_abc","file_name":"demo.md"}'),
            "file_v3_abc",
        )

    def test_extracts_image_key_from_event_content_json(self):
        self.assertEqual(
            extract_resource_key("image", '{"image_key":"img_v3_abc"}'),
            "img_v3_abc",
        )

    def test_probable_bot_event_is_ignored_by_content_prefix(self):
        self.assertTrue(
            is_probable_bot_event(
                {
                    "message_type": "text",
                    "content": "项目资料已创建，请确认 PPT 制作方案：\n\n## 基本信息",
                }
            )
        )

    def test_probable_bot_event_is_ignored_by_sender_type(self):
        self.assertTrue(is_probable_bot_event({"sender_type": "bot", "content": "hello"}))


class AskMaterialTests(unittest.TestCase):
    def test_material_question_is_visible_in_first_line(self):
        result = ask_m_node({})

        self.assertEqual(result["status"], "waiting_material")
        first_line = result["assistant_reply"].splitlines()[0]
        self.assertEqual(first_line, "需求信息已经完整。是否要添加资料？")
        self.assertIn("- 添加资料", result["assistant_reply"])
        self.assertIn("- 不添加，直接生成", result["assistant_reply"])


class CheckRequirementTests(unittest.TestCase):
    def test_generic_ppt_request_is_never_complete(self):
        result = check_r_node(
            {
                "requirement": {
                    "topic": "PPT",
                    "use_case": "制作PPT",
                    "audience": "用户自己",
                    "page_count": 10,
                    "style": "默认风格",
                }
            }
        )

        self.assertFalse(result["requirement_complete"])
        self.assertEqual(
            result["missing_fields"],
            ["topic", "use_case", "audience", "style"],
        )


class CollectRequirementTests(unittest.TestCase):
    def test_short_reply_fills_the_only_missing_audience_field_without_llm(self):
        result = collect_r_node(
            {
                "messages": [_Message("自己看")],
                "requirement": {
                    "topic": "火影忍者",
                    "use_case": "个人欣赏",
                    "page_count": 3,
                    "style": "动漫风格",
                },
                "missing_fields": ["audience"],
            }
        )

        self.assertEqual(result["requirement"]["audience"], "自己看")
        self.assertEqual(result["status"], "collecting")

    def test_lark_reply_prefix_is_removed_before_filling_audience(self):
        result = collect_r_node(
            {
                "messages": [_Message("回复 乔珩:\u00a0\n自己看")],
                "requirement": {
                    "topic": "火影忍者",
                    "use_case": "个人欣赏",
                    "page_count": 3,
                    "style": "动漫风格",
                },
                "missing_fields": ["audience"],
            }
        )

        self.assertEqual(result["requirement"]["audience"], "自己看")


class CollectMaterialTests(unittest.TestCase):
    def test_add_material_choice_waits_for_user_material(self):
        result = collect_m_node(
            {
                "status": "waiting_material",
                "messages": [_Message("添加资料")],
                "material": {"raw_texts": [], "file_paths": []},
                "requirement": {"topic": "火影忍者"},
            }
        )

        self.assertEqual(result["status"], "waiting_material_upload")
        self.assertIn("请发送资料文本或上传资料文件", result["assistant_reply"])

    def test_uploaded_material_text_becomes_ready(self):
        result = collect_m_node(
            {
                "status": "waiting_material_upload",
                "messages": [_Message("鸣人是木叶村忍者，主题包含友情、成长与羁绊。")],
                "material": {"raw_texts": [], "file_paths": []},
                "requirement": {"topic": "火影忍者"},
            }
        )

        self.assertEqual(result["status"], "material_ready")
        self.assertEqual(result["material"]["raw_texts"], ["鸣人是木叶村忍者，主题包含友情、成长与羁绊。"])


class PlanDeckTests(unittest.TestCase):
    def test_fallback_outline_carries_material_evidence_per_slide(self):
        outline = _build_fallback_outline(
            {"topic": "\u706b\u5f71\u5fcd\u8005"},
            {
                "topic": "\u706b\u5f71\u5fcd\u8005",
                "keywords": ["\u7b2c\u4e03\u73ed", "\u7f81\u7eca"],
                "key_points": [
                    "\u9e23\u4eba\u60f3\u6210\u4e3a\u706b\u5f71",
                    "\u4f50\u52a9\u4e0e\u9e23\u4eba\u7684\u5173\u7cfb\u63a8\u52a8\u5267\u60c5",
                ],
                "summary": "\u706b\u5f71\u5fcd\u8005\u56f4\u7ed5\u9e23\u4eba\u7684\u6210\u957f\u3001\u7b2c\u4e03\u73ed\u7684\u7f81\u7eca\u548c\u5fcd\u8005\u4e16\u754c\u5c55\u5f00\u3002",
            },
            3,
        )

        self.assertEqual(len(outline), 3)
        self.assertTrue(all(slide.get("source_evidence") for slide in outline))
        self.assertIn("\u9e23\u4eba", outline[0]["source_evidence"])


class _Message:
    def __init__(self, content: str):
        self.content = content


if __name__ == "__main__":
    unittest.main()
