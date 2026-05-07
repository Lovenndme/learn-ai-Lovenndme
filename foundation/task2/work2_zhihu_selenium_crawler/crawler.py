from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TOPIC_URL = "https://www.zhihu.com/topic/19554298/top-answers"
QUESTION_RE = re.compile(r"https?://(?:www\.)?zhihu\.com/question/(\d+)")

CSV_COLUMNS = [
    "question_index",
    "question_title",
    "question_detail",
    "question_url",
    "answer_index",
    "answer_author",
    "answer_text",
    "answer_url",
]


@dataclass
class QuestionLink:
    question_id: str
    title: str
    url: str


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_selenium_modules() -> tuple[Any, Any, Any, Any, Any, Any, Any]:
    try:
        from selenium import webdriver
        from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.chrome.options import Options as ChromeOptions
    except ImportError as error:
        raise SystemExit(
            "没有安装 Selenium。请先运行：python3 -m pip install -r requirements.txt"
        ) from error

    return webdriver, By, ChromeOptions, EdgeOptions, WebDriverWait, EC, (
        TimeoutException,
        StaleElementReferenceException,
    )


def create_driver(args: argparse.Namespace) -> Any:
    webdriver, _, ChromeOptions, EdgeOptions, _, _, _ = get_selenium_modules()

    profile_dir = Path(args.profile_dir or Path(args.output_dir) / "browser_profile")
    profile_dir.mkdir(parents=True, exist_ok=True)

    if args.browser == "edge":
        options = EdgeOptions()
    else:
        options = ChromeOptions()

    options.add_argument(f"--user-data-dir={profile_dir.resolve()}")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=zh-CN")
    if args.headless:
        options.add_argument("--headless=new")

    if args.browser == "edge":
        return webdriver.Edge(options=options)
    return webdriver.Chrome(options=options)


def wait_for_body(driver: Any, timeout: int = 20) -> None:
    _, By, _, _, WebDriverWait, EC, exceptions = get_selenium_modules()
    TimeoutException, _ = exceptions
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException as error:
        raise RuntimeError("页面加载超时，请检查网络或浏览器状态") from error


def pause_for_login(driver: Any, args: argparse.Namespace) -> None:
    print("浏览器已打开知乎话题页。")
    print("如果页面要求登录，请在浏览器里扫码或用账号正常登录。")
    if args.headless:
        print("当前是 headless 模式，无法扫码登录；请确认 profile 里已经保存过登录状态。")
        time.sleep(args.login_wait)
        return

    if args.skip_login_prompt:
        time.sleep(args.login_wait)
        return

    try:
        input("登录完成并能看到话题内容后，回到终端按 Enter 继续：")
    except EOFError:
        time.sleep(args.login_wait)


def collect_question_links(driver: Any, args: argparse.Namespace) -> list[QuestionLink]:
    questions: OrderedDict[str, QuestionLink] = OrderedDict()

    script = """
    const anchors = Array.from(document.querySelectorAll('a[href*="/question/"]'));
    return anchors.map((a) => {
      const card = a.closest('.ContentItem, .List-item, .QuestionItem, article, div');
      const titleNode = card && card.querySelector(
        '.ContentItem-title, .QuestionItem-title, h1, h2, h3, [class*="title"]'
      );
      return {
        href: a.href,
        text: (a.innerText || a.textContent || '').trim(),
        title: titleNode ? (titleNode.innerText || titleNode.textContent || '').trim() : ''
      };
    });
    """

    for scroll_index in range(args.topic_scroll_times):
        items = driver.execute_script(script) or []
        if not isinstance(items, list):
            print(f"话题页脚本返回异常类型：{type(items).__name__}，本次滚动先跳过")
            items = []

        for item in items:
            href = clean_text(item.get("href"))
            match = QUESTION_RE.search(href)
            if not match:
                continue

            question_id = match.group(1)
            title = clean_text(item.get("title") or item.get("text"))
            if len(title) < 4 or title in {"写回答", "查看全部"}:
                continue

            questions.setdefault(
                question_id,
                QuestionLink(
                    question_id=question_id,
                    title=title,
                    url=f"https://www.zhihu.com/question/{question_id}",
                ),
            )
            if len(questions) >= args.question_limit:
                break

        print(
            f"话题页滚动 {scroll_index + 1}/{args.topic_scroll_times}，"
            f"本次候选链接 {len(items)} 个，已发现 {len(questions)} 个问题"
        )
        if len(questions) >= args.question_limit:
            break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(args.delay)

    return list(questions.values())[: args.question_limit]


def extract_question_info(driver: Any, fallback_title: str) -> tuple[str, str]:
    script = """
    function firstText(selectors) {
      for (const selector of selectors) {
        const node = document.querySelector(selector);
        if (node) {
          const text = (node.innerText || node.textContent || '').trim();
          if (text) return text;
        }
      }
      return '';
    }

    const title = firstText([
      '.QuestionHeader-title',
      '.QuestionPage-title',
      'h1',
      '.ContentItem-title'
    ]);
    const detail = firstText([
      '.QuestionHeader-detail',
      '.QuestionRichText',
      '.QuestionHeader-main .RichText',
      '[class*="QuestionHeader-detail"]',
      '[class*="QuestionRichText"]'
    ]);
    return {title, detail};
    """
    info = driver.execute_script(script)
    title = clean_text(info.get("title") or fallback_title)
    detail = clean_text(info.get("detail"))
    return title, detail


def expand_visible_content(driver: Any) -> None:
    script = """
    const keywords = ['阅读全文', '展开阅读全文', '显示全部', '展开全部', '更多'];
    const buttons = Array.from(document.querySelectorAll('button, a')).filter((node) => {
      const text = (node.innerText || node.textContent || '').trim();
      return keywords.some((keyword) => text.includes(keyword));
    });
    for (const button of buttons.slice(0, 30)) {
      try { button.click(); } catch (error) {}
    }
    return buttons.length;
    """
    driver.execute_script(script)


def extract_answers(driver: Any) -> list[dict[str, str]]:
    script = """
    function textOf(node) {
      return node ? (node.innerText || node.textContent || '').trim() : '';
    }

    const nodes = Array.from(document.querySelectorAll('.AnswerItem, .List-item, .ContentItem'))
      .filter((node) => node.querySelector('.RichContent, .RichContent-inner, [itemprop="text"]'));

    const answers = [];
    for (const node of nodes) {
      const textNode = node.querySelector('.RichContent-inner, [itemprop="text"], .RichContent');
      const authorNode = node.querySelector(
        '.AuthorInfo-name a, .AuthorInfo-name, [itemprop="author"] [itemprop="name"]'
      );
      const metaUrl = node.querySelector('meta[itemprop="url"]');
      const answerLink = node.querySelector('a[href*="/answer/"]');
      const text = textOf(textNode)
        .replace(/阅读全文/g, '')
        .replace(/发布于.*?赞同/g, '赞同')
        .trim();
      if (text.length < 20) continue;
      answers.push({
        author: textOf(authorNode),
        text,
        url: metaUrl ? metaUrl.content : (answerLink ? answerLink.href : '')
      });
    }
    return answers;
    """
    rows = driver.execute_script(script)
    answers: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        text = clean_text(row.get("text"))
        if not text or text in seen:
            continue
        seen.add(text)
        answers.append(
            {
                "answer_author": clean_text(row.get("author")),
                "answer_text": text,
                "answer_url": clean_text(row.get("url")),
            }
        )
    return answers


def collect_answers_for_question(driver: Any, question: QuestionLink, args: argparse.Namespace) -> list[dict[str, str]]:
    answers: list[dict[str, str]] = []

    for scroll_index in range(args.answer_scroll_times):
        expand_visible_content(driver)
        answers = extract_answers(driver)
        print(
            f"  回答页滚动 {scroll_index + 1}/{args.answer_scroll_times}，"
            f"已发现 {len(answers)} 条回答"
        )
        if len(answers) >= args.answer_limit:
            break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(args.delay)

    return answers[: args.answer_limit]


def write_csv(rows: list[dict[str, str]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "zhihu_topic_answers.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def crawl(args: argparse.Namespace) -> list[dict[str, str]]:
    driver = create_driver(args)
    rows: list[dict[str, str]] = []

    try:
        driver.get(args.topic_url)
        wait_for_body(driver)
        pause_for_login(driver, args)

        questions = collect_question_links(driver, args)
        if not questions:
            raise RuntimeError("没有找到问题链接，请确认已经登录并能看到话题内容。")

        print(f"准备爬取 {len(questions)} 个问题。")
        for question_index, question in enumerate(questions, start=1):
            print(f"开始问题 {question_index}/{len(questions)}：{question.title}")
            driver.get(question.url)
            wait_for_body(driver)
            time.sleep(args.delay)

            title, detail = extract_question_info(driver, question.title)
            answers = collect_answers_for_question(driver, question, args)

            for answer_index, answer in enumerate(answers, start=1):
                rows.append(
                    {
                        "question_index": str(question_index),
                        "question_title": title,
                        "question_detail": detail,
                        "question_url": question.url,
                        "answer_index": str(answer_index),
                        **answer,
                    }
                )

        return rows
    finally:
        if not args.keep_browser_open:
            driver.quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="使用 Selenium 爬取知乎话题问题和回答")
    parser.add_argument("--topic-url", default=DEFAULT_TOPIC_URL, help="知乎话题页地址")
    parser.add_argument("--question-limit", type=int, default=20, help="最多爬取多少个问题")
    parser.add_argument("--answer-limit", type=int, default=10, help="每个问题最多爬取多少条回答")
    parser.add_argument("--topic-scroll-times", type=int, default=30, help="话题页最多滚动次数")
    parser.add_argument("--answer-scroll-times", type=int, default=20, help="每个问题页最多滚动次数")
    parser.add_argument("--delay", type=float, default=1.5, help="滚动和请求之间的等待秒数")
    parser.add_argument("--output-dir", default="data", help="输出目录")
    parser.add_argument("--profile-dir", default="", help="浏览器用户数据目录，用于保存登录状态")
    parser.add_argument("--browser", choices=["chrome", "edge"], default="chrome", help="使用的浏览器")
    parser.add_argument("--headless", action="store_true", help="无界面模式，必须已经保存过登录状态")
    parser.add_argument("--login-wait", type=int, default=30, help="跳过登录提示时等待的秒数")
    parser.add_argument("--skip-login-prompt", action="store_true", help="不等待手动按 Enter，直接等待一段时间后开始")
    parser.add_argument("--keep-browser-open", action="store_true", help="运行结束后不自动关闭浏览器")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.question_limit <= 0 or args.answer_limit <= 0:
        raise SystemExit("question-limit 和 answer-limit 必须大于 0")

    rows = crawl(args)
    csv_path = write_csv(rows, Path(args.output_dir))
    print(f"完成，共保存 {len(rows)} 条回答到 {csv_path.resolve()}")
    if len(rows) < args.question_limit * args.answer_limit:
        print("提示：实际数量少于目标值，通常是页面未加载足够内容、登录状态失效或部分问题回答较少。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已手动停止。", file=sys.stderr)
