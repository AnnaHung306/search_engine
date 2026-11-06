# v8.1 進度：已完成的獨立工作與人工交接

本輪按照使用者確認的順序：真實採集 → 相同結果的效能優化 → 診斷與人工待辦。沒有製作 PPT、沒有 push／部署，尚未經使用者驗收。

## 已完成

1. 七站新快照完整跑完：980 個唯一有效頁、1,027 實際 HTTP requests；至少兩秒逐站間隔，robots 拒絕的十個網址未送出內容請求。485 頁取得來源 meta description。原 980 頁快照保留。
2. 新快照建立索引並重新讀取，全部文件 TF／L2 norm 與 1,348,436 個 literal offsets 驗證；九設定 × 十題流程檢查，並使用正常 Flask 表單、解釋、全文與評估導覽。
3. 在原固定資料上做無損效能優化：索引檔 47.9→9.8 MB、初載約 450→313 ms、sql 暖機完整搜尋約 2.90→0.46 ms。條件、冷查詢、p95、九模型與中間退步見 007；這些數字不含 Flask／網路，不代表搜尋相關性提高。
4. 414 次固定搜尋的結果、分數、摘要及解釋完全一致；原六組歷史排名不變。摘要 2,000 隨機對照一致，原 offsets 1,344,488 筆無損。
5. 準備描述性實驗、兩個弱查詢分析草稿與必做十題／50 筆精簡盲評包。所有 reviewer 欄位仍空白，新正式 P@5 未產生。
6. 修掉本輪發現的歷史輸出覆寫、壞 manifest 的 500、不同資料集誤用評估及函式層 holdout 限制問題；兩軸審查問題均處理。

## 需要人工的集中入口

見 [HUMAN_HANDOFF.md](../docs/HUMAN_HANDOFF.md)：先確認資訊需求／相關性規則，再做各 50 筆的獨立判斷與分歧處理；其後視時間擴充模型比較。另需真實分工、個人心得、全組彩排與使用者驗收。

`decompile android apk` 與 Frida、SQLi library／SIP 工具是否滿足需求，原規則有邊界需要先討論。這些決定尚未寫回 frozen suite，不能看完分數才改尺。

## 尚未能下的結論

- 不宣稱 field／proximity 或新 description 已提升 P@5。
- 新舊快照有十個 URL 替換與二十四個共同正文變更，不能混用標籤或比較品質歸因。
- 原十題曾用於開發；新的 holdout 只做相等性回歸，沒有用來調參或挑模型。
- 工程與量測完成不代表組員已參與、報告已獲教授接受或使用者已驗收。

## 引用與可查結果

- [006 真實流程](../docs/changes/006-live-pipeline.md)：TP §2–6、U2、U4。
- [007 效能與退步](../docs/changes/007-lossless-performance.md)：U1／U4、VAR／PY 工程延伸，含全部量測邊界。
- [008 診斷與交接](../docs/changes/008-diagnostics-and-handoff.md)：U3、TP §6–9。
- [兩個弱查詢](WEAK_QUERY_ANALYSIS_V8_1.md)、[兩軸審查](../docs/changes/REVIEW.md)。
- [正常介面實際畫面](../docs/changes/evidence/preview-live-v8.1.png)、[瀏覽器／HTTP 驗證](../docs/changes/evidence/v8.1-browser-and-http.json)。
- 完整來源連結／PDF 頁碼：[references.md](../docs/references.md)。
