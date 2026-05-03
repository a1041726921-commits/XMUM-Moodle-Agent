# XMUM Moodle Downloader

XMUM Moodle Downloader 是一个本地运行的 Python 工具，用于登录 XMUM Moodle，自动发现课程，下载课件资料，并按学期和课程整理到本地文件夹。

## 现成版本

现成的 Windows 版本会发布在 [GitHub Releases](https://github.com/a1041726921-commits/XMUM-Moodle-Agent/releases) 页面，可以直接下载使用。

## 功能

- 登录 XMUM Moodle 并检查账号是否可用
- 自动发现 Moodle 中可见的课程
- 支持按学期筛选课程，例如 `2026/04`、`2025/09`
- 下载选中的课程资料
- 避免覆盖同名本地文件
- 使用索引记录已下载资料，减少重复下载
- 提供 PySide6/Qt 桌面图形界面
- 支持打包为 Windows 独立可执行文件

## 安装

在 PowerShell 中进入项目目录：

```powershell
cd D:\XMUM-Moodle-Downloader
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m xmum_moodle_downloader.cli init
```

然后编辑 `.env`：

```env
XMUM_MOODLE_USERNAME=your-campus-id
XMUM_MOODLE_PASSWORD=your-password
XMUM_COURSE_INCLUDE_REGEX=
XMUM_COURSE_EXCLUDE_REGEX=
```

`XMUM_COURSE_INCLUDE_REGEX` 和 `XMUM_COURSE_EXCLUDE_REGEX` 是可选的课程筛选规则，使用正则表达式匹配完整课程标题。

## 课程筛选示例

下载所有发现到的课程，包括已完成或从视图中隐藏的课程：

```env
XMUM_COURSE_INCLUDE_REGEX=
```

只下载当前学期的 CYS / CST 课程：

```env
XMUM_COURSE_INCLUDE_REGEX=^(CYS|CST).+2026/04
```

排除通识类课程：

```env
XMUM_COURSE_EXCLUDE_REGEX=^G
```

课程发现会打开：

```text
https://l.xmu.edu.my/my/courses.php
```

程序会尽量切换到 `All (including removed from view)` 视图，并展开隐藏的课程卡片，以便发现更多课程。

## 命令行用法

检查 Moodle 登录状态：

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_downloader.cli check-login
```

运行下载流程：

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_downloader.cli run
```

安装每天 08:00 自动运行的 Windows 计划任务：

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_downloader.cli install-schedule --time 08:00
```

## Windows 图形界面

启动桌面 GUI：

```powershell
.\.venv\Scripts\python.exe -m xmum_moodle_downloader.gui
```

图形界面基于 PySide6/Qt 构建，并在启动时启用 Windows 高 DPI 适配，让界面在缩放显示器上保持清晰。

启动后会先显示登录页面。点击 `Sign In to Moodle` 后会弹出登录窗口；登录成功前，课程选择和下载功能会保持锁定。

登录成功后，主界面左侧会显示导航栏：

- `Courses`：选择学期，例如 `2026/04` 或 `2025/09`，然后勾选要下载的课程。
- 学期选项会根据 Moodle 中发现的课程标题自动生成。
- 默认会选择最新学期，并自动勾选该学期的全部课程。
- 点击 `Download Selected` 下载选中课程资料。
- 点击 `Open Folder` 打开本地课件目录。

已经记录在索引中的课件会被跳过；如果本地已经存在同名文件，程序不会覆盖原文件，而是生成新的文件名。

下载后的课件会按学期和课程整理，例如：

```text
data/courses/2025-09/<course name>/
```

## 打包为 Windows 可执行文件

安装开发依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

使用 PyInstaller 打包：

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --onefile --name XUMU-moodle-downloader --paths src --add-data "src\xmum_moodle_downloader\assets;xmum_moodle_downloader\assets" --icon src\xmum_moodle_downloader\assets\xmum.ico src\xmum_moodle_downloader\gui.py
```

生成的可执行文件位于：

```text
dist\XUMU-moodle-downloader.exe
```

不要直接运行 `build\` 目录中的文件；该目录只包含 PyInstaller 的中间产物，可能缺少必要 DLL。

## 输出目录

- 课程文件：`data/courses/<course name>/`
- 下载索引：`data/index.json`

## 安全说明

程序只会从 `.env` 或 Windows 环境变量中读取账号密码。

`.env`、下载的课程文件、运行日志、构建产物和本地状态文件都已通过 `.gitignore` 忽略，不应提交到 GitHub。
