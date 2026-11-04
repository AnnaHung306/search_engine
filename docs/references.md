# 引用資料

頁碼使用 PDF 的實際頁序（從 1 起算）。講義與作業由使用者已登入的課程平台於 2026-11-05 下載；原檔保留於外層盤點的 sources/course/，不混入公開程式交付。

| ID | 來源與位置 | 對應實作 |
|---|---|---|
| TP | [Term Project I，11/12 更新版本](https://elearningv4.nuk.edu.tw/mod/assign/view.php?id=122192)，p.1 §2、p.2 §3–5、p.3 §6、p.4 §7–9 | 範圍、限速、TF-IDF cosine、固定快照與 P@5、交付 |
| U1 | [Unit 1](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=120440)，p.13–16、31–35、43–48 | 倒排索引、postings 交集、短表優先、位置索引與鄰近度 |
| U2 | [Unit 2](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121177)，p.14–31 | frontier、robots、禮貌、URL 正規化與篩選 |
| U3 | [Unit 3](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121734)，p.9、29–38 | 資訊需求、人工標註、一致性、P@k、單一改動與摘要 |
| U4 | [Unit 4](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=123304)，p.15、18、21、25–39 | log TF、collection IDF、query/document vectors、cosine、不同權重方案 |
| REP | [RFC 9309 §2.3.1](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1) | robots 取得失敗與不可達的處理；本專題另遵守更嚴格的 allowlist |
| HTTP | [RFC 9110 §4.2.3、§10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3) | scheme 的預設埠、Retry-After 秒數與 HTTP 日期 |
| ROB | [Protego 官方文件](https://github.com/scrapy/protego)，Usage | robots 最長規則、wildcard、Crawl-delay／Request-rate 解析；下載與限速仍由本專題實作 |

課堂講義沒有直接規定本專題的新欄位混分公式或 proximity multiplier；這些是由 U1 的位置資訊、U4 的向量／欄位概念延伸的**本專題實驗設計**，不得描述成教授原公式，必須與必做 cosine 分開量測。
