# 004：正常產品介面與報告

日期 2026-11-05；狀態：原 Flask 入口整合，瀏覽器操作檢查與使用者驗收分開記錄。

## 引用

TP p.2 §4、p.4 §7：Flask 結果／安全呈現／本機展示；U3 p.37–38：query-dependent summary；U4 p.15–39：計分；來源見 ../references.md。

## 改了哪裡

- app.py、templates/、static/style.css：保留原應用，明示 Required baseline／Compare enhancements；不是另外拼裝的展示頁。
- 每筆展開 Why this result：計分表、norm、base／final score、實際 multiplier 與 coverage 排序說明。
- 正常導覽可看索引全文、評估與人工材料；新成績在人工完成前顯示 pending，不使用 mock。
- snippets.py：使用 query aliases 選取約 80 詞的完整窗口；HTML 在高亮前轉義。
- README、report/REPORT_V8.md、[v8 展示腳本](https://github.com/AnnaHung306/search_engine/blob/950576f5b3fe5dfb87cc004ba86b42d6e343ef4d/report/DEMO_SCRIPT_V8.md)、DEVLOG 的 v8 段：更新安裝／來源、日期、已證實改動與尚缺人工工作。

## 驗證與限制

Flask 應用層已檢查首頁、正常／空／OOV、片語、中文選字、欄位＋鄰近度、錯誤組合、全文／評估頁。瀏覽器由正常搜尋表單與導覽入口操作，驗證範圍及證據見 evidence/verification-summary.json。

新 UI 並未被當成使用者已認可的美觀／驗收結果。真實姓名、各人參與經歷與個人心得不能由 agent 代填。沒有公開部署或 Git 上傳。
