# 集中人工待辦：先完成必做十題

> 2026-11-05 更新：使用者已授權由 LM 代為判定、評分及合理性檢查，v8.2 已完成，見 [模型評估報告](../report/MODEL_EVALUATION_V8_2.md)。以下人工包保留為歷史與可選複核，不再阻擋這版模型結果。真實姓名、分工、個人經驗與課堂另有明定的要求仍不得捏造。

下列為 v8.1 當時的交接狀態：尚無新的正式 P@5，reviewer 欄位空白。原人工流程不允許助手冒填 human；v8.2 結果另存為 llm。

## 1. 先確認資訊需求與相關性規則

來源：TP p.3 §6；U3 p.9、29–36；固定題目在 data/benchmarks/course.json。

- 十題沿用原課程查詢，可供歷史比較；這十題曾用於開發，不能稱為未見過的測試集。
- `decompile android apk` 要求解包／反編譯讀程式碼，但舊 relevance rule 也列 Frida。單純 runtime instrumentation 是否足夠，需先釐清。建議只有明確提供該需求的頁面才算；此建議尚未寫回凍結題目。
- `sql injection tool` 是否包含開發 library、SIP fuzzing 工具，或限於使用者可操作的工具說明，也請在閱讀結果、正式標註前釐清。這會影響難例判定，不應為了分數而事後改規則。
- 若修改規則，保留現有 freeze／材料，另建新版本後再正式評估。不要直接編輯原凍結 JSON。

## 2. 必做版盲評包

位置：data/evaluation/v8.1/course-required/。

- review.html：50 組查詢／文件全文，不顯示模型與排名。
- reviewer-a.csv、reviewer-b.csv：各 50 筆空白紀錄。
- manifest.json／runs.csv：固定 980 頁、十題、純 TF-IDF cosine 的來源與結果。
- 本包只有必做 baseline；不能拿其結果宣稱另外八種方法的品質提升。

每位 reviewer 按資訊需求閱讀全文，填 relevant=0/1、reason、真實 reviewer 名稱、review_origin=human。不要把舊 Hark 標籤改名，不要互看後複製。雙人全面獨立判定是本專題額外提高可信度的設計；教授的要求是人工判定，模糊案例盡可能由另一位組員複核。

```sh
python -B code/evaluate.py --adjudicate --output data/evaluation/v8.1/course-required
# 若有分歧，由組員討論後在該目錄另外填 resolutions.csv。
python -B code/evaluate.py --score --output data/evaluation/v8.1/course-required
```

尚未標註時，上述命令會明確停止；不是可以略過的錯誤。沒有新成績可預填到報告。

## 3. 延伸比較可分階段完成

既有九模型的 course 包有 134 組、development 164 組、holdout 356 組，每份各有兩位 reviewer 的空白表。必做包的 50 組均包含在 course 的 134 組中，pair_id 可對照；後續可保留本人原判斷與來源，不需把同一組當新題重新判斷。

先完成必做版，再處理 development 的方法比較；參數僅可依開發資料調整。holdout 要在方法定案後作最終確認，不拿來選模型／挑參數。本輪只對 holdout 做結果相等性回歸，未做品質調參或弱例分析。

## 4. 確認分析與實際分工

- 核對 report/WEAK_QUERY_ANALYSIS_V8_1.md 的兩個案例與相關性邊界；這是助手診斷草稿，不是人工標籤。
- 填入組別、姓名、各人真實貢獻與個人心得。
- 由正常搜尋入口操作代表性查詢、空查詢／無結果、計分說明與全文，完成 3–5 分鐘全組彩排。
- 使用者確認功能、實驗結論與資料版本後，才視為驗收。PPT 與 Git 上傳仍未進行。

## 保留物與清理

本輪新採集資料、索引、量測與報告都是可追溯成果，保留。沒有落盤的測試 fixture／臨時測試腳本。上一輪列出的三個 Ruff cache 檔仍維持原狀，尚未取得刪除同意；不影響執行。
