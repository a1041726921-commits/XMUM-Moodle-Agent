import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
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


def configure_playwright_browser_path(frozen: bool = False) -> None:
    current_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if current_path and not _is_missing_bundled_playwright_path(current_path, frozen):
        return
    if not frozen:
        return

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        browser_cache = Path(local_app_data) / "ms-playwright"
    else:
        browser_cache = Path.home() / "AppData" / "Local" / "ms-playwright"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_cache)


def _is_missing_bundled_playwright_path(path_text: str, frozen: bool) -> bool:
    if not frozen:
        return False
    path = Path(path_text)
    lower_parts = {part.lower() for part in path.parts}
    return (
        not path.exists()
        and ".local-browsers" in lower_parts
        and "playwright" in lower_parts
        and "driver" in lower_parts
        and "package" in lower_parts
    )


def discover_courses_from_links(links: Sequence[Link]) -> List[Course]:
    courses: List[Course] = []
    seen = {}
    for title, href in links:
        if "/course/view.php" not in href or "id=" not in href:
            continue
        clean_title = _clean_course_title(title) or "Untitled Course"
        key = href.split("#", 1)[0]
        existing_index = seen.get(key)
        if existing_index is not None:
            existing = courses[existing_index]
            if _is_better_course_title(clean_title, existing.title):
                courses[existing_index] = Course(title=clean_title, url=existing.url)
            continue
        seen[key] = len(courses)
        courses.append(Course(title=clean_title, url=key))
    return courses


def discover_resources_from_links(course_title: str, links: Sequence[Link]) -> List[Resource]:
    resources: List[Resource] = []
    seen = {}
    for title, href in links:
        extension = _extension_from_url(href)
        is_resource_page = "/mod/resource/view.php" in href or "/mod/folder/view.php" in href
        is_direct_file = "pluginfile.php" in href and (extension in RESOURCE_EXTENSIONS or not extension)
        if not is_resource_page and not is_direct_file:
            continue
        key = href.split("#", 1)[0]
        clean_title = _clean_resource_title(title) or _title_from_url(href)
        existing_index = seen.get(key)
        if existing_index is not None:
            existing = resources[existing_index]
            if _is_better_title(clean_title, existing.title):
                resources[existing_index] = Resource(
                    title=clean_title,
                    url=existing.url,
                    course_title=existing.course_title,
                    extension=existing.extension or extension,
                )
            continue
        seen[key] = len(resources)
        resources.append(
            Resource(
                title=clean_title,
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


def _clean_course_title(value: str) -> str:
    value = _clean_link_text(value)
    action_match = re.search(r"Actions for course\s+(.+)", value, flags=re.IGNORECASE | re.DOTALL)
    if action_match:
        value = action_match.group(1)
    value = re.sub(r"^Course name\s*", "", value, flags=re.IGNORECASE).strip()
    value = re.sub(r"^Course image\s*", "", value, flags=re.IGNORECASE).strip()
    value = re.sub(r"\s*\d+%\s*(已完成|completed).*$", "", value, flags=re.IGNORECASE | re.DOTALL).strip()
    return value


def _is_better_course_title(candidate: str, current: str) -> bool:
    poor_titles = {"", "course image", "course name", "untitled course"}
    current_lower = current.strip().lower()
    if current_lower in poor_titles or "course image" in current_lower:
        return candidate.strip().lower() not in poor_titles
    if "..." in current and "..." not in candidate:
        return True
    return len(candidate) > len(current) and current.lower() in candidate.lower()


def _clean_resource_title(value: str) -> str:
    value = _clean_link_text(value)
    value = re.sub(r"\s*(文件|File)\s*$", "", value, flags=re.IGNORECASE).strip()
    return value


def _is_better_title(candidate: str, current: str) -> bool:
    poor_titles = {"", "view.php", "resource", "file", "moodle resource"}
    if current.strip().lower() in poor_titles:
        return candidate.strip().lower() not in poor_titles
    return len(candidate) > len(current) and current.lower() in candidate.lower()


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
        """anchors => anchors.map(a => {
            let text = (a.getAttribute('title') || a.innerText || a.getAttribute('aria-label') || '').trim();
            if (a.href.includes('/course/view.php')) {
                const card = a.closest('[data-region="course-content"], .dashboard-card, .card');
                const action = card && card.querySelector('[aria-label^="Actions for course"], [title^="Actions for course"]');
                const actionLabel = action && (action.getAttribute('aria-label') || action.getAttribute('title'));
                if (actionLabel) {
                    text = actionLabel.replace(/^Actions for course\\s*/i, '').trim();
                } else if (card) {
                    const cardText = (card.innerText || card.textContent || '').trim();
                    const match = cardText.match(/Actions for course\\s+([^\\n]+)/i);
                    if (match) {
                        text = match[1].trim();
                    }
                }
            }
            return [text, a.href];
        })""",
    )
    return [(str(title), str(href)) for title, href in links if href]


async def _wait_for_page_ready(page) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass


async def _prepare_all_courses_view(page) -> None:
    await _select_all_courses_filter(page)
    await _wait_for_page_ready(page)
    await _expand_all_course_cards(page)
    await _wait_for_page_ready(page)


async def _select_all_courses_filter(page) -> None:
    try:
        await page.evaluate(
            """() => {
                // Prefer Moodle's "All (including removed from view)" option.
                const hiddenValues = new Set([
                    'allincludinghidden',
                    'allincludingremovedfromview',
                    'allincludingremoved',
                    'allincludinghiddenfromview'
                ]);
                const hiddenText = /all\\s*\\(\\s*including removed from view\\s*\\)|including removed from view|including hidden|removed from view/i;
                const allText = /^(all|all courses|全部|所有|所有课程)$/i;
                const normalize = value => String(value || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
                const dispatchChange = element => {
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                };

                for (const select of document.querySelectorAll('select')) {
                    const options = Array.from(select.options);
                    let option = options.find(candidate => {
                        const text = (candidate.textContent || '').trim();
                        const value = normalize(candidate.value || candidate.getAttribute('data-value'));
                        return hiddenText.test(text) || hiddenValues.has(value);
                    });
                    option = option || options.find(candidate => {
                        const text = (candidate.textContent || '').trim();
                        const value = normalize(candidate.value || candidate.getAttribute('data-value'));
                        return allText.test(text) || value === 'all';
                    });
                    if (option && select.value !== option.value) {
                        select.value = option.value;
                        dispatchChange(select);
                        return true;
                    }
                    if (option) {
                        return true;
                    }
                }

                const candidates = Array.from(document.querySelectorAll(
                    'button, a, [role="option"], [data-value], [data-filtervalue]'
                ));
                let target = candidates.find(element => {
                    const text = (element.textContent || element.getAttribute('aria-label') || '').trim();
                    const value = normalize(
                        element.getAttribute('data-value') ||
                        element.getAttribute('data-filtervalue') ||
                        element.getAttribute('href')
                    );
                    return hiddenText.test(text) || hiddenValues.has(value);
                });
                target = target || candidates.find(element => {
                    const text = (element.textContent || element.getAttribute('aria-label') || '').trim();
                    const value = normalize(element.getAttribute('data-value') || element.getAttribute('data-filtervalue') || '');
                    return allText.test(text) || value === 'all';
                });
                if (target) {
                    target.click();
                    return true;
                }
                return false;
            }"""
        )
    except Exception:
        pass


async def _expand_all_course_cards(page) -> None:
    if not hasattr(page, "locator"):
        return
    selectors = [
        'button:has-text("Show more")',
        'a:has-text("Show more")',
        'button:has-text("Load more")',
        'a:has-text("Load more")',
        'button:has-text("显示更多")',
        'a:has-text("显示更多")',
        'button:has-text("加载更多")',
        'a:has-text("加载更多")',
        '[data-action="more-courses"]',
        '[data-region="paging-control"] button',
    ]
    for _ in range(20):
        clicked = False
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count():
                    await locator.click()
                    clicked = True
                    await _wait_for_page_ready(page)
                    break
            except Exception:
                continue
        if not clicked:
            return


def _classify_links(links: Sequence[Link]) -> Dict[str, int]:
    counts = {
        "total": len(links),
        "course_view": 0,
        "my_courses": 0,
        "mod_resource": 0,
        "pluginfile": 0,
    }
    for _, href in links:
        if "/course/view.php" in href:
            counts["course_view"] += 1
        if "/my/courses.php" in href:
            counts["my_courses"] += 1
        if "/mod/resource/view.php" in href:
            counts["mod_resource"] += 1
        if "pluginfile.php" in href:
            counts["pluginfile"] += 1
    return counts


class MoodleClient:
    def __init__(self, config):
        self.config = config

    async def __aenter__(self):
        configure_playwright_browser_path(frozen=bool(getattr(sys, "frozen", False)))
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
        links: List[Link] = []
        for url in _course_overview_urls(self.config.moodle_courses_url):
            await self.page.goto(url, wait_until="domcontentloaded")
            await _wait_for_page_ready(self.page)
            if "/my/courses.php" in url:
                await _prepare_all_courses_view(self.page)
            links.extend(await _extract_links(self.page))
        return discover_courses_from_links(links)

    async def debug_page(self, output_dir: Path) -> Dict[str, object]:
        output_dir.mkdir(parents=True, exist_ok=True)
        await self.page.goto(_course_overview_urls(self.config.moodle_courses_url)[0], wait_until="domcontentloaded")
        await _wait_for_page_ready(self.page)
        await _prepare_all_courses_view(self.page)
        links = await _extract_links(self.page)
        title = await self.page.title()
        url = self.page.url
        html = await self.page.content()
        screenshot_path = output_dir / "moodle-courses-page.png"
        html_path = output_dir / "moodle-courses-page.html"
        links_path = output_dir / "moodle-links.json"
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        html_path.write_text(html, encoding="utf-8")
        links_path.write_text(
            json.dumps(
                [{"text": title, "href": href} for title, href in links],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return {
            "url": url,
            "title": title,
            "counts": _classify_links(links),
            "course_count": len(discover_courses_from_links(links)),
            "screenshot": str(screenshot_path),
            "html": str(html_path),
            "links": str(links_path),
        }

    async def discover_resources(self, course: Course) -> List[Resource]:
        await self.page.goto(course.url, wait_until="domcontentloaded")
        await _wait_for_page_ready(self.page)
        return discover_resources_from_links(course.title, await _extract_links(self.page))

    async def download_resource_bytes(self, resource: Resource) -> Tuple[bytes, str]:
        response = await self.context.request.get(resource.url, max_redirects=10)
        if not response.ok:
            raise MoodleAutomationError(f"Download failed with HTTP {response.status}: {resource.title}")
        content = await response.body()
        final_url = response.url
        return content, final_url


def _course_overview_urls(configured_url: str) -> List[str]:
    urls = []
    parsed = urlparse(configured_url)
    if parsed.netloc == "l.xmu.edu.my":
        canonical = "https://l.xmu.edu.my/my/courses.php"
        urls.append(canonical)
    if configured_url not in urls:
        urls.append(configured_url)
    return urls
