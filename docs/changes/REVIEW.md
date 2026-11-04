# 兩軸程式審查

固定來源：剛 fetch 的 origin/main `9c7c3a107b9712b5fc2f31d8d432a025be39f27a`。上游只有 ZIP／Word；語義差異另對照已解壓的 v7.1。為遵守 develop 的 review-before-commit，此次用 `git diff 9c7c3a1 -- code docs README.md requirements.txt` 檢查工作稿，而非先 commit 再審。兩位審查 agent 僅讀取，沒有修改或產生測試檔。

## Standards

初查四項：句尾句點破壞片語、active URL 中斷遺失、resume 遺失較長 delay、評估頁未核對凍結題目。另指出 literal matcher 重複會使修正不同步。

複查結果：四項均已修正。片語／摘要共用定義；active URL 在 finally 回填；delay 落盤／還原；畫面核對 suite、runs、全文材料及 reviewer 證據，過期成績明示 stale。

審查原結論：No remaining material Standards findings in the rechecked areas. This is a code recheck plus the stated focused checks, not a claim that the full application or user acceptance has passed.

## Spec

初查四項：dot-segment 路徑可繞過 scope、句尾句點漏片語、中斷遺失工作、offsets／description 欄位尚未完整。後續針對解釋提出 field/pivot 分母缺漏，以及 BM25 表格顯示錯誤 IDF。

複查結果：全部已修正。URL 以 prepared representation 驗證；句尾標點與中斷恢復有實測；offsets 落盤並逐筆驗證；description 只接受來源真實 metadata，明示歷史資料缺欄；所有模式顯示真正使用的分母、IDF 與 query 權重。

審查原結論：All reported Spec findings are resolved; no remaining material findings in this focused review. Human validation and acceptance remain pending as documented.

## 結案範圍

Standards 初查 4 項、Spec 初查 4 項及後續 2 項（兩軸有重疊）；已報問題均處理，所複查範圍無未解 material findings。修正與量測見 005-review-fixes.md；不把審查通過當作使用者驗收或人工標註完成。
