# 008：描述性實驗、人工待辦與審查修正

日期：2026-11-05。引用：TP p.3 §6、p.4 §7–9；U3 p.9、29–38、U4 p.25–39。

## 改了什麼

- diagnostics.py：固定 course/development，輸出九種既有設定的 top-five 重疊、文件 token 長度與 host 分布；函式入口及 CLI 都拒絕 holdout。沒有新增品質分數或調整排序參數。
- evaluate.py／evaluation.py：明示 `--dump --systems tfidf` 可匯出 baseline-only 材料，預設九模型不變。既有資料夾拒絕覆寫。
- 新增 data/evaluation/v8.1/course-required/：十題、50 組全文、兩份空白 reviewer CSV，獨立 manifest 與 runs。原九模型 course 134 組、development 164 組、holdout 356 組原封不動。
- docs/HUMAN_HANDOFF.md：集中列需要組員本人確認的資訊需求／規則、人工標註、分歧、真實分工、心得與操作驗收。特別指出 decompile/APK 與 Frida 的舊規則邊界，以及 SQLi library／SIP 工具的判斷範圍，尚未擅改 frozen suite。
- report/WEAK_QUERY_ANALYSIS_V8_1.md：sql injection tool、wifi password cracking 的具體排名與全文依據。是助手診斷，沒有填成人工標籤。
- run_experiments.py：移除 import 寫入副作用及固定覆寫歷史 JSON 的行為，改為新輸出目錄、非空拒絕與 exclusive create，補上來源 hash。
- load_manifest()：集中驗證 JSON 結構；評估頁／計分共用，壞紀錄顯示 stale。active collection 不同則顯示 different_collection，隱藏舊成績。
- .gitattributes：明確保留 CSV 原 bytes（-text），允許其 CRLF 記錄終止符，仍檢查真正的尾空白／空行／space-before-tab。提交檢查因此不誤報標準 CSV 換行，也不修改已凍結材料的 SHA。

## 改善多少與尚未證實

必做標註的第一階段為每位 reviewer 50 筆，原九模型比較為 134 筆。這是先縮小到必做 baseline 的工作範圍，不能宣稱完成同樣九模型比較卻減少標註。50 組皆可在原 134 組以 pair_id 對照；未產生任何人工答案。

開發十二題的結果文件 token 中位數：cosine 258.5、pivot 788、BM25 683、field+proximity 460；proximity 與 baseline 的平均 Jaccard 0.9246，field+proximity 0.2543。數字描述選到不同文件，不能證明相關性改善。舊六組 Hark 標籤成績仍可重現且排名不變，身份仍是歷史助手參考。

## 審查與根因修正

Standards 找出公開 analyze() 可繞過 CLI 的 holdout 限制，已在入口拒絕並證明未讀取保留題。Spec 找出有效 JSON 但錯誤結構的 manifest 會讓頁面 500，已集中驗證；list、缺欄位、負 pool、bool pool、null 五種皆在記憶體內確認 HTTP 200 與 stale。兩軸複查均無剩餘 material finding，完整紀錄見 REVIEW.md。

所有新 reviewer 表保持空白，缺標時正式計分明確停止。這輪不製作 PPT、不 push、不部署，沒有新 fallback。三個上一輪 Ruff cache 檔因未獲刪除同意而保留；本輪測試未落盤 fixture 或臨時腳本。
