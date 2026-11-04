# 評估與組員複核

引用：TP p.3 §6、U3 p.9、29–36，連結見 references.md。評估對象是資訊需求，而非命中標題關鍵字。

## 凍結與用途

- course：原十題，已多次用來開發，只作課程基準／回歸，不冒稱獨立 test。
- development：12 題，用於開發；人工標註仍待完成。
- holdout：24 題新候選，先凍結，未用新方法成績挑題／調參；組員仍須核對資訊需求、範圍與題目代表性。
- data/benchmarks/freeze.json 保留每份 query JSON 的 SHA-256；修改題目會停止執行，不會悄悄沿用原測試名稱。

九組固定設定：原六組，另加 TF-IDF+proximity、field cosine、field+proximity。title weight=2、proximity weight=0.3 是本輪先定的實驗參數，未由 holdout 成績挑選；後續調參只用開發集。

## 執行與人工工作

1. `python -B code/evaluate.py --dump --suite holdout`。同一 output 不覆寫；新實驗明確指定新 output。
2. 在正常產品的 Evaluation & review，開 Read blinded full texts；輸出隱藏系統名稱與排名，包含資訊需求、規則及完整索引正文。原始採集正文另存 pages.json，可按 URL 查回。
3. 兩位組員各自編輯 data/evaluation/v8/holdout/reviewer-a.csv 與 reviewer-b.csv。每列填 `relevant=0/1`、按全文判斷的 reason、真實 reviewer 名稱與 `review_origin=human`。不要互看後直接覆製，亦不要把助手預標改名當作人工完成。
4. `python -B code/evaluate.py --adjudicate --suite holdout`。缺標會集中列出數量與首批 ID；分歧列需由組員討論後另填 resolutions.csv，欄位與 reviewer CSV 相同，只包含有分歧的列。
5. `python -B code/evaluate.py --score --suite holdout`。程式重新檢查兩份人工紀錄與仲裁，產生 consensus、agreement、每題 scores.csv 及平均 scores.json。

工具只檢查自我聲明、欄位、不同姓名與一致性，無法驗證真正的人員身分。人工複核必須實際發生，不能由程式通過代替。

## 正確性與比較限制

- 每題每系統保留 rank 1–5。空位算 0，分母固定 5；有回傳卻未標的頁面會停止正式計分。
- 同一 (query, URL) 共用一筆判斷；新方法新增頁面必須先盲標，不能猜為 0。
- 兩位 reviewer 的標籤一致率／Cohen's kappa 用同一完整 pool；全同類別或空 pool 時 kappa 未定義，記 null 並說明，不能假填 0。
- scores 留存 reviewer、consensus、runs、manifest 的 hashes，資料改動後頁面不再顯示舊成績。
- 既有 144 筆 Hark 標註只供歷史回歸，沒有自動轉成人工標註。`--legacy-score` 明確標示此限制。
- P@5 是主指標；此次沒有用不完整 pool 計算 Recall/F1，也沒有新增未定義的 nDCG。
- 新增方法品質尚未人工確認，報告／介面不填造新成績。組員確認前，不為了使分數更好而換題或改相關性規則。

## 計時

`python -B code/evaluate.py --timing --suite course --repeats 20`。先載入索引，每題暖機一次，再量測完整 search()（前十名與純文字摘要）；不含解釋表格、Flask、網路。輸出 mean、median、p95、max 與每題 median。索引讀取另於效能比較紀錄，不和查詢時間混算。
