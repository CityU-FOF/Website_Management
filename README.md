# 金融學院教師資料整合

已按澳門城市大學金融學院[全職教師名單](https://fof.cityu.edu.mo/faculty)，把 **43 位老師、86 個中英文個人頁**整合至你上載的 FOF Profile Studio 備份格式。主要資料擷取日期：2026-11-17；生成器 3.11 及 Arman 教授三張相片更新日期：2026-11-18。

## 下載及使用

1. 下載 [Studio 3.11 完整套件](FOF_Profile_Studio_v3_11_Package_2026-11-18.zip)並解壓。亦可分別下載[新版 HTML](FOF_Profile_Studio_v3_11.html)及[新版 JSON](FOF_Profile_Backup_All_Faculty_2026-11-18.json)。
2. 開啟 `FOF_Profile_Studio_v3_11.html`，按「還原JSON備份」，選擇 `FOF_Profile_Backup_All_Faculty_2026-11-18.json`。
3. 在「老師」及語言選單選取個人頁，即可編輯、預覽、確認資料或下載代碼。

亦可直接下載 [全部老師中英文代碼 ZIP](FOF_Profile_Codes_All_Faculty_2026-11-18.zip)，內含 **86 份**可貼入學院後台正文原始碼模式的 `.txt` 代碼，以及匯出說明。

這份 JSON 包含 43 筆教師資料、1,054 筆內容明細、696 筆研究成果及 7 項共用設定。研究成果包括論文、工作論文、會議成果、專著及書籍章節。

## Studio 3.11 新功能

- **選填亮點標籤**：中文／英文各自填寫，每行一個，顯示在老師側欄。已按官方簡介為張偉光及李建強填入全球前 2% 頂尖科學家標籤。
- **日期與內容兩欄**：研究項目、學術服務與指導、獎項及媒體報道均使用左日期／右內容；有日期的原文已抽出至時間欄。未寫日期留空，所有項目保留原排序，供人手調整。
- **媒體報道**：新增可供任何老師使用的版塊，已將 Arman 教授原有 30 項報道拆成逐項可維護的中英紀錄。
- **相片相簿**顯示按順序填入的圖片網址。單張為靜態相片，多張可點選編號或左右滑動，匯出純 HTML／CSS 代碼。Arman 教授的三張相片已填妥。
- **每位老師獨立核對**：提供「編輯資料」「確認資料」及全體老師進度表。提示列明版塊、項次及缺欄／中英日期、數字或項目數差異；確認後該老師提示隱藏，再修改會自動變回編輯中。確認進度跟 JSON／Excel 一起保存，交接時請傳最新備份。

詳見[新版使用說明](STUDIO_V3_11.md)、[資料遷移紀錄](data/studio_v3_11_migration.json)及[功能驗證](data/studio_v3_11_validation.json)。3.10 原始檔及 2026-11-17 備份保留供回查；新版媒體報道版塊請使用 3.11 生成器。

## 論文分欄及經歷日期

- 696 筆成果全部填入「文章名」，分開整理「作者」「期刊名／出版社」「年份」「DOI」；使用 Studio 原生論文版面，原引文保留作核對。
- 已知 DOI 與作者按 Crossref／出版社紀錄核對，未能確認的欄位留空；期刊、會議、書籍及預印本按實際出版載體處理，不套用同名或不同版本的 DOI。
- 125 筆學術工作經驗全部抽出日期填入「時間」，有月份一律使用 `YYYY/MM`；按用戶選擇，只有年份就保留 `YYYY`，不推算月份。英文日期另填英文時間欄。
- 13 筆工作論文原頁沒有完整作者名單，附註待補；王應貴的本人作品清單沒有逐項列出完整署名，列本人姓名並註明限制。
- 合併 13 組王應貴的相鄰中英文引用及另兩組已核對重複成果；一段無法辨識作品的出版社殘句只保留於來源及核對報告。

欄位填寫數、缺失資料及每筆經歷日期見 [分欄核對報告](data/structured_fields_report.json)。

## 整合方式及核對

- 沿用原備份的 `fof-profile-studio`、`schemaVersion: 2` 結構，完整保留 `templateCSS` 及共用設定。
- 原有 4 位老師的 ID 和已填基本資料保留，包括 `_adriancheung`；補齊其餘老師及原頁內容，避免重建院長的重複紀錄。
- 中英文內容分別來自各自官方個人頁，保留各語言的排序及原文。不同段落數按各語言獨立顯示，沒有自行翻譯網站未提供的章節。
- 研究成果按 DOI、明確題目或[已核對的雙語引用配對](data/reviewed_bilingual_pairs.json)合併，保留原始引用及來源網址。完整引用與重複的原語言引用只保留一份，另一語言的不同引文另存。
- 已使用上載的原版 Studio 實測 JSON 還原、43 位老師的中英文代碼生成、JSON 匯出後重新還原、批量 ZIP 及本機自動儲存，沒有資料格式錯誤或 JavaScript 執行錯誤。

詳見 [整合報告](INTEGRATION_REPORT.md)、[原站資料差異](DATA_QUALITY.md)及[驗證結果](data/integration_validation.json)。資料狀態保留「待核對」，供你日後與老師確認；學院網站後台尚未修改。

## 原始檔與可重複執行程式

上載的 `FOF_Profile_Backup_adriancheung_2026-11-17.json` 及 `FOF_Profile_Studio_v3_10.html` 保留原檔。

- [data/faculty_sources.json](data/faculty_sources.json)：完整官方正文 HTML／文字、照片網址、名單資訊及原始回應 SHA-256，屬來源快照。
- [scripts/collect_faculty_sources.py](scripts/collect_faculty_sources.py)：重新擷取公開頁面。
- [scripts/integrate_faculty.py](scripts/integrate_faculty.py)：把來源快照合併至原備份，產生整合 JSON。
- [scripts/structure_faculty.py](scripts/structure_faculty.py)：拆分論文欄位，套用已核對的書目資料。
- [scripts/normalize_career_dates.py](scripts/normalize_career_dates.py)：從官方原文抽出經歷日期。
- [scripts/finalize_structured_backup.py](scripts/finalize_structured_backup.py)：合併重複成果、整理經歷並輸出備份及報告。
- [data/bibliography_verified_metadata.json](data/bibliography_verified_metadata.json)及[人工分欄核對表](data/bibliography_field_overrides.json)：已採用的 Crossref 紀錄、引文配對與特殊格式修正，足夠離線重建現有資料。
- [scripts/verify_integration.py](scripts/verify_integration.py)：逐項來源核對及原版 Studio 瀏覽器驗證。

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/python scripts/integrate_faculty.py
.venv/bin/python scripts/structure_faculty.py --search
.venv/bin/python scripts/finalize_structured_backup.py
CHROMIUM_PATH=/usr/bin/chromium .venv/bin/python scripts/verify_integration.py
```

瀏覽器驗證需要已安裝的 Chromium，可透過 `CHROMIUM_PATH` 指定。`--search` 使用已保存的資料，不會發送網絡查詢；如需另外查詢 Crossref，可用 `scripts/fetch_bibliography_metadata.py`，結果暫存於不提交的 `work/`。來源快照及配對表保留原站矛盾，不代表老師已確認每項資料。

## 重建 Studio 3.11

在前述依賴及 Chromium 已安裝的環境執行：

```sh
.venv/bin/python scripts/build_studio_v3_11.py
.venv/bin/python scripts/migrate_studio_v3_11.py
CHROMIUM_PATH=/usr/bin/chromium .venv/bin/python scripts/verify_studio_v3_11.py
.venv/bin/python scripts/package_studio_v3_11.py
```

新版仍為離線單檔 HTML；功能原始碼在 `scripts/studio_v3_11_features.js`，由建置程式內嵌。已有來源快照可離線重建資料；功能測試會產生 86 份代碼 ZIP。
