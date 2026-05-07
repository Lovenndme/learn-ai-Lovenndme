from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urljoin, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://jwch.fzu.edu.cn/"
LIST_ENTRY_URL = urljoin(BASE_URL, "jxtz.htm")
DEFAULT_OWNER = "1744984858"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)


@dataclass
class NoticeSummary:
    department: str
    title: str
    date: str
    detail_url: str


@dataclass
class Attachment:
    name: str
    url: str
    file_id: str
    owner: str
    download_count: str = ""
    local_path: str = ""


@dataclass
class NoticeDetail:
    notice_id: str
    title: str
    date: str
    content_text: str
    attachments: list[Attachment]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def attr_value(attrs: list[tuple[str, str | None]], name: str) -> str:
    for key, value in attrs:
        if key == name and value is not None:
            return value
    return ""


def class_contains(attrs: list[tuple[str, str | None]], class_name: str) -> bool:
    classes = attr_value(attrs, "class").split()
    return class_name in classes


def fetch_text(url: str, timeout: int = 15) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
    return body.decode("utf-8-sig", errors="replace")


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


class NoticeListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.notices: list[dict[str, object]] = []
        self.in_notice_list = False
        self.notice_list_depth = 0
        self.current: dict[str, object] | None = None
        self.current_li_depth = 0
        self.in_date = False
        self.current_anchor: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "ul" and class_contains(attrs, "list-gl"):
            self.in_notice_list = True
            self.notice_list_depth = 1
            return

        if self.in_notice_list and tag == "ul":
            self.notice_list_depth += 1

        if not self.in_notice_list:
            return

        if tag == "li" and self.current is None:
            self.current = {"text": [], "date": [], "links": []}
            self.current_li_depth = 1
            return

        if self.current is None:
            return

        if tag == "li":
            self.current_li_depth += 1
        elif tag == "span" and class_contains(attrs, "doclist_time"):
            self.in_date = True
        elif tag == "a":
            self.current_anchor = {
                "href": attr_value(attrs, "href"),
                "title": attr_value(attrs, "title"),
                "text": [],
            }

    def handle_data(self, data: str) -> None:
        if self.current is None:
            return

        self.current["text"].append(data)  # type: ignore[index, union-attr]

        if self.in_date:
            self.current["date"].append(data)  # type: ignore[index, union-attr]

        if self.current_anchor is not None:
            self.current_anchor["text"].append(data)  # type: ignore[index, union-attr]

    def handle_endtag(self, tag: str) -> None:
        if self.current_anchor is not None and tag == "a":
            self.current["links"].append(self.current_anchor)  # type: ignore[index, union-attr]
            self.current_anchor = None
            return

        if self.in_date and tag == "span":
            self.in_date = False
            return

        if self.current is not None and tag == "li":
            self.current_li_depth -= 1
            if self.current_li_depth == 0:
                self.notices.append(self.current)
                self.current = None
            return

        if self.in_notice_list and tag == "ul":
            self.notice_list_depth -= 1
            if self.notice_list_depth == 0:
                self.in_notice_list = False


class NoticeDetailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.date_parts: list[str] = []
        self.content_parts: list[str] = []
        self.attachments: list[dict[str, object]] = []
        self.in_title = False
        self.seen_title = False
        self.in_date = False
        self.in_content = False
        self.content_depth = 0
        self.current_attachment: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h4" and not self.seen_title:
            self.in_title = True
            self.seen_title = True
            return

        if tag == "span" and class_contains(attrs, "xl_sj_icon"):
            self.in_date = True
            return

        if tag == "div" and attr_value(attrs, "id") == "vsb_content":
            self.in_content = True
            self.content_depth = 1
            return

        if self.in_content and tag == "div":
            self.content_depth += 1

        href = attr_value(attrs, "href")
        if tag == "a" and "download.jsp" in href:
            absolute_url = urljoin(BASE_URL, href)
            query = parse_qs(urlparse(absolute_url).query)
            self.current_attachment = {
                "name_parts": [],
                "url": absolute_url,
                "file_id": query.get("wbfileid", [""])[0],
                "owner": query.get("owner", [DEFAULT_OWNER])[0],
            }

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_date:
            self.date_parts.append(data)
        if self.in_content:
            self.content_parts.append(data)
        if self.current_attachment is not None:
            self.current_attachment["name_parts"].append(data)  # type: ignore[index, union-attr]

    def handle_endtag(self, tag: str) -> None:
        if self.in_title and tag == "h4":
            self.in_title = False
            return

        if self.in_date and tag == "span":
            self.in_date = False
            return

        if self.current_attachment is not None and tag == "a":
            self.attachments.append(self.current_attachment)
            self.current_attachment = None
            return

        if self.in_content and tag == "div":
            self.content_depth -= 1
            if self.content_depth == 0:
                self.in_content = False


def parse_total_pages(html_text: str) -> int:
    page_numbers = [int(item) for item in re.findall(r'href=["\']jxtz/(\d+)\.htm["\']', html_text)]
    if not page_numbers:
        return 1
    return max(page_numbers) + 1


def list_url_for_page(page_number: int, total_pages: int) -> str:
    if page_number == 1:
        return LIST_ENTRY_URL
    static_page_number = total_pages - page_number + 1
    return urljoin(BASE_URL, f"jxtz/{static_page_number}.htm")


def parse_notice_list(html_text: str, page_url: str) -> list[NoticeSummary]:
    parser = NoticeListParser()
    parser.feed(html_text)
    notices: list[NoticeSummary] = []

    for item in parser.notices:
        links = item.get("links") or []
        if not links:
            continue

        link = links[0]
        raw_text = clean_text("".join(item.get("text", [])))  # type: ignore[arg-type]
        date = clean_text("".join(item.get("date", [])))  # type: ignore[arg-type]
        department_match = re.search(r"【([^】]+)】", raw_text)
        department = department_match.group(1) if department_match else ""
        link_text = clean_text("".join(link.get("text", [])))  # type: ignore[union-attr, arg-type]
        title = clean_text(str(link.get("title") or link_text))  # type: ignore[union-attr]
        href = str(link.get("href") or "")  # type: ignore[union-attr]

        if not title or not href:
            continue

        notices.append(
            NoticeSummary(
                department=department,
                title=title,
                date=date,
                detail_url=urljoin(page_url, href),
            )
        )

    return notices


def extract_notice_id(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    if query.get("wbnewsid"):
        return query["wbnewsid"][0]
    match = re.search(r"/(\d+)\.htm(?:$|\?)", url)
    if match:
        return match.group(1)
    return quote(url, safe="").replace("%", "")


def parse_notice_detail(html_text: str, detail_url: str) -> NoticeDetail:
    parser = NoticeDetailParser()
    parser.feed(html_text)

    title = clean_text("".join(parser.title_parts))
    raw_date = clean_text("".join(parser.date_parts))
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", raw_date)
    date = date_match.group(0) if date_match else raw_date.replace("发布时间：", "")
    content_text = clean_text("".join(parser.content_parts))

    attachments = []
    for item in parser.attachments:
        name = clean_text("".join(item.get("name_parts", [])))  # type: ignore[arg-type]
        attachments.append(
            Attachment(
                name=name,
                url=str(item.get("url", "")),
                file_id=str(item.get("file_id", "")),
                owner=str(item.get("owner", DEFAULT_OWNER)),
            )
        )

    return NoticeDetail(
        notice_id=extract_notice_id(detail_url),
        title=title,
        date=date,
        content_text=content_text,
        attachments=attachments,
    )


def fetch_attachment_count(file_id: str, owner: str) -> str:
    if not file_id:
        return ""
    url = urljoin(
        BASE_URL,
        "/system/resource/code/news/click/clicktimes.jsp"
        f"?wbnewsid={file_id}&owner={owner}&type=wbnewsfile&randomid=nattach",
    )
    try:
        payload = json.loads(fetch_text(url))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return ""
    return str(payload.get("wbshowtimes", ""))


def safe_filename(value: str, suffix: str = "") -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\s]+", "_", value).strip("_")
    return f"{cleaned[:120]}{suffix}"


def write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def download_attachment(attachment: Attachment, output_dir: Path) -> str:
    suffix = Path(attachment.name).suffix or Path(urlparse(attachment.url).path).suffix
    filename = safe_filename(f"{attachment.file_id}_{attachment.name}", suffix="")
    if suffix and not filename.endswith(suffix):
        filename += suffix
    path = output_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(fetch_bytes(attachment.url))
    return str(path)


def crawl(limit: int, output_dir: Path, delay: float, download_attachments: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    details_dir = output_dir / "details"
    attachments_dir = output_dir / "attachments"

    first_page_html = fetch_text(LIST_ENTRY_URL)
    total_pages = parse_total_pages(first_page_html)

    notice_rows: list[dict[str, str]] = []
    attachment_rows: list[dict[str, str]] = []
    collected = 0
    page_number = 1

    while collected < limit and page_number <= total_pages:
        page_url = list_url_for_page(page_number, total_pages)
        html_text = first_page_html if page_number == 1 else fetch_text(page_url)
        summaries = parse_notice_list(html_text, page_url)

        for summary in summaries:
            if collected >= limit:
                break

            print(f"[{collected + 1}/{limit}] {summary.date} {summary.department} {summary.title}")
            detail_html = fetch_text(summary.detail_url)
            detail = parse_notice_detail(detail_html, summary.detail_url)
            notice_id = detail.notice_id or extract_notice_id(summary.detail_url)
            detail_path = details_dir / f"{notice_id}.html"
            detail_path.parent.mkdir(parents=True, exist_ok=True)
            detail_path.write_text(detail_html, encoding="utf-8")

            for attachment in detail.attachments:
                attachment.download_count = fetch_attachment_count(attachment.file_id, attachment.owner)
                if download_attachments:
                    try:
                        attachment.local_path = download_attachment(attachment, attachments_dir)
                    except (HTTPError, URLError, TimeoutError, OSError):
                        attachment.local_path = ""

                attachment_rows.append(
                    {
                        "notice_id": notice_id,
                        "notice_title": summary.title,
                        "department": summary.department,
                        "date": summary.date,
                        "detail_url": summary.detail_url,
                        "attachment_name": attachment.name,
                        "attachment_file_id": attachment.file_id,
                        "attachment_owner": attachment.owner,
                        "download_count": attachment.download_count,
                        "download_url": attachment.url,
                        "local_path": attachment.local_path,
                    }
                )

            notice_rows.append(
                {
                    "notice_id": notice_id,
                    "department": summary.department,
                    "title": summary.title,
                    "date": summary.date,
                    "detail_url": summary.detail_url,
                    "detail_html_path": str(detail_path),
                    "content_text": detail.content_text,
                    "attachment_count": str(len(detail.attachments)),
                    "attachment_names": " | ".join(item.name for item in detail.attachments),
                    "attachment_file_ids": " | ".join(item.file_id for item in detail.attachments),
                    "attachment_download_counts": " | ".join(item.download_count for item in detail.attachments),
                    "attachment_urls": " | ".join(item.url for item in detail.attachments),
                }
            )

            collected += 1
            if delay > 0:
                time.sleep(delay)

        page_number += 1

    write_csv(
        output_dir / "notices.csv",
        notice_rows,
        [
            "notice_id",
            "department",
            "title",
            "date",
            "detail_url",
            "detail_html_path",
            "content_text",
            "attachment_count",
            "attachment_names",
            "attachment_file_ids",
            "attachment_download_counts",
            "attachment_urls",
        ],
    )
    write_csv(
        output_dir / "attachments.csv",
        attachment_rows,
        [
            "notice_id",
            "notice_title",
            "department",
            "date",
            "detail_url",
            "attachment_name",
            "attachment_file_id",
            "attachment_owner",
            "download_count",
            "download_url",
            "local_path",
        ],
    )

    print(f"Saved {len(notice_rows)} notices to {output_dir / 'notices.csv'}")
    print(f"Saved {len(attachment_rows)} attachments to {output_dir / 'attachments.csv'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl FZU jwch teaching notices.")
    parser.add_argument("--limit", type=int, default=500, help="number of notices to crawl")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="directory for CSV files and detail HTML files",
    )
    parser.add_argument("--delay", type=float, default=0.3, help="delay between detail-page requests")
    parser.add_argument(
        "--download-attachments",
        action="store_true",
        help="download attachment files as well",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    crawl(
        limit=args.limit,
        output_dir=args.output_dir,
        delay=args.delay,
        download_attachments=args.download_attachments,
    )


if __name__ == "__main__":
    main()
