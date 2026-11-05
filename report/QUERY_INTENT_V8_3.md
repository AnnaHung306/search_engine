# v8.3：找出失敗原因，再驗證搜尋改善

本輪修正兩個已知問題：**指定 GTFOBins 卻排到別站**，以及**找不到列出程序已載入原生模組的文件**。保留必做 TF-IDF cosine 與原 BM25，在同一搜尋引擎提供明示的 `--intent` 實驗。沒有改索引、爬取、正常網站操作流程或預設模式。

## 追到根因

**GTFOBins sudo。** 原 query 經詞幹處理後，BM25 把 `gtfobin`、`sudo`、`find`、`binary`、`technique` 一起加總。首筆 Kali unhide 只命中部分詞就得 9.57，其中 `technique` 佔 5.50；GTFOBins 的第一筆是第 6 名，原有可用的 `as` 條目為第 74 名。URL 在索引、文件也未被排除。故把明確來源做成 URL host 排序層；同一層保留原本排序，不把指定來源當成相關性的答案。候選首筆 Contributing 仍不相關，另外四筆有 sudo 功能，因此是 4/5。

**Native libraries。** `load / native / library` 會讓 Metasploit 的 .NET 反序列化工具等頁面命中。Frida JavaScript API 在索引、未被過濾，但原排第 23；診斷僅加 `module` 仍第 13。Frida 的[官方 Process API](https://frida.re/docs/javascript-api/#process)與[安裝範例](https://frida.re/docs/installation/)使用 `Process.enumerateModules()`；原查詢沒對到這項證據。候選在「列出／檢查」＋「已載入」＋「原生／shared／程序」＋「模組／函式庫」條件下加入該精確詞，權重 0.5，並讓有 API 證據的文件優先。API 本身與實際安裝範例各提供一筆相關文件，其他三筆未達需求。

明確比較、排除、未載入／將載入語境不啟用意圖。`+`、`-` 與片語仍由原流程處理。來源與 API 都按索引證據，不硬填指定 doc ID，也不重新跑另一種搜尋補結果。

## 凍結比較結果

原 980 頁固定索引，四種設定：原 BM25、只開來源、只開原生、兩者合開。已知兩題先用於診斷，另外 16 題與資訊需求在候選排名前凍結，區分來源 4 題、原生 4 題、控制 8 題。新題刻意對準失敗類型，不代表任意使用者查詢。P@5 固定五筆分母，所有模型共用同一題／URL 判定。

| 組別 | 原 BM25 | 來源 | 原生 | 合開 | 合開差異 |
|---|---:|---:|---:|---:|---:|
| 已知回歸 2 題 | 0.000 | 0.400 | 0.200 | 0.600 | +60.0 pp |
| 新來源 4 題 | 0.450 | 0.450 | 0.450 | 0.450 | +0.0 pp |
| 新原生 4 題 | 0.100 | 0.100 | 0.400 | 0.400 | +30.0 pp |
| 新控制 8 題 | 0.425 | 0.425 | 0.425 | 0.425 | +0.0 pp |
| 16 題新題合計 | 0.350 | 0.350 | 0.425 | 0.425 | +7.5 pp |

**兩道已知失敗**分別由 0 到 0.80、0.40。**16 道新題**共多 6 個相關位置（28/80→34/80），4 勝、12 平、0 負。來源訊號只在已知失敗題看到增益：四道新來源題原版已排同樣的 GTFOBins 文件，來源層不改變同站內的順序。控制組前五筆 URL、順序和分數都一致。

| 查詢 | 原 BM25 | 合開 |
|---|---:|---:|
| `find gtfobins sudo binary techniques` | 0.0 | 0.8 |
| `list loaded native libraries` | 0.0 | 0.4 |
| `gtfobins sudo shell` | 0.6 | 0.6 |
| `gtfobins suid file read` | 1.0 | 1.0 |
| `reverse shell examples from GTFOBins` | 0.0 | 0.0 |
| `GTFOBins sudo arbitrary file write` | 0.2 | 0.2 |
| `show loaded shared libraries in a process` | 0.0 | 0.4 |
| `inspect loaded native modules in target process` | 0.2 | 0.4 |
| `enumerate libraries already loaded into a process` | 0.0 | 0.4 |
| `which native modules are loaded in this process` | 0.2 | 0.4 |
| `list loaded Linux kernel modules` | 0.0 | 0.0 |
| `load a shared library into a process` | 0.6 | 0.6 |
| `list exported symbols of a loaded native module` | 0.2 | 0.2 |
| `compare GTFOBins and Kali privilege escalation techniques` | 1.0 | 1.0 |
| `inspect a tcp handshake in wireshark` | 0.2 | 0.2 |
| `nmap ipv6 host discovery` | 0.6 | 0.6 |
| `forward http requests to upstream proxy mitmproxy` | 0.6 | 0.6 |
| `offline zip archive password recovery` | 0.2 | 0.2 |

## 退步、殘留限制與代價

這組新題沒有觀察到 P@5 退步，並不代表所有查詢都改善。`reverse shell examples from GTFOBins` 終判仍是 0：前三個結果是說明／貢獻或可能繼承功能，其餘也只是執行一般 Perl 腳本。`GTFOBins sudo arbitrary file write` 仍為 0.2：前三個編譯器頁雖掛 file write，正文實際描述刪檔；單靠同站與文字匹配無法保證正確操作。控制組 Linux kernel modules 為 0；保護其不被擴展誤導，沒有修好其基準排序。

暖索引、前十筆含摘要、不含 Flask／解釋；18 題 × 30 次、兩方法交錯。整體中位數 2.99→2.73 ms；**p95 68.37→69.55 ms（多 1.17 ms）**。`show loaded shared libraries in a process` 中位數 36.10→38.34 ms。時間是本機觀察值，無法推論正式站速度。第一次與推論並行的量測也另存；未拿它做最終比較。

已知的 `+as` 會被原 Boolean 詞彙處理視為停用詞。這輪沒有修改原查詢語義；`+base64`、`-sudo` 與片語限制通過實測。若下一輪修正，需先定義明示運算子如何檢查未進原詞彙索引的詞。

## 判定與可追溯性

全文判定：103 組配對、74 篇索引正文、3,094,297 字元、115 段，54 批，共 174 筆分段判定。模型不見系統、排名、分數或歷史標註；保留每批原文、結構化輸出、引句、理由及 hash。批次 0053 兩次 ID 不符遭拒，原始嘗試未刪；將合法 ID 從該批凍結請求寫入輸出 schema 後通過，仍拒絕重複／缺漏，沒有補 0 或更換模型。CLI default 精確模型名稱未由 JSON events 提供。

複核三筆中信心與反向 shell、原生模組正例：兩個只列可能繼承功能的 Perl 工具頁，和 Frida Modes 的兩筆一般能力判定，由 1 改為 0。既有規則與排名未改。新題初判的原版／候選為 0.400／0.475，終判為 0.350／0.425；兩者均下修 5 個百分點，差距仍是 7.5 個百分點。這是同一流程已看過初判的複核，不是獨立雙人或人工驗證。

[初判成績](../data/evaluation/v8.3-intent/initial/scores.json) · [終判與原文引句](../data/evaluation/v8.3-intent/llm_judgments.csv) · [四筆複核](../data/evaluation/v8.3-intent/adjudications.json) · [終判成績與雜湊](../data/evaluation/v8.3-intent/scores.json) · [根因與驗證證據](../docs/changes/evidence/v8.3-diagnosis-and-verification.json)。

## 引用與後續

老師 [Term Project I p.3 §6](https://elearningv4.nuk.edu.tw/mod/assign/view.php?id=122192)與 [Unit 3 p.9、29–38](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121734)支撐固定查詢、資訊需求與 P@5。來源欄位借用 [IR 教材 §6.1](https://nlp.stanford.edu/IR-book/html/htmledition/parametric-and-zone-indexes-1.html)的 metadata 概念；受控擴展來自 [§9.2.2](https://nlp.stanford.edu/IR-book/html/htmledition/query-expansion-1.html)，具體排序規則屬本專題。功能及情境對照 [GTFOBins](https://gtfobins.org/)與 Frida 官方文件；正文評分用本機快照，不混進現行網站。模型評估參考 [Thomas 等人](https://arxiv.org/abs/2309.10621)，本次沒有真人校準。

下一輪最有價值的是分辨同站內「做什麼」與「在哪個權限情境做」：例如把 GTFOBins 的 function、context 與實際例子保留在索引，再驗證它們確實屬同一段落。新原生模組組也僅涵蓋少數問法；不能外推到 Linux kernel 或列出匯出符號。下輪若改模型，用已見題做回歸，另凍結新的檢查題。

驗證：舊九種設定 414 次結果、分數、摘要、解釋完全一致；審查修正後重現 360 筆新排名；原 v8.2 的 654 組判定與資料仍完整。未改 UI、未做 PPT、未 push、未新增應用 fallback；技術通過不等同使用者驗收。
