# 來源核對紀錄

擷取日期：2026-11-17。來源：[中文全職教師名單](https://fof.cityu.edu.mo/faculty)、[英文全職教師名單](https://fof.cityu.edu.mo/en/faculty)。

## 已核對

- 中文名單 43 位，英文名單 43 位；以個人頁識別碼配對，沒有重複或遺漏。
- 最終 86 個個人頁均有有效正文；沒有將錯誤頁匯入老師資料。
- 保留原始正文 HTML，包含段落、列表、超連結、論文標題、DOI、表格及其他原有內容；另附文字版方便查閱。
- 逐筆保留中英文獨立來源，沒有以其中一種語言覆蓋另一種語言。
- 43 位老師均保留名單照片網址。照片檔案沒有下載至 repository。

## 已處理的錯誤連結

張岩老師的中文名單連至 `https://fof.cityu.edu.mo/julianzhsng`。該頁 HTTP 狀態為 200，但正文是「404 Error - Page not found」。

從[英文個人頁](https://fof.cityu.edu.mo/en/julianzhang)的「繁體中文」切換連結，取得正確的[中文個人頁](https://fof.cityu.edu.mo/julianzhang)。JSON 使用 `julianzhang` 配對，並在中文紀錄的 `directory_url` 保留名單的錯誤網址供追查。

## 原站差異，保留待核對

以下為已觀察到的例子，並非所有聯絡資料差異的完整清單：

- [張偉光中文頁](https://fof.cityu.edu.mo/adriancheung)的電郵顯示文字為 `adriancheung@cityu.edu.mo`，但原始 `mailto:` 連至 `adriancheung@cityu.mo`。
- [李迪英文頁](https://fof.cityu.edu.mo/en/dili)把 `8590-2823` 標作 `Office`；[中文頁](https://fof.cityu.edu.mo/dili)把相同號碼標作辦公室電話。
- [李蒙英文頁](https://fof.cityu.edu.mo/en/mengli)的辦公室為 `aaG2202`，而[中文頁](https://fof.cityu.edu.mo/mengli)為 `GD2202`。
- 部分老師的中英文頁分別使用 `@cityu.edu.mo` 和 `@cityu.mo`；保留各頁原文，沒有判定哪個地址正確。
- 中英文頁的論文數量、章節、職銜文字或詳細程度可能不同。資料完整指保留各來源所載內容，並不表示已由老師確認每項事實。

## 生成器驗證已完成

原 JSON 備份及 HTML 生成器已由用戶上載至 repository。已完成整合，輸出為根目錄的 `FOF_Profile_Backup_All_Faculty_2026-11-17.json`。

已用原版 Studio 3.10 通過 JSON 還原、43 位老師的 86 個中英文頁代碼生成、JSON 匯出後重新還原、86 份代碼 ZIP 及本機儲存驗證。來源快照 `data/faculty_sources.json` 仍屬原始資料，請使用新的整合備份作匯入。

## 中英文段落與研究成果差異

中英文原頁的章節、段落數及詳細程度不完全相同。整合保留兩種語言各自的內容及排序，同一筆版塊的中英文欄位不保證是逐句翻譯。Studio 按資料列提示部分英文欄位空白時，也可能是兩種語言段落數不同，請同時參考英文頁實際預覽。

研究成果採原文共用方式，沿用原版生成器的行為。原站提供的另一語言引用另存於 `原始引用（中文）`／`原始引用（英文）`，沒有自行翻譯論文題目。網站中英頁對同一成果的題目、年份或狀態不同時，保留來源引文供追查，例如符通的部分工作論文、李強及蘇正偉的部分中文成果。

原 JSON 已整理的欄位優先保留。例如楊挺的英文學歷在原備份與原站有輕微拼寫差異，仍保留原備份的顯示文字。所有原檔及來源正文均保留，詳見 `data/integration_validation.json`。
