# XMUM Moodle Agent Apple UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the existing Tkinter GUI into the approved native Apple-style white UI, add XMUM executable/window icons, add a locally designed course icon, and enable Windows high-DPI awareness.

**Architecture:** Keep the current Tkinter application and workflow logic intact. Add a small UI support module for theme tokens, asset paths, asset generation, icon loading, and DPI awareness so deterministic behavior can be unit tested without opening the GUI.

**Tech Stack:** Python 3.9, Tkinter/ttk, pre-generated PNG/ICO assets, PyInstaller specs, unittest.

---

### Task 1: Assets, Paths, And DPI Support

**Files:**
- Create: `src/xmum_moodle_agent/gui_assets.py`
- Create: `src/xmum_moodle_agent/assets/xmum.ico`
- Create: `src/xmum_moodle_agent/assets/course.png`
- Modify: `pyproject.toml`
- Test: `tests/test_gui_assets.py`

- [ ] Write tests that assert the app icon path, course icon path, theme colors, and DPI helper exist.
- [ ] Run `python -m unittest tests.test_gui_assets -v` and confirm the tests fail because `gui_assets.py` does not exist.
- [ ] Implement `APPLE_THEME`, `asset_path()`, `app_icon_path()`, `course_icon_path()`, `ensure_icon_assets()`, and `enable_windows_dpi_awareness()`.
- [ ] Generate `xmum.ico` from `C:\Users\10417\Downloads\xmum.jpeg` and draw `course.png` locally with a simple rounded book/course glyph, without adding a runtime image dependency.
- [ ] Run `python -m unittest tests.test_gui_assets -v` and confirm it passes.

### Task 2: Runtime Icon And Apple-Style Tkinter Theme

**Files:**
- Modify: `src/xmum_moodle_agent/gui.py`
- Test: `tests/test_gui_layout.py`

- [ ] Add a failing layout test that creates `MoodleAgentGui`, verifies `app.app_icon.exists()`, checks Apple theme colors, and checks that the courses nav control has an image reference.
- [ ] Run the focused test and confirm it fails before production code changes.
- [ ] Import the new GUI asset helpers.
- [ ] Call `enable_windows_dpi_awareness()` before creating `MoodleAgentGui`.
- [ ] Call `ensure_icon_assets()` and set the Tk window icon via `iconbitmap()` on Windows-compatible `.ico`.
- [ ] Rework style configuration to use white base, `#f5f5f7` app background, Apple blue primary buttons, and neutral system grays.
- [ ] Replace plain text navigation with icon+label nav rows so the Courses item uses the generated course icon.
- [ ] Run `python -m unittest tests.test_gui_layout -v` and confirm it passes.

### Task 3: Packaging Metadata

**Files:**
- Modify: `XMUM-Moodle-Agent-Standalone.spec`
- Modify: `XMUM-Moodle-Agent-Standalone-Fixed.spec`
- Modify: `README.md`
- Test: `tests/test_gui_assets.py`

- [ ] Add failing tests that parse both spec files and assert they include `icon='src\\xmum_moodle_agent\\assets\\xmum.ico'`.
- [ ] Run `python -m unittest tests.test_gui_assets -v` and confirm the new spec assertions fail.
- [ ] Add `datas=[('src\\xmum_moodle_agent\\assets', 'xmum_moodle_agent\\assets')]` and `icon='src\\xmum_moodle_agent\\assets\\xmum.ico'` to both PyInstaller specs.
- [ ] Update README build command to include `--icon src\xmum_moodle_agent\assets\xmum.ico` and mention DPI awareness.
- [ ] Run `python -m unittest tests.test_gui_assets -v` and confirm it passes.

### Task 4: Full Verification

**Files:**
- Modify only as needed based on failures.

- [ ] Run `python -m unittest discover -v`.
- [ ] Run `python -m xmum_moodle_agent.gui` long enough to confirm the GUI launches with the new white Apple-style shell.
- [ ] Confirm `src/xmum_moodle_agent/assets/xmum.ico` and `src/xmum_moodle_agent/assets/course.png` exist.
- [ ] Review `git diff -- src tests pyproject.toml README.md XMUM-Moodle-Agent-Standalone.spec XMUM-Moodle-Agent-Standalone-Fixed.spec`.
