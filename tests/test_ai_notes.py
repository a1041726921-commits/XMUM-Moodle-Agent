import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from xmum_moodle_agent.ai_notes import (
    COURSE_KNOWLEDGE_CHECKLIST_PROMPT,
    OUTPUT_DOCX_FILENAME,
    build_materials_prompt,
    build_provider_request,
    generate_course_knowledge_checklist,
    select_note_provider,
    test_provider_connection,
)
from xmum_moodle_agent.index import MaterialIndex
from xmum_moodle_agent.models import Resource


class AiNotesTests(unittest.TestCase):
    def test_prompt_and_output_filename_match_course_checklist_contract(self):
        self.assertEqual(OUTPUT_DOCX_FILENAME, "Course_Knowledge_Checklist.docx")
        self.assertIn("课程知识整理 Agent", COURSE_KNOWLEDGE_CHECKLIST_PROMPT)
        self.assertIn("章节（Chapter/Module）→小节（Section）→知识点（Key Concepts）", COURSE_KNOWLEDGE_CHECKLIST_PROMPT)
        self.assertIn("python-docx", COURSE_KNOWLEDGE_CHECKLIST_PROMPT)

    def test_select_note_provider_uses_first_connected_provider_without_user_model_choice(self):
        provider = select_note_provider(
            [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4o-mini",
                    "api_key": "",
                    "enabled": True,
                },
                {
                    "id": "deepseek",
                    "name": "DeepSeek",
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "api_key": "sk-test",
                    "enabled": True,
                },
            ]
        )

        self.assertEqual(provider["id"], "deepseek")
        self.assertEqual(provider["model"], "deepseek-chat")

    def test_google_provider_request_uses_official_openai_compatible_endpoint(self):
        url, headers, payload = build_provider_request(
            {
                "id": "google",
                "name": "Google",
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "model": "gemini-3-flash-preview",
                "api_key": "gemini-key",
            },
            "system",
            "ping",
            max_tokens=12,
        )

        self.assertEqual(url, "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
        self.assertEqual(headers["authorization"], "Bearer gemini-key")
        self.assertEqual(payload["model"], "gemini-3-flash-preview")
        self.assertEqual(payload["max_tokens"], 12)

    def test_anthropic_provider_request_uses_messages_api(self):
        url, headers, payload = build_provider_request(
            {
                "id": "anthropic",
                "name": "Anthropic",
                "base_url": "https://api.anthropic.com/v1",
                "model": "claude-sonnet-4-5",
                "api_key": "anthropic-key",
            },
            "system",
            "ping",
            max_tokens=12,
        )

        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(headers["x-api-key"], "anthropic-key")
        self.assertEqual(payload["system"], "system")
        self.assertEqual(payload["max_tokens"], 12)

    def test_provider_connection_sends_minimal_ping_request(self):
        calls = []

        def fake_request(url, headers, payload):
            calls.append({"url": url, "headers": headers, "payload": payload})
            return {"choices": [{"message": {"content": "ok"}}]}

        message = test_provider_connection(
            {
                "id": "openai",
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "api_key": "sk-test",
            },
            request_json=fake_request,
        )

        self.assertEqual(message, "ok")
        self.assertEqual(calls[0]["payload"]["messages"][-1]["content"], "ping")
        self.assertLessEqual(calls[0]["payload"]["max_tokens"], 16)

    def test_build_materials_prompt_groups_parsed_course_content(self):
        text = build_materials_prompt(
            {
                "Linear Algebra": [
                    {
                        "title": "Lecture 01",
                        "source_file": "lecture01.pdf",
                        "text": "Linear transformation maps vectors from one space to another.",
                    }
                ]
            }
        )

        self.assertIn("Course: Linear Algebra", text)
        self.assertIn("Material: Lecture 01", text)
        self.assertIn("Linear transformation maps vectors", text)

    def test_generate_course_knowledge_checklist_calls_api_and_writes_docx(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material = root / "data" / "courses" / "lecture.txt"
            material.parent.mkdir(parents=True)
            material.write_text(
                "Lecture 01: Linear Algebra\n\nLinear Transformation\nA linear transformation preserves addition.",
                encoding="utf-8",
            )
            index = MaterialIndex(root / "data" / "index.json")
            index.upsert_downloaded(
                Resource("Lecture 01", "https://example.test/lecture", "Linear Algebra", ".txt"),
                material,
                "sha",
            )
            index.save()

            calls = []

            def fake_request(url, headers, payload):
                calls.append({"url": url, "headers": headers, "payload": payload})
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "# 课程知识清单\n\n## Chapter 1\n\n### 线性变换（Linear Transformation）\n定义：保持线性结构。"
                            }
                        }
                    ]
                }

            output = generate_course_knowledge_checklist(
                root,
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-test",
                    "enabled": True,
                },
                request_json=fake_request,
            )

            with ZipFile(output) as docx_zip:
                document_xml = docx_zip.read("word/document.xml").decode("utf-8")

        self.assertEqual(output.name, OUTPUT_DOCX_FILENAME)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(calls[0]["payload"]["model"], "gpt-4o-mini")
        serialized_payload = json.dumps(calls[0]["payload"], ensure_ascii=False)
        self.assertIn("课程知识整理 Agent", serialized_payload)
        self.assertIn("Linear Transformation", serialized_payload)
        self.assertIn("课程知识清单", document_xml)
        self.assertIn("线性变换", document_xml)


if __name__ == "__main__":
    unittest.main()
