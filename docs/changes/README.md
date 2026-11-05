# 每批更新：引用、修改與成效

使用者於 2026-11-05 要求每次更新都記錄引用了哪裡、改了哪裡、進步了哪裡。此處同時記錄沒有提升與仍待驗證的部分；通過檢查不等於使用者驗收。

| 批次 | 引用 | 改動與狀態 |
|---|---|---|
| [001 正確性](001-correctness.md) | TP §2–6、U2 p.22–31、U4 p.15–39、REP／HTTP／ROB | 查詢 TF、逐跳爬取限制、明確依賴與缺標停止 |
| [002 位置與排序](002-positional-ranking.md) | U1 p.43–48、U4 p.25–39、TP §9 | 位置索引、欄位／鄰近度實驗、速度與大小取捨 |
| [003 評估](003-evaluation.md) | TP §6、U3 p.9、29–36 | 凍結查詢、盲評包、雙人判斷、仲裁、kappa；品質成績待人工 |
| [004 正常介面與報告](004-product-and-report.md) | TP §4／7、U3 p.37–38、U4 p.15–39 | 正常入口、明示實驗模式、計分解釋、全文／評估導覽及 v8 報告 |
| [005 審查修正與最終量測](005-review-fixes.md) | TP §2–6、U1／U2／U3／U4、HTTP | dot segments、中斷恢復、標點／offsets、真實描述、過期成績、各排序分母與最終代價 |
| [006 真實採集全流程](006-live-pipeline.md) | TP §2–6、U2 p.14–31、U4 p.15–39 | 七站新快照 980 頁、1,027 請求、485 頁真實描述、獨立索引與正常入口 |
| [007 無損效能優化](007-lossless-performance.md) | U1 p.43–48、U4 p.15–39、VAR／PY | schema 4 壓縮／有界快取／共享公式；47.9→9.8 MB；冷熱、九模型及中間退步均保留 |
| [008 診斷與人工交接](008-diagnostics-and-handoff.md) | TP §6–9、U3 p.9、29–38、U4 | 兩個弱查詢、必做 50 筆盲評包、規則模糊處、保護歷史輸出與審查修正 |
| [009 模型判定與評分](009-model-assessment.md) | TP §6、U3 p.9／29–38、LLM | 654 組配對模型判定、六筆複核、九模型成績、改善與退步；不冒稱人工 |
| [010 來源與原生模組查詢](010-query-intent.md) | TP §6、U3／U4、ZONE／QE、GTFO／FRIDA | 兩道已知失敗改善；16 新題 +7.5 個百分點；保留低分、複核下修與計時 |
| [011 GTFOBins 功能與情境](011-gtfo-function-context.md) | TP §6、U3／U4、GTFO-SCHEMA／GTFO-EFFECT | 341 組可查證證據；16 新題 +26.25 個百分點；同站失敗與副作用分開量測 |
| [012 GTFOBins 附加寫入](012-gtfo-append.md) | TP §6、U3、GTFO-APPEND／BASH-REDIR | 分開測量補收與排序，12 題 P@5 +8.33 個百分點 |
| [013 覆寫、刪檔與站外附加](013-write-effects.md) | TP §6、U2／U3、GTFO-EFFECT／WRITE-TOOLS／EXT-APPEND | 效果與來源獨立，12 道新題 P@5 +45 個百分點 |

來源的可查證連結見 [references.md](../references.md)。效能原始量測保留於 [evidence/latency-comparison.json](evidence/latency-comparison.json)。最終驗證、審查與待辦寫入 evidence/verification-summary.json；後續更新新增一批，不覆蓋前批結果。
