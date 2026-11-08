# Gemini Embedding 2 課程實驗補充

[比較報告](比較報告.md) 可以直接交給組員。這份資料沿用課程原本的 980 頁、82 個題組案例與各題判分規則，補上 Gemini Embedding 2 對原 TF-IDF 和 BM25 的實測。

| 內容 | 檔案 |
| --- | --- |
| 整體、版本及各子題組的 P@5 與勝負 | [summary.csv](tables/summary.csv) |
| 82 題的三方分數、原題需求與判分規則 | [per-case.csv](tables/per-case.csv) |
| 三種方法的前五名、檢索分數與相關性 | [top-five.csv](tables/top-five.csv) |
| 前五名所用的 909 筆判分、理由與原文證據 | [judgments.csv](tables/judgments.csv) |
| 310 筆補標及其來源 | [supplemental-judgments.csv](tables/supplemental-judgments.csv) |
| 模型、索引、題組與交付檔案的校驗資料 | [manifest.json](data/manifest.json) |
| 實驗向量及文件與查詢對照 | [vectors.sqlite](data/vectors.sqlite)、[embedding-map.json.gz](data/embedding-map.json.gz) |
| 分段、Gemini 排序、P@5 重算與選用的 API 取向量程式 | [code/](code/) |

CSV 採 UTF-8 BOM。可用 Excel、Numbers 或試算表軟體開啟。以 `benchmark`、`query_id`、`url` 從前五名表對照判分表。檢索分數用於各方法內排序，跨方法比較使用 P@5。

部分原文引句以命令列旗標開頭。CSV 在這些欄位前加單引號供試算表當成文字處理，查對原文時可略去這個前綴。

## 離線重算

使用 Python 3.12 以上，在解壓後的資料夾執行。只用 Python 標準函式庫。

```bash
python3 -B code/reproduce.py
```

程式從 2,187 筆已保存向量重算 Gemini 排名，逐題核對前五名和分數，再用凍結的 TF-IDF、BM25 排名及交付的判分重算三方 P@5。預期總數為 TF-IDF 136/410、BM25 206/410、Gemini 260/410。

課程原索引已隨原專案交付。若要核對原文分段及每個向量輸入，傳入原本的 `data/index-v8.1.json.gz`。

```bash
python3 -B code/reproduce.py --index "/path/to/search_engine/data/index-v8.1.json.gz"
```

若也要重新跑 TF-IDF 和 BM25，請在已安裝課程專案相依套件的 Python 環境傳入原課程資料夾。程式會透過原搜尋入口執行兩種基線，核對前五名。

```bash
python3 -B code/reproduce.py --course-repo "/path/to/search_engine"
```

## 選用的 API 取向量

[regenerate_embeddings.py](code/regenerate_embeddings.py) 可用相同的文件分段、文字格式與 768 維設定向 Gemini API 取得一份新向量。使用前在自己的 Python 環境安裝 [requirements-api.txt](code/requirements-api.txt) 中的相依套件，並準備原索引與自己的 API 金鑰。API 請求受所用專案的配額與計費設定影響。程式逐批寫入另指定的 SQLite 路徑，可用同一路徑續跑。

```bash
python3 -B code/regenerate_embeddings.py \
  --index "/path/to/search_engine/data/index-v8.1.json.gz" \
  --output "../gemini-embedding-2-new.sqlite"
```

報告分數以隨包交付的歷史向量及判分重算。
