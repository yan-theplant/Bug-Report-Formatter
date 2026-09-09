# Jira 写操作机制（建票失败处理 · 附件上传 · 正文内嵌 · 链接补全）

> `bug-report-formatter` 的参考文件。**只在 B 模式（真的要建票）且走到对应步骤时读它**。
> 决策性规则（查重、确认关卡、字段默认值、需求来源、自动 link）都在 `SKILL.md` 第 4 节，这里只放机制细节。

#### 4.5.1 建票失败 / 卡住的处理（**先分类，别一律当 token 问题**）
建票是唯一有副作用的一步，失败时**第一件事永远是确认票到底建没建成**，再谈重试：

```
project = <KEY> AND reporter = currentUser() AND created >= -1h ORDER BY created DESC
```
用 4.2 那个 curl 形式跑（`$AUTH` 已在手，别再走 MCP）。建成了 → 直接进 4.6，**绝不重建**。

没建成时按错误类型分流：

| 症状 | 判断 | 动作 |
|------|------|------|
| 401 / 403 / `Unauthorized` / `invalid_token` / 提示重新授权 | 认证失效 | **提醒用户更新 token**：MCP 侧跑 `/mcp` 重连 Atlassian；curl 侧说明 memory 里 `jira-credentials` 的 API token 已过期、需去 https://id.atlassian.com/manage-profile/security/api-tokens 重开并让我更新那条 memory。**不要重试，不要换路径**——重试只会再撞一次 401 |
| MCP 调用转后台 / 长时间无响应 / `status: failed` 无错误体 | 服务端挂起，与 token 无关 | **不要 `TaskOutput` 阻塞干等**（上次为此白等 2min42s）。先跑上面那条查重 JQL；确认没建成就用 curl 直接打 REST v3 建票（见下），别再走 MCP |
| 缺必填字段 / 字段值非法 | 请求问题 | 走上面的必填字段兜底 |
| 404 project / issuetype 不存在 | 目标错 | 回 4.1 重新确认 key 与 issuetype |

**curl 兜底建票**（认证与 4.6 同一套，`description` 用 ADF 或先建票后用 wiki PUT 正文）：
```bash
curl -s -X POST "https://<site>/rest/api/3/issue" \
  -H "Authorization: Basic $AUTH" -H "Content-Type: application/json" \
  -d '{"fields":{"project":{"key":"<KEY>"},"issuetype":{"name":"Bug"},"summary":"<title>","priority":{"name":"<档位>"},"assignee":{"id":"<accountId>"}}}'
```
curl 也回 401 → 才是 token 问题，转上表第一行。

⚠️ **不要把「失败」默认等同于「token 过期」**：token 失效是**秒回 401/403**；挂 2 分钟以上无响应几乎一定是服务端问题，此时提醒换 token 会让用户白换一个好使的 token，还漏掉「票可能已建成」的重复风险。

### 4.6 上传附件

#### 4.6.0 去音轨 + 按需压缩（**清晰度优先于体积**）

##### 必做：视频一律静音（**与压不压无关**）
嵌进 Jira 的视频**必须没有声音**，包括「体积小、跳过压缩」的那些。先检测：
```bash
ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "<in>"
# 有输出（如 `0`）= 有音轨；空输出 = 本来就静音
```
- **无音轨** → 什么都不用做。
- **有音轨** → 去掉。要压缩的把 `-an` 折进压缩命令；不压缩的用无损剥离：
  ```bash
  ffmpeg -v error -i "<in>" -an -c:v copy "<out>"
  ```
不许上传带声音的视频，即使用户没提。已经传上去了 → 换成静音版并删掉旧附件。

##### Jira 附件上限（**调研结论，2026-09-09 实测**）
- `/rest/api/3/configuration` **不返回** `maxAttachmentSize`（Cloud 上只有 `attachmentsEnabled: true`），所以**没法用 API 查出上限**，别浪费一次调用。
- **同站点实测 32.2MB 的 `.MP4` 附件上传成功**（<MDX-xxxx> 上的 `ScreenRecording_09-08-2026 01-38-00_1.MP4`），另有 29.9MB / 13.0MB / 11.2MB 若干。所以「≤50MB 直传」这条阈值是安全的。
- 真的传失败了才去查具体上限，且以**报错信息**为准（`413` / `file too large`），不要靠猜。

##### 压缩阈值：**≤50MB 一律传原文件，不压**
压缩会把录屏里的 UI 文字 / DevTools / console 压糊，那就失去了证据的意义。
```bash
du -h "<file>"   # 先看原始体积
```
- **≤ 50MB → 直接传原文件**（去音轨后），不要压。
- ⚠️ **例外：可选的「近无损」瘦身，用来省上传时间**（团队反馈，2026-09-03：两支录屏 31MB+11.7MB 合计 43MB，上传是第二大耗时项，「可以考虑将视频压缩到不失真上传」）。
  手机录屏常常码率虚高，近无损重编码往往能砍掉一半体积而看不出差别。**仅在单支视频 > 15MB 时试一次**：
  ```bash
  ffmpeg -v error -i "<in>" -c:v libx264 -crf 18 -preset veryfast -an "<out>"   # 原生宽度，不缩放
  ```
  - **CRF 18 是上限，不许再高**（要压得更狠就走下面 >50MB 那条流程，且必须自检可读性）。
  - **省下不到 40% 就丢弃压缩版直传原文件** —— 为 20% 的体积去冒画质风险不划算。
  - 压完照样要跑下面那条「压缩后必须自检」：抽一帧看 UI 文字是否仍清晰。
  - 这一步是**优化，不是必做**。视频本来就小、或压缩自检没过 → 直传原文件，别卡在这里。
- **> 50MB，或上传确实因体积失败** → 才压，而且要压得清楚：
  - **保持源视频原生宽度**（源本身很小的话至少 1920），**用低 CRF（20–23）**。
  - **绝不用 `1280 + crf 28` 这种重压**——APP 竖屏勉强能看，Web 桌面录屏（如 3022×1846）文字直接不可读。
  ```bash
  # 原生宽度 + 低 CRF + 去音轨
  ffmpeg -v error -i "<in>" -c:v libx264 -crf 22 -preset veryfast -an "<out>"
  ```
  还是太大 → 一档一档降（CRF 23 → 25，或缩到源宽的 3/4），每降一档都重新自检可读性，不要一步压到底。
- 截图基本不用压。真的过大时：纯 UI 截图保持 PNG（有 `pngquant` 就 `pngquant --quality=80-95`），照片类才转 JPEG q85。**不要 `sips -Z 1600` 缩 UI 截图**，文字会发虚。
- **压缩后必须自检**：读一眼压后的文件（视频抽一帧、图直接看），确认 UI 文字仍可读；
  **压后体积 > 原文件 70%，或文字已不可读 → 丢弃压缩版，传原文件**，并在汇报里说明。
- 压缩产物写进 scratchpad，**不覆盖用户原文件**；文件名沿用原名加 `-compressed` 后缀。
- 抽帧（1.5 节）已经跑过 `ffprobe`，元信息直接复用，不重复探测。
- 汇报里写一行：`demo.mp4 24.1MB（≤50MB，去音轨后传原文件）` 或 `demo.mp4 132MB → 46MB（native 宽度 / crf 22）`。
- ⚠️ 第 4.7 节嵌图的尺寸要取**实际上传的那个文件**的尺寸，压缩后重新 `sips` / `ffprobe`。

#### 4.6.1 上传
```bash
# token 来源：memory 里的 jira-credentials（各项目自己的 memory 目录）
printf '<email>:%s' "$TOKEN" | base64 > /tmp/jira_auth && chmod 600 /tmp/jira_auth
AUTH=$(cat /tmp/jira_auth)
curl -s -X POST "https://<site>/rest/api/3/issue/<KEY>/attachments" \
  -H "Authorization: Basic $AUTH" -H "X-Atlassian-Token: no-check" -F "file=@<path>"
```
- 上传前 `ls` 确认路径存在；文件名带空格的先复制成无空格名（wiki 嵌入 `!file!` 不吃空格）。
- **逐个上传、失败不中断**：某个失败就打印原因、跳过、继续，最后在汇报里列出失败项。
- `/tmp/jira_auth` 在 4.2 查重时就已生成，此处直接复用 `$AUTH`，不必重建。
- **整套流程（查重 → 建票 → 附件 → 嵌图 → 链接）全部结束后**再 `rm -f /tmp/jira_auth`，token 不落明文。

### 4.7 附件内嵌（靠左 + 真实尺寸）

⚠️ **「上传附件」和「正文里出现这张图」是两件事。** Jira 网页版拖拽一次同时做完两件，走 API 必须分两步——只做 4.6.1 的上传，图只会躺在 Attachments 面板里，正文里看不到。**用户说「放进去 / 放这 / 放上去 / 内嵌 / 嵌进去」都等于要内嵌**，不要停在上传。给了截图/录屏就默认内嵌，**不要问「要不要嵌进正文」**。

⚠️ **改正文前必须先读回。** PUT description / `editJiraIssue` 都是**整段替换**。用户可能刚在网页上拖了新附件进去，你手上的旧副本一 PUT 就把它冲没了。**每次改正文前重新 GET 一遍 ADF**，重建时把既有的每个 media 节点的 `id` / `collection` / `width` / `height` **逐字复制**保留。拿不准就让用户先保存草稿。

#### 路径 A：纯 ADF（推荐，尤其是只加媒体时）

1. **取真实尺寸**：图 `sips -g pixelWidth -g pixelHeight <file>`；视频 `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 <file>`。用**实际上传的那个文件**的尺寸。
2. **拿 media UUID**（内嵌只认 UUID，**数字 attachment id 不行**）。4.6.1 上传返回的是数字 id，用它换 UUID：
   ```bash
   curl -sS -D - -o /dev/null -H "Authorization: Basic $AUTH" \
     "https://<site>/rest/api/3/attachment/content/<attachmentId>"
   # 看 303 的 Location 头：.../file/<MEDIA-UUID>/binary?... → 取 <MEDIA-UUID>
   ```
3. **GET 读回当前 ADF**，在 content 里插入 `mediaSingle` 节点（描述用 `editJiraIssue` / PUT v3，评论用 `addCommentToJiraIssue`，两边节点形状完全一样）：
   ```json
   { "type": "mediaSingle",
     "attrs": { "layout": "align-start" },
     "content": [ { "type": "media", "attrs": {
       "type": "file", "id": "<MEDIA-UUID>", "collection": "",
       "width": 1080, "height": 2424 } } ] }
   ```
   （文件原生 1080×2424；`mediaSingle` 上**不要**写 width。）
4. **PUT 后 GET 确认** layout 与尺寸生效。

#### 路径 B：wiki 语法（正文和媒体一起大改时更省事）
1. PUT v2 `description`（**wiki 语法**：`*bold*`、`# 有序列表`），**带全文 + 末尾 `!file1!` `!file2!`**——wiki 会替换整段描述。
2. GET v3 `?fields=description` 读回 ADF → 每个 `mediaSingle.attrs.layout` 由 `center` 改 `align-start`；每个 `media` 的 `width`/`height` 按 UUID 改成真实像素（wiki 转换默认塞 200px 缩略尺寸）→ PUT v3 回去。
3. PUT 后 GET 确认 layout 与尺寸生效。

#### 已知报错（都是踩出来的）
| 症状 | 原因 | 修法 |
|---|---|---|
| `ATTACHMENT_VALIDATION_ERROR` | media 节点里用了**数字 attachment id** | 换成 303 Location 里的 media UUID |
| `INVALID_INPUT` | 漏了 `collection` | 必填，且必须是**空字符串** `""` |
| 图渲染成**极小一张** | 在 `mediaSingle.attrs` 上写了 `width` / `widthType` | `mediaSingle.attrs` 只留 `{"layout": "align-start"}`；尺寸只放在**内层 `media`** 节点 |
| 媒体居中 | wiki 转换默认 `layout: "center"` | 一律改 `align-start`（团队约定：**所有图和视频靠左 + 原始尺寸**，正文和评论同一规则） |
| 之前的图/视频不见了 | PUT 整段覆盖 | 改前先 GET 读回，逐字保留既有 media 节点 |

#### 用户直接粘在对话里的图（没有文件路径）
磁盘上通常没有这个文件。**不要去模拟器/真机重新截图**（画面可能已经变了、设备可能正在跑自动化）。从当前会话的 transcript 里取：`~/.claude/projects/<project-dir>/<session-id>.jsonl`（session id 在 scratchpad 路径里），逐行解析 `message.content[]` 里 `type=="image"` 且 `source.type=="base64"` 的块，取最后一个，按 `media_type` 决定 png/jpg 落盘，再 `sips` 取尺寸走正常上传流程。

### 4.7.1 正文里的 URL 与票号（**建完票必做**）

⚠️ **走 API 建票时，正文里的裸 URL 和票号只是纯文本，点不动。** Jira 网页端手打时是前端在识别并补 link mark，`createJiraIssue` 的 markdown → ADF 转换**不做这件事**。复现步骤里的商品/页面链接、Note 里引用的 `<KGM-xxxx>`，用户点不开就得手动复制粘贴——这是开票后最容易被回头挑的一点（<KGM-xxxx> 实测，2026-09-03）。

**适用于正文里出现的每一种链接**，不只是商品页：Slack 会话 / 线程（`*.slack.com/archives/...`）、Figma 设计稿（`figma.com/design/...`、`figma.com/file/...`）、Confluence 需求页、CDN 商品页、STG 环境页面、以及引用的其它票号。写 bug 时贴 Slack 讨论出处和 Figma 设计对照是常事，这些恰恰是开发最需要点开的。

建票后 GET 读回 ADF，给每个 text 节点里的 URL 和票号补 `link` mark 再 PUT 回去：

```python
# URL 永远是 ASCII（RFC 3986），所以直接用 ASCII 字符类 —— 比"排除几个中文标点"可靠得多
URL_RE = re.compile(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+")
KEY_RE = re.compile(r'\b[A-Z][A-Z0-9]+-\d+\b')          # 票号 KEY-123 → https://<site>/browse/KEY-123
TRAIL  = ".,;:!?)]}'\""                                  # 只剩 ASCII 尾标点要处理

def clean(url):
    """剥尾部标点；但 URL 自带的成对括号要留住（.../Foo_(bar)）。"""
    while url and url[-1] in TRAIL:
        if url[-1] == ')' and url.count('(') > url.count(')') - 1:
            break                                        # 这个 ) 是 URL 自己的
        url = url[:-1]
    return url

url = clean(m.group(0))                                  # 先剥尾部标点，再当 href
marks = list(node.get("marks", [])) + [{"type": "link", "attrs": {"href": url}}]
```
（以上正则 2026-09-09 跑过 12 组用例全通：中文句号 / 全角括号 / Slack `?thread_ts=&cid=` / Figma `?node-id=&t=` / 端口 + 锚点 / percent 编码 / 日文紧贴无空格 / 包裹括号 / URL 自带括号 / 一行多个 URL。）
把命中的 text 节点**按匹配位置切成多段**（前缀文本 / 带 link mark 的那段 / 后缀文本），其余节点原样保留。

- ⚠️ **尾部标点必须剥掉**。`[^\s]+` 只排除空白，中文句号「。」、逗号「，」、右括号「）」都不是空白，会被吃进 href 里，链接直接 404。中文正文里这是必然踩到的。
  ⚠️ **只靠 `rstrip` 剥不干净**：全角**左**括号「（」不在尾标点集合里，`https://x.co/a（备注）` 会剥掉「）」后停在「注」，href 变成 `https://x.co/a（备注` —— 照样 404（2026-09-09 实测）。**根治办法是用上面那个 ASCII 字符类**，让非 ASCII 字符压根匹配不进 URL；日文正文里 URL 后面直接跟假名（`詳細はhttps://ex.co/aを参照`）也一并解决。
- ⚠️ **别在 query string 上截断**。Slack 线程链接带 `?thread_ts=...&cid=...`，Figma 带 `?node-id=...&t=...`，这些是定位到具体楼层 / 具体画板的关键，截掉就只跳到频道首页或文件首页，等于没给。用 `[^\s...]+` 一次吃到底，不要按 `?` 或 `&` 分割。
- **超长链接可以换成短标签**：Slack / Figma 链接常有一两百字符，直接铺在正文里很难读。这时 ADF 的 `text` 写 `Slack thread` / `Figma design`，`marks[].attrs.href` 放完整 URL——显示是短标签，点击照样跳对地方。商品页、环境页这类本身就短、且 URL 里带商品码有信息量的，保持原样展示。
- **与 4.7 嵌图同一个 PUT 里做完更省事**，但顺序上要先嵌图再补链接，或反过来——**无论哪个顺序，每次 PUT 前都重新 GET**，别拿旧副本覆盖（4.7 已有的告警同样适用）。
- PUT 后读回校验：既有的 `mediaSingle` 节点还在、`layout` 与尺寸没变，且每个该带链接的 text 都有 `link` mark；**顺手点开验一下 Slack / Figma 那几条**，确认没被标点或 query 截断带偏。
- 票号正则别写死成某个项目，用 `[A-Z][A-Z0-9]+-\d+`；但要注意**别把 Actual 里的 UI 文案误伤**（日文文案里不会出现这种形状，一般安全）。同理，URL 已经匹配成链接的那一段里若含票号形状的子串，不要二次匹配。
