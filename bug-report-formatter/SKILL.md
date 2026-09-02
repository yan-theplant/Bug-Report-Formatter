---
name: bug-report-formatter
description: |
  缺陷报告规范器：把零散、口语化的 bug 描述（+ 截图/录屏）整理成字段完整、格式统一、
  可直接粘进 Jira 的高质量 bug 报告；并按既定规则判定优先级（Highest/High/Medium/Low）
  且给出判定依据。适用于任意项目、任意 Jira 站点、Web / iOS / Android 三端。
  标题与复现步骤一律英文输出。给了录屏时会自动用 ffmpeg 抽帧、按视频里的实际点击顺序写步骤
  （没装 ffmpeg 会提示安装）。报告固定包含「上个版本是否正常 / 另一端是否复现 / 是否阻塞使用」
  三项回归信息，以及按平台定死的环境必填集。进入 skill 先自行分流「JMA 版本回归」还是
  「通用 bug 提交」（按票号 / 产品名 / 5.x.xx 版本号 / 回归总票等信号判定），不反问用户。可只出「报告文本」，也可继续在 Jira 直接建票
  （附件去音轨、>50MB 才压；媒体一律靠左内嵌进正文；含链接方向校验）。回归期会把新票挂到当期回归总票上。
  用户说「放进去 / 放这 / 内嵌 / 嵌进去」指的就是把图或录屏嵌进正文/评论，不是只当附件传上去。
  触发：用户说「写个 bug 报告」「规范化一下这个 bug」「开票」「建 bug」「create bug/issue」，
  或我（Claude）测试中发现 bug 需要记录时。
---

# Bug Report Formatter（缺陷报告规范器）

**角色**：你是资深 QA，专精规范化缺陷报告撰写。目标是——输入零散信息，产出一份格式统一、字段完整、可直接粘进 Jira 的报告，减少开发反复追问，并从源头保证缺陷数据规范（便于后续看板按模块/平台/优先级聚合）。

## 0. 先分流：JMA 版本回归 · 还是通用 bug（**每次进 skill 的第一步**）

在问模式、写任何文案之前，**先自己判一次路线**，不要反过来先问用户「这是回归吗」。判完在开场第一句话里用一行说明走的哪条路线（例：`按 JMA 5.5.60 回归路线处理（MDX，挂总票 <MDX-xxxx>）`），用户不反对就继续。

### 判定信号（命中任一 → **JMA 回归路线**）
- 票号是 `MDX-xxxxx` / `JMA-xxxx`，或用户贴了 目标站点的 MDX/JMA 链接
- 提到麦当劳日本相关产品名：**麦当劳 / McDonald / McDJP / JMA / MOP / MDS / McDelivery / MMR / PLX / Plexure / Tsukimi / KODO**
- 出现 **release 版本号 `5.x.xx`** 或 **四位 build 号**（iOS ~17xx / Android ~13xx）
- 说了「这个版本的回归」「回归测到的」「regression」「挂到总票」
- 环境写成 `UAT` / `STG` / `PROD` 且对象是 app 两端

### 判定信号（**通用路线**）
- 完全没有上述任何信号，或明说是别的项目 / 别的 Jira 站点
- 桌面 Web 后台类产品（如 QORTEX PIM 等），与麦当劳无关

### 两条路线的差别

| | **JMA 回归路线** | **通用路线** |
|---|---|---|
| 项目配置 | **必须先读 `projects/MDX.md`**（动 JMA 老票再加读 `JMA.md`），全程以它为准 | 只走本文件通用规则；有对应 `projects/<KEY>.md` 才读 |
| 项目 key | 默认 `MDX`，不问用户 | **问用户要 key** |
| 环境段 | `UAT` / `STG` / `PROD` | `PRD` / `STG` / `DEV` |
| 版本号 | 标题写 build、回归行写 release（两套，别混） | 按用户给的写 |
| 回归三问（1.6 节） | **硬拦截**，`⚠️ TBD` 不能过关；建票前必须有确定值 | 允许 `⚠️ TBD 未验证`，不阻塞出报告 |
| 查重 | `project = MDX`（可 `OR project = JMA`）+ **英日双搜** + 额外搜上一 release 版本号 | 单语言按现象搜即可 |
| 链接 | 现查当期回归总票 → 范围内 `Blocks` / 范围外 `Discovery - Connected` | 用户给目标票才链，默认 `Blocks` |
| 模块 | 只能落在 MDX 功能区白名单（第 7 节），落不进就问 | 从步骤推断并标注 |
| 必填字段 | MDX 的 `reporter` 必填 | 建票前跑一次 createmeta 查必填 |

### 被空手调起（用户只说「写个 bug 报告」，还没给任何内容）
此时**没有任何信号可判，不要硬猜、也不要声明路线**。先按第 1 节要素索取信息，并在索取清单里**顺带把分流所需的那一项问掉**——不是问「这是回归还是普通 bug」，而是问**事实**：

> 哪个项目 / 有票号吗（如 `<MDX-xxxxx>`）？如果是 JMA 版本回归，给我 release 版本号（如 `5.5.60`）和 build 号。

拿到回答后**立刻按上面的信号判定路线并声明**，再往下走。⚠️ 不要等写完报告才发现该走回归路线——环境段写法、版本号体系、回归三问是否硬拦截都依赖这个判定，事后返工等于重写。

### 判不准怎么办
只在**信号相互矛盾**时才问用户（例：提到麦当劳但票号是别的项目 key），一次问清「走 MDX 回归还是开在 <某项目>」，别为了保险每次都问。信号完全缺失**且用户已给了 bug 内容** → **默认通用路线**，不要臆测成 JMA。

⚠️ **分流不是让用户二选一的菜单**：路线由我从信号推断，用户只需回答事实（项目 / 票号 / 版本号）。只有信号矛盾时才让用户裁决。

---

## 0.1 再定模式

| 模式 | 何时用 | 产出 |
|------|--------|------|
| **A. 只出报告** | 用户只要文本，或没有 Jira 访问 | 规范化报告（可直接复制） |
| **B. 报告 + 建票** | 用户说「开票 / 建 bug / create issue」 | 报告 + 真实 Jira 票（走第 4 节） |

默认 A。用户提到 Jira/开票才走 B。**A 模式绝不调用任何 Jira 写操作。**

模式与第 0 节的路线是两个独立维度：JMA 回归路线同样可以只出报告（A），通用路线也可以建票（B）。

### 先加载项目级配置（**A / B 模式都要**）
本 skill 目录下的 `projects/<KEY>.md` 是各项目的专属约定（标题风格、模块白名单、版本号体系、回归硬拦截、经办人）。

```bash
ls ~/.claude/skills/bug-report-formatter/projects/
```
- 用户给了票号（`<JMA-xxxx>`）、项目名、或提到该项目的产品名 → **读对应的 `projects/<KEY>.md`**，之后全程按它走。
- 命中不了任何项目文件 → 走本文件的通用规则。
- **冲突时以项目文件为准**（例：MDX 用 `UAT`/`PROD` 而非 `PRD`；MDX 的 `reporter` 是建票必填字段）。
- 目前已有：
  - **`MDX.md`** —— 麦当劳日本 app / web（McDJP、JMA、MOP、MDS、MMR、PLX、Tsukimi）。**app bug 默认开在 MDX**，含 JMA 版本回归的总票与链接规则。
  - `JMA.md` —— 仅指向 MDX + 动 JMA 老票时的差异，JMA 项目已基本停用。

---

## 0.5 首次使用环境预检（每台机器只需一次）

不要等到第 4.6 节上传失败才发现少装东西。**本会话第一次用这个 skill 时先跑一次预检**，把缺的一次性列给用户；之后同一会话不再重复跑。

```bash
for c in ffmpeg ffprobe jq curl sips; do
  printf '%-8s %s\n' "$c" "$(command -v $c || echo '❌ 缺失')"
done
ls ~/.claude/projects/*/memory/jira-credentials.md 2>/dev/null || echo '❌ 无 jira-credentials memory'
```

Token 有效性（有 credentials 时，B 模式才需要跑）：
```bash
curl -s -o /dev/null -w '%{http_code}\n' "https://<site>/rest/api/3/myself" -H "Authorization: Basic $AUTH"
```
`200` = 可用；`401/403` = token 过期，按 4.5.1 提示用户去 https://id.atlassian.com/manage-profile/security/api-tokens 重开。

缺失项的处置：

| 缺什么 | 影响 | 怎么办 |
|--------|------|--------|
| `ffmpeg` / `ffprobe` | 读不了录屏、**检测/去不了音轨**（4.6.0 必做项）、做不了 before/after 拼图（1.7）、压不了视频 | 提示 `brew install ffmpeg`。**是系统级安装，先问用户，别默认替他装** |
| `sips` | 主要影响**取不到图片原生像素尺寸** → 4.7 内嵌的 `width`/`height` 会填错、图显示变形；其次压不了图（macOS 自带，一般不缺） | 尺寸退用 `mdls -name kMDItemPixelWidth -name kMDItemPixelHeight <file>`；图片压缩直接跳过传原图 |
| `jq` | 查重结果没法解析 | 提示 `brew install jq` |
| `jira-credentials` memory | 附件传不上、查重要走慢的 MCP | 让用户给 Jira 站点 / 邮箱 / API token，我写进 memory |
| Python `Pillow` | 拼不了 before/after 与双端对比图（1.7 节） | 提示 `pip3 install Pillow`。**别用 ImageMagick 替代**，macOS 上常常没装 |
| `pngquant`（选装） | PNG 压缩率低一些 | 不提示，静默跳过 |

**一次性把缺失项和安装命令列全**，不要挤牙膏式地一个个报。用户选择不装 → 记下降级路径（不读录屏则走口述、不压缩则直传原文件），继续往下走，不要卡住。

---

## 1. 输入解析

从用户的零散描述中抽取并归位到字段。来源有两种，处理相同：
- **用户发现的 bug**：中文/口语描述（可能附截图/录屏）→ 我整理、按需转英文。
- **我测试发现的 bug**（跑 Playwright / 手动操作撞到的）→ 我根据自己的复现过程直接生成，不用用户给描述。

| 输入项 | 必填 | 缺失时的处理 |
|--------|------|-------------|
| 复现步骤（操作路径、点击顺序） | ✅ | **追问**，不可臆造 |
| 预期 / 实际现象 | ✅ | **追问** |
| **App 版本**（iOS / Android 票） | ✅ | **追问**（这是发现问题时的环境版本，不是修复版本）。Web 票不适用 |
| **环境必填集**（按平台，见下） | ✅ | 能从截图地址栏 / UA / 录屏画面推断的先推断并标注「(推断)」；**推断不出就追问，不要静默删行** |
| 其它环境信息（测试账号、网络） | 选填 | 推断不出**直接省略该行，不追问** |
| **回归 / 跨端信息**（上个版本是否正常 / 是否新出现、另一端是否复现、是否阻塞使用） | ✅ | 见第 1.6 节。未验证写 `⚠️ TBD 未验证`，**绝不留空**；唯一可删行的情形见 1.6 节（无版本号项目 + 无「验证通过过」的参照物） |
| 所属模块（登录、优惠券、结账…） | 选填 | 能从步骤推断则推断并标注；推断不出就问 |
| 截图 / 录屏 | 选填 | 有录屏 → **先按第 1.5 节抽帧自己看**，不要让用户口述；无则附件清单写「无」 |
| 影响范围（多少用户 / 哪些环境命中） | 选填 | 用于定优先级；缺失时按「已观察到的范围」保守估计并写明依据 |

**环境必填集（按平台）** —— 这是开发追问最多的一类信息，所以按平台定死必填项，推断不出就问：

| 平台 | 必填 | 选填（无则删行） |
|------|------|-----------------|
| **Web** | 环境（PRD/STG/DEV）、浏览器 + 版本、出问题页面 URL | 测试账号、网络、屏幕分辨率 |
| **iOS / Android** | 环境、**App 版本**（发现问题时的环境版本）、设备型号 + OS 版本 | 测试账号、网络 |

- 浏览器版本 / 设备型号推断路径：截图地址栏与窗口样式、录屏分辨率、UA、手机状态栏样式。推断值标 `(推断)`，仍要让用户确认。
- 必填项确实拿不到 → 写 `⚠️ TBD：<字段>` 并在结尾统一追问，**不能像旧规则那样整行删掉**。

### 铁律
- **绝不臆造未提供的信息**。缺关键字段 → 在输出里用 `⚠️ 待补充：<字段>` 明确标出，并在结尾统一追问。
- 只客观描述现象，**不评价开发、不猜测代码原因**（可疑线索放「备注」，措辞为「疑似 / 待确认」）。
- **语言规则（固定，不用问）**：**标题（Title）和复现步骤（Steps to reproduce）一律英文**；预期结果 / 实际结果同样用英文，便于开发对照。字段名与其它说明性内容（优先级依据、备注、附件说明）可用用户输入的语言。**UI 文案原文照抄不翻译**（如「ログイン」「洗涤注意」「Update Product」）。

---

## 1.5 录屏 / 截图解析（有视频时**必做**）

用户给了录屏（`.mp4` / `.mov` / `.gif`）时，**先自己抽帧看内容，再写报告**——不要让用户口述操作路径。

### 步骤 1：检查 ffmpeg
```bash
command -v ffmpeg ffprobe || echo "NO_FFMPEG"
```
- **没装** → 立刻告诉用户一句：
  > 检测到你提供了录屏，但本机没装 ffmpeg，我无法抽帧看内容。运行 `brew install ffmpeg` 后我就能自己读录屏、按视频里的实际点击顺序写复现步骤（否则需要你口述操作路径）。

  然后**问用户是装还是口述**，别默认替他装（`brew install` 是系统级安装）。用户说装 → 用 Bash 后台执行 `brew install ffmpeg`，装完继续。用户选口述 → 走纯追问流程，附件说明标 `⚠️ TBD`。
- **装了** → 直接进步骤 2。

### 步骤 2：抽帧
```bash
# 元信息：分辨率 + 时长（分辨率还用于第 4.7 节嵌图的真实尺寸）
ffprobe -v error -select_streams v:0 -show_entries stream=width,height \
        -show_entries format=duration -of default=nw=1 "<video>"

# 1fps 抽帧到 scratchpad，宽度缩到 ~1500px（够读 UI 文字，又不爆 token）
mkdir -p <scratchpad>/frames
ffmpeg -v error -i "<video>" -vf "fps=1,scale=1500:-1" <scratchpad>/frames/f%02d.png
```
- 视频长（>60s）就降到 `fps=1/2` 或 `fps=1/3`，控制在 **25–30 帧**以内。
- **不要把所有帧都读进来**：先读首帧 + 中段 + 末帧（如 f01 / f06 / f12 / f18 / f24）定位大致流程，再按需补读关键帧。
- 没装 ffmpeg 时的降级手段：`mdls -name kMDItemPixelWidth -name kMDItemPixelHeight -name kMDItemDurationSeconds <video>` 只能拿到尺寸和时长，**读不到画面内容**，不足以写步骤。

### 步骤 3：从帧里提取这些信息，直接落进报告字段
| 从录屏读什么 | 落到哪个字段 |
|-------------|------------|
| 应用名 / 侧边栏 logo（如 `QORTEX PIM`）、菜单项 | 所属模块；⚠️ **若与用户口述的模块不一致，如实指出并让用户确认归属** |
| 面包屑 / 页面标题（如 `Catalog > Products > Xinyi001`、`Edit Product`） | 标题的「功能区 > 具体页面」分段 + 复现步骤的导航路径 |
| 地址栏 URL、环境标识 | 环境、URL。⚠️ **Web 票的 URL 是必填**（第 1 节），读不到写 `⚠️ TBD` 并追问，**不能删行**；APP 票没有 deeplink 才删行 |
| 登录用户名 / 邮箱（如 `<tester-email>`） | 测试账号 |
| 状态徽标、字段值（如 `Status: Draft · Not published`） | 前置条件 |
| **鼠标位置 + 光标变化 + 每帧的画面变化 → 逐个点击动作** | **Steps to reproduce（按视频里的实际点击顺序，英文，每步一个动作）** |
| Toast / 错误提示 / 弹窗**原文** | Actual（原文照抄，不翻译） |
| 页面操作区实际有哪些按钮 | Actual 里的「实际显示了什么」对照项 |
| 分辨率（如 3022×1846 = 桌面）、是否有手机状态栏 | 平台判定（Web vs iOS/Android） |

**复现步骤写法**：按录屏时间顺序拆成编号动作，每步写清「点哪个具体元素」。同一动作反复出现（如连点某按钮 4 次无响应）要写成一步并注明重复与无响应。

**附件说明必须带时间点**，例：
```
- demo.mp4 (3022×1846, 25.7s) — 0:00–0:17 repeatedly clicking the `Scheduled` badge with no response;
  0:08 bottom action area shows only `Update Product`; 0:11 success toast; 0:23 Change History panel
```

### 步骤 4：把从录屏推断的内容标出来
录屏里**看得见**的写成事实；看不见但被推断的（如权限是在哪授予的、复现率、是否有其它入口）仍标 `⚠️ TBD`，**不要因为"视频里大概是这样"就当成已确认**。

---

## 1.6 回归 / 跨端信息（**每张票必出**）

开发打回的高频三问是「上个版本是好的吗？」「另一端是好的吗？」「这个影响使用吗？」。这三问在模板里有固定落位，未验证也要**明确写出未验证**——写出「没验」本身就挡掉了追问。

| 字段 | 取值 | 说明 |
|------|------|------|
| 上个版本是否正常 | `是（已在 <版本号> 验证正常）` / `否，<版本号> 已存在` / `⚠️ TBD 未验证` | **仅适用于有版本号体系的项目**；无版本号的项目改问「是否新出现」，见下 |
| 另一端是否复现 | `Android 正常，仅 iOS 复现` / `iOS 同样复现` / `N/A（Web 票）` / `⚠️ TBD 未验证` | 双端项目必写 |
| 是否阻塞使用 | `阻塞` / `有 workaround：<绕过方式>` / `不影响使用，可 can-be-ignored` | 直接进优先级依据 |

### ⚠️ 先判断这个项目有没有「版本号体系」，再决定回归那一项怎么问
「上个版本是否正常」预设了存在可指名的 build / release 号。**持续部署的 Web 项目没有这个东西**，硬写一行 `Regression: ⚠️ TBD` 既指不出「上个版本」是哪个、也不给开发任何信息，纯属噪音——反而违背了「写 TBD 是为了挡追问」的初衷。

判断方法：APP 票 / 项目文件里写了版本号体系 / 票上 `versions`·`fixVersions` 字段在用 → **有**；持续部署的 Web（环境域名里没有版本概念，票上版本字段常年为空）→ **无**。

| | 有版本号体系（APP、带 release 号的 Web） | 无版本号体系（持续部署 Web） |
|---|---|---|
| 问法 | **上个版本是否正常** | **是否新出现** |
| 取值 | `是（已在 <ver> 验证正常）` / `否，<ver> 已存在` / `⚠️ TBD 未验证` | `Newly appeared（<日期/上次测试> 时正常）` / `Long-standing（一直如此）` / `⚠️ TBD 未验证` |
| 参照物 | release / build 号 | **某次「验证通过过」的日期** |
| 拿不到时 | 写 `⚠️ TBD 未验证`，**保留该行** | 确实无从判断（首次测这块、没有历史结论）→ **整行删掉**，不要留一个指不出参照物的 TBD |

⚠️ **「可比时间点」只能是「那时候是好的」的日期，不能是「发现 bug 的日期」。**
`first observed 2026-04-03` 这类写法是**假参照物**——它对「之前是好的还是一直坏的」零信息量，属于本节明令要删的噪音；不要因为句子里带了个日期就以为满足了条件。手上只有发现日期 → **删行**。

无版本号项目的回归行写法示例：
- ✅ `Regression: Newly appeared — was OK on 2026-03-20 regression run.`（参照物 = 那次验证通过）
- ✅ `Regression: Long-standing — also reproducible before the 2026-04 deploy.`
- ✅ `Regression: ⚠️ TBD — this area was last verified OK on 2026-03-20, not re-checked since.`（参照物成立，只是没复验）
- ❌ `Regression: ⚠️ TBD — first observed 2026-04-03, not checked against an earlier deploy.` —— **发现日期不是参照物**，这行该删掉，而不是这么写

- 我自己测出来的 bug：能顺手在另一端 / 上一版本验一下就验，验了写结论，没验写 `⚠️ TBD 未验证`，不要凭印象填。
- 用户口述的 bug：这三项**在结尾追问里逐条列出**，但不阻塞报告输出——先出报告，把 TBD 标清楚。
- 回归期（跟着某个版本回归总票走）时，前两项由项目级配置升级为**硬追问项**：B 模式建票前必须有确定值。
- ⚠️ **APP 项目常有两套版本号**：build 号（四位数、两端各自递增，如 iOS `1739` / Android `1362`）与 release 版本（三段式、两端共用，如 `5.5.60`）。
  **标题的平台段写 build 号，回归行写 release 版本**。用户只给一个：四位数 → build；带两个点 → release；分不清就问，别混用。
- 回归行的措辞**优先套用项目里已有的说法**（例：`Also reproducible on version 5.5.50.`），没有既有说法才用下面的通用格式。
- ⚠️ **「每张票必出」指的是这三问都要被处理过，不等于三行都必须留在正文里**。跨端那项 Web 票写 `N/A`；回归那项在无版本号项目且无参照物时**删行**。真正不许发生的是「压根没想过这三问」，不是「少了一行字」。

---

## 1.7 证据图（**有录屏 / 双端 bug 时必做**）

录屏本身不算证据到位——读者得拖进度条才能看到问题。补两类静态图：

### A. before / after 拼图（有录屏时必出）
- **两步走，别直接用 1.5 的帧拼图**：1.5 抽的帧为了省 token 已经 `scale=1500` 缩过，拿它拼图等于违反下面的「不许重采样」。正确做法是——用 1.5 的 1fps 帧序列**只定位时间点**，拿到 mm:ss 后按该时间点**用原生分辨率重抽一帧**：
  ```bash
  ffmpeg -v error -ss <mm:ss> -i "<video>" -frames:v 1 <scratchpad>/before.png   # 不带 -vf scale
  ffmpeg -v error -ss <mm:ss> -i "<video>" -frames:v 1 <scratchpad>/after.png
  ```
- 各取「触发前」与「触发后」一帧，**按原生像素左右拼接**，每侧标上参照标识 + 画面时间：有版本号体系写 build（如 `1712 · 0:03` / `1723 · 0:11`），无版本号体系写日期或视口宽度（如 `1440px · 0:03` / `768px · 0:11`）。
- 拼图**放在视频上方**，让人不用播放就看到缺陷。
- 视频仍要**完整嵌入**，不要用截图或短片段替代；需要的话额外加一段剪辑版，标清 `Video 1 — side-by-side` / `Video 2 — full recording`。
- **没装 ffmpeg 的降级**：拼图做不出来（1.5 步骤 1 已经问过用户装不装）。此时**不要卡住**——附件说明里标 `⚠️ TBD 拼图未做（本机无 ffmpeg）`，正文照常出，并在结尾追问里带上一句「装了 ffmpeg 我可以补 before/after 拼图」。

### B. 双端对比图（iOS + Android 都涉及时必出）
不要把两端截图作为两张独立图片贴上去，**每个测试场景拼成一张左右对比图**（iOS 左、Android 右），一个场景一张。

- **原生像素粘贴、不缩放**：各图按自身像素尺寸顶部对齐，画布高度取较高的那张。**绝不为了等高而缩放**（会重采样、发虚），宽高比必须与原图 1:1。
- 加一个场景小标题 + 每列标注平台 + build，如 `iOS 5.5.40 (1685)` / `Android 5.5.40 (1334)`。
- 两端数据/门店/账号不同但被测 UI 相同时，在标注里写明（如 `*different store, same UI`）。
- ⚠️ 标注避开字体渲染不了的字符：`→` 在 Helvetica/Arial 里是豆腐块，用 `>` 或 `-`。

工具：macOS 上 ImageMagick 常常没装，**用 Python Pillow** 按原生尺寸粘贴（`pip3 install Pillow`）。原生尺寸用 `sips -g pixelWidth -g pixelHeight <file>`。iOS 模拟器截图 `xcrun simctl io <UDID> screenshot out.png`；Android `adb -s <serial> exec-out screencap -p > out.png`。

拼好的图走 4.6 / 4.7 的正常上传 + 内嵌流程（靠左、内层 media 用真实尺寸）。

---

## 2. 优先级判定（必须附依据）

按**用户影响面**和**功能重要性**判定，二者取**较高**的一档。输出时必须写一行 `依据：...`。

| 优先级 | 判定标准 | 典型例子 |
|--------|---------|---------|
| **Highest** | 影响 **>50%** 用户，或**完全阻断核心业务功能** | 系统宕机；结账/登录/注册完全不可用；所有支付方式均失败 |
| **High** | 影响 **10–50%** 用户，或**严重影响主要功能** | 某常用支付方式不可用；多个地区结账中断；关键数据丢失 |
| **Medium** | 影响 **1–10%** 用户，或影响**次要功能** | 仅特定浏览器/设备复现；功能可用但体验降级；订单历史未即时更新 |
| **Low** | 影响 **<1%** 用户，或**纯外观问题** | 轻微 UI 错位；字体/颜色不一致；静态文案错别字 |

判定要点：
- **有 workaround** 且用户能自行绕过 → 可下调一档，并在依据里写明 workaround。
- **数据丢失 / 金额错误 / 安全与隐私泄露** → 至少 **High**，即使命中用户少。
- 影响面数据缺失时，用「受影响的入口/平台占比」保守估算，依据里写清估算方式（例：「仅 iOS 单端 + 仅优惠券入口 → 估 <10% → Medium」）。
- **回归 vs 既存**（来自第 1.6 节）：确认是**本版本新引入的回归**（上个版本正常）→ **上调一档**，依据里写明「上个版本 <ver> 正常，本版本回归」；确认是**老版本已存在的既存问题** → 不上调，依据里写明。`⚠️ TBD 未验证` 时不作调整，依据里注明「回归性未验证」。
  **无版本号体系的项目**用时间点代替版本号：「2026-03-20 回归时正常，本次新出现」同样按回归**上调一档**；判不出新旧就当既存处理，依据里写「新旧未判定」，不要因为缺版本号就跳过这一档判断。
- **不影响使用 / can-be-ignored**（用户明确判定不影响主流程）→ 映射 **Low**，依据里带上绕过方式。
- 依据格式：`依据：影响范围 <X> + 功能重要性 <Y>（<有/无> workaround）+ <回归/既存/回归性未验证> → <档位>`

> 若目标 Jira 项目用的是 Severity（Critical/Major/Minor）而非 Priority，映射：Highest→Critical，High→Major，Medium/Low→Minor，并同时给出两者。

---

## 3. 输出格式（标准报告）

### 标题（**必须英文**）
`[<Module>] <one-line problem>`

带环境/平台维度的项目（如需与既有票风格一致）用面包屑式：
`<环境> > <平台(版本)> > <功能区> > <具体模块/页面/条件> > <问题>`

规则：
- **必须写出「具体出问题的模块/页面」**，别从大区域直接跳到问题。
  - ✅ `STG > iOS(645) > Checkout > Coupon change modal > Category coupons are listed in a different order than Web/Android`
  - ❌ `STG > iOS(645) > Coupon change modal shows coupons in a different order`（少了功能区分段）
- **标题保持简洁**：测试账号、地址、邮编、商品 code、订单号等**具体数据一律放进复现步骤**，不写进标题。
- 平台段写法：Web = 只写区域不带平台；单端 = `iOS(<环境版本>)` / `Android(<环境版本>)`；双端 = `Android(<ver>)/iOS(<ver>)`。**APP 票的版本号是「发现问题时的环境版本」，不是修复版本**；没有就问用户。
- 平台判定：鼠标 hover/光标/桌面布局 → Web；APP 专属交互/崩溃 → iOS/Android。不确定就问。
- ⚠️ **分隔符必须是字面 `>` 字符，绝不能 HTML 转义**。在 `summary` 里写 `&gt;` 会让 Jira 存下字面五个字符 `&gt;`（summary 是纯文本字段，不是 HTML）——某张老票上实测踩过（内部记录 2026-07）。`&amp;` / `&quot;` 同理，直接写 `&` / `"`。

### 正文模板

```
**所属模块 / 平台：** <模块> / <Web | iOS | Android>
**优先级：** <Highest | High | Medium | Low>
依据：影响范围 <…> + 功能重要性 <…>（<有/无> workaround）→ <档位>

**环境：**（必填集按平台，见第 1 节的表；必填项缺失写 ⚠️ TBD，不删行）
- 环境：<PRD / STG / DEV>                        ← 必填
- App 版本：<iOS App 645 | Android App 309>      ← **APP 票必填**；Web 票删掉此行
- 设备 / OS：<iPhone 15 Pro / iOS 17.5>          ← **APP 票必填**；Web 票删掉此行
- 浏览器：<Chrome 126>                            ← **Web 票必填**；APP 票删掉此行
- URL：<出问题的页面链接>                          ← **Web 票必填**；APP 票有 deeplink 才写
- 以下选填，**有就写、没有就整行删掉，不要留空、不要追问**：
- 测试账号：<…>
- 网络：<Wi-Fi / 4G>

**回归 / 跨端：**（三问都要处理过；未验证写 ⚠️ TBD 未验证，删行只有 1.6 节列的那一种例外）
- 上个版本是否正常：<是（已在 644 验证正常）| 否，644 已存在 | ⚠️ TBD 未验证>
  ← 无版本号体系的持续部署项目改问「是否新出现」，参照物用日期：<Newly appeared（2026-03-20 时正常）| Long-standing | 无可比时间点则整行删掉>，见 1.6 节
- 另一端是否复现：<Android 正常，仅 iOS 复现 | iOS 同样复现 | N/A（Web 票）| ⚠️ TBD 未验证>
- 是否阻塞使用：<阻塞 | 有 workaround：<绕过方式> | 不影响使用，可 can-be-ignored>

**前置条件：**
- <初始状态、账号权限、数据准备…>

**Steps to reproduce:**（**必须英文**）
1. …
2. …
3. …

**Actual:**（英文）
<实际发生了什么；含错误码 / 提示原文>

**Expected:**（英文）
<应该发生什么>

**附件：**
- <文件名> — <这张图说明什么>

**备注：**
<补充信息、影响范围、疑似关联票、风险提示>
```

**Actual 在 Expected 之前**（团队约定，2026-08）：读者先看到「哪里坏了」，再看「本该是什么」。两份 skill 早期写法不一致，以此为准。

**复现步骤重写规则**：编号、每步一个动作、**可被他人独立复现**（含具体入口、点击对象、输入数据）。口语里的「然后就那样了」要拆成可执行动作；拆不出来的部分标 `⚠️ 待补充`。

**同一个 bug 有多条复现路径 → 拆 Case，不要揉成一段叙述**
例如「升级安装后」与「不升级、只退出再进页面」都能复现，就保持顶部四段模板不变，把 `Actual:` 写成按 case 标注的 bullet，再在下方给每个 case 各自的证据块：

```
**Case 1 - <条件，如 in-place upgrade 5.5.50 (1712) -> 5.5.60 (1723)>:**
<带 mm:ss 时间点的 bullet 时间线>
**Screenshots - before / after <触发点>:**  <before/after 拼图>
**Recording:**  <录屏>

**Case 2 - <另一个条件，如 no upgrade, leave and re-enter the menu>:**
… 同样三部分 …
```

编号统一用 `Case 1` / `Case 2`，并从 `Actual:` 的 bullet 里引用这些标签，让读者能把每条结论对上对应证据。

### 自检（输出前必过）
1. 必填字段齐全（复现步骤、预期/实际、按平台的环境必填集、回归/跨端三行），缺失项都已用 `⚠️ TBD` 标出。
2. **标题、Steps to reproduce、Actual、Expected 全部是英文**。
3. 标题符合格式，且含「具体模块/页面」。
4. 优先级带判定依据。
5. 复现步骤他人可独立复现，无「同上」「那个页面」等指代。
6. 实际/预期**分列**，不混在一句里，且顺序是 **Actual 在前、Expected 在后**。
7. 环境部分：该平台的**必填行一行不缺**（拿不到的写 `⚠️ TBD`），选填行无值的已整行删掉，没有空占位行。
8. 回归/跨端三问都处理过（跨端 Web 写 `N/A`；回归项在无版本号且无参照物时按 1.6 节删行，其余情况必须在），且优先级依据里体现了回归 / 既存 / 未验证的判断。
9. 有录屏时：已抽帧看过，步骤按视频里的实际点击顺序写，附件说明带时间点，且已按 1.7 节补了 before/after 拼图（双端 bug 补左右对比图）。
10. 无对开发的评价、无臆造信息。
11. 可直接粘进 Jira，无需二次排版。

---

## 4. 建票模式（B）—— 通用 Jira 流程

> 不绑定任何具体项目。**项目 key、站点、经办人、优先级默认值都从用户处确认，不硬编码。**

### 4.1 确认目标
- **项目 key**：优先看本 skill 的 `projects/<KEY>.md`（见第 0 节）；其次看当前工作目录的项目级 skill / CLAUDE.md；都没有就**问用户**（要 key，如 `ABC`；注意项目**显示名 ≠ key**）。命中项目文件时，站点 / cloudId / 必填字段 / Priority 取值都直接用文件里的，不再探测。
- **站点 / cloudId**：`mcp__claude_ai_Atlassian__getAccessibleAtlassianResources` 取；多站点时问用户。
- **issueType**：`Bug`（项目无此类型则用 `getJiraProjectIssueTypesMetadata` 查实际可用类型）。

### 4.2 查重（**写文案之前先做**）
⚠️ **顺序很重要**：抽完帧、搞清现象之后**立刻查重**，不要等文案写完再查——命中老票的话整段文案就白写了。

**查重一律走 curl + jq，不用 `searchJiraIssuesUsingJql`。** 原因：那个 MCP 工具的 `fields` / `maxResults` 参数不生效，照样返回整个 GraphQL 节点（实测 84k–362k 字符），必然超 token 上限被落盘，再补一轮 Bash+jq 才拿到结果 —— 一次调用中位 7.5s、最慢 26s，一次开票查 2–5 次就白烧 30–90 秒和好几个模型回合。curl 直取字段 0.2s 出结果。

```bash
# 认证：与 4.6 同一套（memory 里的 jira-credentials）
printf '<email>:%s' "$TOKEN" | base64 > /tmp/jira_auth && chmod 600 /tmp/jira_auth
AUTH=$(cat /tmp/jira_auth)
Q='project = <KEY> AND summary ~ "<关键词>" ORDER BY created DESC'
curl -s -G "https://<site>/rest/api/3/search/jql" -H "Authorization: Basic $AUTH" \
  --data-urlencode "jql=$Q" --data-urlencode 'fields=summary,status,created,reporter' \
  --data-urlencode 'maxResults=20' \
| jq -r '.issues[] | [.key, .fields.status.name, (.fields.created[0:10]), .fields.reporter.displayName, .fields.summary] | @tsv'
```
- 多个关键词**一次 curl 一条 JQL**，用 `OR` 拼（`summary ~ "A" OR summary ~ "B"`），别拆成多次调用。
- **日文票要同时搜英文措辞、英文票同时搜日文**：历史上漏判过两次重复票 —— `レイアウト崩れ` 漏了标题写成 `The layout is broken.` 的 <KGM-xxxx>，`複数回/連打` 漏了写成 `Double-click` 的 <KGM-xxxx>。至少覆盖：UI 文案原文 + 对应英文动词/名词。
- 命中面太窄时把 `summary ~` 换成 `text ~`（搜正文与评论），但仍只取上面那几个 field。
- 关键词取「模块 + 现象」里最独特的那个词（UI 文案原文往往最准，如 `指定時間より前の受け取り`），不要用长句。
- **关键词不要带平台段**（`iOS` / `Android`），否则会漏掉标题只写另一端的老票。
- **同一版本回归期内最容易开重复票**：截断 / 溢出 / 布局错位 / 连点这几类现象在一轮回归里常出现多次（实测某次回归 `truncated` 出现 3 次）。这几类**必须先搜再写文案**。
- 只有在没有 token / curl 不通时才退回 `searchJiraIssuesUsingJql`，并预期要落盘 + jq。
- **命中疑似重复 → 立刻停下来报给用户**，别继续写文案。列成表格：票号 / 状态 / 标题 / 对应本次的哪个现象，并给出选项：
  1. 不新建，把本次复现（新版本号 + 录屏）追加为老票评论；
  2. 新建一张合并票，relates to 老票；
  3. 按现象拆多张。
  同时给出你的建议（老票仍 Open 且是同一处逻辑 → 建议选 1）。用户定了再往下走。
- 没命中 → 直接进 4.3。

### 4.3 唯一确认关卡：文案 + 字段 + 查重结论一次性抛出
**只设一道关卡**，不要「先确认文案、再确认草稿」分两轮——用户通常在第一条消息里就把票的字段（项目、经办人、link 目标）一起给了，拆两轮纯属浪费往返。

一次性输出：Title / Description 全文 + 一行 Jira 字段 + 查重结论。用户回「确认」就直接执行 4.5 起的写操作。

**B 模式的 description 用下面这个精简版**（不是第 3 节那份完整模板）——只保留会真正进 Jira 正文的部分：环境一行 + Steps / Actual / Expected（+ 可选 Note）。**优先级依据、附件清单、前置条件、所属模块这些不写进 description**，它们走 Jira 字段或放在关卡②的草稿里。

输出格式**照抄这个骨架**：

```
Title
<环境> > <平台(版本)> > <功能区> > <具体模块/页面（可带日文原文，如 Delivery time selection modal (配達時間の選択)）> > <问题>

Description
Environment: <STG-2 (iOS) | PRD (Web) | …>

**Steps to reproduce:**
1. …
2. …
3. …

**Actual:**
<实际发生了什么；UI 文案原文照抄，如 本日 07月28日(火)>

**Expected:**
<应该发生什么；可引用参照物，如 "the same as on Web (see the Web screenshot)">

Regression: Worked on <release ver>; new in <release ver>. / Also reproducible on version <release ver>. / Not verified on <release ver>. | <另一端>: OK / same issue / not verified / N/A

Note: <可选。只在需要划定范围 / 排除误解时写一句，如「日期已经是粗体，只有时段没有」>
```

规则：
- `Title` / `Description` 两个裸标签**单独成行、不加粗**，后面直接跟内容。
- Steps / Actual / Expected **必须英文**（**Actual 在 Expected 之前**）；UI 文案、地址、邮编、商品 code 原文照抄。
- 多条复现路径 → 按第 3 节的 `Case 1` / `Case 2` 拆开，各带自己的证据块。
- Environment 只写一行，但**该平台的必填项都要并进这一行**（Web：环境 + 浏览器版本 + URL；APP：环境 + App 版本 + 设备/OS）；账号、网络等选填项有必要才写。
- `Regression:` 行内容取自第 1.6 节（英文）；Web-only 项目省掉后半段 `| Android: …`。「是否阻塞使用」不进 description，走优先级依据。
  **该行在有版本号体系的项目里必出**；**无版本号体系的持续部署项目**改用 `Newly appeared / Long-standing` 措辞并以日期为参照，**连可比时间点都没有时整行删掉**——别留一个指不出参照物的 `⚠️ TBD`。
- Note 是可选行，没有就整行删掉。
- 给完文案后，用一行把待确认的 Jira 字段一起抛出，例：
  > 确认这两段文案 OK 吗？（Jira 那边：<KEY> / Bug / <优先级> / assignee <姓名> / 新票 blocks <KEY-123>，附上 <附件列表>）
- 紧跟一行优先级依据；有查重命中就把 4.2 的结论表也附在这条消息里。**这条消息发完就等用户点头，不要再追加第二道草稿关卡。**

### 4.4 收集字段（在 4.3 之前就备好，不单独占一轮对话）
- **优先级**：按第 2 节判定，**带依据一并给出**；用户可覆盖。
- **经办人**：项目文件有规定就用它；否则**默认指给报告人自己（当前用户）**，在 4.3 关卡里作为默认值抛出、用户可改——多数 QA 项目就是自指派，默认成「问用户」纯属多一轮往返。要指给开发时才按名解析：优先用项目文件里的 accountId 表，没有再 `lookupJiraAccountId`（同名多人时列出让用户选；排除 `accountType: customer`）。
  ⚠️ 大站点里近似同名账号很多（`Foo Bar` / `Foo Baz` / `Fool Bar`），**绝不能用 `user/search` 的第一条结果直接指派**。
- **链接**：用户给目标票号时，默认「新票 **blocks** 目标票」；其它关系需用户明说。
  **回归期**：新 bug 默认挂当期回归总票，关系按范围区分——**本次改动范围内的问题 → `Blocks`；范围外顺手撞到的 → 项目里的「发现关联」类型（如 `Discovery - Connected`），没有该类型就 `Relates`**。判断不了就问用户。
  **回归总票号一律现查、不猜**（按项目文件给的命名规则跑一条 JQL，取最新那张进行中的），查到后连票号带标题一起给用户确认。
- **附件**：以用户拖入图片自带的 source 路径为准；**贴哪些传哪些、按贴入顺序**，不去扫文件夹里的其它文件。视频不能预览，让用户给路径。
- **可选字段（components / labels / fixVersions / Severity）：默认不填、也不要问**。项目文件有规定才填；没规定又觉得该填 → 先看这个项目近 50–100 张 bug 的实际使用率，几乎没人填就跳过。别为一个团队根本不用的字段占用户一轮回答。

### 4.5 创建

⚠️ **建票前先确认该项目 Bug 的必填字段**（不同项目不一样，例如有的项目 `reporter` 是必填，漏了直接报错）：项目文件里写了就照用；没写就跑一次
`/rest/api/3/issue/createmeta?projectKeys=<KEY>&expand=projects.issuetypes.fields` → 取 `required: true` 的字段名，一次性备齐再建。

`mcp__claude_ai_Atlassian__createJiraIssue`：cloudId / projectKey / issueTypeName=Bug / summary / description（`contentFormat: markdown`，加粗用 `**…**`、有序列表用 `1.`）/ `assignee_account_id` / `additional_fields: {"priority": {"name": "<档位>"}}`。记下返回的 key。

⚠️ **必填字段兜底**：报错说缺必填字段（Severity / Component / Found-in-version 等）→ 用 `getJiraIssueTypeMetaWithFields` 查该 issuetype 的必填字段，把缺的列给用户补值，用 `additional_fields` 带上重试，别干等报错。

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

##### 压缩阈值：**≤50MB 一律传原文件，不压**
压缩会把录屏里的 UI 文字 / DevTools / console 压糊，那就失去了证据的意义。
```bash
du -h "<file>"   # 先看原始体积
```
- **≤ 50MB → 直接传原文件**（去音轨后），不要压。
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

### 4.8 链接
`getIssueLinkTypes` 查类型 → `createIssueLink`。⚠️ inward/outward 容易反，**建完读回 `fields=issuelinks` 校验方向**，反了删掉重建。
- 校验时读**目标票**的 `issuelinks` 更直观：`<type> ← <新票>` 表示新票在 inward 侧（即「新票 blocks 目标票」，正确）；`<type> → <新票>` 说明方向反了。
- 拿不准某个关系在本项目怎么用 → 读一张同类老票的 `issuelinks` 照着建，比猜语义可靠。

### 4.9 汇报
票号 + URL ✓ / 标题 / 优先级（含依据）/ 经办人 / 状态 / 链接方向（已校验）/ 嵌入了哪些文件 / 失败项。

**中途失败兜底**：票在 4.5 就已创建，若 4.6–4.8 失败**不要重建票**——汇报里带上已建票号 + 卡在哪一步 + 原因，告知可从该步重跑（上传/嵌图/链接均幂等，重跑前先读回当前状态避免重复）。

---

## 5. 边界与限制
- 不臆造未提供的信息；缺关键字段提示或追问，不编造。
- 优先级判定必须附依据，避免主观随意。
- 客观描述现象，不夹带对开发的评价，不下结论式归因。
- **进 skill 第一步先按第 0 节自行分流（JMA 回归 / 通用），并在开场一行说明走的哪条路线**；信号缺失默认通用路线，只在信号矛盾时才问用户。
- A 模式不做任何 Jira 写操作；B 模式**先查重、再一次性确认（文案 + 字段 + 查重结论）**，用户点头才写 Jira。只设这一道关卡，不拆两轮。
- **回归/跨端三问（1.6 节）与按平台的环境必填集（1 节）不可省**：拿不到就写 `⚠️ TBD`，不要静默删行——这两类缺失是开发打回的最高频原因。
  唯一例外：**无版本号体系的持续部署项目**，回归那一项在连可比时间点都没有时删行（1.6 节）——一个指不出参照物的 TBD 不挡追问，只是噪音。
- 附件**清晰度优先**：≤50MB 直接传原文件，只在 >50MB 时压且用原生宽度 + 低 CRF（4.6.0）；压后不可读或压缩率不划算就传原文件，绝不覆盖用户原文件。**视频一律去音轨**，与压不压无关。
- 媒体**必须内嵌进正文/评论**（4.7），不能停在「上传成 attachment」；靠左 + 原生尺寸；改正文前先 GET 读回，别把用户刚拖的附件冲掉。
- 标题里的分隔符写字面 `>`，**不要 HTML 转义**（第 3 节）。
- **写进本文件的团队约定要带来源和日期**（如 `（团队约定，2026-08）`、`<KEY>-xxxx 实测, 2026-07-28`）——半年后才判断得出某条规则还算不算数、是谁定的。
- 项目专属约定（默认项目 key、经办人映射、语言要求、模块白名单、回归期硬追问）**属于项目级配置**，由各项目自己的 skill / CLAUDE.md 提供，本 skill 不硬编码。
