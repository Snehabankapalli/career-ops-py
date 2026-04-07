"""Job scraper using Playwright for dynamic content."""

import asyncio
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class JobData:
    """Structured job posting data."""
    url: str
    company: str
    title: str
    description: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    posting_date: Optional[str] = None
    raw_html: Optional[str] = None


class JobScraper:
    """Scraper for job boards using Playwright."""

    SUPPORTED_BOARDS = {
        "greenhouse": r"boards\.greenhouse\.io",
        "lever": r"jobs\.lever\.co",
        "ashby": r"jobs\.ashbyhq\.com",
        "workday": r"wd\d+\.myworkdayjobs\.com",
        "linkedin": r"linkedin\.com/jobs",
    }

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def _detect_board(self, url: str) -> Optional[str]:
        """Detect which job board a URL belongs to."""
        for board, pattern in self.SUPPORTED_BOARDS.items():
            if re.search(pattern, url):
                return board
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def scrape(self, url: str) -> JobData:
        """Scrape a job posting from URL."""
        if not self._browser:
            raise RuntimeError("Scraper not initialized. Use async context manager.")

        board_type = self._detect_board(url)
        page = await self._browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(2)  # Allow JS to render

            if board_type == "greenhouse":
                return await self._parse_greenhouse(page, url)
            elif board_type == "lever":
                return await self._parse_lever(page, url)
            elif board_type == "ashby":
                return await self._parse_ashby(page, url)
            else:
                return await self._parse_generic(page, url)

        finally:
            await page.close()

    async def _parse_greenhouse(self, page: Page, url: str) -> JobData:
        """Parse Greenhouse job board."""
        title = await page.locator("h1.app-title").text_content() or ""
        company = await page.locator("span.company-name").text_content() or ""
        location = await page.locator("div.location").text_content() or ""

        # Get full description
        description = await page.locator("div#content").text_content() or ""
        if not description:
            description = await page.locator("[class*='job-description']").text_content() or ""

        return JobData(
            url=url,
            company=company.strip(),
            title=title.strip(),
            description=description.strip(),
            location=location.strip() if location else None,
        )

    async def _parse_lever(self, page: Page, url: str) -> JobData:
        """Parse Lever job board."""
        title = await page.locator("h2.posting-headline").text_content() or ""
        company = await page.locator("a.main-header-logo").get_attribute("title") or ""

        # Description is usually in sections
        description_parts = []
        sections = await page.locator("section.page-content").all()
        for section in sections:
            text = await section.text_content()
            if text:
                description_parts.append(text)

        description = "\n\n".join(description_parts)

        return JobData(
            url=url,
            company=company.strip(),
            title=title.strip(),
            description=description.strip(),
        )

    async def _parse_ashby(self, page: Page, url: str) -> JobData:
        """Parse Ashby job board."""
        title = await page.locator("h1[data-testid='job-post-title']").text_content() or ""
        company = await page.locator("a[data-testid='company-name']").text_content() or ""

        description = await page.locator("div[data-testid='job-description']").text_content() or ""

        return JobData(
            url=url,
            company=company.strip(),
            title=title.strip(),
            description=description.strip(),
        )

    async def _parse_generic(self, page: Page, url: str) -> JobData:
        """Generic parser for unknown job boards."""
        # Try common selectors
        title_selectors = ["h1", "h2", "[class*='title']", "[class*='job-title']"]
        company_selectors = ["[class*='company']", "[class*='employer']"]
        desc_selectors = ["[class*='description']", "[class*='job-description']", "main", "article"]

        title = ""
        for sel in title_selectors:
            try:
                title = await page.locator(sel).first.text_content() or ""
                if title and len(title.strip()) > 0:
                    break
            except:
                continue

        company = ""
        for sel in company_selectors:
            try:
                company = await page.locator(sel).first.text_content() or ""
                if company and len(company.strip()) > 0:
                    break
            except:
                continue

        description = ""
        for sel in desc_selectors:
            try:
                description = await page.locator(sel).first.text_content() or ""
                if description and len(description.strip()) > 100:
                    break
            except:
                continue

        # Extract domain as company name fallback
        if not company:
            domain = urlparse(url).netloc
            company = domain.replace("www.", "").split(".")[0].capitalize()

        return JobData(
            url=url,
            company=company.strip() if company else "Unknown",
            title=title.strip() if title else "Unknown Position",
            description=description.strip() if description else "",
        )

    async def scrape_batch(self, urls: list[str], max_concurrent: int = 3) -> list[JobData]:
        """Scrape multiple URLs with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_limit(url: str) -> Optional[JobData]:
            async with semaphore:
                try:
                    return await self.scrape(url)
                except Exception as e:
                    print(f"Failed to scrape {url}: {e}")
                    return None

        tasks = [scrape_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
