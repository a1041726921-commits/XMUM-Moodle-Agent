# XMUM Moodle Agent PySide GUI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fully replace the Tkinter GUI with a PySide6 GUI while preserving the current Moodle, course selection, download, API settings, icon, and high-DPI behaviors.

**Architecture:** Build `gui_qt.py` as the new implementation using existing non-UI modules for state, actions, assets, and Moodle automation. Once parity tests pass, turn `gui.py` into a thin PySide entry point and remove Tkinter-specific classes/tests.

**Tech Stack:** Python 3.9, PySide6, Qt Widgets, unittest, PyInstaller.

---

### Task 1: Add PySide6 Dependency And Qt Test Harness

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/test_gui_qt.py`

- [ ] Add `PySide6>=6.6` to project dependencies.
- [ ] Write a failing import test:

```python
class QtGuiImportTests(unittest.TestCase):
    def test_qt_gui_module_exposes_main_window(self):
        from xmum_moodle_agent import gui_qt
        self.assertTrue(hasattr(gui_qt, "MoodleAgentQtWindow"))
```

- [ ] Run `.\.venv\Scripts\python.exe -m unittest tests.test_gui_qt -v`.
- [ ] Expected before implementation: failure because `xmum_moodle_agent.gui_qt` does not exist or PySide6 is missing.

### Task 2: Implement PySide Window Skeleton

**Files:**
- Create: `src/xmum_moodle_agent/gui_qt.py`
- Test: `tests/test_gui_qt.py`

- [ ] Add tests that instantiate a QApplication in offscreen mode, create `MoodleAgentQtWindow(Path(tmp))`, and assert title, page names, nav pages, icon path, and status text.
- [ ] Implement minimal `QMainWindow`, sidebar, stacked pages, app icon, theme stylesheet, and disabled navigation.
- [ ] Run `.\.venv\Scripts\python.exe -m unittest tests.test_gui_qt -v`.
- [ ] Expected after implementation: tests pass.

### Task 3: Port Login And Course Selection Behavior

**Files:**
- Modify: `src/xmum_moodle_agent/gui_qt.py`
- Test: `tests/test_gui_qt.py`

- [ ] Add a failing test for `_handle_login_success()` using three sample courses across two terms.
- [ ] Expected behavior: `logged_in` is true, selected term is latest, current-term courses are selected by default, and Courses page is active.
- [ ] Implement term population, filtering, course table rows, checkbox state, selected count refresh, select-all behavior, and locked navigation behavior.
- [ ] Run `.\.venv\Scripts\python.exe -m unittest tests.test_gui_qt -v`.

### Task 4: Port Login Dialog, API Settings Dialog, And Download Flow

**Files:**
- Modify: `src/xmum_moodle_agent/gui_qt.py`
- Test: `tests/test_gui_qt.py`

- [ ] Add tests for provider combo refresh and note generation enablement using `GuiSettings`.
- [ ] Add tests for empty download selection refusing to start.
- [ ] Implement `LoginDialog`, `ApiSettingsDialog`, save handlers, background-thread login worker, background-thread download worker, busy state, and error dialogs.
- [ ] Run `.\.venv\Scripts\python.exe -m unittest tests.test_gui_qt -v`.

### Task 5: Switch Public Entry Point And Remove Tkinter

**Files:**
- Modify: `src/xmum_moodle_agent/gui.py`
- Modify: `tests/test_gui_layout.py`
- Test: `tests/test_gui_qt.py`

- [ ] Replace `src/xmum_moodle_agent/gui.py` with a thin compatibility wrapper:

```python
from xmum_moodle_agent.gui_qt import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] Remove Tkinter-specific layout tests or rewrite them to import PySide classes.
- [ ] Keep asset tests because they remain framework-independent.
- [ ] Run `.\.venv\Scripts\python.exe -m unittest tests.test_gui_qt tests.test_gui_assets -v`.

### Task 6: Update Packaging And Documentation

**Files:**
- Modify: `XMUM-Moodle-Agent-Standalone.spec`
- Modify: `XMUM-Moodle-Agent-Standalone-Fixed.spec`
- Modify: `README.md`

- [ ] Ensure both PyInstaller specs still target `src\\xmum_moodle_agent\\gui.py`, include assets, and preserve the XMUM icon.
- [ ] Update README to say the desktop GUI is PySide6-based and high-DPI aware.
- [ ] Run `.\.venv\Scripts\python.exe -m unittest discover -v`.
- [ ] Run `.\.venv\Scripts\python.exe -m PyInstaller --noconfirm XMUM-Moodle-Agent-Standalone.spec`.
