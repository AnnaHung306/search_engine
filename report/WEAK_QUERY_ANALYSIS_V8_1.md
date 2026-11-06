# 弱查詢分析 v8.1：待組員核對的診斷草稿

依據 TP p.3 §6、U3 p.9、29–38 與 U4 p.25–39。資料固定為原 980 頁；新爬取快照不混入比較。結果來源：docs/changes/evidence/v8.1-course-diagnostics.json；各系統的計算方式未因本輪效能優化而改變。

這裡沒有新增人工 0/1、P@5 或「最佳模型」結論。排名變動、文件長度與命中詞是可重算觀察，相關性結論由組員按資訊需求、全文與預先確認的規則判定。

## 案例一：sql injection tool

資訊需求：尋找可用來發現／利用 SQL injection 的工具。

| 設定 | 可重現觀察 | 需釐清的問題 |
|---|---|---|
| 純 cosine | 第一名 siparmyknife 63 個索引 token；sqlmap 未進前五 | 短文件的正規化較有利；siparmyknife 正文確實說會 fuzz SQL injection，不能只因名稱含 SIP 就直接判不相關 |
| pivot / BM25 | sqlmap 均第一，接著 jsql | 排名更接近工具名稱，但仍需人工全文確認，不能據此填成正式品質提升 |
| field + proximity | SQL Injection library 第一；cmd injection module 第二；ReflectiveDLL Injection 第三 | 標題與局部詞距可能放大 injection，後兩項缺 sql/tool；需要區分開發 library 與使用者要找的操作工具 |

原文證據在固定索引中：siparmyknife 說明是 SIP fuzzing tool，並明列 SQL injection；Metasploit 的 SQL Injection 頁則在講 library、include Msf::Exploit::SQLi 與 create_sqli。這些不同內容也揭露原規則的邊界需要事先確認。

推測根因：完整 L2 正規化、較短文件、標題詞權重與資訊需求不完全一致。可比較方向：以既有 pivot/BM25 和單項開關做消融；在 development 上研究後再定案。不要為這一題硬編工具白名單，也不因它的排名重新挑 holdout。

## 案例二：wifi password cracking

資訊需求：尋找 Wi-Fi WEP/WPA 密碼或握手相關工具。

| 設定 | 前五中的可重現現象 |
|---|---|
| 純 cosine | 第三 sipcrack（缺 wifi）、第四 johnny（缺 wifi）、第五 sucrack（缺 wifi） |
| pivot | 前五改為 wifi-honey、fern-wifi-cracker、reaver、kismet、john |
| BM25 | 前五為 fern-wifi-cracker、seclists、wifi-honey、reaver、john |
| field + proximity | 第一是 Hashes and Password Cracking（缺 wifi）；詞距／標題沒有自動保證 Wi-Fi 情境 |

全文可確認 sipcrack 在處理 SIP digest authentication；sucrack 在處理本機 Linux/UNIX su 帳號。它們會命中 password/crack，但情境與資訊需求不同。另一方面，部分 Wi-Fi 文件未出現字面的 password，不能因少一個詞就一律排除；john/kismet 是否包含指定 Wi-Fi 工作流程也必須看全文。

推測根因：聯集候選容許部分詞命中；純詞彙方法沒有完整表達 Wi-Fi 情境；coverage 優先及同義詞擴展也可能把字多但目的不同的頁面推高。

可比較方向：固定同一批文件，分別觀察 normalization、coverage、query expansion 的單項影響，列出新增／移除結果的人工理由。先用 development 確認方法，再用保留題檢驗。

## 描述性整體觀察

十二題 development 的前五結果，文件 token 數中位數：cosine 258.5、pivot 788、BM25 683、field+proximity 460。這證明方法選到的文件長度分布不同，不能證明較長文件比較相關。

同組 development 上 proximity 與 baseline 的平均 top-five Jaccard 為 0.9246；field+proximity 為 0.2543。前者多數結果相近，後者變動大；變動大也不等於改善大。全部新模型仍等待人工評估。
