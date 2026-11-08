# Gemini Embedding 2 實驗整合（2026-11-08）

- 引用：課程專題 TP §6、U3 p.29–38（見 `docs/REFERENCES.md`）；[Gemini embeddings 文件](https://ai.google.dev/gemini-api/docs/embeddings)；使用者提供的 Gemini Embedding 2 實驗資料包。
- 原況：專案尚未集中保存這份語意檢索實驗與三方比較；原有搜尋使用詞彙排序。
- 修改：將完整資料包放入 `experiments/gemini-embedding-2/`，在 `report/REPORT_V8.md` 補充方法、結果與限制，並從根目錄 README 連結。
- 固定資料：980 頁索引的 SHA-256 為 `4eebfa9c8b22d773db53274c0e9f06b0ddb1a3db5d57be281eb4d9ed325e0bd4`。82 個案例的 TF-IDF、BM25、Gemini P@5 分別為 0.332、0.502、0.634。以上為原實驗結果，非產品功能修改前後的上線成效。
- 驗證：依實驗 README 執行離線重算，並核對實際索引雜湊；具體結果見本次交付說明。
- 限制：模型盲評尚未經獨立人工評審；各題組有重複查詢，依原規則分別計分。報告中的實驗未接入網頁查詢，也未證明對新查詢、其他資料集或成本與延遲的效果。待使用者驗收。
