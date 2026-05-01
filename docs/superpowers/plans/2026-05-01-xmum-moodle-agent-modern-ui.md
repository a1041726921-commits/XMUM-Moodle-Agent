# XMUM Moodle Agent Modern UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved modern PySide6 UI refresh for XMUM Moodle Agent.

**Architecture:** Keep the GUI in `src/xmum_moodle_agent/gui_qt.py`, adding focused reusable widgets for animated buttons and the moving light backdrop. Reuse existing page classes and signal wiring so behavior remains unchanged while visuals become consistent.

**Tech Stack:** Python 3.9+, PySide6, pytest.

---

### Task 1: Lock UI Structure With Tests

**Files:**
- Modify: `tests/test_gui_qt.py`

- [ ] Add tests that instantiate the Qt window with `QT_QPA_PLATFORM=offscreen`.
- [ ] Assert `AnimatedButton` and `LightBackdrop` are importable.
- [ ] Assert title bar exposes `minimizeButton` and `closeButton`, and not `maximizeButton`.
- [ ] Assert key buttons such as sidebar nav, login, download, and API settings are `AnimatedButton` instances.

### Task 2: Add Animated Widgets

**Files:**
- Modify: `src/xmum_moodle_agent/gui_qt.py`

- [ ] Add `AnimatedButton`, a `QPushButton` subclass with a paint-time scale property.
- [ ] Add hover animation through a dynamic `hoverProgress` property and stylesheet selectors.
- [ ] Add click feedback through `QPropertyAnimation` shrinking to about `0.94` then returning to `1.0`.
- [ ] Add variants for normal, primary, nav, title-minimize, and title-close.

### Task 3: Add Dynamic Backdrop

**Files:**
- Modify: `src/xmum_moodle_agent/gui_qt.py`

- [ ] Add `LightBackdrop`, a QWidget that paints two radial moving lights.
- [ ] Use `QTimer` to update slow movement.
- [ ] Place the light backdrop behind `windowContainer`.

### Task 4: Apply Unified Styling

**Files:**
- Modify: `src/xmum_moodle_agent/gui_qt.py`

- [ ] Replace button construction with a helper that returns `AnimatedButton`.
- [ ] Move title controls to the right and remove the old Mac traffic-light controls.
- [ ] Update stylesheet to use Source Han Serif with SimSun fallback.
- [ ] Update all panels, dialogs, tables, inputs, side nav, and status bars to share the same visual tokens.

### Task 5: Verify

**Files:**
- Modify: no production files unless failures require fixes.

- [ ] Run `python -m pytest tests/test_gui_qt.py`.
- [ ] Run the broader relevant test set if the focused test passes.
- [ ] Report exact verification status.
