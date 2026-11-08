# Term Project I：課程整合更新 v8（待組員補充／使用者驗收）

作業最新截止為 2026-11-12 23:59。組別、姓名與實際分工待組員填入，不沿用舊草稿「只剩心得」或「技術全部完成」的說法。

## 目標與資料

延續資安工具／方法文件搜尋主題，使用固定 980 頁、7 hosts、8 seeds。原始 v7.1 索引及資料保留，v8 的索引新增欄位 norms、literal positions 與 collection hash。完整種子／路徑／配額見 code/config.py。

歷史紀錄為 1,016 個主爬取嘗試、980 有效頁、0 已記錄失敗；舊程式未把 robots 與自動轉址各跳全部計入，不能把這數字稱為所有實際 HTTP 請求。本輪未全站重爬。當前固定 pages.json 重算平均正文 8,908.9 字元，舊 summary 的 8,910.3 是歷史採集紀錄，兩者區分呈現。

```mermaid
flowchart TD
    Seeds[8 seeds / 7 hosts] --> Gate[逐跳 scope / robots / 限速]
    Gate --> Pages[固定 980 頁 pages.json]
    Pages --> Pre[共用前處理與正文清理]
    Pre --> Index[倒排索引 / 欄位 norms / literal positions]
    Query[正常 Flask 搜尋入口] --> Retrieve[Postings 候選與位置片語篩選]
    Index --> Retrieve
    Retrieve --> Rank[必做 cosine / 明示比較模型]
    Rank --> Results[摘要 / 命中詞 / 可展開計分]
    Index --> Eval[凍結查詢 / 九組結果 pooling]
    Eval --> Humans[兩位組員全文盲評與仲裁]
    Humans --> Scores[P@5 / 一致率 / kappa]
```

## 引用課程後的修改

1. U4 p.15–39／TP §3–5：查詢詞頻改為實際 log TF，與文件、toy example 一致。`sql sql sql injection tool` 第一名分數由錯誤 0.1834 修正成 0.1755。
2. U2 p.22–31／TP §2：每跳請求前驗 scope／robots；robots、轉址與失敗共用 budget／限速。暫時 robots 失敗與 429 暫停該 host；移除 fail-open。
3. U1 p.43–48／TP §9：位置索引保留停用詞，title/body 分開。片語不會跨欄位、跨停用詞間隔或把 export 當 port。
4. U4 p.25–39：結果能展開 TF、DF、IDF、query/document norm 及逐詞貢獻。新 field cosine 與 proximity 是本專題延伸，非教授原公式。
5. U3 p.9、29–38／TP §6：凍結新查詢、盲評全文、兩位組員獨立紀錄、分歧仲裁、kappa；未標註停止正式計分。摘要按查詢挑選約 80 詞，正文足夠時不因命中在尾端而只剩幾個字。

完整來源連結見 docs/references.md；各批檔案與證據見 docs/changes/。

## 現有結果與限制

原六組固定排名均重現不變：TF-IDF 0.46、coverage 0.72、pivot 0.84、pivot+coverage 0.80、BM25 0.80、BM25+title+synonyms 0.74。這些是原 Hark 標註的歷史參考，尚不能代替組員人工確認。

九組新比較的正式成績 **待人工盲評**，不預填。12 題 development、24 題 holdout 候選已先凍結；組員仍須確認題目代表性與相關性規則。新模型是否改善 P@5，必須等這些工作完成後再寫結論。

最終同機順序比較、每題暖機一次後 30 次完整搜尋：片語加排除約 49.0→4.4 ms；一般 sql injection tool 約 0.36→3.03 ms。加入完整 offsets 後，索引 15.8→47.9 MB，該次初次載入約 84→641 ms。這是局部機器／查詢的量測，非普遍效能保證，也不含瀏覽器網路時間。第一輪尚無 offsets 的量測另保留於更新紀錄，不混作最終成效。

字元 offsets 已逐一對回 1,344,488 個 literal occurrences。title／description／body 各自有 norms；description 只從來源真實 metadata 取得，原 980 頁缺此欄，沒有推測補值，該欄的品質效果需未來另凍結的新資料集驗證。

## Gemini Embedding 2 語意檢索補充實驗

本實驗使用與基線相同的固定 980 頁語料（索引 SHA-256：`4eebfa9c8b22d773db53274c0e9f06b0ddb1a3db5d57be281eb4d9ed325e0bd4`），比較純 TF-IDF cosine、純 BM25 與 Gemini Embedding 2。82 個題組案例包含 78 個不同查詢；同一查詢若出現在不同題組，依各題組規則分別評分。此實驗是離線比較，現有網頁預設搜尋流程沒有接入 Gemini。

文件正文切成 2,109 段，每段最多 6,000 UTF-8 bytes，約重疊 500 bytes；文件段落輸入包含標題與正文，查詢輸入包含檢索任務提示。使用 768 維向量，經正規化後計算 cosine，每頁取最高的段落分數。方法參考 [Gemini embeddings 文件](https://ai.google.dev/gemini-api/docs/embeddings)。

| 方法 | 前五名中的相關結果 | 平均 P@5 |
|---|---:|---:|
| TF-IDF | 136 / 410 | 0.332 |
| BM25 | 206 / 410 | 0.502 |
| Gemini Embedding 2 | 260 / 410 | 0.634 |

Gemini 比 TF-IDF 高 30.2 個百分點，比 BM25 高 13.2 個百分點；逐題相對 BM25 為 37 勝、32 平、13 負。例如 `mitmproxy modify http response` 的 BM25 P@5 為 1.00、Gemini 為 0.60，顯示語意方法並非每題都較佳。若將重複查詢先平均，使 78 個不同查詢等權，三者依序為 0.336、0.526、0.636。

相關性依既有題組規則與凍結正文進行模型盲評；原有及補充判分尚未經獨立人工評審。不同快照、題組或判分定義的分數不可直接比較，也不能將這些觀察視為對未見查詢的保證。完整方法、逐題結果及證據見 [Gemini 比較報告](../experiments/gemini-embedding-2/比較報告.md) 和 [重算說明](../experiments/gemini-embedding-2/README.md)。

## 開發過程與心得素材

詳見 DEVLOG.md 的歷史紀錄與新增 v8 章。可討論：先分清 seed 與 query；爬蟲中斷後可續跑；高 P@5 可能來自太寬鬆的尺；功能疊加會互相抵消；回到課堂公式後發現重複詞頻落差；用位置索引換取片語速度並承認記憶體代價。

## 組員仍需完成

- 真實分工、組別、姓名與每人個別心得。
- 題目／資訊需求確認、獨立全文標註與分歧仲裁。
- 依正常產品入口完成 3–5 分鐘全組彩排；老師提問時能自己解釋程式與小例子。
- 使用者檢視本輪改動並明確驗收；任何 Git 上傳另行取得同意。
