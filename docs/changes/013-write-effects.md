# 013 覆寫、刪檔與站外附加

從 `527a346` 繼續，分支 `codex/ir-course-upgrade`，本輪核對的 origin/main 為 `9c7c3a1`。引用 TP §6、U2、U3、GTFO-SCHEMA、GTFO-EFFECT、BASH-REDIR、WRITE-TOOLS、EXT-APPEND。 [引用資料](../references.md)

- 原七站快照已有覆寫例子，缺效果排序。在站外快照未核對到同一例子有 sudo 和附加。補收三篇形成獨立 986 頁快照。僅補收或只排除來源，三篇仍排在前五外。
- `build_write_effects.py` 產出 27 筆原文證據。`write_effects.py` 拆開效果判定和來源排除。`search.py` 增加 `--write-effects`，對明確限制先篩站點，再依同例效果與權限排序。
- 兩題已知 P@5 分別從 0.20 到 1.00、0.00 到 0.60。12 道新題由 0.1833 到 0.6333，8 進步、4 持平、0 下降。比較來源和站外 SUID 附加仍為 0。四道站外新題命中相同三份文件。
- 最後一次暖查詢中位數 2.56 → 2.98 ms，p95 6.06 → 7.11 ms。前兩次樣本及較高延遲也保存在驗證檔。
- 116 組 LM 判定，複核修正 check_log 一筆。初判、複核及原始證據均已保存。Codex CLI 日誌有既有狀態查找回退，七批判定皆驗證。使用者尚未驗收。
- 審查修正來源排除與混合語境，以及 Python 版本的重建差異。584 次舊搜尋、818 份舊資料、140 列本輪結果核對通過。

[方法與詳細結果](../../report/GTFO_WRITE_EFFECTS_V8_6.md) · [驗證與計時](evidence/v8.6-diagnosis-and-verification.json)
