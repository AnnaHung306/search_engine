# IR Lab 現場操作卡

口頭報告約 16 分鐘，接著操作 5 分鐘。使用投影片講者備註掌握每段節奏。

## 上台前

用 Chrome 開啟 [IR Lab](http://127.0.0.1:5057/)，確認搜尋頁顯示 **980**，再開 [v8.6 站外附加](http://127.0.0.1:5057/?mode=effects&variant=append&q=outside+GTFOBins+append+to+a+local+file+with+sudo) 確認顯示 **986**。兩個網址使用同一個 Flask 程式。

需要重開伺服器時，在專案根目錄執行以下命令。使用已準備的 Python 相依套件和本機索引。

```sh
uv run --offline --with-requirements requirements.txt python -B -m flask --app code/app.py run --host 127.0.0.1 --port 5057
```

| 時間 | 操作 | 觀眾看到的重點 |
|---|---|---|
| 0:00–0:35 | 開首頁，點 `SQL injection` | 980 頁課程語料，使用 TF-IDF cosine，顯示來源、摘要和名次。 |
| 0:35–1:25 | 展開第一筆的 `Why this result?`，再點 `查看索引原文` | 詞的權重與分數來源可以查，原文直接從課程索引讀出。看完按瀏覽器返回。 |
| 1:25–2:15 | 開已備好的 v8.6 站外附加分頁，停在 v8.5 對照 | 986 頁語料。指出查詢同時要求站外、sudo 和附加，先看舊排名的結果。 |
| 2:15–3:35 | 點 `切換至 v8.6 證據排序`，展開第一筆的 `查看同例證據` | 語料與查詢保持相同。先排除 GTFOBins，再提升有同例證據的結果。前三為 Debian Wiki 和兩篇 Ubuntu 文件。第一筆的原文片段可看到 `sudo tee -a`。 |
| 3:35–4:25 | 點 `評估` | 說明 P@5 是前五筆符合的比例。課程、開發、保留題分欄列出，評估頁標明語言模型判定，並可下載理由。 |
| 4:25–5:00 | 回搜尋，輸入 `zzzxxyynotfound` | 顯示沒有符合文件的正常狀態。交棒給問答。 |

作業的主要展示仍是 980 頁課程搜尋。切到 986 頁後再講來源與寫入效果對照。

[Term Project I](https://elearningv4.nuk.edu.tw/mod/assign/view.php?id=122192) · [v8.6 評估與來源](GTFO_WRITE_EFFECTS_V8_6.md)
