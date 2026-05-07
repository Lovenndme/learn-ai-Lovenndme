# Task 2 Work 1 - FZU Jwch Notice Crawler

This crawler collects teaching notices from the Fuzhou University Academic Affairs Office.

Target page:

<https://jwch.fzu.edu.cn/jxtz.htm>

## What It Collects

- notice department
- notice title
- publish date
- detail page URL
- detail page HTML, saved locally
- detail page text
- attachment name
- attachment download URL
- attachment file ID
- attachment download count from the Ajax endpoint

The script writes two CSV files:

- `data/notices.csv`: one row per notice
- `data/attachments.csv`: one row per attachment

Generated data is ignored by Git. If the reviewer needs the CSV, run the script locally.

Initial implementation assisted by Codex; make sure you understand each part before submitting.

## Run

```bash
python3 crawler.py --limit 500
```

For a quick test:

```bash
python3 crawler.py --limit 5 --delay 0
```

To also download attachment files:

```bash
python3 crawler.py --limit 500 --download-attachments
```

## Notes

The download count is loaded dynamically on the page. The script calls the same endpoint used by the page:

```text
/system/resource/code/news/click/clicktimes.jsp
```

This avoids using Selenium for the attachment count.
