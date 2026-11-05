# 006：新爬蟲真實採集與獨立快照

日期：2026-11-05。引用：TP p.1 §2、p.2 §3–5、p.3 §6；U2 p.14–31、U4 p.15–39。來源連結見 ../references.md。

## 原本的缺口

v8 已有受控請求檢查與一次 Nmap 讀取，尚未證明新爬蟲可跑完整七站流程。原 980 頁沒有獨立 description metadata，不能把新欄位的存在寫成已驗證其品質。

## 實際執行與改動

- 沿用原 8 seeds、7 hosts、scope、額度與每 host 至少兩秒；crawler／request gate／URL／config 的執行來源均核對為 commit 5d1da8f，沒有為了湊頁數調整限制。
- 正常 crawler CLI 寫入 data/crawls/v8-live-20261105/，保留 pages、checkpoint、逐請求 log、summary 與 run_manifest。原研究快照完全保留。
- 以正常 indexer 建立該快照的 schema-4 索引，再以 IR_INDEX_PATH 明確選取它，從原 Flask 首頁、表單、解釋、全文與評估導覽操作。
- 搜尋可明確選另一份真實索引；不同 collection 的評估會顯示不同資料集、隱藏舊成績，避免同為 980 頁就誤認相同。

## 結果與改善

| 項目 | 本次結果 |
|---|---:|
| 有效／唯一 URL／唯一正文 | 各 980 |
| 實際 HTTP requests | 1,027（robots 7、content／轉址各跳 1,020） |
| summary 定義的 HTTP／網路失敗 | 0 |
| robots 拒絕而未送出內容請求 | 10 |
| 七站的最短完成至下一請求間隔 | 全部至少 2.000 秒 |
| 真實 meta description | 485 / 980（49.5%） |
| 新索引 | 58,403 terms；9,881,135 bytes |
| 新快照逐筆驗證 literal occurrences | 1,348,436 |

逐站頁數：Kali 430、Nmap 150、Metasploit 150、Wireshark 80、mitmproxy 30、Frida 40、GTFOBins 100。mitmproxy 可用 frontier 為 30 頁，因此總數為 980；沒有放寬 scope 補到 1,000。31 個薄頁、1 個非 HTML、4 個重複 URL 也明確記錄。GTFOBins robots 的 404 是明確不存在，依既有協定分支處理，未把網路錯誤當作允許。

改善是補齊真實全流程證據、請求計數與來源 metadata，並完成新資料的全部文件 counts／L2 norm 重算、九組設定 × 十題搜尋及逐詞解釋加總。這不是搜尋相關性的提升證明。

## 變動、限制與退步

- 舊、新快照各有 980 頁，但只有 970 個共同 URL；各有 10 個不同 URL，24 個共同 URL 的正文也變了。不能把其差異歸因於排序改進。
- 495 頁仍沒有 description，保留空白。原始正文最大 1,229,908 字元；沒有偷偷截斷後當作完整內容。
- 平均正文 8,800.3 字元，原固定檔重算為 8,908.9；平均更短不代表品質較好。
- 沒有對新資料套用舊標籤或填新 P@5；source／robots 是採集當時的狀態，未來重爬不保證一樣。
- 本輪沒有新增 fallback；資料與索引均保留為正式可追溯成果。

證據：evidence/v8.1-live-crawl-audit.json、evidence/v8.1-live-pipeline.json；完整原始 log／manifest 位於上述快照目錄。
