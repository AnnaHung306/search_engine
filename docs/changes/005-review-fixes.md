# 005：獨立審查後的修正與最終量測

日期 2026-11-05；狀態：程式及所列驗證完成，組員人工工作與使用者驗收仍待完成。

## 引用

- TP §2／U2 p.22–31／HTTP：送出前的範圍、URL 正規化、延遲與可續爬。
- U1 p.43–48／TP §9：verified contiguous phrase、位置與原文字元 offsets。
- U4 p.15–39／TP §3–5：實際使用的 IDF、norm 與逐詞計分，不能用另一種公式替代解釋。
- U3 p.9、29–38／TP §6：固定題目、全文判斷與過期成績。

完整連結在 ../references.md。審查的標準／需求兩軸與結案狀態在 REVIEW.md。

## 發現、修正與驗證

| 根因／問題 | 修改 | 驗證結果 |
|---|---|---|
| absolute／encoded dot segments 通過 prefix，Requests 送出卻成另一條路徑 | crawl_urls.py 拒絕解碼後 dot/backslash 路徑，採實際 prepared URL 驗證；相對連結仍先正常 urljoin | Kali /tools/../blog、%2e%2e、Metasploit /docs/../api 均在任何請求前拒絕 |
| 句尾句點被 literal regex 吃入 term | positions.py 只保留詞內 dot；snippets 共用 literal matcher | port scan.、SQL injection.、C++.、802.11. 均正確；不跨欄位／停用詞／逗號 |
| 中斷時 active URL 已被 popleft | crawler.py 保留 active，finally 回填未完成 URL 再 checkpoint | 記憶體檔案系統中實際觸發 KeyboardInterrupt，再 resume，頁面成功恢復 |
| 續爬只記時間，忘了更長站方 delay | crawl_http.py state 儲存／還原 delays | 恢復後第一次 robots 請求也遵守已學到的 5 秒 |
| offsets 尚未落盤、描述欄位未分開 | schema 3 加 position_offsets、真實 description postings/norms；新 crawler 保存 meta description | 全部 1,344,488 個 literal occurrences 的 offsets 逐一對回原字串；真實 Nmap 頁存在描述，原 980 頁缺描述不補猜測值 |
| 題目／全文審查材料改變仍可能顯示舊分數 | evaluation.py 驗 suite/run/review HTML/reviewer hashes；app 明示 stale | 受控修改證據後，顯示 stale 且不顯示舊分數 |
| field/pivot 解釋少真正分母；BM25 卻顯示 TF-IDF IDF | search/ranking/templates 顯示各欄位 norms、pivot effective norm、BM25 ln IDF／長度／平均長度與 query TF／multiplier | 依畫面數值獨立重算 field、pivot、BM25，與 base score 一致；排序計算不改 |

沒有新增放行失敗請求、代填資料或以舊索引替代新索引的 fallback。偵測過期評估是明示拒絕顯示成績的狀態，沒有替代分數。

## 最終成效與代價

同機順序執行、相同依賴；先載入索引、每題暖機一次，再量 30 次完整 search()（前十名與摘要，不含 Flask／網路／解釋表格）。

| 項目 | v7.1 | 最終 v8 |
|---|---:|---:|
| `"port scan" -metasploit` median | 49.025 ms | 4.358 ms |
| `sql injection tool` median | 0.357 ms | 3.026 ms |
| 索引 bytes | 15,827,676 | 47,933,880 |
| 該次索引初載 | 84.2 ms | 641.3 ms |

片語約快 11.2 倍；一般搜尋較慢、索引約為原本 3 倍，成本來自 positions／原文字元 offsets／欄位 norms 與完整窗口摘要。先前 002 的 28.9 MB 是尚未存 offsets 的第一輪，不把它當最終大小。原始資料見 evidence/latency-final.json；九組、十題 × 每題 20 次另見 evidence/timing-v8.json。

原六組排名及 P@5 不變。field/proximity 的正式品質仍未知，sql injection tool 的失敗例保留，沒有選它作預設。

## 交付與待辦

- 三份盲評包：course 134、development 164、holdout 356 pairs；兩份 reviewer CSV 均維持空白，不代填人工標籤。
- 正常 Flask 瀏覽器已實際走搜尋、解釋、全文、評估及盲評材料導覽；畫面證據 evidence/preview-explanation.png。
- 188 項聚焦 assertions、全部 offsets、額外 kappa／過期結果／三種分母驗證完成；測試腳本與受控檔案系統只在記憶體中。
- 最後一個純解釋修正發生在盲評包匯出後，因此沒有覆寫舊 manifest／材料／標籤；另重跑九組 × 全部 46 題，確認每筆 URL／排名／分數與凍結 runs 一致，記錄 final-run-compatibility.json 與最終 code hashes。
- 使用者需驗收；組員需確認候選題、完成人工標註／分工／心得與彩排。沒有 Git 上傳、公開部署或攻擊操作。
