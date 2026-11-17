# 金融學院教師資料整合

已按澳門城市大學金融學院[全職教師名單](https://fof.cityu.edu.mo/faculty)整合 43 位老師、86 個中英文個人頁，資料擷取日期為 2026-11-17。範圍為該名單上的全職教師，包括院領導、課程主任、教授、副教授、助理教授及講師。

## 已備妥資料

- [data/faculty_sources.json](data/faculty_sources.json)：每位老師的中英文姓名、職銜、指導資格、名單分組、照片網址、個人頁網址，以及個人頁完整正文 HTML 和文字。原頁的學歷、簡介、教學、研究、工作經驗、論文及其他章節全部保留；沒有摘要或翻譯替代原文。
- [DATA_QUALITY.md](DATA_QUALITY.md)：已發現的原站問題及核對結果。
- [scripts/collect_faculty_sources.py](scripts/collect_faculty_sources.py)：可重複執行的資料擷取程式。

## 生成器匯入狀態

**此 JSON 是資料來源快照，尚未轉成現有 HTML 生成器的匯入格式。**

本次對話未提供可讀取的原始 JSON 備份或 HTML 生成器附件；指定 repository 原本亦為空。需要兩個原檔，才能確認欄位結構、合併老師紀錄及驗證實際匯入。網站上的新版示範頁只提供排版結果，不能證明生成器的 JSON 結構。

快照使用 `fof-faculty-source-snapshot/v1` 格式，`profiles` 依中文教師名單排序，每筆具有 `id`、`zh`、`en`。`studio_import_status` 明確標示 `pending_original_json_and_html_schema`。來源未提供的資料沒有自行補寫；中英文版本之間的差異亦保留原樣。

## 重新擷取

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/collect_faculty_sources.py
```

程式下載公開頁面至 `work/source/`，再輸出 JSON。加上 `--use-cache` 可沿用本機快取。程式檢查名單內重複老師、中英文配對、空白正文，以及 HTTP 200 回傳的 404 錯誤頁。每個個人頁保留原始回應的 SHA-256，方便核對。

此 repository 的資料整理不會修改學院網站後台。
