# 002：位置索引、欄位與鄰近度

日期 2026-11-05；狀態：功能與計算不變量通過；品質待人工評估，待使用者驗收。

## 引用

U1 p.43–48：短 postings 優先、位置資訊與鄰近度；U4 p.25–39：向量、正規化與權重；TP p.4 §9：片語／Boolean 延伸。公式是本專題設計，非直接引用老師的欄位／鄰近度公式。連結見 ../references.md。

## 改了哪裡

- positions.py：literal positions、保留 stopwords、title/body 各自編號、alias 對應、片語交集及最短位置窗。
- indexer.py：schema 3、collection hash、title/description/body norms、position postings；保留原 index.json，另產生 index-v8.json。
- ranking.py：自寫 cosine／BM25／field cosine；同一份 per-term 計算同時用於排序及解釋。
- search.py：片語改查位置索引；明示 field_weight、proximity_weight，與必做基準分開。

## 改前、改後與驗證

- 片語不再對每個候選正文跑全文 regex；手工不變量確認不跨 title/body、不略過 and、不把 export 當 port、不把逗號視為允許的連接符。
- `port-scan` 可命中 `"port scan"`；`port and scan` 只命中含 and 的完整片語。
- 解釋的逐詞 contributions 加總等於實際 base score；後續 multiplier 另列，不用生成文字猜測計分原因。
- 同機順序比較、各暖機一次後 30 次完整搜尋：`"port scan" -metasploit` median 49.565→4.040 ms（約快 12.3 倍）；`sql injection tool` 0.398→2.623 ms。
- 索引 15,827,676→28,874,309 bytes；該次載入 96.3→315.6 ms。較快片語來自額外索引空間；較完整摘要與通用計分有一般查詢成本。
- 原六組的排名／P@5 均維持，不以新實驗未標註頁面填 0 來比較。

量測原始資料及邊界：evidence/latency-comparison.json。這是指定查詢與機器的局部結果，不宣稱所有查詢加速。不同位置／欄位邊界造成的正確性修正可能改變片語結果，不能把舊的錯誤命中當回歸目標。

## 尚待證實

field cosine `(body + description + 2*title)/4`；proximity multiplier `1+0.3*closeness`。設定先凍結，尚未由 holdout 品質調參；是否改善檢索需要人工標註，沒有保證超過 pivot 或 BM25。

正常 UI 負面案例：`sql injection tool` 的 field+proximity 版本把 SQL injection library、cmd injection module、DLL injection 文件排前面，sqlmap 第六。這是標題詞相近卻資訊需求不同的例子；保留為失敗分析，不改測試題或用其成績調 holdout 參數。

審查後新增 char offsets（每個 literal position 對應正文／欄位原字串的 start/end）、description postings/norms 與句尾句點處理。v7.1 的 980 頁沒有 description metadata，故該欄為空，沒有推測補值；新爬蟲會保存來源實際提供的 meta description。欄位混分為 (body + description + 2×title)/4。上列大小／速度是審查前第一輪量測；最終索引與量測另記 005-review-fixes.md，不覆寫第一輪紀錄。
