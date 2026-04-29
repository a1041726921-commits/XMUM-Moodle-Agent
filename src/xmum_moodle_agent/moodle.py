import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from urllib.parse import unquote, urlparse

from .files import safe_filename
from .models import Course, Resource

Link = Tuple[str, str]

RESOURCE_EXTENSIONS = {
    ".pdf",
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
    ".txt",
}


class MoodleAutomationError(RuntimeError):
    """Raised when Moodle browser automation cannot complete a required step."""


def discover_courses_from_links(links: Sequence[Link]) -> List[Course]:
    courses: List[Course] = []
    seen = set()
    for title, href in links:
        if "/course/view.php" not in href or "id=" not in href:
            continue
        clean_title = _clean_link_text(title) or "Untitled Course"
        key = href.split("#", 1)[0]
        if key in seen:
            continue
        seen.add(key)
        courses.append(Course(title=clean_title, url=key))
    return courses


def discover_resources_from_links(course_title: str, links: Sequence[Link]) -> List[Resource]:
    resources: List[Resource] = []
    seen = set()
    for title, href in links:
        extension = _extension_from_url(href)
        is_resource_page = "/mod/resource/view.php" in href or "/mod/folder/view.php" in href
        is_direct_file = "pluginfile.php" in href and (extension in RESOURCE_EXTENSIONS or not extension)
        if not is_resource_page and not is_direct_file:
            continue
        key = href.split("#", 1)[0]
        if key in seen:
            continue
        seen.add(key)
        resources.append(
            Resource(
                title=_clean_link_text(title) or _title_from_url(href),
                url=key,
                course_title=course_title,
                extension=extension,
            )
        )
    return resources


def _clean_link_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = re.sub(r"^(file|resource)\s*", "", value, flags=re.IGNORECASE).strip()
    return value


def _extension_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path)
    suffix = Path(path).suffix.lower()
    return suffix if suffix in RESOURCE_EXTENSIONS else ""


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name or "Moodle Resource"
    return safe_filename(name)


async def _extract_links(page) -> List[Link]:
    links = await page.eval_on_selector_all(
        "a[href]",
        """anchors => anchors.map(a => [
            (a.innerText || a.getAttribute('aria-label') || a.title || '').trim(),
            a.href
        ])""",
    )
    return [(str(title), str(href)) for title, href in links if href]


class MoodleClient:
    def __init__(self, config):
        self.config = config

    async def __aenter__(self):
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            raise MoodleAutomationError(
                "Playwright is required for Moodle automation. Run: python -m pip install -e . && python -m playwright install chromium"
            ) from exc

        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.config.headless)
        self.context = await self.browser.new_context(accept_downloads=True)
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.context.close()
        await self.browser.close()
        await self._playwright.stop()

    async def login(self) -> None:
        await self.page.goto(self.config.moodle_courses_url, wait_until="domcontentloaded")
        if await self._is_logged_in():
            return

        username = self.page.locator("input[name='username'], input#username").first
        password = self.page.locator("input[name='password'], input#password").first
        if not await username.count() or not await password.count():
            raise MoodleAutomationError("Could not find Moodle username/password fields on the login page.")

        await username.fill(self.config.username)
        await password.fill(self.config.password)
        login_button = self.page.locator("button[type='submit'], input[type='submit'], button#loginbtn, input#loginbtn").first
        await login_button.click()
        await self.page.wait_for_load_state("domcontentloaded")

        if not await self._is_logged_in():
            raise MoodleAutomationError("Moodle login did not reach the courses page. Check Campus ID credentials.")

    async def _is_logged_in(self) -> bool:
        current = self.page.url
        if "/login/" in current:
            return False
        links = await _extract_links(self.page)
        return any("/course/view.php" in href for _, href in links) or "my/courses.php" in current

    async def discover_courses(self) -> List[Course]:
        await self.page.goto(self.config.moodle_courses_url, wait_until="domcontentloaded")
        return discover_courses_from_links(await _extract_links(self.page))

    async def discover_resources(self, course: Course) -> List[Resource]:
        await self.page.goto(course.url, wait_until="domcontentloaded")
        return discover_resources_from_links(course.title, await _extract_links(self.page))

    async def download_resource_bytes(self, resource: Resource) -> Tuple[bytes, str]:
        response = await self.context.request.get(resource.url, max_redirects=10)
        if not response.ok:
            raise MoodleAutomationError(f"Download failed with HTTP {response.status}: {resource.title}")
        content = await response.body()
        final_url = response.url
        return content, final_url
