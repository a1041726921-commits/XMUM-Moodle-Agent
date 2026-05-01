# XMUM Moodle Agent

This local Python agent logs in to XMUM Moodle, downloads course materials, organizes them by course folder, and rebuilds a bilingual Word knowledge checklist.

## Setup

```powershell
cd D:\AGENT
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m xmum_moodle_agent.cli init
```

Edit `.env`:

```env
XMUM_MOODLE_USERNAME=your-campus-id
XMUM_MOODLE_PASSWORD=your-password
XMUM_COURSE_INCLUDE_REGEX=
XMUM_COURSE_EXCLUDE_REGEX=
```

Course discovery opens `https://l.xmu.edu.my/my/courses.php`, switches the Moodle
view to `All (including removed from view)` when possible, and expands hidden
course cards. Course filtering is optional and uses regular expressions against
the full Moodle course title.

Examples:

```env
# Download every discovered course, including completed and expired courses.
XMUM_COURSE_INCLUDE_REGEX=

# Only CYS/CST courses in the current semester.
XMUM_COURSE_INCLUDE_REGEX=^(CYS|CST).+2026/04

# Exclude general education courses.
XMUM_COURSE_EXCLUDE_REGEX=^G
```

## Commands

Check login:

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_agent.cli check-login
```

Run the agent:

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_agent.cli run
```

Install the daily 08:00 Windows scheduled task:

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_agent.cli install-schedule --time 08:00
```

## Windows GUI

Launch the desktop GUI:

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_agent.gui
```

The GUI is built with PySide6/Qt and enables Windows high-DPI awareness at startup
so the modern white interface stays sharp on scaled displays.

The GUI opens on a startup page with a `Sign In to Moodle` button. Pressing it opens a
login popup; course selection, downloads, and knowledge-note settings stay locked
until the login succeeds.

After login, the main window uses a left sidebar:

- `Courses`: choose a semester such as `2026/04` or `2025/09`, then tick courses.
  The semester selector is generated from visible Moodle course titles, defaults
  to the latest term, and ticks all courses in that term after login. Use
  `Download Selected` to download, or `Open Folder` to open the local courseware folder.
- `Knowledge Notes`: choose an API source such as `OPENAI`, `GOOGLE`,
  `ANTHROPIC`, `ALIBABA`, `XIAOMI`, or `DEEPSEEK`, enter the API key, and use
  `Test API` to check the connection before generating notes. The app does not
  expose model selection in the UI; each provider uses an internal default model
  and writes `Course_Knowledge_Checklist.docx`.

Existing indexed courseware is skipped, and an existing same-name local file is
not overwritten. Downloaded courseware is grouped by semester under
`data/courses/<term>/<course name>/`, for example `data/courses/2025-09/...`.

Build a Windows executable:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onefile --name XMUM-Moodle-Agent-Standalone --paths src --add-data "src\xmum_moodle_agent\assets;xmum_moodle_agent\assets" --icon src\xmum_moodle_agent\assets\xmum.ico src\xmum_moodle_agent\gui.py
```

The generated executable is:

```text
dist\XMUM-Moodle-Agent-Standalone.exe
```

Do not run executables from `build\`; that folder only contains PyInstaller
intermediate files and can miss bundled DLLs.

## Output

- Course files: `data/courses/<course name>/`
- Download index: `data/index.json`
- Knowledge checklist: `data/Course_Knowledge_Checklist.docx`

## Security Notes

The agent reads credentials from `.env` or Windows environment variables only. `.env`, downloaded course files, generated documents, and logs are ignored by git.
