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

## v8.1 Standards

固定比較點 5d1da8f205d9db6e2473893dcc3925eb85281f81，使用 git diff 5d1da8f -- code 加新增 offsets.py／diagnostics.py 審查工作稿。明確範圍為使用者核可的真實採集、同結果效能優化、診斷與人工交接。

初查 codec／快取／共享計分／gzip／明示 subset 未見 material finding；補查發現 analyze() 可直接傳入 holdout，僅 CLI 限制不足。已在函式入口拒絕，複查通過。最後候選排名省略 offset 解碼、回傳解釋才補齊也通過 focused review。審查 agent 另做 1,000 組 codec round-trip 等記憶體檢查，未修改或產生檔案。

## v8.1 Spec

初查未見 material finding；補查發現合法 JSON 的錯誤 manifest 結構會讓正常評估頁 HTTP 500。已以共用 load_manifest() 驗證、保持 stale 狀態，五種壞結構由 root 與 reviewer 各自用記憶體 patch 確認；複查通過。不同 collection、保護歷史輸出及最後按需解碼也通過 focused review。

Reviewer 另對照舊版做 3,000 組隨機摘要、1,000 組 offsets、400 組 ranking maps／解釋 row 比對；未落盤測試產物。最終真實採集、正常瀏覽器與 414 次完整回歸由 root 驗證，人工相關性與使用者驗收仍未完成。

本輪 Standards 1 項、Spec 1 項，均已解決；所審範圍無剩餘 material finding。兩軸結論不等於全部未來狀況保證。

## v8.2 Standards／Spec

固定比較點 ef9e0a0e2e2873b59bc04746ab6af4eb650254a5，審查新增模型評估、共用 P@5、分類器與正常產品評估入口。依 code-review skill 使用既有兩位只讀 reviewer，未產生測試檔。

Standards 初查：逾時遺失部分輸出、摘要平均／選擇未重新驗算、錯誤 manifest 結構可能 AttributeError／500。Spec 初查：浮點加總打破真正平手、逾時證據遺失（兩軸重疊）。改為保存原始部分 bytes、重新驗算凍結 scores.csv、嚴格結構驗證與整數分子比較；兩軸 focused recheck 均無剩餘 material finding。

追加六筆明示自我複核後，兩軸再檢查：6 筆改動／648 筆不變，所有系統共用題目／URL 標籤，原標籤／policy hash／引句／llm 來源／初判與終判保存，holdout 未改動且未參與選模型。所審範圍無 material finding。審查與模型評分完成不等於使用者驗收或人工判定準確率。

## v8.3 Standards／Spec

固定比較點 `bf9455f`，依使用者授權與凍結計畫 `data/benchmarks/intent-v8.3-plan.json`，兩位 reviewer 各自唯讀審查工作稿。

**Standards**：原守門漏掉非當前狀態；共用 verify 尚未在評分及分類前綁定 plan／manifest 設定；批次 schema 欄位與檔案需要存在性一致。已補條件、檢查兩份設定並核對 schema 路徑／hash／重新推導內容。最後 focused recheck 未見剩餘重大問題。

**Spec**：排除／否定語境誤觸發；兩版計分器錯用資料目錄可能先寫出中間產物。修正後，反向詞、縮寫與未載入條件停止擴展，兩個入口均在蒐集或寫入前拒絕錯版本。指定範圍複查通過；後續 `no longer`／過往狀態同以記憶體驗證。

Root 另核對每對完整分段、兩版分數檔、初終判及 360 筆凍結排名重現；原 414 次搜尋及 460 份資料檔不變。詳細量測與負面結果見 [010](010-query-intent.md)。使用者驗收仍獨立。

## v8.4 Standards／Spec

固定比較點 `27ef47a`；兩位 reviewer 唯讀審查功能、情境、效果及 `data/benchmarks/gtfo-v8.4-plan.json`。

**Standards**：解釋中的關聯資料可能暴露可改的快取、一般 capabilities 誤當 Linux 權限、重建依賴未列。已複製回傳資料、要求明確 Linux 詞組，並用獨立 requirements 鎖定 PyYAML。前兩項 reviewer 用真實索引複查，乾淨重建依賴及資料由 root 再核對。

**Spec**：官方連字號名稱未辨識，已補後重跑 360 列；自訂複核檔案的重跑防護漏掉零修正。現在把複核路徑寫入成績摘要並檢查，實際 `review.json` 零修正仍拒絕不帶複核的重跑，且在蒐集／寫入前拒絕。

341 筆關聯用固定來源及真實索引重建，全部一致；360 筆凍結結果、486 次舊搜尋、709 份舊資料均通過。所檢查問題已修正，不等於使用者驗收。詳見 [011](011-gtfo-function-context.md)。

## v8.5 Standards／Spec

固定比較點 `78f4664`。兩位 reviewer 唯讀審查資料與凍結計畫。Standards 發現收錄檔雜湊、新目的地獨占與舊索引拒絕需補強。修正後重新核對舊、新集合，Python 3.13 在記憶體重建與兩份新成品逐位元組一致。

Spec 發現混合功能、只說保留內容及附加但不覆寫的措辭需區分。修正後，混合與保留但未寫入的查詢不提升附加頁，明確附加且不覆寫可辨識。對原 980 頁與 983 頁的凍結結果重新核對，指定範圍複查通過。詳見 [012](012-gtfo-append.md)。

## v8.6 Standards／Spec

固定比較點 `527a346`。兩軸唯讀審查發現排除與附加耦合、混合來源或操作會誤觸發，以及重建時未核對輸出雜湊。

來源排除已與操作獨立，混合語境沿用原順位，否定排除保留來源資格。複查涵蓋覆寫、刪檔、附加、只限制來源、比較來源，以及否定排除的數種說法。Spec 與 Standards 複查均通過。

Python 3.11 的 `sum` 曾產生不同的平均 norm 與 gzip。改用 `math.fsum` 後，3.11、3.12、3.13 三次重建的凍結位元組相同。建置器在建立目錄前核對成品，任一成品雜湊不符即拒絕。原查詢的 584 次結果、818 份舊資料、140 筆凍結排名均核對通過。 [本批成效](013-write-effects.md)
