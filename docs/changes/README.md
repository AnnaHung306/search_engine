# 每批更新：引用、修改與成效

使用者於 2026-11-05 要求每次更新都記錄引用了哪裡、改了哪裡、進步了哪裡。此處同時記錄沒有提升與仍待驗證的部分；通過檢查不等於使用者驗收。

| 批次 | 引用 | 改動與狀態 |
|---|---|---|
| [001 正確性](001-correctness.md) | TP §2–6、U2 p.22–31、U4 p.15–39、REP／HTTP／ROB | 查詢 TF、逐跳爬取限制、明確依賴與缺標停止 |
| [002 位置與排序](002-positional-ranking.md) | U1 p.43–48、U4 p.25–39、TP §9 | 位置索引、欄位／鄰近度實驗、速度與大小取捨 |
| [003 評估](003-evaluation.md) | TP §6、U3 p.9、29–36 | 凍結查詢、盲評包、雙人判斷、仲裁、kappa；品質成績待人工 |
| [004 正常介面與報告](004-product-and-report.md) | TP §4／7、U3 p.37–38、U4 p.15–39 | 正常入口、明示實驗模式、計分解釋、全文／評估導覽及 v8 報告 |
| [005 審查修正與最終量測](005-review-fixes.md) | TP §2–6、U1／U2／U3／U4、HTTP | dot segments、中斷恢復、標點／offsets、真實描述、過期成績、各排序分母與最終代價 |

來源的可查證連結見 [references.md](../references.md)。效能原始量測保留於 [evidence/latency-comparison.json](evidence/latency-comparison.json)。最終驗證、審查與待辦寫入 evidence/verification-summary.json；後續更新新增一批，不覆蓋前批結果。
