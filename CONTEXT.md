# 專案脈絡

使用者於 2026-11-05 核可外層「專題盤點與優化建議」的實作方向，並要求每次更新記錄引用、進步與改動。

- **Collection snapshot**：固定 pages.json，980 頁；不可因測試重爬而覆蓋。
- **Required baseline**：自寫倒排索引、log TF × collection IDF、L2 cosine；新 UI 預設無擴展或重排。
- **Experiment**：明示的 BM25、pivot、coverage、field cosine、proximity 或 query correction；成效需同快照同人工判斷比較。
- **Frozen suite**：含資訊需求與規則、由 SHA-256 固定的查詢集。course 已用於開發，holdout 候選需組員核對。
- **Human judgment**：組員按全文獨立給的 0/1 與理由；助手歷史標註不能轉名冒充。
- **Acceptance**：使用者的明確認可；自動化通過或本機畫面可操作均不等於已驗收。

本輪不公開部署、不 push、不執行攻擊、不代寫組員真實經歷。新 UI、位置／欄位實驗與獨立評估方向已於本輪使用者確認；Git 上傳仍需另外明確同意。
