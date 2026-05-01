# -*- coding: utf-8 -*-
import asyncio
import math
import os
import re
import sys
import threading
import traceback
from pathlib import Path

from PySide6.QtCore import Property, QEasingCurve, QObject, QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QPropertyAnimation

from xmum_moodle_agent.ai_notes import generate_course_knowledge_checklist, select_note_provider, test_provider_connection
from xmum_moodle_agent.gui_actions import (
    course_terms_from_courses,
    download_selected_courses,
    filter_courses_by_term,
    visible_courses_after_login,
)
from xmum_moodle_agent.gui_assets import (
    app_icon_path,
    asset_path,
    enable_windows_dpi_awareness,
    ensure_icon_assets,
)
from xmum_moodle_agent.gui_state import (
    agent_config_from_gui_settings,
    can_generate_notes,
    load_gui_settings,
    save_gui_settings,
)
from xmum_moodle_agent.moodle import MoodleClient


class OperationSignals(QObject):
    login_success = Signal(list)
    download_success = Signal(object)
    notes_success = Signal(str)
    error = Signal(str, str)


MODERN_THEME = {
    "app_bg": "rgba(255, 255, 255, 42)",
    "sidebar_bg": "rgba(255, 255, 255, 118)",
    "title_bg": "rgba(255, 255, 255, 74)",
    "surface": "rgba(255, 255, 255, 176)",
    "surface_alt": "rgba(244, 249, 255, 146)",
    "border": "#cbd8e8",
    "border_soft": "#dce7f4",
    "text": "#182232",
    "text_secondary": "#64748b",
    "text_tertiary": "#94a3b8",
    "primary": "#2563eb",
    "primary_active": "#1d4ed8",
    "primary_disabled": "#a9c4f8",
    "nav_active": "#dbeafe",
}


_LOADED_UI_FONT_FAMILIES = None


def _load_ui_fonts():
    global _LOADED_UI_FONT_FAMILIES
    if _LOADED_UI_FONT_FAMILIES is not None:
        return list(_LOADED_UI_FONT_FAMILIES)

    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = (
        # Drop custom fonts here when you want PyInstaller to bundle them.
        asset_path("fonts/SegoeUI.ttf"),
        asset_path("fonts/MicrosoftYaHei.ttc"),
        asset_path("fonts/NotoSansSC-VF.ttf"),
        asset_path("fonts/SourceHanSansCN-Normal.ttf"),
        asset_path("fonts/MicrosoftYaHei.ttf"),
        windir / "Fonts" / "segoeui.ttf",
        windir / "Fonts" / "msyh.ttc",
    )
    families = []
    for path in candidates:
        if not path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            continue
        for family in QFontDatabase.applicationFontFamilies(font_id):
            if family not in families:
                families.append(family)
    _LOADED_UI_FONT_FAMILIES = families
    return list(families)


def _ui_font_stack() -> str:
    families = [
        "Segoe UI",
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "Segoe UI",
        "PingFang SC",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
    ]
    families = _load_ui_fonts() + families
    unique = []
    for family in families:
        if family and family not in unique:
            unique.append(family)
    return ", ".join(f'"{family}"' for family in unique) + ", sans-serif"


def _preferred_widget_font_family() -> str:
    families = _load_ui_fonts()
    for family in ("Microsoft YaHei", "Microsoft YaHei UI", "Segoe UI"):
        if family in families:
            return family
    return "Microsoft YaHei"


def _css_color(value) -> QColor:
    if isinstance(value, QColor):
        return QColor(value)
    text = str(value).strip()
    match = re.fullmatch(r"rgba?\(([^)]+)\)", text, flags=re.IGNORECASE)
    if match:
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) in (3, 4):
            red, green, blue = (max(0, min(255, int(float(part)))) for part in parts[:3])
            alpha = 255
            if len(parts) == 4:
                raw_alpha = float(parts[3])
                alpha = round(raw_alpha * 255) if raw_alpha <= 1 else round(raw_alpha)
                alpha = max(0, min(255, alpha))
            return QColor(red, green, blue, alpha)
    return QColor(text)


def _mix_color(start: str, end: str, progress: float) -> QColor:
    progress = max(0.0, min(1.0, progress))
    a = _css_color(start)
    b = _css_color(end)
    return QColor(
        round(a.red() + (b.red() - a.red()) * progress),
        round(a.green() + (b.green() - a.green()) * progress),
        round(a.blue() + (b.blue() - a.blue()) * progress),
        round(a.alpha() + (b.alpha() - a.alpha()) * progress),
    )


class AnimatedButton(QPushButton):
    PALETTES = {
        "default": {
            "base": "#f8fbff",
            "hover": "#eaf3ff",
            "checked": "#dbeafe",
            "border": "#d6e1ee",
            "text": "#182232",
            "disabled": "#eef3f8",
        },
        "primary": {
            "base": "#2563eb",
            "hover": "#1d4ed8",
            "checked": "#1d4ed8",
            "border": "#2563eb",
            "text": "#ffffff",
            "disabled": "#a9c4f8",
        },
        "nav": {
            "base": "rgba(255, 255, 255, 0)",
            "hover": "#eaf3ff",
            "checked": "#dbeafe",
            "border": "rgba(255, 255, 255, 0)",
            "text": "#334155",
            "checked_text": "#174ea6",
            "disabled": "rgba(255, 255, 255, 0)",
        },
        "titleMinimize": {
            "base": "rgba(255, 255, 255, 0)",
            "hover": "#dbeafe",
            "checked": "#dbeafe",
            "border": "rgba(255, 255, 255, 0)",
            "text": "#334155",
            "disabled": "rgba(255, 255, 255, 0)",
        },
        "titleClose": {
            "base": "rgba(255, 255, 255, 0)",
            "hover": "#fee2e2",
            "checked": "#fee2e2",
            "border": "rgba(255, 255, 255, 0)",
            "text": "#334155",
            "hover_text": "#dc2626",
            "disabled": "rgba(255, 255, 255, 0)",
        },
    }

    def __init__(self, *args, variant: str = "default", parent=None):
        if len(args) >= 2 and isinstance(args[0], QIcon):
            super().__init__(args[0], args[1], parent)
        elif args:
            super().__init__(args[0], parent)
        else:
            super().__init__(parent)
        self.variant = variant
        self._hover_progress = 0.0
        self._press_scale = 1.0
        self._hover_animation = QPropertyAnimation(self, b"hoverProgress", self)
        self._hover_animation.setDuration(180)
        self._hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._press_animation = QPropertyAnimation(self, b"pressScale", self)
        self._press_animation.setDuration(130)
        self._press_animation.setEasingCurve(QEasingCurve.OutBack)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMinimumHeight(34)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    def get_hover_progress(self) -> float:
        return self._hover_progress

    def set_hover_progress(self, value: float) -> None:
        self._hover_progress = float(value)
        self.update()

    hoverProgress = Property(float, get_hover_progress, set_hover_progress)

    def get_press_scale(self) -> float:
        return self._press_scale

    def set_press_scale(self, value: float) -> None:
        self._press_scale = float(value)
        self.update()

    pressScale = Property(float, get_press_scale, set_press_scale)

    def enterEvent(self, event) -> None:
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._animate_press(0.94, 100)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._animate_press(1.0, 260)
        super().mouseReleaseEvent(event)

    def _animate_hover(self, target: float) -> None:
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._hover_progress)
        self._hover_animation.setEndValue(target)
        self._hover_animation.start()

    def _animate_press(self, target: float, duration: int) -> None:
        self._press_animation.stop()
        self._press_animation.setDuration(duration)
        self._press_animation.setStartValue(self._press_scale)
        self._press_animation.setEndValue(target)
        self._press_animation.start()

    def paintEvent(self, event) -> None:
        palette = self.PALETTES.get(self.variant, self.PALETTES["default"])
        base = palette["checked"] if self.isChecked() else palette["base"]
        if not self.isEnabled():
            fill = _css_color(palette["disabled"])
            text = _css_color("#94a3b8")
        else:
            fill = _mix_color(base, palette["hover"], self._hover_progress)
            text_start = _css_color(palette.get("checked_text", palette["text"]) if self.isChecked() else palette["text"])
            text = _mix_color(text_start.name(), palette.get("hover_text", text_start.name()), self._hover_progress)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)
        center = rect.center()
        painter.translate(center)
        painter.scale(self._press_scale, self._press_scale)
        painter.translate(-center)

        radius = 8
        if self.variant.startswith("title"):
            radius = 6
        painter.setPen(_css_color(palette["border"]))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, radius, radius)

        painter.setPen(text)
        painter.setFont(self.font())
        metrics = painter.fontMetrics()
        icon = self.icon()
        icon_size = self.iconSize()
        spacing = 8 if not icon.isNull() and self.text() else 0
        text_width = metrics.horizontalAdvance(self.text())
        content_width = (icon_size.width() if not icon.isNull() else 0) + spacing + text_width
        if self.variant == "nav":
            x = rect.left() + 12
        else:
            x = rect.left() + max(0, (rect.width() - content_width) // 2)
        y = rect.top()
        if not icon.isNull():
            icon_rect = rect.adjusted(x - rect.left(), 0, 0, 0)
            icon_rect.setWidth(icon_size.width())
            icon_rect.setHeight(icon_size.height())
            icon_rect.moveTop(rect.top() + (rect.height() - icon_size.height()) // 2)
            icon.paint(painter, icon_rect, Qt.AlignCenter, QIcon.Normal if self.isEnabled() else QIcon.Disabled)
            x += icon_size.width() + spacing
        text_rect = rect.adjusted(x - rect.left(), 0, -10, 0)
        align = Qt.AlignVCenter | (Qt.AlignLeft if self.variant == "nav" else Qt.AlignCenter)
        if self.variant != "nav":
            text_rect = rect
        painter.drawText(text_rect, align, self.text())


class LightBackdrop(QWidget):
    def __init__(self, parent=None, radius: int = 14):
        super().__init__(parent)
        self.setObjectName("lightBackdrop")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.radius = radius
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    def _advance(self) -> None:
        self._phase = (self._phase + 0.012) % (math.tau)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        clip = QPainterPath()
        clip.addRoundedRect(self.rect(), self.radius, self.radius)
        painter.setClipPath(clip)
        painter.fillRect(self.rect(), QColor("#edf4fb"))
        width = max(1, self.width())
        height = max(1, self.height())
        lights = (
            (
                QPointF(width * (0.26 + 0.08 * math.cos(self._phase)), height * (0.28 + 0.06 * math.sin(self._phase * 0.8))),
                QColor(73, 142, 255, 88),
                max(width, height) * 0.42,
            ),
            (
                QPointF(width * (0.74 + 0.07 * math.sin(self._phase * 0.7)), height * (0.68 + 0.08 * math.cos(self._phase))),
                QColor(30, 184, 150, 66),
                max(width, height) * 0.36,
            ),
        )
        for center, color, radius in lights:
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0.0, color)
            gradient.setColorAt(0.55, QColor(color.red(), color.green(), color.blue(), 24))
            gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawEllipse(center, radius, radius)


class TitleBar(QWidget):
    def __init__(self, window: QMainWindow):
        super().__init__(window)
        self.window = window
        self._drag_offset = None
        self.setObjectName("titleBar")
        self.setFixedHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 10, 0)
        layout.setSpacing(10)

        title = QLabel("XMUM Moodle Agent")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        self.minimize_button = self._title_button("-", "minimizeButton", "titleMinimize")
        self.close_button = self._title_button("x", "closeButton", "titleClose")
        self.minimize_button.clicked.connect(window.showMinimized)
        layout.addWidget(self.minimize_button)
        self.close_button.clicked.connect(window.close)
        layout.addWidget(self.close_button)

    def _title_button(self, text: str, object_name: str, variant: str) -> AnimatedButton:
        button = AnimatedButton(text, variant=variant)
        button.setObjectName(object_name)
        button.setFixedSize(42, 30)
        button.setFlat(True)
        button.setFocusPolicy(Qt.NoFocus)
        return button

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton and self._drag_offset is not None:
            if self.window.isMaximized():
                self.window.showNormal()
            self.window.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)


class Sidebar(QFrame):
    def __init__(self, brand_icon: QIcon):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(248)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        brand_row = QHBoxLayout()
        brand_mark = QLabel()
        brand_mark.setObjectName("brandMark")
        brand_mark.setFixedSize(28, 28)
        brand_mark.setPixmap(brand_icon.pixmap(28, 28))
        brand_mark.setScaledContents(True)
        brand = QLabel("XMUM Agent")
        brand.setObjectName("brandLabel")
        brand_row.addWidget(brand_mark)
        brand_row.addWidget(brand, 1)
        layout.addLayout(brand_row)
        layout.addSpacing(16)

        self.nav_buttons = {
            "home": self._nav_button("首页", QIcon()),
            "courses": self._nav_button("课程", QIcon()),
            "notes": self._nav_button("笔记", QIcon()),
        }
        for button in self.nav_buttons.values():
            layout.addWidget(button)
            button.setFixedHeight(46)
        layout.addStretch(1)

        self.login_button = AnimatedButton("登录 Moodle", variant="primary")
        self.login_button.setObjectName("primaryButton")
        layout.addWidget(self.login_button)

        self.status_label = QLabel("登录 Moodle 后开始")
        self.status_label.setObjectName("sidebarStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    def _nav_button(self, text: str, icon: QIcon) -> AnimatedButton:
        button = AnimatedButton(icon, text, variant="nav")
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setFixedHeight(46)
        button.setFocusPolicy(Qt.NoFocus)
        return button


class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("homeView")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        title = QLabel("欢迎回来")
        title.setObjectName("heroTitle")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("登录 Moodle，选择学期，并保持课程资料井然有序。")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        self.login_button = AnimatedButton("登录 Moodle", variant="primary")
        self.login_button.setObjectName("primaryButton")
        self.login_button.setMinimumWidth(164)

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(subtitle)
        layout.addSpacing(26)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.login_button)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(2)


class CoursesView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("课程")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch(1)
        term_label = QLabel("学期")
        term_label.setObjectName("fieldLabel")
        header.addWidget(term_label)
        self.selected_term_combo = QComboBox()
        self.selected_term_combo.setMinimumWidth(132)
        header.addWidget(self.selected_term_combo)
        self.download_button = AnimatedButton("下载", variant="primary")
        self.download_button.setObjectName("primaryButton")
        header.addWidget(self.download_button)
        layout.addLayout(header)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(12)

        panel_header = QHBoxLayout()
        self.course_count_label = QLabel("登录后显示课程")
        panel_header.addWidget(self.course_count_label)
        panel_header.addStretch(1)
        self.open_button = AnimatedButton("打开文件夹")
        panel_header.addWidget(self.open_button)
        panel_layout.addLayout(panel_header)

        select_row = QHBoxLayout()
        self.select_all_check = QCheckBox("选择本学期全部课程")
        select_row.addWidget(self.select_all_check)
        select_row.addStretch(1)
        self.selected_count_label = QLabel("尚未选择课程")
        self.selected_count_label.setObjectName("hintLabel")
        select_row.addWidget(self.selected_count_label)
        panel_layout.addLayout(select_row)

        self.course_table = QTableWidget(0, 2)
        self.course_table.setHorizontalHeaderLabels(["", "课程"])
        self.course_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.course_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.course_table.setColumnWidth(0, 44)
        self.course_table.verticalHeader().setVisible(False)
        self.course_table.setAlternatingRowColors(False)
        panel_layout.addWidget(self.course_table, 1)

        hint = QLabel("系统会从 Moodle 课程标题中的 YYYY/MM 自动识别学期。")
        hint.setObjectName("hintLabel")
        panel_layout.addWidget(hint)
        layout.addWidget(panel, 1)


class NotesView(QWidget):
    def __init__(self, status_text: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        title = QLabel("笔记")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        panel = QFrame()
        panel.setObjectName("settingsPanel")
        form = QFormLayout(panel)
        form.setContentsMargins(18, 14, 18, 14)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft)

        self.api_status_label = QLabel(status_text)
        self.api_status_label.setObjectName("settingsValue")
        self.api_button = AnimatedButton("连接 API", variant="primary")
        self.api_button.setObjectName("primaryButton")
        self.generate_button = AnimatedButton("一键生成笔记", variant="primary")
        self.generate_button.setObjectName("primaryButton")
        hint = QLabel("生成时会自动使用已连接的 AI 公司 API，并套用内置课程知识整理提示词。")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)

        form.addRow("API 状态", self.api_status_label)
        form.addRow("AI 公司 API", self.api_button)
        form.addRow("生成笔记", self.generate_button)
        form.addRow("", hint)
        layout.addWidget(panel)
        layout.addStretch(1)


class MoodleAgentQtWindow(QMainWindow):
    def __init__(self, root_path: Path):
        super().__init__()
        self.root_path = root_path.resolve()
        self.settings = load_gui_settings(self.root_path)
        self.current_courses = []
        self.visible_courses = []
        self.selected_course_urls = set()
        self.logged_in = False
        self.active_page = "home"
        self.log_path = self.root_path / "state" / "gui.log"
        self._updating_table = False
        self._worker_signals = []

        ensure_icon_assets()
        self.app_icon = app_icon_path()
        self.setFont(QFont(_preferred_widget_font_family(), 10))

        self.setWindowTitle("XMUM Moodle Agent")
        self.setWindowIcon(QIcon(str(self.app_icon)))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(980, 680)
        self.setMinimumSize(880, 620)
        self.setStyleSheet(_app_stylesheet())

        self._build_layout()
        self._refresh_note_controls()
        self._set_navigation_enabled(False)
        self._show_page("home")
        self._log("Qt GUI started")

    def _build_layout(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        root_stack = QStackedLayout(root)
        root_stack.setContentsMargins(0, 0, 0, 0)
        root_stack.setSpacing(0)
        root_stack.setStackingMode(QStackedLayout.StackAll)

        shell_root = QWidget()
        shell_root.setObjectName("shellRoot")
        root_layout = QVBoxLayout(shell_root)
        root_layout.setContentsMargins(14, 10, 14, 16)
        root_layout.setSpacing(0)

        self.window_container = QFrame()
        self.window_container.setObjectName("windowContainer")
        shadow = QGraphicsDropShadowEffect(self.window_container)
        shadow.setBlurRadius(34)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(26, 45, 70, 54))
        self.window_container.setGraphicsEffect(shadow)

        container_stack = QStackedLayout(self.window_container)
        container_stack.setContentsMargins(0, 0, 0, 0)
        container_stack.setSpacing(0)
        container_stack.setStackingMode(QStackedLayout.StackAll)

        self.backdrop = LightBackdrop(radius=14)
        container_stack.addWidget(self.backdrop)

        foreground = QWidget()
        foreground.setObjectName("windowForeground")
        container_layout = QVBoxLayout(foreground)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        container_layout.addWidget(self.title_bar)

        content = QWidget()
        content.setObjectName("content")
        shell = QHBoxLayout(content)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = Sidebar(QIcon(str(self.app_icon)))
        self.nav_buttons = self.sidebar.nav_buttons
        self.sidebar_login_button = self.sidebar.login_button
        self.status_label = self.sidebar.status_label
        self.nav_buttons["home"].clicked.connect(lambda: self._show_page("home"))
        self.nav_buttons["courses"].clicked.connect(lambda: self._show_page("courses"))
        self.nav_buttons["notes"].clicked.connect(lambda: self._show_page("notes"))
        self.sidebar_login_button.clicked.connect(self._open_login_window)

        main = QFrame()
        main.setObjectName("mainArea")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(28, 28, 28, 24)
        main_layout.setSpacing(14)

        self.pages = QStackedWidget()
        home_view = HomeView()
        courses_view = CoursesView()
        notes_view = NotesView(self._api_status_text())
        self.page_widgets = {
            "home": home_view,
            "courses": courses_view,
            "notes": notes_view,
        }
        for page in ("home", "courses", "notes"):
            self.pages.addWidget(self.page_widgets[page])
        main_layout.addWidget(self.pages, 1)

        self.splash_login_button = home_view.login_button
        self.splash_login_button.clicked.connect(self._open_login_window)

        self.selected_term_combo = courses_view.selected_term_combo
        self.selected_term_combo.currentTextChanged.connect(self._apply_term_filter)
        self.course_count_label = courses_view.course_count_label
        self.download_button = courses_view.download_button
        self.download_button.clicked.connect(self._run_download_selected_courses)
        self.select_all_check = courses_view.select_all_check
        self.select_all_check.toggled.connect(self._toggle_select_all_visible_courses)
        self.selected_count_label = courses_view.selected_count_label
        self.course_table = courses_view.course_table
        self.course_table.itemChanged.connect(self._handle_course_item_changed)
        courses_view.open_button.clicked.connect(self._open_download_directory)

        self.api_status_label = notes_view.api_status_label
        self.generate_notes_button = notes_view.generate_button
        notes_view.api_button.clicked.connect(self._open_api_window)
        self.generate_notes_button.clicked.connect(self._run_generate_notes)

        self.bottom_status_label = QLabel("登录 Moodle 后开始")
        self.bottom_status_label.setObjectName("bottomStatus")
        main_layout.addWidget(self.bottom_status_label)

        shell.addWidget(self.sidebar)
        shell.addWidget(main, 1)
        container_layout.addWidget(content, 1)
        container_stack.addWidget(foreground)
        container_stack.setCurrentWidget(foreground)
        root_layout.addWidget(self.window_container, 1)
        root_stack.addWidget(shell_root)
        root_stack.setCurrentWidget(shell_root)
        self.setCentralWidget(root)

    def _nav_button(self, text: str, icon: QIcon) -> AnimatedButton:
        button = AnimatedButton(icon, text, variant="nav")
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setMinimumHeight(42)
        if text in ("Courses", "课程"):
            button.clicked.connect(lambda: self._show_page("courses"))
        else:
            button.clicked.connect(lambda: self._show_page("notes"))
        return button

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        title = QLabel("XMUM Moodle Agent")
        title.setObjectName("heroTitle")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("登录 Moodle，选择学期，并下载课程资料。")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        self.splash_login_button = AnimatedButton("登录 Moodle", variant="primary")
        self.splash_login_button.setObjectName("primaryButton")
        self.splash_login_button.clicked.connect(self._open_login_window)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.splash_login_button)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(2)
        return page

    def _build_courses_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("课程")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(QLabel("学期"))
        self.selected_term_combo = QComboBox()
        self.selected_term_combo.setMinimumWidth(128)
        self.selected_term_combo.currentTextChanged.connect(self._apply_term_filter)
        header.addWidget(self.selected_term_combo)
        layout.addLayout(header)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(12)

        panel_header = QHBoxLayout()
        self.course_count_label = QLabel("登录后显示课程")
        panel_header.addWidget(self.course_count_label)
        panel_header.addStretch(1)
        open_button = AnimatedButton("打开文件夹")
        open_button.clicked.connect(self._open_download_directory)
        panel_header.addWidget(open_button)
        self.download_button = AnimatedButton("下载所选课程", variant="primary")
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self._run_download_selected_courses)
        panel_header.addWidget(self.download_button)
        panel_layout.addLayout(panel_header)

        select_row = QHBoxLayout()
        self.select_all_check = QCheckBox("选择本学期全部课程")
        self.select_all_check.toggled.connect(self._toggle_select_all_visible_courses)
        select_row.addWidget(self.select_all_check)
        select_row.addStretch(1)
        self.selected_count_label = QLabel("尚未选择课程")
        self.selected_count_label.setObjectName("hintLabel")
        select_row.addWidget(self.selected_count_label)
        panel_layout.addLayout(select_row)

        self.course_table = QTableWidget(0, 2)
        self.course_table.setHorizontalHeaderLabels(["", "课程"])
        self.course_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.course_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.course_table.setColumnWidth(0, 44)
        self.course_table.verticalHeader().setVisible(False)
        self.course_table.setAlternatingRowColors(False)
        self.course_table.itemChanged.connect(self._handle_course_item_changed)
        panel_layout.addWidget(self.course_table, 1)

        hint = QLabel("勾选课程即可下载。系统会从课程标题中的 YYYY/MM 自动识别学期。")
        hint.setObjectName("hintLabel")
        panel_layout.addWidget(hint)
        layout.addWidget(panel, 1)
        return page

    def _build_notes_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        title = QLabel("知识笔记")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(12)
        self.api_status_label = QLabel(self._api_status_text())
        panel_layout.addWidget(self.api_status_label)

        api_button = AnimatedButton("连接 API", variant="primary")
        api_button.setObjectName("primaryButton")
        api_button.clicked.connect(self._open_api_window)
        panel_layout.addWidget(api_button, alignment=Qt.AlignLeft)

        self.generate_notes_button = AnimatedButton("一键生成笔记", variant="primary")
        self.generate_notes_button.setObjectName("primaryButton")
        self.generate_notes_button.clicked.connect(self._run_generate_notes)
        panel_layout.addWidget(self.generate_notes_button, alignment=Qt.AlignLeft)

        hint = QLabel("生成时会自动使用已连接的 AI 公司 API，并套用内置课程知识整理提示词。")
        hint.setObjectName("hintLabel")
        panel_layout.addWidget(hint)
        layout.addWidget(panel)
        layout.addStretch(1)
        return page

    def _show_page(self, page_name: str) -> None:
        if page_name != "home" and not self.logged_in:
            self._set_status("登录 Moodle 后开始")
            self._open_login_window()
            return
        self.active_page = page_name
        self.pages.setCurrentWidget(self.page_widgets[page_name])
        for name, button in self.nav_buttons.items():
            button.setChecked(name == page_name)

    def _set_navigation_enabled(self, enabled: bool) -> None:
        for name, button in self.nav_buttons.items():
            button.setEnabled(name == "home" or enabled)

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)
        self.bottom_status_label.setText(text)

    def _open_login_window(self) -> None:
        dialog = LoginDialog(self)
        dialog.exec()

    def _open_api_window(self) -> None:
        dialog = ApiSettingsDialog(self, self.settings.model_providers, self._save_api_settings)
        dialog.exec()

    def _save_moodle(self) -> None:
        save_gui_settings(self.root_path, self.settings)
        self._set_status("Moodle 登录设置已保存")

    def _save_api_settings(self, providers) -> None:
        self.settings.model_providers = providers
        save_gui_settings(self.root_path, self.settings)
        self._refresh_note_controls()
        self._set_status("AI 公司 API 设置已保存")

    def _run_generate_notes(self) -> None:
        provider = select_note_provider(self.settings.model_providers)
        if not provider:
            self._show_warning("尚未连接 API", "请先在 API 设置中启用一个 AI 公司并填写 API Key。")
            return
        self._set_busy(True)
        self._set_status("正在整理课程资料并生成 Word 笔记...")
        signals = OperationSignals()
        self._worker_signals.append(signals)
        signals.notes_success.connect(self._handle_notes_success)
        signals.error.connect(self._show_error)
        threading.Thread(target=self._notes_worker, args=(signals, provider), daemon=True).start()

    def _notes_worker(self, signals: OperationSignals, provider) -> None:
        try:
            output_path = generate_course_knowledge_checklist(self.root_path, provider)
        except Exception as exc:
            signals.error.emit("笔记生成失败", self._exception_detail(exc))
            return
        signals.notes_success.emit(str(output_path))

    def _handle_notes_success(self, output_path: str) -> None:
        message = f"笔记已生成：{output_path}"
        self._set_busy(False)
        self._set_status(message)
        self._log(message)
        self._show_info("笔记生成完成", message)

    def _run_login_and_load_courses(self) -> None:
        if not self.settings.moodle_username or not self.settings.moodle_password:
            self._show_warning("缺少登录信息", "请输入 Moodle 账号和密码。")
            return
        self._set_busy(True)
        self._set_status("正在登录 Moodle 并加载课程...")
        signals = OperationSignals()
        self._worker_signals.append(signals)
        signals.login_success.connect(self._handle_login_success)
        signals.error.connect(self._show_error)
        threading.Thread(target=self._login_worker, args=(signals,), daemon=True).start()

    def _login_worker(self, signals: OperationSignals) -> None:
        try:
            courses = asyncio.run(self._load_courses_async())
        except Exception as exc:
            signals.error.emit("Moodle 登录失败", self._exception_detail(exc))
            return
        signals.login_success.emit(courses)

    async def _load_courses_async(self):
        config = agent_config_from_gui_settings(self.root_path, self.settings)
        async with MoodleClient(config) as moodle:
            return await visible_courses_after_login(moodle)

    def _handle_login_success(self, courses) -> None:
        self.current_courses = list(courses)
        self.selected_course_urls.clear()
        self.logged_in = True
        save_gui_settings(self.root_path, self.settings)
        self._set_navigation_enabled(True)
        self._populate_terms()
        self._apply_term_filter()
        self._toggle_select_all_visible_courses(True)
        self._set_busy(False)
        self._show_page("courses")
        self._set_status(f"已登录，找到 {len(self.current_courses)} 门课程。")
        self._log(f"Login succeeded; courses={len(self.current_courses)}")
        self._show_info("登录完成", "Moodle 登录成功。现在可以选择课程并下载资料。")

    def _populate_terms(self) -> None:
        terms = course_terms_from_courses(self.current_courses)
        self.selected_term_combo.blockSignals(True)
        self.selected_term_combo.clear()
        self.selected_term_combo.addItems(terms)
        self.selected_term_combo.setEnabled(bool(terms))
        self.selected_term_combo.blockSignals(False)
        if terms:
            self.selected_term_combo.setCurrentText(terms[0])

    def _apply_term_filter(self) -> None:
        self.visible_courses = filter_courses_by_term(self.current_courses, self.selected_term_combo.currentText())
        self._populate_course_table()
        self._refresh_course_count()

    def _populate_course_table(self) -> None:
        self._updating_table = True
        self.course_table.setRowCount(0)
        for course in self.visible_courses:
            row = self.course_table.rowCount()
            self.course_table.insertRow(row)
            checked = QTableWidgetItem()
            checked.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checked.setCheckState(Qt.Checked if course.url in self.selected_course_urls else Qt.Unchecked)
            checked.setData(Qt.UserRole, course.url)
            self.course_table.setItem(row, 0, checked)

            title = QTableWidgetItem(course.title)
            title.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            title.setData(Qt.UserRole, course.url)
            self.course_table.setItem(row, 1, title)
        self._updating_table = False
        self._refresh_select_all_state()

    def _handle_course_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_table or item.column() != 0:
            return
        url = item.data(Qt.UserRole)
        if item.checkState() == Qt.Checked:
            self.selected_course_urls.add(url)
        else:
            self.selected_course_urls.discard(url)
        self._refresh_course_count()
        self._refresh_select_all_state()

    def _toggle_select_all_visible_courses(self, checked=None) -> None:
        checked = self.select_all_check.isChecked() if checked is None else bool(checked)
        visible_urls = {course.url for course in self.visible_courses}
        if checked:
            self.selected_course_urls.update(visible_urls)
        else:
            self.selected_course_urls.difference_update(visible_urls)
        self._populate_course_table()
        self._refresh_course_count()

    def _refresh_select_all_state(self) -> None:
        visible_urls = {course.url for course in self.visible_courses}
        checked = bool(visible_urls) and visible_urls.issubset(self.selected_course_urls)
        self.select_all_check.blockSignals(True)
        self.select_all_check.setChecked(checked)
        self.select_all_check.blockSignals(False)

    def _selected_courses(self):
        return [course for course in self.current_courses if course.url in self.selected_course_urls]

    def _refresh_course_count(self) -> None:
        total = len(self.visible_courses)
        selected = len(self.selected_course_urls)
        if self.current_courses:
            term = self.selected_term_combo.currentText() or "全部"
            self.course_count_label.setText(f"{term}：{total} 门课程，已选择 {selected} 门")
        else:
            self.course_count_label.setText("登录后显示课程")
        self.selected_count_label.setText(f"已选择 {selected} 门课程" if selected else "尚未选择课程")

    def _run_download_selected_courses(self) -> None:
        selected_courses = self._selected_courses()
        if not selected_courses:
            self._show_warning("尚未选择课程", "下载前请至少选择一门课程。")
            return
        self._set_busy(True)
        self._set_status(f"正在下载 {len(selected_courses)} 门课程的资料...")
        signals = OperationSignals()
        self._worker_signals.append(signals)
        signals.download_success.connect(self._handle_download_success)
        signals.error.connect(self._show_error)
        threading.Thread(target=self._download_worker, args=(signals, selected_courses), daemon=True).start()

    def _download_worker(self, signals: OperationSignals, selected_courses) -> None:
        try:
            report = asyncio.run(self._download_selected_courses_async(selected_courses))
        except Exception as exc:
            signals.error.emit("下载失败", self._exception_detail(exc))
            return
        signals.download_success.emit(report)

    async def _download_selected_courses_async(self, selected_courses):
        config = agent_config_from_gui_settings(self.root_path, self.settings)
        async with MoodleClient(config) as moodle:
            await moodle.login()
            return await download_selected_courses(self.root_path, moodle, selected_courses)

    def _handle_download_success(self, report) -> None:
        message = (
            f"下载完成：{report.courses} 门课程，{report.resources} 个资源，"
            f"新增 {report.downloaded} 个，跳过 {report.skipped} 个。"
        )
        self._set_busy(False)
        self._set_status(message)
        self._log(message)
        self._show_info("下载完成", message)

    def _open_download_directory(self) -> None:
        path = self.root_path / "data" / "courses"
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(path))
        except Exception as exc:
            self._show_error("打开文件夹失败", self._exception_detail(exc))

    def _refresh_note_controls(self) -> None:
        connected = [
            provider
            for provider in self.settings.model_providers
            if provider.get("enabled") and str(provider.get("api_key", "")).strip()
        ]
        self.api_status_label.setText(self._api_status_text())
        enabled = can_generate_notes(self.settings)
        self.generate_notes_button.setEnabled(enabled)

    def _api_status_text(self) -> str:
        count = sum(
            1
            for provider in self.settings.model_providers
            if provider.get("enabled") and str(provider.get("api_key", "")).strip()
        )
        return f"已连接 {count} 个 AI 公司 API" if count else "尚未连接 AI 公司 API"

    def _set_busy(self, busy: bool) -> None:
        for widget in (self.splash_login_button, self.sidebar_login_button, self.download_button, self.generate_notes_button):
            widget.setEnabled(not busy)
        if not busy:
            self._set_navigation_enabled(self.logged_in)
            self._refresh_note_controls()

    def _show_info(self, title: str, text: str) -> None:
        self._show_message(QMessageBox.Information, title, text)

    def _show_warning(self, title: str, text: str) -> None:
        self._show_message(QMessageBox.Warning, title, text)

    def _show_error(self, title: str, detail: str) -> None:
        self._set_busy(False)
        self._set_status(title)
        self._show_message(QMessageBox.Critical, title, detail or title)

    def _show_message(self, icon, title: str, text: str) -> None:
        message_box = self._build_message_box(icon, title, text)
        message_box.exec()

    def _build_message_box(self, icon, title: str, text: str) -> QMessageBox:
        message_box = QMessageBox(self)
        message_box.setObjectName("messageBox")
        message_box.setIcon(icon)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setStandardButtons(QMessageBox.Ok)
        message_box.setStyleSheet(self.styleSheet())
        message_box.setFont(QFont(_preferred_widget_font_family(), 10))
        return message_box

    def _exception_detail(self, exc: Exception) -> str:
        message = str(exc).strip()
        if message:
            return message
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()

    def _log(self, message: str) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(message.rstrip() + "\n")
        except Exception:
            pass


class LoginDialog(QDialog):
    def __init__(self, parent: MoodleAgentQtWindow):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("loginDialog")
        self.setStyleSheet(parent.styleSheet())
        self.setFont(parent.font())
        self.setWindowTitle("登录 Moodle")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        title = QLabel("登录 Moodle")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        subtitle = QLabel("选择课程、下载文件或生成笔记前，请先登录。")
        subtitle.setObjectName("hintLabel")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        panel = QFrame()
        panel.setObjectName("settingsPanel")
        form = QFormLayout(panel)
        form.setContentsMargins(18, 16, 18, 16)
        form.setSpacing(12)
        self.username_input = QLineEdit(parent.settings.moodle_username)
        self.username_input.setPlaceholderText("校园 ID / Moodle 账号")
        self.password_input = QLineEdit(parent.settings.moodle_password)
        self.password_input.setPlaceholderText("Moodle 密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.remember_check = QCheckBox("记住密码")
        self.remember_check.setChecked(parent.settings.remember_password)
        self.auto_login_check = QCheckBox("保存为自动登录配置")
        self.auto_login_check.setChecked(parent.settings.auto_login)
        form.addRow("校园 ID / Moodle 账号", self.username_input)
        form.addRow("Moodle 密码", self.password_input)
        form.addRow("", self.remember_check)
        form.addRow("", self.auto_login_check)
        layout.addWidget(panel)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        save_button = AnimatedButton("保存设置")
        save_button.clicked.connect(self._save_only)
        cancel_button = AnimatedButton("取消")
        cancel_button.clicked.connect(self.reject)
        login_button = AnimatedButton("登录并加载课程", variant="primary")
        login_button.setObjectName("primaryButton")
        login_button.clicked.connect(self._sign_in)
        actions.addWidget(save_button)
        actions.addStretch(1)
        actions.addWidget(cancel_button)
        actions.addWidget(login_button)
        layout.addLayout(actions)

    def _sync_settings(self) -> None:
        settings = self.parent_window.settings
        settings.moodle_username = self.username_input.text().strip()
        settings.moodle_password = self.password_input.text()
        settings.remember_password = self.remember_check.isChecked()
        settings.auto_login = self.auto_login_check.isChecked()

    def _save_only(self) -> None:
        self._sync_settings()
        self.parent_window._save_moodle()

    def _sign_in(self) -> None:
        self._sync_settings()
        self.accept()
        self.parent_window._run_login_and_load_courses()


class ApiSettingsDialog(QDialog):
    def __init__(self, parent: MoodleAgentQtWindow, providers, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.providers = [dict(provider) for provider in providers]
        self.current_provider_index = 0
        self.provider_widgets = []
        self.setObjectName("apiSettingsDialog")
        self.setStyleSheet(parent.styleSheet())
        self.setFont(parent.font())
        self.setWindowTitle("AI 公司 API 设置")
        self.resize(620, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)
        title = QLabel("AI 公司 API 设置")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        subtitle = QLabel("启用 AI 公司并输入 API Key 后，即可一键生成课程知识清单；模型由应用内置，不在界面中开放选择。")
        subtitle.setObjectName("hintLabel")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        panel = QFrame()
        panel.setObjectName("settingsPanel")
        form = QFormLayout(panel)
        form.setContentsMargins(18, 16, 18, 16)
        form.setSpacing(12)

        self.provider_select = QComboBox()
        self.provider_select.setObjectName("providerSelect")
        self.provider_select.addItems([str(provider.get("name", "")) for provider in self.providers])
        self.provider_select.currentIndexChanged.connect(self._change_provider)
        self.enabled_check = QCheckBox("启用此 API")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("Base URL")
        form.addRow("API 来源", self.provider_select)
        form.addRow("", self.enabled_check)
        form.addRow("API Key", self.api_key_input)
        form.addRow("Base URL", self.base_url_input)
        layout.addWidget(panel, 1)

        self.provider_widgets.append(
            {
                "enabled": self.enabled_check,
                "api_key": self.api_key_input,
                "base_url": self.base_url_input,
            }
        )
        self._load_provider(0)

        actions = QHBoxLayout()
        self.test_button = AnimatedButton("测试 API")
        self.test_button.clicked.connect(self._test_api)
        actions.addWidget(self.test_button)
        actions.addStretch(1)
        cancel_button = AnimatedButton("取消")
        cancel_button.clicked.connect(self.reject)
        save_button = AnimatedButton("保存 API 设置", variant="primary")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self._save)
        actions.addWidget(cancel_button)
        actions.addWidget(save_button)
        layout.addLayout(actions)

    def _load_provider(self, index: int) -> None:
        if not self.providers:
            return
        provider = self.providers[index]
        self.enabled_check.setChecked(bool(provider.get("enabled")))
        self.api_key_input.setText(str(provider.get("api_key", "")))
        self.base_url_input.setText(str(provider.get("base_url", "")))

    def _sync_current_provider(self) -> None:
        if not self.providers:
            return
        provider = self.providers[self.current_provider_index]
        provider["enabled"] = self.enabled_check.isChecked()
        provider["api_key"] = self.api_key_input.text().strip()
        provider["base_url"] = self.base_url_input.text().strip()

    def _change_provider(self, index: int) -> None:
        self._sync_current_provider()
        self.current_provider_index = max(0, index)
        self._load_provider(self.current_provider_index)

    def _current_provider(self):
        self._sync_current_provider()
        return dict(self.providers[self.current_provider_index])

    def _test_api(self) -> None:
        provider = self._current_provider()
        if not provider.get("api_key"):
            self._show_test_result(False, "缺少 API Key", "请先输入 API Key。")
            return
        try:
            test_provider_connection(provider)
        except Exception as exc:
            self._show_test_result(False, "API 测试失败", str(exc) or "连接失败。")
            return
        self._show_test_result(True, "API 测试成功", f"{provider.get('name')} 连接正常。")

    def _show_test_result(self, success: bool, title: str, text: str) -> None:
        icon = QMessageBox.Information if success else QMessageBox.Warning
        message_box = QMessageBox(self)
        message_box.setObjectName("messageBox")
        message_box.setIcon(icon)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setStandardButtons(QMessageBox.Ok)
        message_box.setStyleSheet(self.styleSheet())
        message_box.setFont(QFont(_preferred_widget_font_family(), 10))
        message_box.exec()

    def _save(self) -> None:
        self._sync_current_provider()
        self.on_save(self.providers)
        self.accept()


def _app_stylesheet() -> str:
    t = MODERN_THEME
    checkmark = (
        "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIg"
        "dmlld0JveD0iMCAwIDEyIDEyIj48cGF0aCBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lk"
        "dGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgZD0iTTMgNi4y"
        "IDUuMSA4LjMgOSAzLjgiLz48L3N2Zz4="
    )
    font_stack = _ui_font_stack()
    return f"""
QMainWindow {{
    background: transparent;
}}
QWidget#root {{
    background: transparent;
}}
QWidget#shellRoot {{
    background: transparent;
}}
QFrame#windowContainer {{
    background: {t['app_bg']};
    border: 1px solid rgba(255, 255, 255, 150);
    border-radius: 14px;
}}
QWidget#windowForeground {{
    background: transparent;
}}
QWidget#titleBar {{
    background: {t['title_bg']};
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    border-bottom: 1px solid {t['border_soft']};
}}
QLabel#titleLabel {{
    color: {t['text']};
    font-family: {font_stack};
    font-size: 11.5pt;
    font-weight: 700;
}}
QPushButton#closeButton, QPushButton#minimizeButton {{
    border: 0;
    background: transparent;
    padding: 0;
    font-family: "Segoe UI", {font_stack};
    font-size: 11pt;
}}
QFrame#sidebar {{
    background: {t['sidebar_bg']};
    border-right: 1px solid {t['border_soft']};
}}
QFrame#mainArea {{
    background: transparent;
}}
QFrame#panel {{
    background: {t['surface']};
    border: 1px solid {t['border_soft']};
    border-radius: 8px;
}}
QFrame#settingsPanel {{
    background: {t['surface']};
    border: 1px solid {t['border_soft']};
    border-radius: 8px;
}}
QLabel {{
    color: {t['text']};
    font-family: {font_stack};
    font-size: 10.5pt;
}}
QLabel#brandMark {{
    background: transparent;
    border-radius: 0;
}}
QLabel#brandLabel {{
    font-size: 17pt;
    font-weight: 700;
}}
QLabel#heroTitle {{
    font-size: 30pt;
    font-weight: 700;
}}
QLabel#pageTitle {{
    font-size: 21pt;
    font-weight: 700;
}}
QLabel#dialogTitle {{
    font-size: 18pt;
    font-weight: 700;
}}
QLabel#subtitle, QLabel#hintLabel, QLabel#sidebarStatus, QLabel#bottomStatus, QLabel#fieldLabel {{
    color: {t['text_secondary']};
}}
QLabel#sidebarStatus {{
    font-size: 10.5pt;
    line-height: 150%;
}}
QLabel#bottomStatus {{
    background: {t['surface_alt']};
    border: 1px solid {t['border_soft']};
    border-radius: 8px;
    padding: 8px 12px;
}}
QPushButton {{
    background: transparent;
    color: {t['text']};
    border: 0;
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 20px;
    font-family: {font_stack};
    font-size: 10.5pt;
}}
QPushButton:hover, QPushButton:pressed, QPushButton:checked {{
    background: transparent;
}}
QPushButton:disabled {{
    color: {t['text_tertiary']};
}}
QPushButton#primaryButton {{
    color: white;
    font-weight: 700;
    font-size: 11pt;
}}
QPushButton#navButton {{
    text-align: left;
    background: transparent;
    border: 0;
    padding: 11px 14px;
    border-radius: 8px;
    font-size: 12pt;
    font-weight: 650;
}}
QPushButton#navButton:checked {{
    background: {t['nav_active']};
    font-weight: 700;
}}
QLineEdit, QComboBox {{
    background: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 7px 9px;
    font-family: {font_stack};
    color: {t['text']};
}}
QTableWidget {{
    background: {t['surface']};
    border: 1px solid {t['border_soft']};
    border-radius: 8px;
    gridline-color: {t['border_soft']};
    selection-background-color: #dbeafe;
    selection-color: {t['text']};
    font-family: {font_stack};
}}
QHeaderView::section {{
    background: {t['surface_alt']};
    color: {t['text_secondary']};
    border: 0;
    border-bottom: 1px solid {t['border_soft']};
    padding: 7px;
}}
QCheckBox {{
    color: {t['text']};
    spacing: 8px;
    font-family: {font_stack};
}}
QCheckBox::indicator, QTableWidget::indicator, QTableView::indicator {{
    width: 14px;
    height: 14px;
    background: #ffffff;
    border: 1px solid #c7c7cc;
    border-radius: 3px;
}}
QCheckBox::indicator:checked, QTableWidget::indicator:checked, QTableView::indicator:checked {{
    background: {t['primary']};
    border: 1px solid {t['primary']};
    image: url(data:image/svg+xml;base64,{checkmark});
}}
QCheckBox::indicator:disabled, QTableWidget::indicator:disabled, QTableView::indicator:disabled {{
    background: #f2f2f7;
    border: 1px solid {t['border_soft']};
}}
QScrollArea {{
    border: 0;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QDialog, QMessageBox {{
    background: #f6faff;
    font-family: {font_stack};
}}
QDialog QWidget, QMessageBox QWidget {{
    background: transparent;
}}
QDialog QLabel, QMessageBox QLabel {{
    color: {t['text']};
    font-family: {font_stack};
    font-size: 10.5pt;
}}
QMessageBox QLabel {{
    color: {t['text']};
    padding: 4px 2px;
}}
QDialog QPushButton, QMessageBox QPushButton {{
    background: rgba(255, 255, 255, 210);
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    padding: 8px 16px;
    min-width: 72px;
    min-height: 26px;
    font-family: {font_stack};
    font-size: 10.5pt;
}}
QDialog QPushButton:hover, QMessageBox QPushButton:hover {{
    background: #eaf3ff;
    border: 1px solid {t['primary']};
}}
QDialog QPushButton:pressed, QMessageBox QPushButton:pressed {{
    background: #dbeafe;
}}
QMessageBox#messageBox {{
    background: #f6faff;
}}
"""


def _qt_application(argv=None) -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(list(sys.argv if argv is None else argv))
    return app


def main(argv=None) -> int:
    app = _qt_application(argv)
    window = MoodleAgentQtWindow(Path.cwd())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
