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
XMUM_COURSE_INCLUDE_REGEX=2026/04
XMUM_COURSE_EXCLUDE_REGEX=
```

Course filtering uses regular expressions against the full Moodle course title.

Examples:

```env
# Current semester only.
XMUM_COURSE_INCLUDE_REGEX=2026/04

# Only CYS/CST courses in the current semester.
XMUM_COURSE_INCLUDE_REGEX=^(CYS|CST).+2026/04

# Download every visible course.
XMUM_COURSE_INCLUDE_REGEX=

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

The GUI has a Moodle login screen and a separate model API access window. If at
least one enabled model provider has an API key, the note generation choice
becomes selectable. The current GUI only saves the choice; automatic AI note
generation is not wired yet.

Build a Windows executable:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --name XMUM-Moodle-Agent --paths src src\xmum_moodle_agent\gui.py
```

The generated executable is:

```text
dist\XMUM-Moodle-Agent\XMUM-Moodle-Agent.exe
```

## Output

- Course files: `data/courses/<course name>/`
- Download index: `data/index.json`
- Knowledge checklist: `data/XMUM_Knowledge_Checklist.docx`

## Security Notes

The agent reads credentials from `.env` or Windows environment variables only. `.env`, downloaded course files, generated documents, and logs are ignored by git.
