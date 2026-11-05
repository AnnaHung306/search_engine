# v8.6 覆寫、附加、刪檔與來源限制

## 根因

**GTFOBins 的 sudo 覆寫有資料，舊排序缺少效果判定。** 原 980 頁已有 Bash、ash、csh、cp、aria2c 等例子。舊排名靠「write」「sudo」和來源，已知題前五只有 aria2c 達到覆寫條件。check_log 只證明能指定輸出，c89 等條目雖列在 File write，正文卻明示會刪除目標檔。v8.5 補收的 tee 也有兩種效果，預設覆寫，`-a` 才附加。 [GTFOBins check_log](https://gtfobins.org/gtfobins/check_log/#file-write) · [GTFOBins c89](https://gtfobins.org/gtfobins/c89/#file-write) · [GNU Bash 手冊](https://www.gnu.org/s/bash/manual/html_node/Redirections.html) · [GNU tee 手冊](https://www.gnu.org/s/coreutils/manual/html_node/tee-invocation.html)

**非 GTFOBins 的 sudo 附加同時缺文件和排序訊號。** 在原 980 頁的 880 篇站外文件中，候選掃描找不到 `sudo tee`，也找不到鄰近 sudo 的 `>>` 或 `--append`。兩個 `tee -a` 命中都在 Kali Faraday，實際寫入端未套 sudo。這是本次可驗證的文件缺口，掃描範圍與條件保存在驗證檔。舊版把「GTFOBins alternatives」視為停用來源優先，983 頁快照上的前五仍有四篇來自 GTFOBins。 [Kali Faraday](https://www.kali.org/tools/faraday/) · [原排名及掃描記錄](../docs/changes/evidence/v8.6-diagnosis-and-verification.json)

## 實作

1. 從 Ubuntu 官方文件及 Debian Wiki 定向補收三頁。每頁都有套在實際寫入端的 sudo，以及保留既有內容的 `tee -a`。共 5 次 HTTP 請求，包含兩次 robots，全部 200。採集使用既有逐站限速和 robots 檢查。986 頁、九站是獨立實驗快照，課程比較仍可用原七站 980 頁。 [採集記錄](../data/gtfo-v8.6/capture.json) · [Ubuntu Apache2](https://documentation.ubuntu.com/security/security-features/network/version-banners/apache2/) · [Ubuntu vsftpd](https://documentation.ubuntu.com/security/security-features/network/version-banners/vsftpd/) · [Debian Wiki](https://wiki.debian.org/BootstrapBootableSystem) · [Unit 2](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121177)
2. 建立 27 筆效果與權限證據。18 筆覆寫分屬 sudo、SUID、一般權限，每種各六筆。六筆刪檔為三個正式別名各在 sudo／一般權限。三筆站外附加全部是 sudo。保留 v8.5 的九筆 GTFOBins 附加情境。證據連到原文位置和手冊。覆寫範例的語義包含 shell 預設重導向、tee 或 cp 的既有檔案處理、aria2c 明示的覆寫選項。實際可用性依版本、檔案權限、shell 的 noclobber 或下載選項而異。 [效果證據](../data/gtfo-v8.6/effects.json) · [引用清單](../docs/references.md)
3. 在 `--write-effects` 模式辨識寫入效果與權限，將同例證據排在一般文字命中前。明確排除 GTFOBins 時，先依 URL host 移除本站和子網域。這項限制獨立於附加、覆寫或刪檔。混合來源、否定排除及混合操作都有守門。字面片語和 Boolean 條件仍由原解析器套用。 [查詢辨識](../code/write_effects.py) · [搜尋入口](../code/search.py)

## 評估

沿用 Term Project I §6 和 Unit 3 p.9、29–38 的資訊需求與 P@5。每題前五固定為分母。兩個版本在同一份 986 頁索引上比較。兩個已知失敗另外列出，12 道新題與判定規則在檢索前固定。7 批模型用 45 份文件、116 組題目與文件配對做全文分段判定。兩版共用標籤。助理依手冊及凍結正文複核，把已知覆寫題的 check_log 從 1 改為 0。v8.5 在 986 頁的該題因此從初判 0.40 下修到 0.20。初判、原始回覆、證據和複核皆留存。判定來源為 LM。 [Term Project I](https://elearningv4.nuk.edu.tw/mod/assign/view.php?id=122192) · [Unit 3](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121734) · [題組](../data/benchmarks/write-effects-v8.6.json) · [複核](../data/evaluation/v8.6-effects/review.json) · [終判成績](../data/evaluation/v8.6-effects/scores.json)

| 已知題 | v8.5／983 頁 | v8.5／986 頁 | v8.6／986 頁 |
|---|---:|---:|---:|
| GTFOBins sudo 覆寫 | 0.20 | 0.20 | 1.00 |
| 非 GTFOBins sudo 附加 | 0.00 | 0.00 | 0.60 |

三篇站外文件在補收後仍落在前五之外。用同一份 986 頁索引關掉效果排序，單看來源排除，可分辨篩選與證據重排各做了什麼。 [消融排名](../docs/changes/evidence/v8.6-diagnosis-and-verification.json)

| 文件 | 舊排序 | 只排除 GTFOBins | 排除並依效果證據排序 |
|---|---:|---:|---:|
| Debian hosts | 26 | 22 | 1 |
| Ubuntu vsftpd | 347 | 245 | 2 |
| Ubuntu Apache2 | 549 | 447 | 3 |

| 新題 | 題數 | v8.5／986 頁 | v8.6／986 頁 | 差值 |
|---|---:|---:|---:|---:|
| 覆寫（sudo、SUID、一般權限） | 4 | 0.2500 | 1.0000 | +0.7500 |
| 站外 sudo 附加 | 4 | 0.0000 | 0.6000 | +0.6000 |
| 對照題 | 4 | 0.3000 | 0.3000 | 0 |
| 全部新題 | 12 | 0.1833 | 0.6333 | +0.4500 |

新題 8 題進步、4 題持平、0 題下降。刪檔與 GTFOBins 附加對照題各維持 0.60。比較 Ubuntu 與 GTFOBins 的題仍為 0.00，兩個來源可出現，但本輪未對跨站比較做證據重排。站外 SUID 附加也為 0.00，已套用來源排除，三篇新增文件只支持 sudo。站外正例都用 tee，衡量的是文件命中，工具多樣性尚未驗證。覆寫證據清單也有範圍限制。例如 cpio 的 `-u` 由官方手冊證實可在 copy-pass 覆寫，SUID 新題已判相關，但本輪證據清單是在評分前固定，這筆僅有原文字排名。 [各組逐題分數](../data/evaluation/v8.6-effects/) · [GTFOBins cpio](https://gtfobins.org/gtfobins/cpio/#file-write) · [GNU cpio 手冊](https://www.gnu.org/software/cpio/manual/html_node/Options.html)

## 重現與限制

584 次歷史搜尋的分數、名次、摘要及解釋相符，818 份已追蹤的舊資料逐檔一致。本輪 140 列凍結排名在審查修正後也重現。重建改用穩定浮點加總，Python 3.11、3.12、3.13 均產出相同 gzip。建置器在建立輸出目錄前會檢查集合及三份成品雜湊。 [驗證檔](../docs/changes/evidence/v8.6-diagnosis-and-verification.json) · [審查紀錄](../docs/changes/REVIEW.md)

暖機後對 14 題交錯重複各 30 次，每次取前十筆，計時包含摘要，排除載入索引。最後一次量測的中位數由 2.56 增至 2.98 ms，p95 由 6.06 增至 7.11 ms。前兩次量測也較慢，中位數分別由 2.74 增至 3.28 ms、8.90 增至 11.38 ms，p95 分別由 6.31 增至 7.39 ms、20.43 增至 31.19 ms。各次樣本都保留。 [原始計時](../docs/changes/evidence/v8.6-diagnosis-and-verification.json)

Codex CLI 的既有狀態資料庫查找遇到不一致，日誌記錄回退查找。七批模型回覆均通過結構、證據與雜湊驗證。搜尋按指定快照和證據執行，證據不足時保留較低層的文字命中，`matched_documents` 回報符合證據的數量。 [原始執行記錄](../data/evaluation/v8.6-effects/raw/)

```sh
IR_INDEX_PATH=data/gtfo-v8.6/index.json.gz python -B code/search.py --bm25 --write-effects 'GTFOBins sudo overwrite a local file'
IR_INDEX_PATH=data/gtfo-v8.6/index.json.gz python -B code/search.py --bm25 --write-effects 'outside GTFOBins append to a local file with sudo'
IR_INDEX_PATH=data/gtfo-v8.6/index.json.gz python -B code/write_effects_evaluation.py score --adjudications data/evaluation/v8.6-effects/review.json
```
