# v8 正常產品展示（目標 4 分 30 秒）

引用 TP p.4 §7–9。先依根目錄 README 啟動原 Flask 入口；使用固定資料，不在台上重爬或重建索引。

| 時間 | 正常操作 | 說明 |
|---|---|---|
| 0:00–0:35 | 說明主題、980 頁與離線／線上架構 | 自寫倒排索引與 TF-IDF cosine，引用 U1／U4 |
| 0:35–1:15 | 搜 decompile android apk，展開第一筆 Why this result | 查看 TF、DF、IDF、norm、逐詞貢獻；不是生成的解釋 |
| 1:15–2:00 | 搜 sql injection tool，再切 Compare enhancements，分別試 BM25／pivot | 展示基準的弱點，說明正規化不同；不要把新方法直接叫必做 cosine |
| 2:00–2:35 | 回基準搜 sql sql sql injection tool，查看 sql 的 query weight | 重複詞頻按 log TF；用 toy_example.py 回答計分問題 |
| 2:35–3:05 | 搜 "port scan" -metasploit | 位置索引驗證連續詞、排除條件；不跨 title/body |
| 3:05–3:35 | 試空查詢與 qwzxv；實驗模式試 無缐 破解 並勾 typo | 展示空／OOV、明示容錯；所有功能使用正常入口 |
| 3:35–4:10 | 導覽 Evaluation & review，開全文盲評包 | 十題課程基準與新題分開；人工未完成就沒有正式新分數 |
| 4:10–4:30 | 每位組員準備一個真實學習點，依時間擇要 | 高分的尺、功能互相抵消、速度與索引大小取捨；各人心得另交 |

新 field/proximity 可作備用展示，需清楚說仍在研究驗證。個人參與不可由此腳本代替。
