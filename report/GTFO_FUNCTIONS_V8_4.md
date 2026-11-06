# v8.4：GTFOBins 功能、權限情境與實際效果

在原本 980 頁快照中，反向 shell 舊失敗 P@5 **0.00 → 0.60**，sudo 寫檔 **0.20 → 1.00**。16 題新題 **0.3375 → 0.6000（+26.25 個百分點）**，共多 21 個相關位置（27/80 → 48/80），8 勝、8 平、0 負。新選項使用同一搜尋引擎，不換預設或產品流程。

## 失敗根因與修改

1. **反向 shell 命中站內標題，沒有命中可用例子。** v8.3 的前五筆是 Contributing、Scope、cpan、cowthink、cowsay。前兩個定義分類，後三個是可能繼承的通用 Perl 功能。把真正功能區塊排在前面後，前 3 為 BusyBox、VS Code 通道、Bash。VS Code 需要 GitHub 帳號並有遠端 Terminal 例子，不能當成無條件可用。原快照只有這 3 個有直接反向 shell 證據的執行檔頁面；其餘兩格不算相關。
2. **sudo 或 SUID 出現在頁面，不保證屬於該功能。** [官方格式](https://gtfobins.org/contributing/) 把 context 放在每個 function 變體中，且可以覆寫該例程式。使用固定 [官方 revision](https://github.com/GTFOBins/GTFOBins.github.io/tree/acd524623f9c406acedd2754ebd9c2431f3675ad)，從原索引核對功能標題、同段情境、實際例子。`SUID reverse shell` 中，BusyBox 與 VS Code 雖有直接反向 shell，沒有該功能的 SUID；只認功能會把它們放到前五，配對後只有 Bash 得到證據優先，名次從 4 到 1。P@5 同為 0.20，首筆命中改善。
3. **分類不等於效果。** v8.3 sudo 寫檔前三筆 c89、c99、cc 是 GCC 的正式別名，[c89 File write](https://gtfobins.org/gtfobins/c89/#file-write) 原文指明例子實際會刪檔。只認功能或只核對 sudo 時，這三筆仍在前面。將明示刪檔排除於寫檔證據後，候選前五均提供實際寫入：arj、cpio、Bash、check_log、csh。這項排除只依可對照的官方註記，沒有用推測判讀所有程式行為。

附加資料含 97 個執行檔頁面、341 筆函式／情境／例子關聯，6 筆明示刪檔（3 個別名 × 2 情境）。22 個可能繼承的例子不算直接功能。固定原始封存檔與正文 SHA、功能／情境／例子位置皆可驗證；重建後相符，沒有用新抓文件替換舊索引。正式 alias 只沿用已核對的證據，保留 canonical 名稱，不誤推論任意 inherit。

新選項只對明示 GTFOBins、單一可辨識功能、最多一個明示情境的自由詞生效。支援官方連字號名稱與常見同義寫法；比較、排除、append 或模糊語境不加結構層。查詢的片語、正負條件仍照原流程。排序先看關聯，同層保留 v8.3 原順序；未命中證據的文件仍在同一次排序較後面。沒有另跑搜尋當 fallback。

## 同資料比較與新題

P@5 設計依 [TP p.3 §6](https://elearningv4.nuk.edu.tw/mod/assign/view.php?id=122192) 和 [Unit 3 p.9、29–38](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121734)。文字底分沿用 v8.3，與 U4 的核心排名概念相接；結構排序是本專題延伸。兩題已見失敗獨立記為回歸。新題與資訊需求先凍結，含 4 道反向 shell、4 道寫檔、4 道功能／情境、4 道對照；用途是目標驗證，非代表全部搜尋。四個設定共用同一題／URL 判定，分母固定 5。

| 題組 | v8.3 | 只認功能 | 配對情境 | 驗證效果 | 最終差異 |
|---|---:|---:|---:|---:|---:|
| 2 題已知回歸 | 0.1000 | 0.5000 | 0.5000 | 0.8000 | +70.00 pp |
| 4 題新反向 shell | 0.2000 | 0.5000 | 0.5000 | 0.5000 | +30.00 pp |
| 4 題新寫檔 | 0.4500 | 0.4500 | 0.4500 | 0.7500 | +30.00 pp |
| 4 題新情境配對 | 0.5500 | 0.8000 | 1.0000 | 1.0000 | +45.00 pp |
| 4 題新對照 | 0.1500 | 0.1500 | 0.1500 | 0.1500 | +0.00 pp |
| 16 題新題 | 0.3375 | 0.4750 | 0.5250 | 0.6000 | +26.25 pp |

| 查詢 | v8.3 | 只認功能 | 配對情境 | 驗證效果 |
|---|---:|---:|---:|---:|
| `reverse shell examples from GTFOBins` | 0.0 | 0.6 | 0.6 | 0.6 |
| `GTFOBins sudo arbitrary file write` | 0.2 | 0.4 | 0.4 | 1.0 |
| `GTFOBins outbound shell examples` | 0.0 | 0.6 | 0.6 | 0.6 |
| `GTFOBins reverse shell through sudo` | 0.0 | 0.6 | 0.6 | 0.6 |
| `GTFOBins SUID reverse shell examples` | 0.2 | 0.2 | 0.2 | 0.2 |
| `GTFOBins unprivileged connect back shell` | 0.6 | 0.6 | 0.6 | 0.6 |
| `GTFOBins write contents to a local file with sudo` | 0.4 | 0.4 | 0.4 | 1.0 |
| `GTFOBins SUID write data to a file` | 1.0 | 1.0 | 1.0 | 1.0 |
| `GTFOBins unprivileged local file writing` | 0.4 | 0.4 | 0.4 | 1.0 |
| `GTFOBins append data to a file with sudo` | 0.0 | 0.0 | 0.0 | 0.0 |
| `GTFOBins read a local file under sudo` | 0.8 | 1.0 | 1.0 | 1.0 |
| `GTFOBins read protected files with setuid` | 0.2 | 0.2 | 1.0 | 1.0 |
| `GTFOBins SUID interactive shell` | 0.8 | 1.0 | 1.0 | 1.0 |
| `GTFOBins sudo noninteractive command execution` | 0.4 | 1.0 | 1.0 | 1.0 |
| `compare GTFOBins and Kali sudo tool documentation` | 0.0 | 0.0 | 0.0 | 0.0 |
| `GTFOBins contribution schema and examples` | 0.4 | 0.4 | 0.4 | 0.4 |
| `GTFOBins alternatives for Linux privileged file write` | 0.0 | 0.0 | 0.0 | 0.0 |
| `Frida inspect exported functions from a module` | 0.2 | 0.2 | 0.2 | 0.2 |

## 仍未改善與效能代價

- SUID 反向 shell 只剩 1 筆可驗證例子；P@5 仍 0.20，但從第 4 到第 1。沒有靠新增文件湊滿五筆。
- sudo 附加寫入仍為 0。不能從一般寫檔分類推論會保留原內容，因此不啟用新層。新對照組平均 0.15，排名與分數相同，不代表原比較／替代來源題已經做得好。
- 每方法 18 題 × 30 次，兩方法交錯，索引與附加資料暖機，前十筆含摘要、不含 HTTP 或解釋。中位數 **2.04 → 2.29 ms**；p95 **3.19 → 3.36 ms**。最大單題中位數增量約 0.46 ms（outbound shell）。這是本機暖機觀察，不是正式站保證。

## 判定、查證與重現

121 組配對、58 篇完整索引正文、60 段、7 批，共 123 筆分段判定。LM 看不到排序來源／名次／舊標籤，引用必須在正文中，缺標停止計分。七批均通過，沒有重試。另複核 VS Code 通道、寫檔目的路徑、SUID 同段、刪檔警告與 append；121 組均維持初判。保留明示零修正複核，未冒稱獨立人工評分；CLI default 的精確模型 ID 未暴露，信心也未校準。只分析文件，未執行任何頁面範例。

[凍結計畫](../data/benchmarks/gtfo-v8.4-plan.json) · [正文判定](../data/evaluation/v8.4-gtfo/llm_judgments.csv) · [複核](../data/evaluation/v8.4-gtfo/review.json) · [完整分數](../data/evaluation/v8.4-gtfo/scores.json) · [重建與驗證證據](../docs/changes/evidence/v8.4-diagnosis-and-verification.json)。

審查補上官方連字號、明確 Linux capabilities、隔離回傳證據與快取、獨立建置依賴、保護零更正複核。原 486 次搜尋結果與解釋逐筆相同，360 筆新排名可逐列重現，709 份原資料檔未變更。這輪使用本機 Markdown，未留下測試暫存檔；沒有製作 PPT、push 或新增應用 fallback。技術驗證不代表使用者已驗收。
