# Demo 腳本（目標 4–5 分鐘，v7.1）

事前：`cd code && python app.py`，瀏覽器開 http://127.0.0.1:5000/，終端機另開一個視窗備用。每一步的預期畫面都在 `report/screenshots/`。

| 時間 | 做什麼 | 說什麼（重點） |
|---|---|---|
| 0:00–0:40 | 秀架構圖 `architecture.png` | 「我們做的是滲透測試工具搜尋引擎。從 Kali、Nmap、Metasploit、Wireshark、mitmproxy、Frida、GTFOBins 7 個官方文件站爬了 980 頁，倒排索引和 TF-IDF cosine 都是自己寫的。」 |
| 0:40–1:10 | 講爬蟲 | 「遵守 robots.txt、同站間隔 2 秒、每站設上限讓 Kali 不會占滿。1,016 次請求、0 失敗。中途會被環境中斷，所以有 checkpoint 續爬。」 |
| 1:10–1:40 | 搜 `decompile android apk`（TF-IDF） | 指出標題、URL、摘要粗體、分數、已索引 980 頁、查詢時間。前三名 jadx、apktool、bytecode-viewer 都是反編譯工具。 |
| 1:40–2:30 | 搜 `sql injection tool`，再切 BM25，再勾 pivot | 「純 cosine 第一名不是 sqlmap，因為 cosine 偏好短頁；BM25 或 pivot 一開，sqlmap 就第一。這是我們最重要的發現：必做 TF-IDF 0.46，只改長度正規化就 0.84。」 |
| 2:30–2:55 | 搜 `reverse shell payload`（TF-IDF） | 指 cowsay 那幾筆的「Missing: payload」：「短頁只有 reverse shell 兩個字也能排很前面，介面直接告訴你它缺什麼。勾『more query words first』後就掉出前五。」 |
| 2:55–3:20 | 搜 `intercept htps trafic` | 紅字「Showing results for: htps → http, trafic → traffic」：「打錯字會用編輯距離修正。」 |
| 3:20–3:40 | 搜 `無缐 破解` | 「缐是選錯字，用拼音修成無線，再對應到 wireless crack，前三名都是 Wi-Fi 破解工具。」 |
| 3:40–3:55 | 搜 `"port scan" -metasploit` | 「片語要求連續出現，減號排除 Metasploit 頁。」 |
| 3:55–4:05 | 空查詢、再搜 `qwzxv` | 兩種提示訊息，系統不會出錯。 |
| 4:05–4:40 | 秀 P@5 表（報告 7.2） | 「144 組依內容逐筆標註。純 TF-IDF 0.46、pivot 0.84、BM25 0.80。一開始用寬鬆的自動標註得到 0.96，後來發現尺太鬆。」 |
| 4:40–5:00 | 心得 | 每人一句：學到什麼、最難的地方。 |

備用（老師問到算分時）：終端機跑 `python toy_example.py`，逐步講 IDF、權重、norm、cosine。
備用（老師問到評估時）：`python evaluate.py --score` 現場重算 P@5。

注意：查詢結果依附上的索引快照，現場不要重新爬或重建索引。
