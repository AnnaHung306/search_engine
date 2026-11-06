# 專案脈絡

使用者於 2026-11-05 核可外層「專題盤點與優化建議」的實作方向，並要求每次更新記錄引用、進步與改動。

- **Collection snapshot**：固定 pages.json，980 頁；不可因測試重爬而覆蓋。
- **Required baseline**：自寫倒排索引、log TF × collection IDF、L2 cosine；新 UI 預設無擴展或重排。
- **Experiment**：明示的 BM25、pivot、coverage、field cosine、proximity 或 query correction；成效需同快照同人工判斷比較。
- **Frozen suite**：含資訊需求與規則、由 SHA-256 固定的查詢集。course 已用於開發，holdout 候選需組員核對。
- **Human judgment**：組員按全文獨立給的 0/1 與理由；助手歷史標註不能轉名冒充。
- **Acceptance**：使用者的明確認可；自動化通過或本機畫面可操作均不等於已驗收。

本輪不公開部署、不 push、不執行攻擊、不代寫組員真實經歷。新 UI、位置／欄位實驗與獨立評估方向已於本輪使用者確認；Git 上傳仍需另外明確同意。

使用者後續核可依序補真實採集、同結果效能優化、排名診斷與集中人工交接；本輪先不做 PPT。v8.1 使用 schema 4 壓縮索引，原 980 頁仍為預設研究 collection；data/crawls/v8-live-20261105/ 是另一份真實快照。新快照沒有人工品質結論，兩份資料不可混用標籤。

使用者再明確指示由 LM／助手代為決定規則、判定相關性並計分，不再等待組員逐筆標註。**Model judgment**：來源標為 llm 的內容判定，保留規則、全文分段、引文、信心與模型原回應；與 Human judgment 分開，不冒稱真人、獨立雙人評估或教授已接受。本輪以 data/evaluation/v8.2-llm/ 保存，新舊人工表格不覆寫；仍不做 PPT、不 push。

v8.3 使用者要求處理 GTFOBins sudo 與 native libraries 兩題失敗並重新評估。**Intent experiment** 是既有排名的獨立選項：來源層使用 URL host，原生模組以有語境的精確 API 證據補足用詞差異；不改必做基準或既有產品流程。兩題已知案例屬回歸，另凍結 16 題新比較，資料及模型標註另存於 data/evaluation/v8.3-intent/。仍不做 PPT、不 push。

v8.4 使用者要求改善 GTFOBins 同站反向 shell、sudo 寫檔與 SUID 配對。**Function/context evidence**：固定官方資料的同一功能例子，必須能對照原索引正文的功能、情境與例子。官方 alias 保留正式條目來源，可能繼承不算直接；明示刪檔不算寫入內容。以獨立索引附加檔和 opt-in 排序驗證，原索引及網站不變。

v8.5 在另建的 983 頁實驗快照中補收 hashcat、screen、tee。**Append evidence** 對應同一功能及情境的明示附加效果或選項。實驗用同語料比較 v8.4 與附加順位，原 980 頁的失敗另作收錄診斷。

v8.6 把覆寫、附加、刪檔分開判定，明確排除來源則在候選階段依 URL host 套用。站外補收三頁形成 986 頁實驗快照，原七站快照仍供必做比較。已知失敗與 12 道新題分開計分，終判及初判保存於 data/evaluation/v8.6-effects/。
