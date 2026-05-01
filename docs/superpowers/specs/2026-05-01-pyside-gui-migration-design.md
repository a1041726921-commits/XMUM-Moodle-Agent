# XMUM Moodle Agent PySide GUI Migration Design

## Goal

Replace the Tkinter desktop GUI with a polished PySide6 GUI while preserving all existing GUI workflows: Moodle sign-in, course discovery, semester filtering, course selection, selected-course download, local download folder opening, model API provider settings, note generation enablement state, app icon, course icon, and Windows high-DPI behavior.

## Approved Direction

Use PySide6 as the new GUI framework. The visual style remains the approved native Apple-style white interface:

- White main surfaces.
- Light Apple gray application shell.
- Apple blue primary actions.
- Soft borders, generous spacing, and clean typography.
- XMUM seal as the window and executable icon.
- Locally designed blue course icon for the Courses navigation item.

## Migration Strategy

Implement the new GUI in a separate module first, then switch the public entry point after parity checks pass:

- Create `src/xmum_moodle_agent/gui_qt.py` for the PySide6 implementation.
- Keep existing shared modules: `gui_actions.py`, `gui_state.py`, `gui_assets.py`, and `moodle.py`.
- Update `src/xmum_moodle_agent/gui.py` into a small compatibility entry point that imports and runs the PySide6 GUI.
- Remove Tkinter classes and Tkinter tests only after the PySide6 version covers the same behavior.

This keeps the risky part of the migration contained while preserving the `xmum-moodle-agent-gui` console script.

## PySide UI Structure

The main window uses:

- `QMainWindow` with a fixed minimum size around `980x680`.
- Left sidebar with brand label, Courses and Knowledge Notes navigation buttons, sign-in button, and status text.
- `QStackedWidget` for Home, Courses, and Knowledge Notes pages.
- Home page with centered app title and sign-in call to action.
- Courses page with semester `QComboBox`, course table, select-all checkbox, selected count, open-folder button, and download button.
- Notes page with API status, provider combo, note generation checkbox, and API settings dialog.

Dialogs:

- Login dialog collects username, password, remember password, and auto-login settings.
- API settings dialog edits the existing model provider list.

## Functional Parity

The PySide GUI must preserve the behaviors currently tested for Tkinter:

- Sidebar exposes only `courses` and `notes`.
- Navigation is disabled before login.
- Attempting to open a locked page prompts login.
- Successful login stores the discovered courses, chooses the latest term, filters visible courses, and selects all courses in that term.
- Course checkbox toggling updates selected course URLs and count text.
- Download action refuses empty selection and downloads selected courses through `download_selected_courses`.
- API settings save through `save_gui_settings`, refresh provider choices, and enable note generation only when at least one provider is enabled and keyed.
- DPI awareness runs before the Qt app is created.

## Threading

Long operations should not block the Qt event loop:

- Login/course loading runs on a Python background thread and returns results to the UI through Qt signals.
- Downloading selected courses runs on a Python background thread and returns the report through Qt signals.
- UI controls enter a busy disabled state during background work.

## Packaging

Use PySide6 as a runtime dependency. PyInstaller specs should:

- Point to `src\xmum_moodle_agent\gui.py`.
- Include `src\xmum_moodle_agent\assets`.
- Keep `icon='src\\xmum_moodle_agent\\assets\\xmum.ico'`.

The generated executable remains `dist\XMUM-Moodle-Agent-Standalone.exe`.

## Tkinter Removal

After PySide6 parity verification:

- Remove Tkinter implementation classes from `gui.py`.
- Remove Tkinter-specific tests and replace them with Qt tests.
- Keep `gui_assets.py` because PySide6 still uses the shared asset paths and DPI helper.

## Verification

Required checks:

- `python -m unittest discover -v`
- A Qt smoke test that instantiates the main window offscreen and verifies title, icon path, navigation pages, theme QSS, and login-success course selection behavior.
- A manual launch of `python -m xmum_moodle_agent.gui` once PySide6 is installed.
- A PyInstaller build using `XMUM-Moodle-Agent-Standalone.spec`.
