# 引用資料

頁碼使用 PDF 的實際頁序（從 1 起算）。講義與作業由使用者已登入的課程平台於 2026-11-05 下載；原檔保留於外層盤點的 sources/course/，不混入公開程式交付。

| ID | 來源與位置 | 對應實作 |
|---|---|---|
| TP | [Term Project I（PDF 截止 11/12）](https://elearningv4.nuk.edu.tw/mod/assign/view.php?id=122192)，p.1 §2、p.2 §3–5、p.3 §6、p.4 §7–9 | 範圍、限速、TF-IDF cosine、固定快照與 P@5、交付；11/12 是截止日期，不是更新日期 |
| U1 | [Unit 1](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=120440)，p.13–16、31–35、43–48 | 倒排索引、postings 交集、短表優先、位置索引與鄰近度 |
| U2 | [Unit 2](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121177)，p.14–31 | frontier、robots、禮貌、URL 正規化與篩選 |
| U3 | [Unit 3](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=121734)，p.9、29–38 | 資訊需求、人工標註、一致性、P@k、單一改動與摘要 |
| U4 | [Unit 4](https://elearningv4.nuk.edu.tw/mod/resource/view.php?id=123304)，p.15、18、21、25–39 | log TF、collection IDF、query/document vectors、cosine、不同權重方案 |
| REP | [RFC 9309 §2.3.1](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1) | robots 取得失敗與不可達的處理；本專題另遵守更嚴格的 allowlist |
| HTTP | [RFC 9110 §4.2.3、§10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3) | scheme 的預設埠、Retry-After 秒數與 HTTP 日期 |
| ROB | [Protego 官方文件](https://github.com/scrapy/protego)，Usage | robots 最長規則、wildcard、Crawl-delay／Request-rate 解析；下載與限速仍由本專題實作 |
| VAR | [Protocol Buffers Encoding：Base 128 Varints](https://protobuf.dev/programming-guides/encoding/#varints) | unsigned base-128 整數的位元與延續位元；本專題自行設計 offset gap/length 容器，並非 Protobuf message，也未加入其函式庫 |
| PY | [Python gzip](https://docs.python.org/3.13/library/gzip.html)、[functools.lru_cache](https://docs.python.org/3.13/library/functools.html#functools.lru_cache) | 明確 gzip 格式、mtime=0 與有界快取；屬工程延伸，不是教授指定的排序公式 |
| GIT | [Git attributes：text／whitespace](https://git-scm.com/docs/gitattributes#_checking_whitespace_errors) | 保留 CSV 的凍結 bytes 與 CRLF；不對已凍結材料做換行正規化 |
| LLM | [Thomas et al., Large language models can accurately predict searcher preferences](https://arxiv.org/abs/2309.10621)；[Microsoft Research 原文頁](https://www.microsoft.com/en-us/research/publication/large-language-models-can-accurately-predict-searcher-preferences/) | LLM 搜尋偏好評估的研究依據；該研究有使用者回饋校準，本次未校準，不借用其準確率 |
| ZONE | [Manning、Raghavan、Schütze, Introduction to Information Retrieval §6.1](https://nlp.stanford.edu/IR-book/html/htmledition/parametric-and-zone-indexes-1.html) | 區分文件 metadata 與詞彙；v8.3 的 URL host 排序層為本專題設計，非教材加權公式 |
| QE | [Introduction to Information Retrieval §9.2.2](https://nlp.stanford.edu/IR-book/html/htmledition/query-expansion-1.html) | 受控詞彙補足查詢與文件用詞差異；v8.3 的語境條件、0.5 權重與證據優先皆為本專題設計 |
| GTFO | [GTFOBins 官方網站](https://gtfobins.org/) | 確認集合名稱、執行檔與 sudo／SUID context 的關係；評分以凍結網頁正文為準 |
| GTFO-SCHEMA | [GTFOBins Contributing：File format、Functions、Contexts、Aliases](https://gtfobins.org/contributing/)；[固定官方原始碼](https://github.com/GTFOBins/GTFOBins.github.io/tree/acd524623f9c406acedd2754ebd9c2431f3675ad) | 每個例子各自有 context；情境可覆寫同一例子的程式片段，正式 alias 與可能繼承有不同意義 |
| GTFO-EFFECT | [c89 的 File write](https://gtfobins.org/gtfobins/c89/#file-write)、[Bash 的 Reverse shell](https://gtfobins.org/gtfobins/bash/#reverse-shell) | 明示刪檔不等於寫入內容；直接範例的情境以同一功能區塊為準。僅以文件評估，沒有執行命令 |
| GTFO-APPEND | [hashcat](https://gtfobins.org/gtfobins/hashcat/#file-write)、[screen](https://gtfobins.org/gtfobins/screen/#file-write)、[tee](https://gtfobins.org/gtfobins/tee/#file-write) | 逐例區分實際附加、需選項的附加及 sudo／SUID |
| BASH-REDIR | [GNU Bash 手冊 §3.6.2–3](https://www.gnu.org/s/bash/manual/html_node/Redirections.html) | 截斷與附加重導向的文件語義 |
| WRITE-TOOLS | [POSIX Shell §2.7.2](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html#tag_19_07_02)、[FreeBSD csh](https://man.freebsd.org/cgi/man.cgi?query=csh&sektion=1)、[GNU tee](https://www.gnu.org/s/coreutils/manual/html_node/tee-invocation.html)、[GNU cp](https://www.gnu.org/software/coreutils/manual/html_node/cp-invocation.html)、[aria2](https://aria2.github.io/manual/en/html/aria2c.html#cmdoption-allow-overwrite) | 依同一原文範例辨識覆寫與附加，保留明示選項及 shell 條件 |
| EXT-APPEND | [Ubuntu Apache2](https://documentation.ubuntu.com/security/security-features/network/version-banners/apache2/)、[Ubuntu vsftpd](https://documentation.ubuntu.com/security/security-features/network/version-banners/vsftpd/)、[Debian Wiki](https://wiki.debian.org/BootstrapBootableSystem) | 外部附加的三份原始文件，sudo 套用於實際寫入的 tee |
| FRIDA | [Frida 官方 JavaScript API：Process](https://frida.re/docs/javascript-api/#process)、[Installation](https://frida.re/docs/installation/) | 已載入模組的 API 名稱與實際列舉範例；評分以凍結網頁正文為準 |

課堂講義沒有直接規定本專題的新欄位混分公式或 proximity multiplier；這些是由 U1 的位置資訊、U4 的向量／欄位概念延伸的**本專題實驗設計**，不得描述成教授原公式，必須與必做 cosine 分開量測。
