# 001：計分與爬蟲正確性

日期 2026-11-05；狀態：實作及聚焦檢查完成，待使用者驗收。

## 引用

- U4 p.15、18、21、25–39；TP p.2 §3–5：log TF、collection IDF、向量與 cosine。
- U2 p.22–31；TP p.1 §2：robots、每 host 延遲、範圍含轉址、attempt budget。
- REP §2.3.1、HTTP §4.2.3／10.2.3、ROB Usage：robots 狀態／規則、scheme 預設埠、Retry-After。
- TP p.3 §6：有結果但未標註不能被當成已確認不相關。

完整連結見 ../references.md。

## 改了哪裡

- code/weighting.py、search.py、indexer.py、toy_example.py：共用 log TF／向量規則，保留重複查詢詞頻。
- code/crawl_urls.py：scheme 正確的預設埠、fragment、query、public URL 與 scope。
- code/crawl_http.py：每跳先驗限制；robots／轉址／網路失敗共用 budget、時間戳與限速；暫時失敗暫停 host；秒數／日期型 Retry-After。
- code/crawler.py：只在獨立 crawl 目錄輸出、保留 checkpoint；不覆蓋原評估資料。統計區分實際 HTTP 與考慮的 URL。
- requirements.txt、fuzzy.py：明確依賴與 fail-fast，移除 pypinyin 載入失敗後靜默停用。
- evaluation.py／evaluate.py：正式缺標停止；歷史助手標註另走 legacy reproduction。

## 改前、改後與驗證

- `sql sql sql injection tool` 第一名：舊程式 0.1834，依報告應 0.1755；新版為 0.1755，與獨立重算吻合。
- 原六組十題排名不變，P@5 仍為 0.46／0.72／0.84／0.80／0.80／0.74；正確性修正沒有被寫成品質分數增加。
- 受控回應檢查：500／429／timeout 不發內容請求；robots 禁止路徑不發請求；越界轉址不送出；同 host robots→內容遵守測試設定的 5 秒；跨站轉址含兩站 robots 共四次請求。
- 非預設 `http:443` 不再被移除；Retry-After HTTP 日期可解析，異常值有明確 unknown 紀錄，仍暫停 host。
- 改用鎖版 Protego 解析 robots 規則，避免所用 Python 標準庫對小數 Crawl-delay 的落差（2.5 被解析為 None；Protego 為 2.5）；下載／轉址／限速不交給 parser。

## 影響與限制

移除了 robots fail-open 及 pypinyin 靜默降級。沒有新增程式 fallback。404／410 的「robots 不存在」是明確記錄的正常協定分支，不等同網路失敗放行。新爬蟲的 count 口徑不同於 v7.1；未重爬七站，不回寫歷史數字來假裝已驗證。
