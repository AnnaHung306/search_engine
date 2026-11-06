# 007：維持結果相同的效能優化

日期：2026-11-05。引用：U1 p.43–48、U4 p.15–39、TP §3–6／9；工程延伸 VAR、PY，連結見 ../references.md。壓縮、快取與稀疏選窗不是教授的新排序公式。

## 根因與實作

初次 profile 的兩個測試查詢中，摘要約占八成時間；schema-3 offsets 的 JSON 占 19,381,560 bytes。排序又為每個候選重算 query norm、BM25 IDF，並建立只供解釋使用的逐詞 row。

- offsets.py：以 start gap／length 的 unsigned base-128 varint 與 Base64 儲存，0 保留標點位置空位；不可還原或格式錯誤直接報錯。按需解碼，最多快取 128 個欄位。這是自製容器，並未使用 Protobuf message 或 ready-made 搜尋引擎。
- indexer.py／search.py：schema 4、固定 mtime/filename 標頭的 gzip、原子替換、明確 IR_INDEX_PATH；舊索引仍保留，不靜默改讀。
- snippets.py：只在命中進出窗口的起點評估，保留 coverage/count 與最早起點的 tie policy；空白位置和查詢字面位置各有 128 筆有界快取。沒有快取排名、分數或使用者結果。
- ranking.py：每次查詢預算 norm／BM25 IDF，排名與解釋共用同一個 contribution 算式，不更動數學定義。
- positions.py／search.py：候選排序只用位置窗；完整字元座標延後到真正回傳且要求解釋的結果，直接呼叫 proximity() 仍預設回傳完整證據。

## 固定 980 頁的同批比較

基準 commit 5d1da8f。相同 Python 3.13.14／依賴／機器，舊新交錯各五個新程序；檔案系統已暖。每題先搜尋一次，再各 30 次完整搜尋；另做每次清空詞彙／offset 快取的 10 次冷查詢。以下 query 數字不含初載、Flask、HTML、解釋表或網路。

| 指標 | 修改前 | 修改後 | 變化 |
|---|---:|---:|---:|
| 目前採用的索引檔 | 47.93 MB | 9.81 MB | 減少約 79.5% |
| 初載中位數 | 449.53 ms | 313.14 ms | 減少約 30.3% |
| 初載後程序 RSS peak 中位數 | 746.36 MB | 463.93 MB | 減少約 37.8% |
| sql injection tool，暖機 | 2.905 ms | 0.458 ms | 減少約 84.2% |
| 同題，清空詞彙／offset 快取 | 2.929 ms | 1.699 ms | 減少約 42.0% |
| "port scan" -metasploit，暖機 | 4.523 ms | 0.598 ms | 減少約 86.8% |
| 同題，清空詞彙／offset 快取 | 4.716 ms | 3.073 ms | 減少約 34.8% |
| network packet sniffer，暖機 | 3.173 ms | 0.370 ms | 減少約 88.3% |

MB 以 1,000,000 bytes 計。RSS 是該程序到載入完畢為止的 peak，不能當作穩態記憶體；保留歷史索引也代表整個 repository 的總磁碟用量並未跟著減少 79.5%。

另以原十題、每題暖機一次後 20 次完整搜尋，比較全部九組設定。這一批所有 90 個 query/system 的中位數均未退步；九組整體 median 範圍由 3.005–11.158 ms 降至 0.440–4.673 ms。這是不同於上述交錯五程序的第二個量測，不把兩批混成一個樣本。逐模型／逐題數據與 p95 均保留。

## 曾經退步的部分與修正

最早的快取版本會為全文建立不需要的詞彙表，首次摘要較慢；改成只記錄當次字面詞的位置。壓縮 offsets 的中間版本又在所有候選提早解碼，sql+proximity 冷查詢中位數 83.33 ms（含解釋 81.03 ms）；延後到回傳結果後為 5.25 ms（含解釋 5.66 ms）。保留 intermediate 與 final 證據，不隱藏這次回歸。

正常瀏覽器的新快照 field+proximity 查詢，修正前曾顯示 292.0 ms，修正後的操作顯示 9.6 ms；前一次與完整回歸同時執行，兩者只是實際可見觀察，不當成受控效能比值。另存 browser-and-http.json 與實際畫面 preview-live-v8.1.png。

採集仍在執行時的第一次交錯量測也保留在 performance-during-crawl.json，其中 cold phrase p95 曾達 89.32 ms；其背景負載與最終批次不同，不能當作演算法效果。headline 使用採集與兩次索引建置都完成後的批次。

快取仍需要額外記憶體；冷查詢仍比暖機慢，128 筆限制也不是總 bytes 限制。gzip／varint 增加格式與解碼成本，所有機器／文件長度不保證都有相同改善。與 v7 的不同時段歷史量測保留在 005，不混作本次同批結果。

## 結果正確性

原 980 頁的 1,344,488 筆 offsets 無損還原；摘要對照舊版的 2,000 個固定隨機案例一致；九模型 × 46 題，共 414 次搜尋的狀態、URL、排名、分數、摘要與完整解釋相等。holdout 僅用於正確性相等回歸，未用於品質調參。正式品質仍待人工。

證據：v8-baseline-search.json.gz、v8.1-final-verification.json、v8.1-performance-final.json、v8.1-proximity-{intermediate,final}.json、v8.1-system-timing-{before,after}/timing.json、v8.1-system-timing-comparison.json，均在 evidence/。
