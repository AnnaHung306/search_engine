# v8.5 GTFOBins 附加寫入的收錄與排序

舊題的 P@5 由 0.00 升到 0.60，增益來自補收三頁。用同一份 983 頁索引增加附加排序後，舊題的 P@5 仍為 0.60，第三個相關結果由第 4 升到第 3。12 道新題平均 P@5 由 0.4333 升到 0.5167，多 5 個相關位置（26/60 → 31/60）。

## 根因

原 980 頁索引有 100 個 GTFOBins 頁面，其中 12 組 sudo 寫檔證據涵蓋一般寫檔與明示刪檔，沒有文件證據支持在同一例子追加內容並保留舊資料。原索引的 comm 提到追加換行，指的是輸出內容的格式。Bash、ash、csh 寫檔範例中的一般輸出重導向會截斷既有檔案，不能用文件未教的修改計為相關。 [Bash 重導向手冊](https://www.gnu.org/s/bash/manual/html_node/Redirections.html)

核對前輪已固定的 GTFOBins 官方 revision，找到 hashcat、screen、tee 三個明示附加例子。原爬取紀錄對三頁都寫明 host_cap。三頁實際不存在於原索引。 [固定官方版本](https://github.com/GTFOBins/GTFOBins.github.io/tree/acd524623f9c406acedd2754ebd9c2431f3675ad) · [舊爬取紀錄](../data/crawl_log.jsonl)

| 來源 | 附加證據 | 情境與條件 |
|---|---|---|
| hashcat | 輸出會接在舊內容之後 | sudo、一般使用者。範例有準備輸入資料的步驟。 |
| screen | 指定的日誌範例附加文字 | sudo、一般使用者。官方分列兩個版本，會轉換換行格式。 |
| tee | 同一寫檔功能明列附加選項 | sudo、SUID、一般使用者。採用附加選項才符合需求。 |

[hashcat 原文](https://gtfobins.org/gtfobins/hashcat/#file-write) · [screen 原文](https://gtfobins.org/gtfobins/screen/#file-write) · [tee 原文](https://gtfobins.org/gtfobins/tee/#file-write)

## 改動

用既有請求門檻另收三頁。robots 回應 404，依既有規則記為缺少 robots 文件，三次內容請求均為 200，同站從上次完成起間隔至少兩秒。原 980 筆文件逐筆保留，加三頁得到 983 頁、GTFOBins 103 頁。這是明確加三頁的實驗語料，原 crawler 的每站 100 頁設定照舊。重建核對捕捉紀錄、三頁正文、原頁面與附加證據的雜湊，新目的地需獨占。 [收錄紀錄](../data/gtfo-v8.5/capture.json)

依官方例子各自定義 function 與 context 的格式，核對同段原文附加註記、權限與程式範例。共有 9 筆附加情境證據，包含明示選項與例子本身附加兩類。這是對三種官方註記的具體判讀，範圍限於這批文件。對明確要求 GTFOBins 附加寫檔的查詢，先排有相符權限的附加證據，同層保留文字排序。已有片語與正負條件仍生效。混合功能、只說保留內容、排除 GTFOBins 等情況不觸發附加層。明確要求附加又說不覆寫的正向條件可辨識。未驗證的文字命中仍可能出現在較後名次。 [GTFOBins 官方格式](https://gtfobins.org/contributing/) · [附加證據](../data/gtfo-v8.5/relations.json)

## 分開量測收錄和排序

| 舊題 | 原 980 頁 v8.4 | 補收三頁，沿用 v8.4 | 同語料，附加排序 |
|---|---:|---:|---:|
| P@5 | 0.00 | 0.60 | 0.60 |
| P@3 | 0.00 | 0.6667 | 1.00 |

新題在候選排名前凍結，8 題測附加或指定權限，4 題作對照。兩種方法使用同一份 983 頁索引與同一批判定。主指標為固定分母 5 的 P@5。加報 P@3 描述前三名差異。 [Term Project I §6](https://elearningv4.nuk.edu.tw/mod/assign/view.php?id=122192) · [Unit 3](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121734)

| 新題組 | v8.4 規則 | 附加排序 | P@5 差異 |
|---|---:|---:|---:|
| 4 題 sudo 附加 | 0.4500 | 0.6000 | +15.00 pp |
| 4 題權限與情境 | 0.3000 | 0.4000 | +10.00 pp |
| 4 題對照 | 0.5500 | 0.5500 | +0.00 pp |
| 12 題合計 | 0.4333 | 0.5167 | +8.33 pp |

| 查詢 | v8.4 規則 P@5 | 附加排序 P@5 |
|---|---:|---:|
| `GTFOBins append data to a file with sudo` | 0.6 | 0.6 |
| `GTFOBins sudo append to an existing file` | 0.6 | 0.6 |
| `GTFOBins add text to the end of a local file via sudo` | 0.2 | 0.6 |
| `GTFOBins write to a file keeping existing contents with sudo` | 0.4 | 0.6 |
| `GTFOBins sudo append lines to a log` | 0.6 | 0.6 |
| `GTFOBins file append under SUID` | 0.2 | 0.2 |
| `GTFOBins append file contents as an unprivileged user` | 0.6 | 0.6 |
| `GTFOBins add new data to the end of an existing file` | 0.2 | 0.6 |
| `GTFOBins setuid append a line to an existing log` | 0.2 | 0.2 |
| `GTFOBins write data to a local path through sudo` | 1.0 | 1.0 |
| `GTFOBins alternatives for appending text to a file with sudo` | 0.0 | 0.0 |
| `GTFOBins sudo overwrite a local file` | 0.2 | 0.2 |
| `GTFOBins setuid read contents from a local file` | 1.0 | 1.0 |

## 代價與限制

12 題有 3 題進步、9 題持平、0 題退步，P@3 由 0.5278 升到 0.7500。其中一題 SUID 只找到 tee，P@5 持平 0.20，名次由第 4 到第 1。覆寫對照題仍是 0.20，找其他來源的附加題仍是 0。部分追加查詢的後排仍會命中刪檔或覆寫文件，因此應以可查看的附加證據區分。

13 題各交錯測試 30 次，暖索引、前十筆含摘要，省略 HTTP 與解釋。每方法 390 筆。中位數 2.37 → 2.42 ms，p95 3.18 → 3.30 ms。新增索引壓縮後約 9.4 MiB。

72 組查詢／網頁、24 篇原文分成兩批由 LM 判定。複核將 check_log 從覆寫對照題的相關改為不相關，因為指定輸出檔的原文證據未交代既有內容的處置。兩組都扣同一筆，初判與終判各自保存。判定來自同一流程，文件例子以原文核對。

[終判及理由](../data/evaluation/v8.5-append/llm_judgments.csv) · [逐題完整成績](../data/evaluation/v8.5-append/scores.json) · [測量及核對證據](../docs/changes/evidence/v8.5-diagnosis-and-verification.json)

原資料 776 檔的位元組一致。558 次既有查詢比對結果、分數與解釋，130 筆本輪凍結排名逐列重現。本機 Markdown 記錄完成，使用者尚未驗收。
