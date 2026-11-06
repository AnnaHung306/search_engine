# 專案工作規則

## 工作原則

- Git 上傳或 git push 前，必須取得使用者明確同意。
- 優先採好維護、職責清楚的結構，修正根因；新增或使用 fallback 必須說明原因與影響。
- 新 branch／worktree 前先執行 git fetch origin main，從剛更新的 origin/main 建立。
- 修改或預覽前回報 checkout 路徑、分支與基底 commit；既有未提交工作必須保留，另建獨立 worktree。
- 正常產品預覽必須用完整應用入口、路由、導覽與真實資料流程；不得以 demo、mock、假權限、空函式或記憶體儲存代替整合驗證。
- 發現問題納入同輪處理；不影響外觀及既有方法的修正直接完成。影響美觀、方法或流程的改動先取得具體確認，並繼續其他不受影響的工作。
- 修正後說明原因、改動與驗證，提供可查看結果；使用者確認前不得自行視為驗收。
- 測試完成後清理臨時產物；刪除前列出具體檔案及範圍。若要保留永久測試而與使用者清理規則衝突，先確認。
- 有關過往專案、設定與偏好先查 memwal_recall。記憶寫入依當前使用者授權與上層記憶規則，不保存敏感／一次性資料。

## 每次更新的引用與成效紀錄

使用者於 2026-11-05 確認：每次更新、每次進步，都要寫引用了哪裡、進步了哪裡、改了哪裡。

每個完成的改動批次在 docs/changes/ 記錄：

1. 引用資料 ID、講義頁碼／規格章節與可查證連結。
2. 改動前的問題與根因。
3. 修改檔案、方法與理由。
4. 固定資料／設定下的改前、改後結果與驗證方法。
5. 尚未證實的效果、退步、人工待辦與限制。不可把修正完成寫成已獲使用者驗收。

## 正式前端部署

- 部署前 audit build asset size，尤其 JS chunk、圖片、影片。
- source、concept、AI 原始素材不可混入 public／dist。
- Hashed JS／CSS／assets 應 gzip 或 brotli 並 long immutable cache；HTML／API／auth callback／socket 不可 long cache。
- 大型固定 MP4、重圖與公開媒體優先 R2／CDN；需 live curl、header、timing 驗證。
- 本專題目前僅本機執行；未授權公開部署。

## 圖片管理

- AI 候選圖先存 work/generated-images/<日期或任務>/，列編號、檔名與預覽供使用者選擇。
- 未收到保留編號與「其餘刪除」前不得刪除。選定後才移正式輸出，刪除前列完整檔案清單。
- 不刪原始／參考／已交付／其他任務圖片；來源不明保留並詢問。
- 回報保留、刪除、待決定圖片及位置；無本機檔的對話預覽／快取不得宣稱已清除。

## Agent skills

### Issue tracker

使用 Local Markdown，規格與需要持續追蹤的任務放 .scratch/<feature>/。見 docs/agents/issue-tracker.md。

### Triage labels

採預設五種 triage 狀態。見 docs/agents/triage-labels.md。

### Domain docs

Single-context。見 docs/agents/domain.md。
