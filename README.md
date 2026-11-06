# Pentest Tool Search — 課程整合更新 v8.6

本機資安文件搜尋引擎。從 v7.1 的固定 980 頁公開資料出發，保留自寫倒排索引、TF-IDF 與 cosine，新增位置索引、欄位／鄰近度實驗及逐筆計分解釋。

## 報告、改動與心路歷程

- **報告**　[課程專題報告](report/REPORT_V8.md) 說明整體系統與評估方法。[v8.6 實驗報告](report/GTFO_WRITE_EFFECTS_V8_6.md) 整理本輪方法、實測結果與限制。
- **本次改動**　區分覆寫、附加與刪檔，依查詢套用來源排除，並在同一份 986 頁語料上切換 v8.5 與 v8.6。詳見 [排序改動](docs/changes/013-write-effects.md)、[搜尋介面改動](docs/changes/015-demo-polish.md) 與 [各版更新紀錄](docs/changes/README.md)。
- **完整心路歷程**　從最初選題、爬蟲與排序的嘗試，到 v8.6 的實驗與取捨，集中放在 [DEVLOG.md](DEVLOG.md)。

作業截止為 2026-11-12 23:59（教學平台）。本輪程式尚待使用者驗收。

## 安裝與正常入口

Python 3.10+。

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B code/indexer.py
python -B code/app.py
```

開啟 http://127.0.0.1:5000/ 。預設為必做 TF-IDF cosine，無錯字修正、同義詞、pivot、覆蓋優先或欄位重排。若要比較加強功能，選 Compare enhancements，再選模型／開關並搜尋。點 Why this result 可查看 TF、DF、IDF、norm 與各詞分數貢獻。

若 5000 已被其他服務占用，明確指定同一 Flask 應用的埠：`python -B -m flask --app code/app.py run --host 127.0.0.1 --port 5001`。本輪 macOS ControlCenter 占用 5000，因此實際預覽使用 5001。

依賴鎖在 requirements.txt：requests 2.34.2、beautifulsoup4 4.15.0、Flask 3.1.3、pypinyin 0.55.0、Protego 0.7.0。缺少依賴會直接報錯，不靜默停用功能。

## 資料與來源

- 上游 main 基底：`9c7c3a107b9712b5fc2f31d8d432a025be39f27a`，<https://github.com/AnnaHung306/search_engine>。
- 原始 search-engine.zip、REPORT_DRAFT.docx、data/pages.json、data/index.json 與舊評估都保留。
- 目前索引：data/index-v8.1.json.gz，schema 4；literal offsets 採 gap/length varint，按需解碼，外層固定標頭 gzip。原 schema-3 index-v8.json 仍保留。缺少新索引或格式錯誤會直接報錯，不改讀舊檔。
- 舊 Word 與 report/REPORT_DRAFT.md 是 **v7.1 歷史草稿**，各輪報告仍按版本保存。最新寫入效果評估見 [v8.6 報告](report/GTFO_WRITE_EFFECTS_V8_6.md)。docs/HUMAN_HANDOFF.md 保留歷史人工材料與交付欄位。
- 講義頁碼／作業條文與延伸來源見 [引用資料](docs/references.md)；每批改動見 [更新紀錄](docs/changes/README.md)。

## 爬蟲

8 seeds 與 7 hosts 詳見 code/config.py：Kali、Nmap、Metasploit、Wireshark、mitmproxy、Frida、GTFOBins。保留原有路徑限制、每站額度與 1,000 頁總上限。

新爬蟲不覆蓋固定評估資料：

```sh
python -B code/crawler.py --output data/crawls/new-crawl
python -B code/crawler.py --output data/crawls/new-crawl --resume
python -B code/indexer.py --pages data/crawls/new-crawl/pages.json --output data/index-new-crawl.json.gz
IR_INDEX_PATH="$PWD/data/index-new-crawl.json.gz" python -B -m flask --app code/app.py run --host 127.0.0.1 --port 5002
```

明確指定 `IR_INDEX_PATH` 才會切換資料。預設固定研究快照仍為原 data/pages.json 的 980 頁，不混入新資料。不同 collection 的舊評估會顯示不同資料集的提醒並隱藏成績。

本輪已完整重爬七站，新快照另存 data/crawls/v8-live-20261105/：980 頁、1,027 實際 HTTP requests、485 頁有來源 meta description。逐站最小間隔、robots 拒絕、唯一性與來源 manifest 見 docs/changes/evidence/v8.1-live-crawl-audit.json。新舊資料即使頁數相同，也不是同一 collection，品質成績不能直接混比。

每一個實際 HTTP 請求（含 robots、轉址各跳、失敗）共用 attempt budget、host 限速與紀錄。內容轉址送出前先檢查白名單／路徑／robots；robots metadata 可在白名單 host 上取得，不受內容路徑前綴限制。至少 2 秒，並遵守更長的 Crawl-delay／Request-rate 間距。500、429、timeout 等不會被當成允許爬取；受影響 host 在該次 crawl／resume 中暫停，需要新的 crawl 才重新嘗試。

URL 保留 query string、去 fragment，僅移除 scheme 對應的預設埠。正常正文抽取、去重、checkpoint／resume 仍在；無法辨識編碼時記錄跳過，不猜測成有效內容。

## 前處理與排序

- 文件／查詢共用 code/preprocess.py：小寫、英文 stopwords、輕量 stemming、保留 C++／802.11／複合詞及其部分。完整政策沿用 v7.1，見程式與報告。
- 文件及查詢：`tf = 1 + log10(count)`；`idf = log10(N/df)`；共用 collection IDF；必做分數是完整 L2 cosine。重複查詢詞現在確實計入 TF。
- BM25：k1=1.5、b=0.75，IDF=`ln(1+(N-df+0.5)/(df+0.5))`，query multiplier 為 log TF × 擴展權重。
- 片語使用 literal positions，保留 stopwords；標題／正文分開，不跨欄位拼接。空白、連字號、斜線、底線可銜接；其他標點造成位置間隔。`+must`、`-mustnot` 仍支援。
- pivot slope 0.2、coverage-first、title boost 0.5、synonyms 0.5、typo correction 0.7 為明示實驗；pivot／coverage 不宣稱為純 cosine。
- 新 field cosine：`(body_cosine + description_cosine + 2*title_cosine)/4`，各欄位共用 collection IDF、各自 L2 norm。
- 新 proximity：以同欄位內包含查詢詞的最短位置窗，計算 coverage × closeness；乘數 `1+0.3*closeness`。這兩個新公式是本專題延伸設計，不是教授原公式，也未宣稱品質提升。

## 評估與展示

```sh
python -B code/evaluate.py --legacy-score
python -B code/evaluate.py --dump --suite course --systems tfidf --output data/evaluation/my-course-required
python -B code/evaluate.py --dump --suite development --output data/evaluation/my-development
python -B code/evaluate.py --timing --suite course --output data/evaluation/my-timing
python -B code/diagnostics.py --suite development --output experiments/my-development-diagnostics.json
```

匯出不覆蓋既有結果；重新實驗用 `--output <新的資料夾>`。原人工 `--score` 仍要求兩份真實 reviewer CSV；已另完成模型流程，保存輸入、原始回覆、理由／引句、初判與六筆修正，不更改人工檔案。完整步驟見 [評估流程](docs/evaluation.md)。

```sh
python -B code/model_evaluation.py verify
# 重算同一凍結結果，不重新呼叫模型；明示套用六筆複核
python -B code/model_evaluation.py score --adjudications data/evaluation/v8.2-llm/adjudications.json
```

新模型實驗必須使用新目錄：先 `model_evaluation.py prepare --output <新目錄>`，再 `llm_grader.py --output <新目錄>`，最後 score。分類器使用已登入的 Codex CLI，會消耗帳號用量；這輪 99 批有效回覆已存好，不需再推論。

已準備的精簡必做包在 data/evaluation/v8.1/course-required/：十題、純 cosine、50 組全文與兩份空白 reviewer 表。無需為了標註重新匯出。原九模型材料仍保留，人工工作依 docs/HUMAN_HANDOFF.md 分階段處理。`--systems` 只限制新匯出包的模型，預設九模型不變。

diagnostics 只接受 course/development，產生排名重疊、文件長度與網站分布；這些描述統計不是相關性成績。holdout 本輪已評估，未參與選模型或調參，此後屬已見回歸集。舊 run_experiments.py 使用新輸出目錄與 exclusive create，避免覆寫歷史資料。

原六組固定查詢排名重現不變：0.46／0.72／0.84／0.80／0.80／0.74，僅為舊助手標註參考。12 題開發集與 24 題 holdout 已凍結並完成另存的模型判定，原人工材料保持空白。不得把未知結果自動填 0，或將不同標籤定義的分數直接相減。

正常導覽的 Evaluation & review 提供全文盲評包及 CSV。3–5 分鐘展示參考 report/DEMO_SCRIPT_V8.md。組別、真實分工與各人心得仍需組員補充。

### v8.3 查詢意圖實驗

原 BM25 可能把指定 GTFOBins 的查詢排成跨站部分匹配；已載入原生函式庫的查詢也會漏掉用 `Process.enumerateModules` 描述的頁面。新增 opt-in：同一套 BM25，以 URL host 與精確 API 證據排序。原網站、預設純 cosine、原九種設定與索引不變。可直接比較：

```sh
python -B code/search.py --bm25 'find gtfobins sudo binary techniques'
python -B code/search.py --bm25 --intent 'find gtfobins sudo binary techniques'
python -B code/search.py --bm25 --intent 'list loaded native libraries'
```

兩題已知失敗作回歸；16 題新題固定於 data/benchmarks/intent-v8.3.json，並分來源、原生模組與控制組。LM 終判的新題 P@5 由 0.350 到 0.425；四種設定、判定與逐題成績見 [v8.3 報告](report/QUERY_INTENT_V8_3.md)。使用既存模型輸出重算，無需再呼叫模型：`python -B code/intent_evaluation.py score --adjudications data/evaluation/v8.3-intent/adjudications.json`。新實驗用 `--output <新目錄>`，舊 v8.2 結果保留。

### v8.4 GTFOBins 功能與情境

明示的 GTFOBins 查詢可用 `--bm25 --gtfo-functions` 比較。同一索引加載 97 頁、341 組從固定官方資料重建並逐例核對正文的功能／情境證據。保留官方別名的正式來源；可能繼承不視為直接證據，明示刪檔不視為寫入內容。原網站與預設排序不變。

```sh
python -B code/search.py --bm25 --gtfo-functions 'GTFOBins SUID reverse shell examples'
uv run --with-requirements requirements-gtfo-build.txt python -B code/build_gtfo_functions.py --output data/gtfo-v8.4/rebuilt.json
```

第二行是選擇性重建，只下載固定官方原始碼並對照本機索引，不執行網頁命令、不覆寫原檔。已有 venv 時也可用 `python -m pip install -r requirements-gtfo-build.txt` 後直接執行建置器。PyYAML 是重建依賴，搜尋執行時不需要。結果、配對限制與負面數據見 [v8.4 報告](report/GTFO_FUNCTIONS_V8_4.md)。

### v8.5 GTFOBins 附加寫入

原 980 頁索引未收錄三個有附加證據的 GTFOBins 條目。補充快照有 983 頁，包含 9 筆附加情境證據。以下在同一索引比較 v8.4 與附加排序。

```sh
IR_INDEX_PATH=data/gtfo-v8.5/index.json.gz python -B code/search.py --bm25 --gtfo-functions 'GTFOBins append data to a file with sudo'
IR_INDEX_PATH=data/gtfo-v8.5/index.json.gz python -B code/search.py --bm25 --gtfo-append 'GTFOBins append data to a file with sudo'
IR_INDEX_PATH=data/gtfo-v8.5/index.json.gz python -B code/append_evaluation.py score --adjudications data/evaluation/v8.5-append/review.json
```

選擇性重建可用 `uv run --with-requirements requirements-gtfo-build.txt python -B code/build_gtfo_append.py --output data/gtfo-v8.5-rebuilt`，目的地須為新目錄。舊題的 P@5 增益來自收錄，同語料的新題排序使 P@5 再增加 8.33 個百分點。詳見 [v8.5 報告](report/GTFO_APPEND_V8_5.md)。

### v8.6 檔案效果與站外附加

另建 986 頁快照，使用明確來源篩選與同一範例的操作、權限證據。兩版在相同快照上的 12 道新題 P@5 從 0.1833 提升至 0.6333。 [v8.6 報告](report/GTFO_WRITE_EFFECTS_V8_6.md)

本機搜尋頁的「v8.6 實驗」可用同一份語料切換 v8.5 與 v8.6，並展開實際例子。現場步驟見 [五分鐘操作卡](report/DEMO_SCRIPT_V8_6.md)。

```sh
IR_INDEX_PATH=data/gtfo-v8.6/index.json.gz python -B code/search.py --bm25 --write-effects 'GTFOBins sudo overwrite a local file'
IR_INDEX_PATH=data/gtfo-v8.6/index.json.gz python -B code/search.py --bm25 --write-effects 'outside GTFOBins append to a local file with sudo'
IR_INDEX_PATH=data/gtfo-v8.6/index.json.gz python -B code/write_effects_evaluation.py score --adjudications data/evaluation/v8.6-effects/review.json
uv run --with-requirements requirements-gtfo-build.txt python -B code/build_write_effects.py --output data/gtfo-v8.6-rebuilt
```

重建使用已凍結的本機採集檔，目的地須為新目錄。已在 Python 3.11、3.12、3.13 重建並核對成品雜湊。

### description 資料限制

固定 v7.1 頁面只有 title/text，沒有獨立 meta description。v8 具備真實 description 的抽取、postings、norms 及位置／offset 儲存，但這 980 頁的 description 均空白，不以正文開頭或生成文字冒充。後續新資料集才能量測 description 的效果，需另凍結；目前欄位比較的 description 分量為零。

新採集快照 485/980 頁有真實 meta description，其餘仍空白。已能驗證完整索引與搜尋流程；description 是否改善品質，仍需新資料集的獨立評估，不能借用舊快照的標籤或 P@5。
