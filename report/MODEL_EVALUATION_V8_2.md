# v8.2：模型判定、評分與下一步

日期：2026-11-05。這輪已依使用者授權，代為完成相關性判定、規則合理性檢查與計分。狀態是 **模型評估完成，尚待使用者驗收**。沒有製作 PPT、push 或部署。

## 從以前到現在

| 階段 | 實際完成與學到的事 |
|---|---|
| 原 v7.1 | 七站 980 頁、自寫倒排索引、TF-IDF/cosine、BM25、介面與舊標註；有成果，但舊標註不能當獨立驗證。 |
| v8 | 對照老師 Unit 1–4 與 Term Project：修正查詢 TF、爬取限制及評估缺標；加入位置、欄位、鄰近度與計分解釋，保留必做純 cosine。 |
| v8.1 | 真實重爬 980 頁、1,027 請求、485 頁來源 description，獨立存放；索引 47.93→9.81 MB，414 次搜尋結果／分數／摘要／解釋一致；暖 sql 搜尋 2.90→0.46 ms。 |
| v8.2 本輪 | 46 題、九模型、654 組配對、362 篇完整索引文件，由模型判定並重新計分；保留六筆自我複核修正、改善與退步。排序本身沒有改。 |

前幾輪重點是「先能跑，再確保方法正確」；這輪是「實際量測哪些改進有用」。目前經驗是：更多功能不一定更好，相關性也不能只看關鍵字或模型的高信心。這些是可由紀錄支持的技術反思，不能替組員捏造個人心情或分工。

## 老師要求與現在的證據

TP p.1–4 §2–9、U1 p.43–48、U2 p.14–31、U3 p.9／29–38、U4 p.15–39 的連結見 [引用資料](../docs/references.md)。自寫採集、前處理、倒排索引、log TF／collection IDF／cosine、搜尋展示與 P@5 比較已有實作與紀錄；必做模式仍預設純 TF-IDF cosine。BM25 等是另列的實驗。

本輪補上先前缺少的品質判定，但明示由 LM 產生。沒有宣稱教授已接受模型取代人工評估；若課堂另要求指定評者或人工證據，需按該要求補件。組別、姓名、真實分工與個人心得仍只使用實際資料。

## 九模型比較

下表均為本輪最終模型標籤的 mean P@5；每題分母固定 5，空位計 0，回傳文件缺標則停止計分。

| 系統 | course 10 題 | development 12 題 | holdout 24 題 |
|---|---:|---:|---:|
| 必做 TF-IDF cosine | 0.4000 | 0.4500 | 0.4000 |
| + 覆蓋優先 | 0.7200 | 0.5667 | 0.4750 |
| + pivot | 0.8000 | 0.5667 | 0.6250 |
| + pivot + 覆蓋 | 0.8600 | 0.5833 | 0.5833 |
| BM25 | 0.8000 | 0.6333 | 0.6250 |
| BM25 + title + synonyms | 0.8200 | 0.6000 | 0.6250 |
| TF-IDF + proximity | 0.4600 | 0.4667 | 0.4250 |
| field cosine | 0.4600 | 0.4667 | 0.3667 |
| field + proximity | 0.4800 | 0.5167 | 0.3583 |

**依 development 選 BM25**：38/60=0.6333，基準 27/60=0.4500，增加 11 個相關結果位置、18.33 個百分點。以這個選擇報告 holdout：75/120=0.6250，基準 48/120=0.4000，增加 27 個相關位置、22.5 個百分點。24 題有 16 勝、6 平、2 負。pivot 與加強 BM25 在 holdout 同為 0.6250；沒有依 holdout 重新選模型。

**退步：**field + proximity 的 holdout=0.3583，比基準低 4.17 個百分點；field cosine=0.3667。舊 collection 的 description 全空白，欄位加權效果不代表新 description 的效果。保留實驗選項與負面結果，沒有把它們宣稱成提升。

## 弱查詢與實際例子

| 查詢 | TF-IDF | BM25 | 檢查結果與限制 |
|---|---:|---:|---|
| `find gtfobins sudo binary techniques` | 1.0 | 0.0 | 基準前五筆 as／cat／base64／aoss／cdist 都有 sudo 功能；BM25 排入 unhide、dnsmap、commix、Nmap version detection、burpsuite，未滿足指定 GTFOBins 需求。可確認排序錯配；不能只憑結果斷言單一公式根因。 |
| `list loaded native libraries` | 0.0 | 0.0 | 相關的 Frida JavaScript API（doc 170）實際寫有 `Process.enumerateModules()`，但未進入九模型此題前五筆 pool。詞彙 libraries／modules 不一致是可檢查的改善方向，尚未以新實驗證明原因。沒有把 pool 外證據塞進既有分數。 |
| `decrypt tls sessions with key log` | 0.6 | 0.4 | BM25 仍有單題退步，不以整體平均掩蓋。 |

course 十題逐題結果：

| 題目 | 純 cosine | BM25 |
|---|---:|---:|
| wifi password cracking | 0.4 | 0.8 |
| sql injection tool | 0.2 | 0.6 |
| port scanning techniques | 0.4 | 0.8 |
| intercept https traffic | 0.2 | 1.0 |
| web application vulnerability scanner | 0.6 | 0.6 |
| network packet sniffer | 0.8 | 1.0 |
| exploit metasploit module | 0.0 | 0.6 |
| decompile android apk | 0.6 | 0.8 |
| directory enumeration web server | 0.4 | 0.8 |
| reverse shell payload | 0.4 | 1.0 |

三組全部逐題／九模型資料：[course](../data/evaluation/v8.2-llm/course/scores.csv)、[development](../data/evaluation/v8.2-llm/development/scores.csv)、[holdout](../data/evaluation/v8.2-llm/holdout/scores.csv)。

## 如何完成模型判定

先固定資訊需求與政策，把同一題／URL 合併，隱去系統、排名、分數與舊標籤。完整索引正文 5,498,678 字元分成 409 個重疊段落、99 批，所有段落都需有效回覆；任一段有實質正面證據才彙總成相關。全文指搜尋引擎索引的抽取正文，不是每個網站的所有 HTML 或圖片。

Codex CLI 分類器禁用工具，保存原始 events 與結構化回覆；每筆有 0/1、理由、信心及可驗證的連續原文引句。遺漏、錯 ID、非原文引句、工具動作都拒收，缺標不補 0。精確模型識別碼未由 CLI events 暴露，因此只記 Codex CLI default model，不猜版本。

判定規則先釐清：SQLi 工具需明確提供所求能力，開發 library 不自動算使用者工具；泛 SQLi 題沒有擅加 web-only 條件；APK／DEX 反編譯不等於 runtime hook。針對 use/run 的需求要求實際操作流程，但明確查 developer API 的題目可接受 API 文件。原九模型 runs、原 queries 與人工檔案未改，衍生政策單獨保存。

[Thomas 等人原始研究](https://arxiv.org/abs/2309.10621)研究 LLM 預測搜尋偏好，並以使用者回饋校準。這輪沒有校準，也不借用論文中的準確率。信心高／中／低是主觀類別，不能當機率。

## 自我複核與六筆修正

逐一檢查原 27 筆中信心理由與引句，再核對 course-07 全部 11 筆正例、讀完 14 篇爭議／對照正文。此時已看過初判彙總，不是獨立第二評者。六筆改動套用到同一題所有模型，不依排名挑選。

| 題目／文件 | 初判→終判 | 修正理由 |
|---|---|---|
| course-07／doc 598 | 1→0 | 全文是撰寫與提交Go模組的開發步驟，未提供使用者選用、設定及執行exploit模組的操作；應依資訊需求而非較寬主題字判定。 |
| course-07／doc 581 | 1→0 | 全文介紹HttpServer mixin與Ruby回呼，沒有終端使用者執行exploit模組的流程；僅開發機制不足以滿足use/run需求。 |
| course-07／doc 651 | 1→0 | 全文是fileformat API、虛構exploit程式片段與檔名設定，未提供使用exploit模組的操作流程。 |
| course-07／doc 590 | 1→0 | 全文是模組開發原則、空白Ruby模板及Git貢獻流程，沒有可操作的exploit使用步驟。 |
| development-08／doc 859 | 0→1 | 用法同時提供-r dumpfile與filter，能讀取已擷取檔並套用篩選；與接受dsniff離線pcap過濾的同一規則一致。 |
| course-10／doc 34 | 0→1 | 雖以前置既有shell為條件，全文確實提供shell_to_meterpreter及reverse_tcp payload設定，能建立新的反向Meterpreter連線，並非僅提及酬載名稱。 |

BM25 初判→複核：course 0.82→0.80；development 0.6167→0.6333；holdout 0.625→0.625。判定修正造成的升降不是演算法提升。終判信心 628 高、26 中、0 低；高信心也發生過修正，因此不能以「沒有低信心」表示可靠性已證實。

可查：[終判與引句](../data/evaluation/v8.2-llm/llm_judgments.csv)、[初始彙總](../data/evaluation/v8.2-llm/raw_llm_judgments.csv)、[六筆修正](../data/evaluation/v8.2-llm/adjudications.json)、[初判成績](../data/evaluation/v8.2-llm/initial/scores.json)、[政策](../data/evaluation/v8.2-llm/policy.json)。

## 實作可靠性與代價

審查後修正四類問題：用整數相關位置總數判平手，避免浮點加總誤選；逾時保存部分原始 bytes；頁面重新驗算 CSV 而非只信 scores.json；錯誤 manifest 結構顯示 stale，避免 HTTP 500。模型與人工來源分開，人工入口仍拒絕 llm 冒充 human。

100 次 CLI 呼叫取得 99 份有效回覆；一批 ID 漏字被拒收後原樣重試，失敗輸出保留。所有輸入／回覆／原始 events 是正式可追溯證據，不是臨時測試檔。CLI 曾有既有 state DB falling_back／技能掃描上限 metadata 警告，stderr 保留；本專題沒有新增應用 fallback，也沒有改用其他模型或跳過文件。

正常產品的 Search → Evaluation & review 顯示表格並提供下載；5002 新快照必須隱藏舊 collection 成績。驗證與兩軸 review 見 [009 紀錄](../docs/changes/009-model-assessment.md)、[驗證證據](../docs/changes/evidence/v8.2-completion.json)。

## 接下來可以完成什麼

1. 這一版可先確認報告與正常網站是否符合展示需求；目前模型評分已完成，不再以人工標註作為此版本的阻礙。
2. 若要下一輪更進階，先以 development 設計詞彙與網站意圖處理、修正欄位混分，再凍結新測試集驗證；已看過的 holdout 只能作回歸，不能再稱未見測試。這些會改方法，應先集中確認方案。
3. 新採集 collection 有 485 頁真實 description，可獨立建立對照實驗，重新固定查詢／pool／判定；不能沿用本輪舊 collection 分數。
4. 正式交付前補真實組別／姓名／分工／個人心得與課堂指定事項；LM 不能代造。使用者確認內容後才進 PPT，Git 上傳仍需明確授權。

## 尚未證實的部分

course 已反覆用於開發，兩條規則在前輪診斷後釐清；不是獨立測試。單一模型與同流程自我複核可能共享偏差，沒有人工校準、獨立評者 kappa 或未標全文庫的 Recall/F1。本輪只評原 980 頁 collection，沒有聲稱重爬或 description 提升品質。v7.1 的舊標註定義不同，不與這輪分數直接作前後差。
