from __future__ import annotations

import argparse
import csv
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


BASE_URL = "https://summer-ospp.ac.cn"
PROJECT_LIST_API = urljoin(BASE_URL, "/api/getProList")
PROJECT_DETAIL_API = urljoin(BASE_URL, "/api/getProDetail")
PUBLIC_APPLICATION_API = urljoin(BASE_URL, "/api/publicApplication")
PROJECT_DETAIL_URL = urljoin(BASE_URL, "/org/prodetail/")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)

SUPPORT_LANGUAGE = {
    0: "中文&English",
    1: "中文",
    2: "English",
}

CSV_COLUMNS = [
    "program_code",
    "project_name",
    "project_name_en",
    "org_name",
    "org_name_en",
    "difficulty",
    "support_language",
    "selected_student",
    "tech_tags",
    "programming_language_tags",
    "description",
    "output_requirements",
    "tech_requirements",
    "repos",
    "mentor_name",
    "mentor_email",
    "completion_time_hours",
    "arch",
    "license",
    "detail_url",
    "application_pdf_url",
    "application_pdf_file",
    "raw_detail_file",
]


class HtmlTextExtractor(HTMLParser):
    block_tags = {"p", "div", "li", "br", "tr", "h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "li":
            self.parts.append("\n- ")
        elif tag == "br":
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.block_tags:
            self.parts.append("\n")

    def text(self) -> str:
        return clean_text("".join(self.parts))


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def one_line(value: Any) -> str:
    return re.sub(r"\s+", " ", clean_text(value)).strip()


def safe_filename(value: Any) -> str:
    filename = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value))
    return filename.strip("._") or "untitled"


def parse_json_field(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return default


def join_values(values: Any) -> str:
    if values in (None, ""):
        return ""
    if isinstance(values, list):
        return "; ".join(clean_text(item) for item in values if item not in (None, ""))
    return clean_text(values)


def parse_tag_pairs(value: Any) -> list[str]:
    items = parse_json_field(value, [])
    tags: list[str] = []
    if not isinstance(items, list):
        return tags
    for item in items:
        if isinstance(item, list) and len(item) >= 2:
            tags.append(clean_text(item[1]))
        elif item not in (None, ""):
            tags.append(clean_text(item))
    return tags


def html_to_text(html_text: Any) -> str:
    if not html_text:
        return ""
    parser = HtmlTextExtractor()
    parser.feed(str(html_text))
    parser.close()
    return parser.text()


def flatten_requirement(items: Any) -> str:
    requirements = parse_json_field(items, [])
    if not isinstance(requirements, list):
        return clean_text(requirements)

    lines: list[str] = []
    for item in requirements:
        if not item:
            continue
        if isinstance(item, dict):
            title = clean_text(item.get("title"))
            if title:
                lines.append(title)
            children = item.get("children") or []
            if isinstance(children, list):
                for child in children:
                    child_text = clean_text(child)
                    if child_text:
                        lines.append(f"  - {child_text}")
        else:
            item_text = clean_text(item)
            if item_text:
                lines.append(item_text)
    return "\n".join(lines)


def post_json(url: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    body, content_type, _ = post_bytes(url, payload, timeout)
    if "json" not in content_type and not body.lstrip().startswith((b"{", b"[")):
        raise RuntimeError(f"接口没有返回 JSON：{url}")
    return json.loads(body.decode("utf-8", errors="replace"))


def post_bytes(
    url: str,
    payload: dict[str, Any],
    timeout: int = 30,
) -> tuple[bytes, str, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Referer": BASE_URL + "/org/projectlist",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return (
                response.read(),
                response.headers.get("content-type", ""),
                response.headers.get("content-disposition", ""),
            )
    except HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"请求失败：{url} HTTP {error.code} {message}") from error
    except URLError as error:
        raise RuntimeError(f"请求失败：{url} {error.reason}") from error


def fetch_project_page(
    page_num: int,
    page_size: int,
    keyword: str,
    difficulties: list[str],
    lang: str,
) -> dict[str, Any]:
    payload = {
        "supportLanguage": [],
        "techTag": [],
        "programmingLanguageTag": [],
        "programName": keyword,
        "difficulty": difficulties,
        "pageNum": page_num,
        "pageSize": page_size,
        "lang": lang,
        "orgName": [],
    }
    return post_json(PROJECT_LIST_API, payload)


def fetch_project_detail(program_code: str) -> dict[str, Any]:
    return post_json(PROJECT_DETAIL_API, {"programId": program_code, "type": "org"})


def normalize_project(
    summary: dict[str, Any],
    detail: dict[str, Any],
    raw_detail_file: str,
    application_pdf_file: str = "",
) -> dict[str, str]:
    program_code = clean_text(detail.get("programCode") or summary.get("programCode"))
    org_program_id = detail.get("orgProgramId") or summary.get("proId")
    support_language = detail.get("supportLanguage", summary.get("supportLanguage", ""))
    tech_tags = parse_tag_pairs(detail.get("techTag") or summary.get("techTag"))
    programming_language_tags = parse_json_field(detail.get("programmingLanguageTag"), [])

    return {
        "program_code": program_code,
        "project_name": clean_text(detail.get("programName") or summary.get("programName")),
        "project_name_en": clean_text(detail.get("programNameEN") or summary.get("programNameEN")),
        "org_name": clean_text(summary.get("orgName")),
        "org_name_en": clean_text(summary.get("orgNameEN")),
        "difficulty": clean_text(detail.get("difficulty") or summary.get("difficulty")),
        "support_language": SUPPORT_LANGUAGE.get(support_language, clean_text(support_language)),
        "selected_student": clean_text(detail.get("matchedStudentName") or summary.get("matchedStudentName")),
        "tech_tags": join_values(tech_tags),
        "programming_language_tags": join_values(programming_language_tags),
        "description": html_to_text(detail.get("programDesc") or detail.get("programDescEN")),
        "output_requirements": flatten_requirement(detail.get("outputRequirement") or detail.get("outputRequirementEN")),
        "tech_requirements": flatten_requirement(detail.get("techRequirement") or detail.get("techRequirementEN")),
        "repos": join_values(detail.get("repo")),
        "mentor_name": clean_text(detail.get("nickname") or detail.get("firstName")),
        "mentor_email": clean_text(detail.get("email")),
        "completion_time_hours": clean_text(detail.get("completionTime")),
        "arch": clean_text(detail.get("arch")),
        "license": join_values(detail.get("license")),
        "detail_url": f"{PROJECT_DETAIL_URL}{program_code}?lang=zh&list=pro",
        "application_pdf_url": f"{BASE_URL}/previewPdf/{org_program_id}" if org_program_id else "",
        "application_pdf_file": application_pdf_file,
        "raw_detail_file": raw_detail_file,
    }


def download_application_pdf(pro_id: Any, program_code: str, output_dir: Path) -> str:
    if not pro_id:
        return ""

    body, content_type, _ = post_bytes(PUBLIC_APPLICATION_API, {"proId": pro_id}, timeout=60)
    if "application/pdf" not in content_type and not body.startswith(b"%PDF"):
        raise RuntimeError(f"申请书接口没有返回 PDF：{program_code}")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{safe_filename(program_code)}.pdf"
    pdf_path.write_bytes(body)
    return str(pdf_path)


def write_outputs(projects: list[dict[str, str]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "projects.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(projects)

    json_path = output_dir / "projects.json"
    json_path.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8")


def crawl(args: argparse.Namespace) -> list[dict[str, str]]:
    output_dir = Path(args.output_dir)
    raw_dir = output_dir / "raw_details"
    pdf_dir = output_dir / "applications"
    projects: list[dict[str, str]] = []
    page_num = 1
    total = None

    while True:
        page = fetch_project_page(
            page_num=page_num,
            page_size=args.page_size,
            keyword=args.keyword,
            difficulties=args.difficulty,
            lang=args.lang,
        )
        page_rows = page.get("rows") or []
        total = page.get("total", total)
        if not page_rows:
            break

        for summary in page_rows:
            if args.limit and len(projects) >= args.limit:
                break

            program_code = clean_text(summary.get("programCode"))
            if not program_code:
                continue

            print(f"正在抓取项目 {len(projects) + 1}: {program_code}")
            detail = fetch_project_detail(program_code)

            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_path = raw_dir / f"{safe_filename(program_code)}.json"
            raw_path.write_text(
                json.dumps({"summary": summary, "detail": detail}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            application_pdf_file = ""
            if args.download_applications:
                pro_id = detail.get("orgProgramId") or summary.get("proId")
                try:
                    application_pdf_file = download_application_pdf(pro_id, program_code, pdf_dir)
                except RuntimeError as error:
                    print(f"申请书下载失败：{program_code}，原因：{error}")

            projects.append(
                normalize_project(
                    summary=summary,
                    detail=detail,
                    raw_detail_file=str(raw_path),
                    application_pdf_file=application_pdf_file,
                )
            )
            if args.delay > 0:
                time.sleep(args.delay)

        if args.limit and len(projects) >= args.limit:
            break
        if total is not None and page_num * args.page_size >= int(total):
            break
        page_num += 1

    write_outputs(projects, output_dir)
    return projects


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="开源之夏项目列表和详情接口爬虫")
    parser.add_argument("--limit", type=int, default=20, help="最多抓取多少个项目，0 表示抓取全部")
    parser.add_argument("--page-size", type=int, default=50, help="列表接口每页项目数量")
    parser.add_argument("--keyword", default="", help="按项目名称关键词搜索")
    parser.add_argument("--difficulty", action="append", default=[], help="按难度筛选，可重复传入")
    parser.add_argument("--lang", default="zh", choices=["zh", "en"], help="列表接口语言")
    parser.add_argument("--delay", type=float, default=0.2, help="每个详情请求之间的等待秒数")
    parser.add_argument("--output-dir", default="data", help="输出目录")
    parser.add_argument("--download-applications", action="store_true", help="同时下载中选项目申请书 PDF")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    projects = crawl(args)
    print(f"完成，共保存 {len(projects)} 个项目到 {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
