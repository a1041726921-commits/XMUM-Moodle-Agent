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

## Output

- Course files: `data/courses/<course name>/`
- Download index: `data/index.json`
- Knowledge checklist: `data/XMUM_Knowledge_Checklist.docx`

## Security Notes

The agent reads credentials from `.env` or Windows environment variables only. `.env`, downloaded course files, generated documents, and logs are ignored by git.
