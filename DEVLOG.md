# 開發紀錄與心路歷程（DEVLOG）

## 從原型到 v8.6

原型到 v7.1 的故事來自 [原始 ZIP](search-engine.zip) 內的 `DEVLOG.md`。原文收錄在下方第 1–13 節，第 14 節起接續 v8 之後的課程整合與實驗。早期分數與待辦描述的是當時版本。

1. **先搞清楚要做的東西。** 一開始分不清主題、網站、種子網址和使用者的查詢。組員提議做自主滲透 Agent，討論後把它收斂成資安文件搜尋。種子網址是爬蟲的出發點，使用者的關鍵字則在建好的資料裡搜尋。這個區分讓專題有了能說清楚、能驗證的範圍。見原紀錄第 1–2 節。
2. **先讓爬蟲跑得完，再讓資料有用。** 同站要間隔兩秒，執行環境卻會中途結束，於是加上進度存檔和續跑。Kali 頁面太多，就用各站配額和輪流爬取控制比例。正文抽取時把導覽、側欄和頁尾分開，減少索引收進的雜訊。見原紀錄第 3、10 節。
3. **做出搜尋後，第一次把排名改壞。** 早期直接給標題命中加固定分數，標題反而蓋過正文。後來試乘法權重、BM25 和同義詞，改善了一些查詢，卻也讓 `sqlmap` 從第 1 掉到第 4。當時 `P@5` 一度有 0.96，但關鍵字只要出現就容易被算成相關。v5 改按內容判斷、留下理由，純 TF-IDF 算出 0.42。前後標註標準不同，這兩個分數記錄的是評估方法的轉折。見原紀錄第 5、6、10 節。
4. **回到老師要求的 TF-IDF，把每個問題分開測。** v5 恢復純 TF-IDF cosine 為預設，BM25 保留作比較。v6 發現 Java 反編譯器 jd-gui 因頁尾廣告提到 SQL injection 而進前五，就在建索引時清掉樣板，再單獨測詞幹還原和文件長度調整。見原紀錄第 5、10 節。
5. **v7 擴到七站，v7.1 發現加強功能會互相抵銷。** mitmproxy 一度只抓到 3 頁，原因是側欄在抽連結前就被移除。改成先抽連結、再取正文後抓到 30 頁。另處理 Frida 的編碼亂碼、加入錯字與中文選字容錯，形成七站 980 頁的資料集。到了 v7.1，把導覽總表移出結果後，純 cosine 仍為 0.46。同一份早期標註下，單用 pivot 是 0.84，加上詞覆蓋優先反而是 0.80。逐項比較才看得出這個取捨。見原紀錄第 11、13 節。
6. **後來把這套方法用在更難的題目。** v8 對照 Unit 1–4，修正片語位置、爬取規則、詞頻公式和評估流程。v8.1 把索引從 47.9 MB 壓到 9.8 MB，核對結果一致。v8.2 開始用凍結題組和 LM 全文判定比較排序。v8.3–v8.6 接著分清來源、功能、權限、寫入效果，最後把「原資料沒收進來」和「收進來卻排太後面」拆開量。詳細引用與結果見 [後續更新紀錄](docs/changes/README.md)。

目前本機已完成 v8.6 實驗。交件仍要整合主報告、確認課堂採用 LM 判定的方式，並補上真實分工、個人心得與彩排。 [目前結果](report/GTFO_WRITE_EFFECTS_V8_6.md) · [交接紀錄](docs/HUMAN_HANDOFF.md)

## v7.1 原始開發紀錄

> 這份給組員寫報告用。記錄主題怎麼定、系統怎麼一步步做出來、每次改動「改了什麼、為什麼、改前長怎樣、改後長怎樣」。
> 專案：IR & GenAI Term Project I — Web Search Engine。主題：**滲透測試工具搜尋**（輸入資安問題 → 找到該用哪個 Kali / Nmap / Metasploit 工具）。

---

## 1. 主題怎麼定的（心路歷程）

一開始其實很混亂，分不清楚「主題、網站、seed URL、搜尋引擎」之間的關係。後來理清楚一件重要的事：

- **seed URL 不是使用者每次搜尋輸入的東西**，而是爬蟲的「出發點」。給一次就好，爬蟲會沿著網頁裡的連結自己往外爬。
- 這個作業做的是**縮小版的 Google**：先爬一批網頁、建好索引，之後使用者只打關鍵字，我們只在「自己爬下來的資料」裡面找。

主題選擇上，組員 Zheng 提議做「自主滲透 AI Agent / Kali 指令」。我們釐清：作業要交的是**搜尋引擎**不是攻擊工具，但把它轉成搜尋主題剛剛好——
**「使用者描述一個資安問題，搜尋引擎回傳該用哪個滲透測試工具」**。這個主題：

- 資料結構整齊（Kali 每個工具一頁），容易判斷相關性。
- 全英文，TF-IDF 這種「比對字」的方法最單純。
- 夠「酷」，demo 起來有梗。

### 選網站與驗證（為什麼是這三個站）

挑網站的標準：同主題、權威、有大量內部連結、**靜態 HTML（不靠 JavaScript 才看得到內容）**、robots.txt 沒禁止、不是 Cloudflare/CAPTCHA 擋人的站。實際測試後：

| 網站 | 結果 | 用不用 |
|---|---|---|
| `www.kali.org/tools/` + `/docs/` | robots 幾乎全開、每個工具一頁、靜態、文字量足 | ✅ 主力 |
| `nmap.org/book/` | 官方教科書，掃描技巧寫很細，robots 只擋 /search /mailman | ✅ |
| `docs.metasploit.com` | robots 全開、HTTP 200 | ✅ |
| `wiki.wireshark.org` | HTTP 403（擋爬蟲） | ❌ |
| Fandom / Bulbapedia / 部分 wiki | Cloudflare 挑戰頁 | ❌（題目禁止 CAPTCHA 頁） |

**最後 seed（8 個、3 個 host）** 見 `code/config.py`。題目只要求 5–10 個 seed URL 和列出 hostname，**沒有要求跨不同網站**——這點一度誤會，後來確認「同一個站的不同頁」也完全合規，只是我們還是多加了兩個站讓內容更豐富。

---

## 2. 系統架構（一句話版）

```
seed URLs ──> crawler.py ──> data/pages.json  {url,title,text,fetch_time}
                                   │
                              indexer.py ──> data/index.json  (倒排索引 + df/idf + 文件長度)
                                   │
          使用者查詢 ──> search.py (TF-IDF cosine / BM25 + 標題加權) ──> app.py (Flask 介面)
                                   │
                              evaluate.py ──> 10 個固定查詢的 Precision@5
```

分工模組：`config / crawler / preprocess / indexer / search / app / evaluate`，`preprocess.py` 是**文件與查詢共用的同一套前處理**（題目硬性要求一致）。

---

## 3. 爬蟲（crawler.py）做了哪些「乖乖爬」的規矩

這些都是題目明列的要求，實作時逐一對上：

- 只爬 `www.kali.org`、`nmap.org`、`docs.metasploit.com` 三個 host，且限制路徑（kali 只 `/tools/`、`/docs/`，nmap 只 `/book/`），**重導向之後也會再檢查一次是否還在範圍內**。
- 讀每個站的 **robots.txt 並遵守**（用我們自己的 User-Agent 去抓，因為某些站對預設 UA 會回 403）。
- **同一個 host 兩次請求至少間隔 2 秒**，若 robots 要求更長的 Crawl-delay 就聽它的。做法是「每個 host 一條佇列、輪流取」，讓三個站的等待時間互相重疊，不浪費時間。
- timeout 10 秒；總嘗試上限；遇到 **HTTP 429（被限流）就 backoff**，不硬重試。
- URL 正規化：相對連結轉絕對、去掉 `#fragment`、host 小寫、去預設埠；**保留 query string**（題目特別提醒 query 可能代表不同頁）。
- 去重：相同正文（MD5）只留一份；正文少於 200 字視為無效頁。
- 每一次嘗試都寫 log（成功 / 跳過+原因 / 失敗+狀態碼）到 `data/crawl_log.jsonl`，統計寫 `data/crawl_summary.json`。

> 踩雷紀錄：第一次整站爬到一半，因為執行環境有 20 分鐘上限被中斷、資料沒存到。後來加了**每 25 頁存一次 checkpoint + `--resume` 續爬**才順利跑完。這也是報告「implementation challenges」可以寫的一點。

### 爬蟲統計（改前，`data/crawl_summary.json`）

> 🔄 v7（2026-10-21）重爬為 7 站 980 頁、失敗 0，見第 11 節；下面是 v6 以前的 964 頁數字。

- 有效頁面：**964**（Kali 600、Nmap 164、Metasploit 200）
- 總嘗試（實際發出的 HTTP 請求，含失敗）：**990** = 有效 964 + 非 HTML 17 + 太短 8 + 重複正文 1
- 失敗（連線錯誤或非 200）：**0**；429 限流：0
- 平均正文長度：約 **9,813 字元**
- 未發請求就跳過：超過單站上限 1,125（不算 attempt）

---

## 4. 前處理與評分定義

**前處理（preprocess.py，文件與查詢共用）**
- 全部轉小寫。
- token = 連續英數字，允許內部含 `+ - . / #`，所以 `c++`、`802.11`、`wifi-cracking`、`example.com` 不會被拆爛。
- 複合詞**額外再拆**：`machine-learning` → 同時保留 `machine-learning`、`machine`、`learning`，避免被併成 `machinelearning`，也讓只打其中一半也搜得到。
- 小型英文停用詞表（the/of/is…），不停掉資安術語；不做字根還原（stemming），保持 demo 好解釋。
- 標題和內文一起進索引。

**TF-IDF（核心，自己實作，沒有用 TfidfVectorizer）**
- `tf(t,d) = 1 + log10(count)`
- `idf(t) = log10(N / df(t))`，N = 索引頁數
- 權重 = tf × idf；**文件與查詢用同一套 collection idf**，不會每次查詢重算。
- 排序 = 查詢向量與文件向量的 cosine 相似度。

---

## 5. 一步步改進：每個版本改了什麼、改前 vs 改後

我們用**同樣 10 個固定查詢**跑每個版本，比較前五名。每版的前五名原始結果都存在 `experiments/*.json`（v0_tfidf、v1_tfidf_title_additive、v2_bm25、v3_bm25_title_final），改版前的程式碼留在 `experiments/v0_code/`。相關性判斷用「看頁面實際內容」的關鍵字規則（報告最終版建議再人工覆核 `data/eval_results.csv`）。

| 版本 | 改了什麼 | 平均 P@5 | 平均查詢時間 |
|---|---|---|---|
| v0 | TF-IDF cosine（核心） | 0.96 | ~1 ms |
| v1 | TF-IDF + 標題加權（**加法式**，失敗） | **0.80** ⬇ | ~1 ms |
| v2 | 改用 **BM25**（k1=1.5, b=0.75） | 0.94 | ~1 ms |
| v3 | BM25 + 標題加權（乘法式） | 0.96 | ~1.5 ms |
| v4 | v3 + 同義詞擴展 + 中文關鍵字對照 | 0.98 | ~2 ms |
| **v5** | **對齊老師規格：預設改回純 TF-IDF cosine；BM25／加權／同義詞變成可切換的對照組；改用嚴格的「合併標註」重新評估** | 見第 6 節 | ~0.9 ms |
| **v6** | **專攻必做的 TF-IDF：清掉網站樣板文字 + 輕量詞幹還原（預設）；新增可切換的 pivoted length normalization；標註第二輪複查** | TF-IDF 0.42 → **0.54**；+pivot **0.68**（嚴格標註） | ~0.9 ms（pivot ~2.5 ms） |

> ⚠️ **上表 v0–v4 的 P@5 是用「寬鬆的關鍵字自動標註」算的，數字被灌水了**（例如頁面只要提到 wifi 就算相關）。v5 改用嚴格標準重新標註後，同樣的系統分數掉很多，見第 6 節。上表保留下來，是為了記錄「我們一開始的評估方法有問題」這件事本身。

> P@5 數字看起來都很高，是因為這個主題的詞彙很集中（工具頁幾乎都命中），所以 P@5 不是最有鑑別度的指標。**真正的差別在「第一名是不是最對的工具」**，看下面的例子最清楚。

### 例子 A：`sql injection tool`（BM25 的關鍵勝利）

- **改前（TF-IDF）前五名**：`siparmyknife`、`laudanum`、`sqldict`、`dbeaver`、`jd-gui`
  → 最該出現的 **sqlmap 連前五都沒有**。
- **改後（BM25）第一名**：`sqlmap`（業界最知名的 SQL injection 工具）✅
- **為什麼**：TF-IDF 的 log tf 對「長文件裡剛好多次出現某字」太敏感；BM25 有**文件長度正規化**和 tf 飽和，短而精準的 sqlmap 頁就贏過又臭又長的雜訊頁。

### 例子 B：標題加權，為什麼「加法」失敗、「乘法」成功

- **v1（加法式：score += 0.5 × 標題命中數）**：cosine 分數本身只有 0.1 上下，一個 +0.5 直接把分數蓋掉。結果**任何標題裡剛好有 "tool"、"login" 的頁都爆衝到第一**，例如 `sql injection tool` 第一名變成一個標題含 injection 的 Metasploit DLL injection 頁——完全跑掉。`directory enumeration web server` 也一樣被標題含 web/server 的頁搶走，**平均 P@5 從 0.96 掉到 0.80**。
- **v3（乘法式：score ×= (1 + 0.5 × 標題命中數)）**：不管底層是 cosine（~0.1）還是 BM25（~15），加權比例一致，不會壓垮原本的分數。
  - 效果：`wifi password cracking` 把 `fern-wifi-cracker`（標題就有 wifi+cracker）穩穩推到第一；`port scanning techniques` 把 `man-port-scanning-techniques` 這種標題正中的頁拉上來。

> 教訓（報告可寫）：**做分數融合時，不同評分法的數值範圍不一樣，用「乘法／比例」比「加法」穩**。

### 例子 C：同義詞擴展（v4），專治「詞彙不匹配」

**動機**：弱查詢 `wifi password cracking` 一直找不到 aircrack-ng。查了 aircrack-ng 頁面的詞頻：`wpa` 出現 60 次、`wep` 50 次、`key` 46 次，但 `wifi` 只有 3 次、`password` 4 次。使用者講「wifi 密碼」，文件講「WPA key」——字對不上，TF-IDF/BM25 再聰明也沒用。

**做法**（`code/synonyms.py`）：
- 手工建一張資安領域同義詞表：wifi→wireless/wpa/wep/802.11、password→key/passphrase、cracking→crack/recover…
- 查詢時把同義詞**加進查詢，但權重只有 0.5**（原字是 1.0），避免同義詞喧賓奪主。
- 標題加權只算**原字**，不算同義詞。
- **文件不動**，所以「文件和查詢用同一套前處理」的規定仍然成立；擴展是查詢端的加權。
- 順便加了**中文關鍵字對照**：「破解 wifi 密碼」→ `crack wifi password`。demo 時台下有人打中文也有結果；對照表沒有的中文（例如「你好」）仍顯示 OOV 提示。
- 介面上有勾選框可以開關，demo 時可以現場比較。

**改前 vs 改後（前五名）**：

| 查詢 | v3（改前） | v4（改後） |
|---|---|---|
| wifi password cracking | **kali.org/tools 總覽頁**、fern-wifi-cracker、wifi-honey、sparrow-wifi、ophcrack | fern-wifi-cracker、**aircrack-ng**、**reaver**、wifi-honey、wifiphisher |
| password hash cracking | hash-identifier、hashcat、hashid、goshs、passing-the-hash | hash-identifier、**rainbowcrack**、hashcat、**john**、cowpatty |
| brute force login | patator、crowbar、AuthBrute、CNPILOT、medusa | AuthBrute、dirsearch、**hydra**、crowbar、patator |
| directory enumeration web server | arsenal-ng、gobuster、dirb、(nmap book)、bloodhound | autorecon、gobuster、**feroxbuster**、smbmap、wpscan |
| sql injection tool | **sqlmap**、jsql、sqlninja、siparmyknife、MSSQL_SQLI | MSSQL_SQLI、jsql、sqlninja、sqlmap、sqlsus |

- ✅ aircrack-ng 終於進前二，總覽頁也被擠掉；john、hydra、rainbowcrack 這些「經典工具」都冒出來了。
- ⚠️ **副作用**：`sql injection tool` 的 sqlmap 從第 1 掉到第 4。因為 `sqli` 這個同義詞讓 Metasploit 的 `MSSQL_SQLI` 頁（滿滿都是 SQLI）衝上第一。前五還是全部相關，但「最佳答案」變差了。
- 📝 **誠實說明**：同義詞表是看了弱查詢之後才補的，有「對著考題調參」的風險。報告裡應該寫清楚這點，並說明真正的解法是用一組**獨立的開發查詢**來調同義詞，或改用 embedding 這種自動學語意相近的方法。

> 教訓（報告可寫）：**query expansion 提升召回（找得到更多對的），但可能犧牲精準度（第一名不一定最好）**——這就是 IR 裡經典的 recall vs precision 取捨。

### 例子 D：v5「對照老師規格」的大修（2026-10-17）

逐條對照題目 PDF 後，發現幾個會被扣分的地方，於是改了：

| 問題 | 為什麼會被扣分 | 怎麼改 |
|---|---|---|
| 預設排序是 BM25 + 加權 + 同義詞 | 題目必做的是「用 TF-IDF 向量的 cosine 排序」，BM25 只是加分的**比較** | `search()` 預設改成 `model="tfidf", title_boost=0, use_synonyms=False`；介面預設也是 TF-IDF，其餘是勾選框 |
| 評估只跑了一個版本 | 加分條件寫「BM25 要用**同一組查詢和判斷**來比較」 | `evaluate.py` 一次跑 3 個系統（tfidf / bm25 / bm25_boost_syn），用「合併標註（pooling）」：同一個（查詢, 頁面）只判一次，三個系統共用 |
| 標註是寬鬆的關鍵字自動判斷 | 題目要「依內容判斷」，且評分看「正確性」 | 112 組（查詢, 頁面）逐一看內容重判，寫理由；32 組模稜兩可的標成 AMBIGUOUS 等第二位組員複查 |
| 爬蟲統計沒有「失敗數」欄位 | 報告要列 attempts、valid、hosts、**failures**、平均長度 | `crawl_summary.json` 補 `failed`（0）和 attempts 細項；說明 host_cap 跳過的 1,125 個 URL 沒有發出請求，所以不算 attempt |
| 計時只有單次顯示 | 加分條件要「清楚的計時邊界 + 總結」 | `evaluate.py --timing`：每題暖機一次再跑 20 次，輸出平均／中位數／最大值，邊界寫清楚（不含載入索引、Flask、網路） |
| 片語搜尋用字串包含 | `"port scan"` 會誤中 `export scan`、`port scanning` | 改成有字邊界的連續詞比對（regex），符合「verified contiguous matches」 |
| 沒有小例子可以示範算分 | 題目說「要能示範一個小例子的計分」 | 新增 `code/toy_example.py`：3 篇小文件，一步步印出 tokens、倒排索引、IDF、權重、norm、cosine |
| 結果連結沒有限制協定 | 題目要求只放 HTTP/HTTPS 連結 | `search.py` 過濾非 http(s) 網址，模板再檢查一次 |

### 例子 E：v6「專攻必做 TF-IDF」（2026-10-21）

**為什麼做**：老師評分看的是必做的純 TF-IDF cosine，但它在嚴格標註下只有 0.42，是三個系統裡最低的。v5 的弱查詢分析已經指出三個病因：(1) 網站樣板文字污染、(2) 詞形不一致（scanning ≠ scan）、(3) cosine 偏好短文件。v6 就照這三點一個一個治，**每一步都在同一份標註上量前後差異**（`experiments/v6_ablation.json`）。

**第 0 步：標註第二輪複查（先把尺定好再改系統）**
- 把 32 筆 AMBIGUOUS 用「一致的規則」再看一次，改了 3 筆：
  - `sql injection tool` × `Msf::Exploit::Remote::MSSQL_SQLI`：1 → 0。它是開發者 API（程式庫），不是使用者會拿來跑的工具；同一條規則下，`exploit metasploit module` 底下的 API 頁本來就都標 0，這裡要一致。
  - `brute force login` × `Msf::Auxiliary::AuthBrute`：1 → 0，理由同上。
  - `password hash cracking` × `cowpatty`：0 → 1。它用字典破解 WPA-PSK 的雜湊（PMK），和已標 1 的 sipcrack（破解 SIP digest 雜湊）是同一類，要一致。
- 改完後 v5 的分數變成 TF-IDF 0.42 / BM25 0.62 / BM25+加權+同義詞 0.70（只有 BM25 那兩欄小變動）。
- v6 新系統會排出新的頁面，所以標註池從 112 筆擴大到 **147 筆**；新加的 35 筆同樣依內容判斷、寫理由，其中 12 筆標 AMBIGUOUS。現在總共 **44 筆 AMBIGUOUS 要組員複查**。
- 心得：**改系統前要先把評估的尺固定**，不然分數變了也不知道是系統變好還是尺變了。所以下面的消融實驗全部用同一份最終標註來算。

**第 1 步：清掉網站樣板文字（`code/clean.py`）**
- 發現：每個 Kali 工具頁最後都有一段 OffSec 課程廣告，還有「Edit this page jboss-autopwn johnny」這種**上一個/下一個工具**的導覽。最明顯的例子是 **jd-gui（Java 反編譯器）**：它本身跟 SQL 完全無關，但廣告寫了「ManageEngine … **SQL Injection** RCE」，所以在 v5 的 `sql injection tool` 排第 5。jd-gui 整頁 112 個詞，有 54 個是廣告和導覽。
- 做法：建索引時用 regex 移除「Learn more with OffSec…」、「Updated on / Author / Edit this page / Create a new page 之後的導覽」、「Table of Contents」、Metasploit API 頁的「Documentation by YARD」。**`pages.json` 不動**，只在建索引時清，所以爬蟲統計不會變。
- 結果：TF-IDF 0.42 → 0.48。jd-gui 清完後完全沒有 sql/injection，掉出前五，sqlmap 補進第 5 名。（laudanum 還在第 2：它自己的介紹就寫「when SQL injection flaws are found」，這不是樣板問題，是它真的提到 SQLi，但它是 SQLi 之後用的網頁後門，不是 SQLi 工具，標 0。）

**第 2 步：輕量詞幹還原（`preprocess.stem()`）**
- 做法：自己寫一個很小的後綴去除（Porter 第一步的子集）：`ies→y`、`sses→ss`、去 `ing`/`ed`（scann→scan 會去重複子音）、去複數 `s`（但 `ss/us/is` 不動，像 pass、status、analysis）。只處理長度 > 4 的純英文字，所以 `aircrack-ng`、`c++`、`802.11` 這類工具名完全不受影響。文件和查詢用**同一個函式**。
- 例子：`Port scanning techniques for cracking vulnerabilities` → `port, scan, technique, crack, vulnerability`。
- 結果：單獨加 stemming 0.42 → 0.48；**清樣板 + stemming 一起：0.54**（這就是 v6 的預設必做系統，仍然是純 TF-IDF cosine）。
- `port scanning techniques` 從 0.00 → 0.20：TCP Maimon Scan 頁進前五了。
- 同義詞表也跟著做詞幹還原（`synonyms._stemmed_table()`），不然 `cracking` 這個 key 會對不到已經變成 `crack` 的查詢詞。

**第 3 步：Pivoted length normalization（可切換，`search(..., pivot=0.2)`）**
- 問題：cosine 除以 ‖d‖，短頁很吃香（v5 弱查詢 1：只有 68 個詞的 dbeaver 贏過 sqlmap）。
- 做法（Singhal, Buckley & Mitra 1996）：把分母從 ‖d‖ 改成 `(1 − s) × 平均‖d‖ + s × ‖d‖`。s = 0 就是原本的 cosine；s 越小，長短頁差距被壓得越平。我們**事先**選 s = 0.2（常見值），沒有拿這 10 題去挑。
- 比喻：原本像「考試總分除以題目字數」，字少的考卷佔便宜；pivot 是「大家先除一個平均值，只保留一點點長短差」。
- 結果：v6 預設 + pivot = **0.68**；`exploit metasploit module` 0.20 → 0.80（API 頁被擠出去，換成 Running modules、How to use a Metasploit module 等教學頁），`port scanning techniques` 0.20 → 0.60（Port Scanning Techniques 正牌頁回來了）。
- 誠實說明：
  - 敏感度：s = 0.2 和 0.3 都是 0.68，不是剛好挑到一個幸運值。
  - **消融結果有個意外**：只加 pivot、不清樣板也不 stem 也有 0.70，比三個全加的 0.68 還高一點。也就是說，對這 10 題來說，**最大的病因是長度正規化**，清樣板和 stemming 在有 pivot 之後幫助不大（差 1 題，在誤差範圍）。我們還是保留清樣板和 stemming，因為它們是有道理的修正（不是為了這 10 題調的），而且讓「純 cosine」從 0.42 進步到 0.54。
  - pivot 不是嚴格意義的 cosine，所以做成開關（UI 勾選「pivoted length norm」），必做系統的預設仍是純 cosine。

**v6 結果總表（同一份 147 筆標註，`python evaluate.py --score`）**

| 查詢 | TF-IDF（v6 預設，必做） | TF-IDF + pivot | BM25 | BM25 + 標題 + 同義詞 |
|---|---|---|---|---|
| wifi password cracking | 0.40 | 0.60 | 0.60 | 0.80 |
| sql injection tool | 0.40 | 0.60 | 0.80 | 1.00 |
| port scanning techniques | 0.20 | 0.60 | 0.40 | 0.80 |
| password hash cracking | 0.60 | 0.80 | 1.00 | 0.60 |
| web application vulnerability scanner | 0.80 | 0.60 | 0.80 | 0.40 |
| network packet sniffer | 0.60 | 0.80 | 1.00 | 0.60 |
| exploit metasploit module | 0.20 | 0.80 | 0.60 | 0.80 |
| brute force login | 0.80 | 0.60 | 0.60 | 0.40 |
| directory enumeration web server | 0.40 | 0.40 | 0.80 | 0.60 |
| wireless deauthentication attack | 1.00 | 1.00 | 1.00 | 1.00 |
| **平均 P@5** | **0.54**（v5: 0.42） | **0.68** | **0.76** | **0.70** |

（BM25 那兩欄也因為清樣板 + stemming 而變動，BM25 0.62 → 0.76。）

查詢時間（`data/timing_summary.json`，暖機後每題 20 次，不含載入索引）：TF-IDF 平均 0.94 ms、TF-IDF+pivot 2.52 ms、BM25 2.01 ms、BM25+加權+同義詞 2.73 ms。

**消融實驗（`experiments/v6_ablation.json`，平均 P@5）**

| | 純 cosine | pivot s=0.2 | pivot s=0.3 |
|---|---|---|---|
| v5 原始 | 0.42 | 0.70 | 0.66 |
| + 清樣板 | 0.48 | 0.66 | 0.66 |
| + stemming | 0.48 | 0.70 | 0.66 |
| + 清樣板 + stemming（v6） | **0.54** | 0.68 | 0.68 |

**v6 之後還弱的查詢（給報告的弱查詢分析）**
1. `exploit metasploit module`（純 cosine 0.20）：前五還是 `Msf::Exploit::Remote::...` API 頁。它們短、而且 Module/Exploit 一直重複，cosine 最愛。開 pivot 後變 0.80，證明根因是長度正規化。
2. `directory enumeration web server`（兩種 TF-IDF 都 0.40）：`enumeration` 讓 dnsrecon、enum4linux-ng、ldeep（DNS/SMB/LDAP 列舉）、Nmap 的 CPE（Common Platform Enumeration）擠進來。這是**一字多義**：enumeration 在資安裡可以列舉任何東西，TF-IDF 不懂「web directory」要一起出現。可能的改善：片語/鄰近度加分（`directory` 和 `web` 靠近才加分）、或同義詞把 directory 擴到 dirb/dirbuster/content discovery。
3. `brute force login`（pivot 後 0.80 → 0.60）：pivot 讓長頁回來，結果 john（離線雜湊破解）這種長頁進來了。pivot 不是每題都進步。

**程式改了哪些檔**：新增 `code/clean.py`；`preprocess.py`（stem）；`indexer.py`（建索引前 clean、存 `avg_norm`）；`search.py`（`pivot` 參數、CLI `--pivot`）；`synonyms.py`（詞幹化同義詞表）；`evaluate.py`（新增 `tfidf_pivot` 系統）；`app.py`（pivot 勾選框）。v5 版程式備份在 `experiments/v5_code/`，v5 標註備份在 `experiments/eval_judgments_v5_draft.csv`。

### 其他加的功能（對應題目加分項）

- **BM25 比較**（加分 5）——介面上可切換；v5 起用同一組查詢和同一份判斷與 TF-IDF 比較。
- **片語搜尋 + 布林**（加分 3）：`"port scan"` 要求整個片語以連續詞出現（有字邊界）；`+term` 必須包含、`-term` 必須不含。例：`"port scan" -metasploit` 只回 Nmap 的 port scan 頁。
- **顯示查詢耗時**（加分 2）：每次搜尋回傳 `elapsed_ms`，介面會顯示「xx ms」。索引只在啟動時載入一次，不計入查詢時間；v5 起有正式總結：TF-IDF 平均 0.91 ms、BM25 1.99 ms（`data/timing_summary.json`）。

---

## 6. 必做的評估：Precision@5（10 個固定查詢）

10 個查詢在凍結後才評估，不是挑好看的才留。每題有「資訊需求」和「相關性規則」（`code/evaluate.py`）。
P@5 = 前五名中相關的數量 / 5（**分母永遠是 5**），再把 10 題平均。

**評估方法（v5）**：同一份索引快照，3 個系統各取前五名 → 合併成 112 組不重複的（查詢, 頁面）→ 每組依頁面內容判 1/0 並寫理由（`data/eval_judgments.csv`）→ 三個系統共用這份判斷算分（`data/eval_results.csv`）。

> ⚠️ 目前的 1/0 是 Hark 依內容先標的**草稿**，`reviewer` 欄寫著 DRAFT。報告交出前要由組員確認，AMBIGUOUS 的 32 筆要第二人複查，數字可能再變動。
>
> 🔄 **v7 最新（新 10 題、980 頁）請看第 11 節。**
>
> 🔄 **這一節是 v5 的結果。v6（2026-10-21）之後最新的表格、標註池（147 筆、44 筆 AMBIGUOUS）和弱查詢，請看第 5 節「例子 E」；報告請用 v6 的數字。**

| 查詢 | TF-IDF cosine（必做） | BM25（加分比較） | BM25 + 標題加權 + 同義詞 |
|---|---|---|---|
| wifi password cracking | 0.40 | 0.00 | 1.00 |
| sql injection tool | 0.20 | 1.00 | 1.00 |
| port scanning techniques | 0.00 | 0.20 | 0.80 |
| password hash cracking | 0.40 | 0.20 | 0.60 |
| web application vulnerability scanner | 0.40 | 0.80 | 0.60 |
| network packet sniffer | 0.60 | 1.00 | 0.40 |
| exploit metasploit module | 0.20 | 0.80 | 0.40 |
| brute force login | 0.80 | 0.80 | 0.80 |
| directory enumeration web server | 0.20 | 0.60 | 0.60 |
| wireless deauthentication attack | 1.00 | 1.00 | 1.00 |
| **平均 P@5** | **0.42** | **0.64** | **0.72** |

查詢時間（`data/timing_summary.json`，10 題 × 20 次）：TF-IDF 平均 0.91 ms（中位數 0.76）、BM25 1.99 ms、BM25+加權+同義詞 3.12 ms。

**觀察**：
- 嚴格標註後，必做的 TF-IDF 只有 0.42，比之前寬鬆標註的 0.96 低很多。這不是系統變差，是**之前的尺太鬆**。
- BM25 比 TF-IDF 高 0.22，主因是**長度正規化方式不同**（見弱查詢 1）。
- 加上標題加權和同義詞後平均最高，但不是每題都進步：`network packet sniffer` 從 1.00 掉到 0.40、`exploit metasploit module` 從 0.80 掉到 0.40。同義詞把 `traffic`、`payload` 這類較廣的詞拉進來，帶進不相關頁面。

### 弱查詢分析（題目硬性要求，以必做的 TF-IDF 為主）

1. **`sql injection tool`（TF-IDF 0.20，BM25 1.00）——cosine 偏好短文件**
   - 現象：TF-IDF 前五是 siparmyknife、laudanum、sqldict、**dbeaver（資料庫客戶端）**、**jd-gui（Java 反編譯器）**；sqlmap 不在前五。
   - 原因：cosine 會除以文件向量長度 ‖d‖。sqlmap 頁有 663 個詞、‖d‖ = 29.5；dbeaver 頁只有 68 個詞、‖d‖ = 10.9，而且完全沒有 `injection`。短頁只要剛好出現 `sql`、`tool` 一兩次，除以很小的 ‖d‖ 後分數就衝上去。BM25 的長度正規化比較溫和（b = 0.75，而且 tf 會飽和），所以 sqlmap、jsql、sqlninja 都回來了。
   - 改善：用 BM25，或對 cosine 做 pivoted length normalization；也可以要求查詢的稀有詞（`injection`）必須出現。
2. **`port scanning techniques`（TF-IDF 0.00）——詞形不一致 + 主題太廣的詞**
   - 現象：前五是 Kali non-root 文件、Nmap 的 host discovery、書本導覽頁、portspoof（防禦工具）、防禦 Nmap 的章節。真正講 port scan 的 `scan-methods` 不在前五。
   - 原因：(a) **沒有詞幹還原**：Nmap 書大多寫 `scan`（scan-methods 頁 27 次），查詢寫的是 `scanning`（只有 7 次），兩者被當成不同詞。(b) `port` 出現在 367 頁、idf 只有 0.42，區分力很弱。(c) host discovery 頁短，又一樣是 cosine 偏好短文件。
   - 改善：stemming（scanning→scan）、同義詞擴展（v4 加了 scanning→scan 後 P@5 到 0.80）、或給標題更高權重（`Port Scanning Techniques` 正好是標題）。
3. **`wifi password cracking`（TF-IDF 0.40，BM25 0.00）——詞彙不匹配**
   - 現象：BM25 第一名竟是 `kali.org/tools/` 總覽頁，其餘是一般密碼破解工具（ophcrack、ncrack、johnny）。aircrack-ng 不在前五。
   - 原因：aircrack-ng 頁大量寫 `wpa`（60 次）、`wep`、`key`、`handshake`，很少寫 `wifi`（3 次）、`password`（4 次）。總覽頁把上千個工具名字列在一起，剛好包含 wifi、crack 等字。
   - 改善：同義詞擴展（v4 後 P@5 = 1.00，aircrack-ng 排第 2）；把總覽頁之類的「目錄頁」降權或不收錄。
4. **`exploit metasploit module`（TF-IDF 0.20）——開發者 API 頁淹沒使用教學**
   - 現象：前四名都是 `docs.metasploit.com/api/Msf/Exploit/...` 的類別參考頁。
   - 原因：API 頁短，標題和內文一直重複 `Module`、`Exploit`，cosine 分數高；但使用者要的是「怎麼用模組」的教學。
   - 改善：對 `/api/` 路徑降權，或爬蟲直接排除 API 參考頁。

## 7. 能不能架到網路上？

可以，但題目只要求本機 demo（`python app.py` → `http://127.0.0.1:5000/`）。要上線的話：它就是一個 Flask app + 一個 17MB 的 `index.json`，用 `gunicorn app:app` 起、`debug=False`，丟到我們平常用的 Zeabur 即可。架上去是加分印象分，不是必要。

---

## 8. 測試後發現還能加的（下一輪候選）

1. ~~同義詞擴展~~ ✅ 已在 v4 完成。
2. ~~中文查詢對照表~~ ✅ 已在 v4 完成（基本關鍵字）。
3. **修 sqlmap 退步**：把 `sqli` 同義詞的權重再降低，或對 API 參考頁（docs.metasploit.com/api/）降權。
4. **排除目錄頁**：BM25 會把 `kali.org/tools/`（420 個工具的總覽頁）排到 `wifi password cracking` 第一，因為它什麼字都有。可以在索引時把這類列表頁降權。
5. ~~詞幹還原（stemming）~~ ✅ v6 完成（輕量版）。
7. ~~cosine 偏好短文件~~ ✅ v6 加了 pivoted length normalization（開關）。
8. **一字多義**：`enumeration` 會拉進 DNS/SMB/LDAP 列舉工具。可試鄰近度加分（查詢詞在文件中靠得近才加分），需要 positional index。
9. **API 參考頁**：純 cosine 下 `docs.metasploit.com/api/` 仍會淹沒 Metasploit 查詢；可考慮在爬蟲範圍排除（要同步改爬蟲統計說明）。
6. **部署到 Zeabur**（加分印象，非必要）。

## 9. 待辦 / 報告還要補的（v7.1 更新：技術部分全部完成）

- [x] 標註定案：144 筆、0 AMBIGUOUS（第 13 節）
- [x] 報告數字更新到 v7.1：`report/REPORT_DRAFT.md/.docx`
- [x] 架構圖（7 站）：`report/architecture.png`
- [x] demo 腳本：`report/DEMO_SCRIPT.md`
- [x] 介面截圖 9 張：`report/screenshots/`
- [x] 弱查詢分析 4 題、實作挑戰 11 點（報告第 8、9 節）
- [ ] （組員）組別、姓名、分工表
- [ ] （組員）每人個人心得（reflection）
- [ ] （組員）照 demo 腳本練習一次，控制在 5 分鐘內

## 10. 遇到的困難點總整理（報告「Implementation challenges」可直接用）

| # | 困難 | 發生什麼事 | 怎麼解決 / 學到什麼 |
|---|---|---|---|
| 1 | 爬蟲被執行環境中斷 | 同 host 間隔 2 秒，爬 990 次要 30 分鐘以上，但執行環境約 20 分鐘就會強制結束，爬到一半全部重來 | 加 checkpoint（每 25 頁存一次 frontier、seen、pages）和 `--resume`，分段爬完。學到：長時間任務一定要能續跑 |
| 2 | Kali 頁面太多，擠掉其他站 | Kali 工具頁上千個，不設限的話資料集幾乎全是 Kali | 每個 host 設上限（Kali 600、Nmap 200、Metasploit 200），用 round-robin 輪流爬。1,125 個 URL 因為額滿被跳過（沒有發請求） |
| 3 | 正文抽取 | 頁面有導覽列、側欄、頁尾，會被當成內容，稀釋主題 | 先移除 nav/header/footer/aside/script/style，再取 main/article；過短（< 200 字元）的頁面跳過 |
| 4 | 標點與特殊詞 | `c++`、`802.11`、`wifi-cracking`、`-sS` 很容易被切壞或黏在一起 | 自訂 tokenizer：詞中保留 `+ - . / #`，複合詞同時保留整體和拆開的部分 |
| 5 | 標題加權用「加法」失敗 | TF-IDF cosine 分數只有 0~1，加上固定 +0.3 等於整個蓋過內容分數，P@5 從 0.96 掉到 0.80 | 改成乘法 `score × (1 + 0.5 × 標題命中數)`，不受分數尺度影響 |
| 6 | 詞彙不匹配 | 使用者說「wifi password」，文件寫「WPA key」，字對不上就找不到 | 查詢端同義詞擴展（權重 0.5）。但副作用是 sqlmap 從第 1 掉到第 4、sniffer 查詢退步，學到 recall 和 precision 的取捨 |
| 7 | 對著考題調參的風險 | 同義詞表是看了弱查詢後才補的，等於偷看考卷 | 在報告誠實說明；正確做法是另外準備開發用查詢來調，再用凍結的 10 題評估 |
| 8 | **評估的尺太鬆** | 一開始用「頁面有沒有提到關鍵字」自動標註，幾乎每頁都算相關，P@5 高達 0.96，看不出系統好壞 | 改成依內容逐筆判斷、寫理由，嚴格後 TF-IDF 只剩 0.42。學到：評估方法本身就可能是最大的誤差來源，高分不代表系統好 |
| 9 | 功能做太多，偏離必做規格 | 為了提升效果把預設改成 BM25 + 加權 + 同義詞，但題目必做的是 TF-IDF cosine | 對照規格逐條檢查後，預設改回純 TF-IDF，其他做成可切換的對照組。學到：先把必做做對，加分項要能「開關」並且比較 |
| 10 | cosine 偏好短文件 | sqlmap 這種內容豐富的長頁，輸給只有 68 個詞的 dbeaver | 理解 ‖d‖ 正規化的副作用；BM25 的長度正規化較溫和，這是 BM25 贏的主因 |
| 11 | 片語搜尋誤判 | 用字串包含判斷時，`"port scan"` 會中 `export scan`、`port scanning` | 改用有字邊界的連續詞比對 |
| 12 | 片語搜尋比較慢 | 片語要對候選頁的全文跑 regex，`"port scan" -metasploit` 約 100 ms，一般查詢約 1 ms | 目前可接受；更好的做法是在索引裡存詞的位置（positional index），直接比對位置 |
| 13 | 改系統時評估的尺也在變 | v6 排出新頁面，標註池要擴大；又同時複查舊標註，分不清分數變化是系統還是標註造成 | 先把標註定下來（第二輪複查 3 筆 + 新增 35 筆），再用**同一份最終標註**對每個改動做消融實驗 |
| 14 | 網站樣板文字污染 | Kali 每頁的 OffSec 課程廣告寫著「SQL Injection」等攻擊主題，上一頁/下一頁導覽塞進別的工具名，讓跟 SQL 無關的 jd-gui（Java 反編譯器）排進 SQLi 查詢前五 | 建索引時用 regex 清掉（`clean.py`），不改爬下來的原始資料；TF-IDF 0.42 → 0.48 |
| 15 | 詞幹還原會誤傷工具名 | 一般 stemmer 會把 `aircrack-ng`、`802.11` 之類切壞，也會把 `status` 變 `statu`、`analysis` 變 `analysi` | 自寫輕量版：只動長度 > 4 的純英文字，`ss/us/is` 結尾不去 s；同義詞表也要一起詞幹化，不然對不上 |
| 16 | 改進效果不能疊加 | 只加 pivot 就 0.70，三個全加反而 0.68；清樣板和 stemming 在有 pivot 後幫助不大 | 消融實驗才看得出「真正的病因是長度正規化」。學到：要一次只改一件事、分別量，不能只看最後總分 |


---

## 11. v7（2026-10-21）：擴大主題範圍 + 打錯字/選錯字容錯

### 為什麼做
使用者希望搜尋引擎不要只有 Kali/Nmap/Metasploit 三站，而是能涵蓋更廣的資安主題：**封包攔截/分析、HTTPS 中間人、手機 App 反編譯、反向 shell/後滲透**。重點是「加深同一個主題」，不是變成什麼都收，否則固定 10 題評估會被稀釋。

### 資料集改了什麼
- seed 從 8 個（3 站）→ 8 個（**7 站**）。新增四站，每站都先用我們的 User-Agent + robots 實測可爬：
  - `www.wireshark.org/docs/wsug_html_chunked/`（Wireshark 官方使用手冊，封包分析）cap 80
  - `docs.mitmproxy.org/stable/`（HTTPS 中間人代理）cap 50
  - `frida.re/docs/`（App 動態插樁、Android 反編譯）cap 40
  - `gtfobins.org`（提權 / 反向 shell / 後滲透）cap 100
- **總量仍壓在 1000 頁以內**（題目上限）：把 Kali 上限 600→430、Nmap 200→150，讓出空間給新站，也順手治了「資料集幾乎全是 Kali」的老問題。
- Metasploit 的 `/api/`（開發者 API reference）排除——那些頁對「哪個工具 / 怎麼做」的查詢沒用，之前還一直污染 `exploit metasploit module`。
- 兩個踩雷：
  1. **mitmproxy 第一次只爬到 3 頁**：它的章節連結只放在側欄 `<nav>`，而我抽連結是在移除 nav 之後才做的。改成**先從整頁抽連結、再移除樣板取正文**（scope 白名單仍決定要不要跟進），mitmproxy 變 30 頁。
  2. **Frida 的「•」變成亂碼「â¢」**：frida.re 回傳 HTML 沒帶 charset，requests 預設用 ISO-8859-1 解 UTF-8。改成 charset 未知時用偵測編碼；已爬下來的用 `code/fix_encoding.py` 就地修了 70 個欄位。

最終爬蟲統計（`data/crawl_summary.json`）：有效 **980** 頁、實際請求 **1,016**、**失敗 0**、單站額滿跳過 1,075（不發請求）、平均正文約 8,910 字元。

### 評分核心：新增打錯字 / 選錯字容錯（`code/fuzzy.py`）
查詢字如果不在索引詞彙表裡，很可能是打錯、拼錯，或中文選錯字 / 選錯注音。依序嘗試：
1. **編輯距離**（Damerau-Levenshtein，含相鄰字對調）：`injetcion→injection`、`scaner→scanner`、`wiresahrk→wireshark`。只動長度 ≥ 4 的純英文字，上限 2 次編輯。
2. **中文拼音**：和已知中文關鍵字（`synonyms.ZH`）比拼音，拼音相同但字不同就修：`無缐→無線`、`掃瞄→掃描`。
修正後的字以**較低權重 0.7** 加進查詢，介面顯示「did you mean: injetcion → injection」。文件完全不動，只修查詢。
- 速度：建索引詞彙的長度分桶 + 字母差集預篩，純英文打錯字查詢約 20–40 ms，中文拼音約 1 ms，一般正確查詢仍 ~1 ms。
- 幾個 tie-break 眉角：索引存的是**詞幹**（`https` 被存成 `http`），所以比對時也拿 `cand+"s"` 一起比；少打一個字母是最常見錯誤，所以偏好「把打的字當子序列包住」的候選（`htps→http` 而非 `hops`）。
- **評估不含容錯**：10 題都是拼對的，容錯不會觸發，所以另外用例子展示（上面那組），不混進 P@5。

### 介面可解釋性（`code/app.py`）
- 每筆結果顯示**命中 / 缺少哪些關鍵字**（像 Google 的「Missing: …」）：命中的字綠色標籤，缺的字劃掉。
- snippet 內把命中的查詢字**粗體**標出（用同一套 tokenize + 詞幹比對，所以 `injection` 也會標到 `injections`）。
- 新增「typo tolerance」勾選框（首次進站預設開）。

### 固定查詢換了 3 題（換完才看結果，之後凍結）
原本 10 題偏 Kali 破解；為了測新範圍，**在看任何 v7 結果前**換掉 3 題：
- `password hash cracking` →（和 wifi cracking 太像）`intercept https traffic`
- `brute force login` → `decompile android apk`
- `wireless deauthentication attack`（每個系統都 1.00，分不出好壞）→ `reverse shell payload`

### P@5 結果（`data/eval_results.csv`，標註池 134 筆，35 筆 AMBIGUOUS 待組員確認；沿用 v6 已標的同 (查詢, 網址) 判斷，新增 44 筆由 Hark v7 草標）

| 系統 | v6（舊 10 題 / 964 頁） | v7（新 10 題 / 980 頁） |
|---|---|---|
| TF-IDF cosine（必做） | 0.54 | **0.46** |
| TF-IDF + pivot | 0.68 | **0.78** |
| BM25 | 0.76 | **0.74** |
| BM25 + 標題加權 + 同義詞 | 0.70 | **0.74** |

> 數字不能跨版本直接比（查詢和資料集都換了）。v7 裡結論一致：**純 cosine 最大的病還是長度正規化**，pivot 單獨就把 0.46 拉到 0.78，仍是四個系統最高。新站進來後 `intercept https traffic`、`network packet sniffer` 兩題 pivot/BM25 都到 1.00，而純 cosine 因為偏好 Metasploit 的短 API 頁只有 0.60–0.80。timing（`data/timing_summary.json`）：TF-IDF 0.95 ms、pivot 2.17 ms、BM25 2.04 ms、enhanced 2.50 ms。

### 困難點（接續第 10 節）

| # | 困難 | 發生什麼事 | 怎麼解決 / 學到什麼 |
|---|---|---|---|
| 17 | 新站連結抽不到 | mitmproxy 章節只連在側欄，移除 nav 後才抽連結 → 只爬到 3 頁 | 改成先整頁抽連結、再移除樣板取正文；scope 白名單仍把關 |
| 18 | 編碼亂碼 | frida.re 不帶 charset，UTF-8 被當 Latin-1 解，「•」變「â¢」 | charset 未知時用偵測編碼；舊資料用 `fix_encoding.py` 就地 latin-1→utf-8 修復 |
| 19 | 容錯比對很慢 | 一個打錯字要和五萬多個詞算編輯距離 | 用長度分桶 + 字母差集預篩只留少數候選；只修 df≥2 的純字母詞，跳過雜湊/ID |
| 20 | 詞幹 vs 字面 | 索引存詞幹，`https` 被存成 `http`，`htps` 修不到；且容易修成 `hops` | 比對時同時拿 `cand+"s"`；tie-break 偏好把打的字當子序列包住的候選 |
| 21 | 換查詢會不會作弊 | 換 3 題有「挑對自己有利」的嫌疑 | 規則：換題只看「主題涵蓋 / 鑑別度」，**在看任何 v7 分數前**換好並凍結；報告誠實說明理由 |

## 12. v7 待辦（給組員）——✅ 已在 v7.1 全部完成（見第 13 節），組員只需寫報告文字、分工、心得
- [ ] 確認 `data/eval_judgments.csv` 的 35 筆 AMBIGUOUS（多半是 GTFOBins 只繼承 perl 函式的頁、mitmproxy UI 導覽頁、john 這種非 Wi-Fi 破解頁）。
- [ ] 確認後重跑 `evaluate.py --score`、`--timing`，把報告數字換成最終版。
- [ ] 報告正文（`report/REPORT_DRAFT.md`/`.docx`）仍是 v5 數字，要整段換成 v7；架構圖 `report/architecture.svg` 仍畫 3 站，要改成 7 站。
- [ ] UI 截圖補拍含「did you mean」「Missing:」「中文 → 英文」的畫面。

---

## 13. v7.1（2026-10-21 晚）：收尾——必做 TF-IDF 再加強 + 所有組員待辦都做完

使用者要求：「必做的 TF-IDF 和其他所有東西都做完，組員只負責寫報告。」所以這一輪把第 9、12 節的待辦全部清掉。

### 標註定案
- 35 筆 AMBIGUOUS 做第二輪複查，改判 3 筆（都是看了頁面全文才發現）：
  - `wifi password cracking` × john：頁面有 `wpapcap2john`，把 802.11 WPA 握手封包轉給 John 破解 → 0 改 1
  - `wifi password cracking` × kismet：頁面列出 autowep（算 WEP key）和 ptw（Aircrack-NG PTW 攻擊）外掛 → 0 改 1
  - `reverse shell payload` × Meterpreter Stageless Mode：在講怎麼產生 reverse_tcp / reverse_https payload → 0 改 1
- 新系統排出的 10 筆新頁面也標好。最終 **144 筆、0 筆未標、0 筆 AMBIGUOUS**，reviewer 欄寫 `Hark FINAL`。草稿版備份在 `experiments/eval_judgments_v7_draft.csv`。

### 必做 TF-IDF 的兩個加強
1. **導覽頁不當結果**（`clean.is_hub`）：Metasploit 每章的 "Table of contents" 頁只有 34–49 個詞、全是子頁標題，cosine 最愛這種「每個字都是關鍵字」的短目錄。加上 Kali 全部工具列表、GTFOBins 首頁、Nmap 目錄、Metasploit 模組總表，共 12 頁。保留在資料集（爬蟲靠它們找到真正的頁面），只是不回傳。
2. **查詢詞覆蓋優先**（`coverage=True`，介面「more query words first」）：包含越多個不同查詢詞的頁排越前，同組內仍用 cosine。分數完全不變，等於搜尋引擎預設的 AND。

消融（`experiments/v7_1_ablation.json`，同一份最終標註）：

| 系統 | 導覽頁照常 | 導覽頁不回傳 |
|---|---|---|
| TF-IDF（必做） | 0.46 | 0.46 |
| TF-IDF + 覆蓋優先 | 0.68 | **0.72** |
| TF-IDF + pivot | 0.84 | **0.84** |
| TF-IDF + pivot + 覆蓋 | 0.78 | 0.80 |
| BM25 | 0.76 | 0.80 |

心得：
- 純 cosine 拿掉導覽頁後還是 0.46——空出來的位置又被別的短頁（GTFOBins 的 cowsay 這種）占走。**病根是長度正規化**，拿掉幾個壞頁治標不治本。
- pivot 單獨 0.84 是全場最高，連 BM25 都超過。
- pivot + 覆蓋（0.80）比只有 pivot（0.84）差：`wifi password cracking` 掉了，因為覆蓋優先把「三個字都有、但講的是 SIP 密碼破解」的頁排上來。改進不能疊加，又一次證明要一次只改一件事。
- 預設系統仍是純 TF-IDF cosine（題目必做），改進版做成勾選框，報告裡並列比較。

### 其他收尾
- `fix_encoding.py` 加強：字串裡同時有正常非 Latin-1 字元時，改成逐段修 mojibake（又修了 14 個欄位，Frida 的 "what’s" 不再亂碼）。
- 架構圖更新成 7 站、6 個評估系統、容錯與導覽頁（`report/architecture.svg/png`）。
- 用 headless Chromium 拍了 9 張介面截圖（`report/screenshots/`）：首頁、TF-IDF vs BM25、did you mean、中文選錯字、片語+布林、Missing 標籤、pivot、OOV 提示。
- `report/REPORT_DRAFT.md/.docx` 全部換成 v7.1 數字（爬蟲統計、6 系統 P@5、計時、4 個弱查詢、11 個挑戰、6 個搜尋案例對應截圖）；只留組別、姓名、分工、個人心得給組員。
- `report/DEMO_SCRIPT.md` 改成 v7.1 流程。
- 計時（`data/timing_summary.json`）：TF-IDF 1.18 ms、+覆蓋 2.13、+pivot 2.31、+兩者 3.00、BM25 1.92、BM25+標題+同義詞 2.37。

### 困難點（接續）
| # | 困難 | 發生什麼事 | 怎麼解決 / 學到什麼 |
|---|---|---|---|
| 22 | 拿掉壞頁沒有用 | 導覽頁拿掉後，純 cosine 分數不變，位置被其他短頁補上 | 證實病根是長度正規化，不是個別壞頁；治本要改正規化（pivot） |
| 23 | 改進互相打架 | pivot 0.84、覆蓋 0.72，兩個一起 0.80 | 覆蓋優先會把「字都對、主題錯」的頁往前推；用消融表分開看 |
| 24 | 標註要看全文 | 只看摘要會把 john、kismet 判成和 Wi-Fi 無關 | 模糊的都打開全文搜關鍵字（wpapcap2john、ptw）再判 |


## 14. v8（2026-11-05）：把課堂依據、修改與證據連在一起

使用者確認上一輪盤點方向，並要求每次更新寫清楚「引用了哪裡、進步了哪裡、改了哪裡」。詳見 docs/changes/README.md 的四批紀錄與 docs/references.md 的來源頁碼。

- **001，U4／TP §3–5**：修正正式搜尋忽略重複 query TF；範例由錯誤 0.1834 修為 0.1755。**U2／TP §2**：每跳先驗 scope／robots，包含 robots 與 redirect 的請求計數；移除 robots 失敗放行與拼音依賴靜默停用。
- **002，U1 p.43–48**：加入 literal positions，保留停用詞，分開 title/body；片語整體搜尋中位數 49.6→4.0 ms，但索引 15.8→28.9 MB、一般搜尋 0.4→2.6 ms。這是取捨，不能只寫加速。
- **002，U4 p.25–39 延伸實驗**：新增 field cosine／proximity；在正常 UI 的 sql injection tool 例子仍把開發文件排前面，sqlmap 第六，保留為失敗案例，不拿來當預設或宣稱已提升品質。
- **003，U3／TP §6**：原十題維持歷史回歸，另凍結 12 題開發與 24 題 holdout 候選，準備隱藏模型／排名的全文盲評與雙人紀錄；沒有代填人工標籤或新成績。
- **004，TP §4／7、U3／U4**：沿原 Flask 正常入口整合實驗模式與逐詞計分表、全文與評估導覽；更新 v8 報告／展示腳本，舊 Word、素材及原快照保留。

這一輪的學習點是：公式可重算、結果可解釋、成績有可信的尺，比把所有開關一起打開更重要。新功能存在不等於新模型更好；原六組成績可重現，也不等於原助手標註已獲組員人工確認。組員實際參與、個人心得與人工盲評仍需本人完成；使用者尚未驗收，沒有 Git 上傳或部署。


## 15. v8 審查收斂：承認失敗、補齊可重算的證據

引用與逐檔修改見 docs/changes/005-review-fixes.md。獨立 Standards／Spec 審查找出 dot-segment scope、中斷／resume、句尾標點、offsets 與過期成績問題，已完成修正及複查；各模型的解釋也改為真正使用的 IDF／norm／長度。

新增完整字元 offsets 後，最終索引 47.9 MB，片語加排除約 49.0→4.4 ms、一般查詢 0.36→3.03 ms、初載約 84→641 ms。第一輪 28.9 MB 的記錄保留為過程，不能當最終成本。980 頁缺 description metadata，程式只為新資料保存真實描述，不生成假欄位。

三份盲評包共 654 組，全部人工欄位保持空白。完成程式與審查，仍不代表新模型品質已獲證實，也不代表組員心得或使用者驗收已完成。

## 16. v8.1（2026-11-05）：先把可獨立驗證的工作完成

使用者要求按照順序完成可獨立部分，每批引用／修改／成效／退步都記錄，人工參與集中交接，不做 PPT、不 push。沿用 codex/ir-course-upgrade，自 5d1da8f 繼續；本輪 fetch 的 origin/main 仍為 9c7c3a1。沒有另外建 branch／worktree、spec 或 ticket。

- **006／TP §2–6、U2**：正常爬蟲完整採集七站，980 頁、1,027 實際 HTTP requests、485 頁有真實 description；逐站最短間隔皆 ≥2 秒，10 個 robots 拒絕未送出內容請求。另建新索引、重算全部 norm 與 1,348,436 筆 literal occurrences；原快照保留，不混作新品質成績。
- **007／U1、U4、VAR／PY 工程延伸**：壓縮 offsets、gzip、有界詞彙快取、稀疏摘要窗口、排名與解釋共享預算。固定原快照的索引 47.9→9.8 MB，交錯五程序量測初載 450→313 ms，sql 暖機 2.905→0.458 ms。完整條件與冷查詢、p95、九模型記錄見 007。
- **中間退步也保留**：壓縮後太早解碼字元座標，sql+proximity 冷查詢約 83 ms；改成僅對回傳解釋解碼後約 5.25 ms（含解釋約 5.66 ms）。採集負載中的第一次 timing 另留，沒有挑掉高延遲樣本。
- **008／U3、TP §6–9**：九模型 × 46 題的 414 次完整結果含解釋／摘要仍相等。新增 course/development 描述診斷、兩個弱查詢草稿、必做 baseline-only 50 筆盲評包與 HUMAN_HANDOFF.md；沒有代填人工標籤、換題挑成績或使用 holdout 調參。
- **根因修正**：保護舊實驗輸出；manifest 結構驗證共用；不同 collection 不冒用舊成績；開發診斷函式本身禁止 holdout。Standards／Spec 找出的本輪兩項問題均修正並複查。

這一輪的心得素材：效能改善要分清初載、冷查詢與暖機；壓縮可能把成本轉移到首次解碼，必須在實際入口發現再修正。搜尋的難處也包含相關性規則：SIP 工具可能確實提到 SQL injection，Frida 與反編譯則不完全相同，不能只看標題或讓助手把模糊處直接定案。人工判斷、真實分工／個人心得與使用者驗收仍由本人完成。

## 2026-11-05 · v8.2 模型判定與評分

依使用者授權由 LM 完成先前判定項目，新增獨立來源流程，保留 human CSV 空白及其檢查。46 題／九模型前五筆去重為 654 組、362 篇，完整索引正文 5,498,678 字元／409 段／99 批。100 次 CLI 呼叫取得 99 份有效回覆；一批 ID 漏字拒收後重試，失敗原始輸出保留。自我複核修正六筆，初判與終判分開保存。

只依 development 選 BM25：38/60=0.6333；holdout 75/120=0.6250，基準 48/120=0.4000，+22.5 個百分點。field+proximity=0.3583 退步；GTFOBins sudo 題 BM25=0、基準=1，native libraries 兩者=0。沒有改排序參數或用 holdout 調參。引用、改動、所有升降及限制見 docs/changes/009-model-assessment.md、report/MODEL_EVALUATION_V8_2.md。

修正整數平手、逾時部分輸出保存、摘要對 CSV 重新驗算及 manifest 結構檢查；兩軸 review 複查通過。CLI metadata falling_back／技能掃描警告留在 stderr，未新增應用 fallback。原快照、舊評估、姓名／分工／個人心得未造填；不做 PPT、不 push。

## v8.3 · 先定位為什麼找不到，再分開修

GTFOBins 的問題是來源意圖被跨站的普通詞命中蓋過；Frida 的問題是人用 `libraries` 提問、文件用已載入模組的 API 描述。新選項分別處理 URL host 與有語境的精確 API，保留原基準。模型終判的兩題 P@5 分別由 0 到 0.8／0.4；16 題新題由 0.350 到 0.425。來源四題與控制八題持平。複核發現「可能繼承」與「只列能力」不足以判相關，四筆修正使兩版本平均都比初判低 0.05。這讓本輪結論有界：修復來源錯配與術語不對，不保證同站找得到正確操作。詳細證據見 docs/changes/010-query-intent.md、report/QUERY_INTENT_V8_3.md。

## v8.4 · 同一網站也需要找到正確段落

指定 GTFOBins 後，頁面仍可能只談分類、可能繼承，或談不同功能的 sudo；寫檔分類甚至包含明示刪檔的例子。用固定官方資料建立可對照原索引的功能／情境證據，再將顯式效果納入排序。反向 shell 0→0.60、sudo 寫檔 0.20→1.00；16 新題 0.3375→0.6000。新 SUID 讀檔顯示只認功能仍 0.20，配對後 1.00。附加寫入還是 0；沒有把正確站名或分類等同於已符合需求。詳見 docs/changes/011-gtfo-function-context.md。

## v8.5 · 分開處理收錄與排序

原每站 100 頁額度使三個有附加寫入證據的 GTFOBins 條目被跳過。另建 983 頁快照後，舊題 P@5 到 0.60。附加排序將其三個相關結果集中到前三名。固定同語料的新題 P@5 由 0.4333 到 0.5167，暖查詢 p95 由 3.18 到 3.30 ms。覆寫對照的誤判兩組共同下修。 [本輪證據](docs/changes/012-gtfo-append.md)

## v8.6 · 查到文件之後，還要證明它答對了

這一輪有兩種不同的卡點。原資料已經有 sudo 覆寫範例，但舊排序分不清覆寫、附加與刪檔。站外 sudo 附加則先要補足文件，還要把來源排除當成真的篩選條件。補收三篇後，舊排序仍把它們放在第 26、347、549 名。核對同一範例的操作和權限再排序，三篇才升到第 1–3 名。

在同一份 986 頁快照上，覆寫舊題 P@5 由 0.20 到 1.00，站外附加由 0 到 0.60。12 道新題平均由 0.1833 到 0.6333。暖查詢中位數由 2.56 增到 2.98 ms，跨站比較和站外 SUID 附加仍為 0。這輪延續早期的教訓，分開記錄評估標準、文件收錄與排序各自造成的差異。 [本輪成效與來源](docs/changes/013-write-effects.md)
