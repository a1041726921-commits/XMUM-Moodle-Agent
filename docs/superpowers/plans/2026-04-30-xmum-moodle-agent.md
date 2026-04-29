# XMUM Moodle Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local scheduled Python agent that downloads XMUM Moodle course materials and maintains a bilingual `.docx` knowledge checklist.

**Architecture:** Use a small Python package with clear modules for config, Moodle browser automation, downloads, indexing, parsing, knowledge generation, DOCX writing, and scheduling. Keep Moodle-specific Playwright selectors isolated so deterministic local behavior can be unit tested without logging in.

**Tech Stack:** Python 3.9+, Playwright, python-dotenv, beautifulsoup4, python-docx, pypdf, python-pptx, unittest.

---

### Task 1: Project Skeleton And Config

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/xmum_moodle_agent/__init__.py`
- Create: `src/xmum_moodle_agent/config.py`
- Test: `tests/test_config.py`

- [ ] Write tests for `.env` parsing, default paths, and missing credentials.
- [ ] Implement `AgentConfig` and `load_config()`.
- [ ] Verify tests pass with `python -m unittest tests.test_config -v`.

### Task 2: Models, Index, And File Naming

**Files:**
- Create: `src/xmum_moodle_agent/models.py`
- Create: `src/xmum_moodle_agent/index.py`
- Create: `src/xmum_moodle_agent/files.py`
- Test: `tests/test_index_and_files.py`

- [ ] Write tests for course/resource models, safe filenames, hash calculation, and index upsert behavior.
- [ ] Implement minimal model dataclasses and JSON index persistence.
- [ ] Verify tests pass with `python -m unittest tests.test_index_and_files -v`.

### Task 3: Parsing And Knowledge Generation

**Files:**
- Create: `src/xmum_moodle_agent/parser.py`
- Create: `src/xmum_moodle_agent/knowledge.py`
- Test: `tests/test_parser_knowledge.py`

- [ ] Write tests for plain text extraction fallback and deterministic bilingual note generation.
- [ ] Implement supported extractors for TXT, PDF, DOCX, PPTX, with graceful unsupported handling.
- [ ] Implement local professor-style note generation from extracted headings and text chunks.
- [ ] Verify tests pass with `python -m unittest tests.test_parser_knowledge -v`.

### Task 4: DOCX Writer

**Files:**
- Create: `src/xmum_moodle_agent/docx_writer.py`
- Test: `tests/test_docx_writer.py`

- [ ] Write tests that generate a `.docx` and verify expected text appears.
- [ ] Implement Word checklist generation.
- [ ] Verify tests pass with `python -m unittest tests.test_docx_writer -v`.

### Task 5: Moodle Automation, Downloads, Scheduler, CLI

**Files:**
- Create: `src/xmum_moodle_agent/moodle.py`
- Create: `src/xmum_moodle_agent/downloader.py`
- Create: `src/xmum_moodle_agent/scheduler.py`
- Create: `src/xmum_moodle_agent/cli.py`
- Create: `README.md`

- [ ] Implement Playwright login from environment credentials.
- [ ] Implement course and resource discovery from Moodle pages.
- [ ] Implement download orchestration and index updates.
- [ ] Implement `xmum-moodle-agent run`, `check-login`, `init`, and `install-schedule`.
- [ ] Document setup and daily schedule installation.

### Task 6: Verification

**Files:**
- Modify as needed based on failures.

- [ ] Run `python -m unittest discover -v`.
- [ ] Run `python -m xmum_moodle_agent.cli --help` with `PYTHONPATH=src`.
- [ ] Run `python -m xmum_moodle_agent.cli init` in a safe local workspace.
- [ ] Confirm no secrets are present in committed files or logs.
