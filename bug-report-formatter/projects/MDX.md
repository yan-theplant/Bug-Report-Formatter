# MDX 项目级配置（McDJP Digital Channels — 麦当劳日本 app / web，含 JMA 回归）

> 被 `SKILL.md` 第 0 节 / 4.1 节引用。用户提到 **麦当劳 / McDJP / JMA / MOP / MDS / MMR / PLX / Tsukimi**、
> 给出 `MDX-xxxxx` 票号、或说「这个版本的回归」时加载本文件。
> 冲突时**以本文件为准**。

## 0. ⚠️ 项目归属：app bug 现在开在 MDX，不是 JMA

- `JMA` 项目最后一张 bug 是 **<JMA-xxxx>（2026-07-28）**，之后 QA 的 app bug **全部开在 `MDX`**。
- 5.5.60 回归的 18 张 bug 全在 MDX（<MDX-xxxx> ~ <MDX-xxxx>）。
- **默认建在 `MDX`。** 用户明确说要开在 JMA 才用 JMA（见 `JMA.md`）。

## 1. Jira 目标

| 项 | 值 |
|---|---|
| 站点 | `<your-site>.atlassian.net` |
| cloudId | `<YOUR_CLOUD_ID>` |
| 项目 key | `MDX`（显示名 `McDJP Digital Channels [Shared]`） |
| issueType | `Bug` |
| **必填字段** | `project` / `issuetype` / `summary` / **`reporter`** —— ⚠️ MDX 的 `reporter` 是必填，建票时必须带上（默认当前用户 `<your-email>`），漏了会报缺字段 |
| Priority 可选值 | Highest / High / Medium / Low / Lowest（实际用 Highest/High/Medium/Low） |
| components | 有（ANA CMS Coupons Delivery INF JMA KCHP MBE MGMT STAMP WEB）但**近 100 张 bug 只有 2 张填了** → **不填，也不要问用户** |
| fixVersions / labels | 近 100 张 bug **零使用** → 不填，不要问 |

凭证走 memory 里的 `jira-credentials`（同一套站点 token）。

## 2. 两套版本号（最容易搞错）

| 类型 | 形态 | 用在哪 |
|------|------|--------|
| **Build 号** | iOS `1739`、Android `1362`（四位数，两端各自递增） | **标题的平台段**：`iOS(1739)` / `Android(1362)` |
| **Release 版本** | `5.5.60`、`5.5.50`（三段式，两端共用） | **回归对比行** + 回归总票命名 |

- 标题写 build，回归行写 release。例：标题 `iOS(1739)`，正文 `Also reproducible on 5.5.50.`
- 两端 build 差很远是正常的（iOS ~1730-1742 / Android ~1355-1362），不是笔误。
- 四位数 → build；带两个点 → release。分不清就问。

## 3. 标题格式（对齐 MDX 既有风格）

```
<业务前缀（可选）> <环境> > <平台(build)> > <OS 条件（可选）> > <功能区> > <具体模块/页面> > <条件（可选）> > <问题>
```

从近 100 张 MDX bug 归纳：
- **环境段**：`UAT`（约 60%）/ `STG`（约 32%）/ `PROD`。
  ⚠️ MDX 混用过 `PROD` 和 `Prod`；**统一写 `PROD`**（大写，与多数票一致）。别写成 KGM 的 `PRD`。
- **平台段**：单端 `iOS(1739)` / `Android(1362)`；双端 `iOS(1742) / Android(1362)`（**iOS 在前**）。
  非 app 的票没有平台段，直接写载体：`McDelivery web`、`Tsukimi > LP`。
- **业务前缀**：`[MDS]`（McDelivery 配送）· `[JMA]`（明确限定 app 端）· `[PLX]`（Plexure / VMob 侧）。加在环境段之前，例 `[MDS]UAT > iOS(1739) > ...`。
- **OS 条件段**：仅特定 OS / 机型复现时紧跟平台段，例 `iOS 26.5(iPhone SE)`、`iOS 27(iPhone 11)`、`iOS 26、27`。
- 日文 UI 文案原文照抄不翻译（`注文を確定`、`商品の準備を始めてよろしいでしょうか？`、`交換から最大xx日間`）。
- **回归/跨端问题的标题惯例**（现成句式，优先套用）：
  - `... changed from previous version`（<MDX-xxxx>）
  - `... inconsistent with iOS`（<MDX-xxxx>）
  - `... than in 5.5.50`

## 4. 正文结构（**用 SKILL.md 第 3 节的通用模板**）

MDX 的票正文就是通用那套，**不要**用 <JMA-xxxx> 的 `Pre-condition/Description/Expected result/Actual result`：

```
Environment: <UAT (iOS 1739, iPhone SE / iOS 26.5) | STG (Android 1362) | STG (McDelivery web, Chrome 126)>

**Steps to reproduce:**
1. …
2. …

**Expected:**
…

**Actual:**
…

Regression: <见下> | <另一端>: <OK / same issue / not verified>

Note: <可选，划定范围，如「Only reproduces on iPhone SE (narrow screen); larger devices display correctly.」>
```

**Regression 行的写法**（沿用 MDX 已有措辞）：
- 老版本也有：`Also reproducible on version 5.5.50.` ← <MDX-xxxx> 的原话
- 本版本新引入：`Worked on 5.5.50; new in 5.5.60.`
- 没验：`Not verified on 5.5.50.`
- 跨端后半段：`Android: same issue` / `Android: OK` / `Android: not verified` / `N/A (web only)`

`Note:` 的用法看 <MDX-xxxx>：**限定复现条件、排除误解**，一句话，别写成分析。

## 5. 回归期硬拦截（本项目升级为必填）

`SKILL.md` 1.6 节的三问在 MDX 全为**硬追问项**，`⚠️ TBD` 不能过关：

| 字段 | 要求 |
|------|------|
| 上个版本是否正常 | 必须有确定值，写 release 版本号。没验 → 停下来让用户在上一版本复验；用户明确说「不验，按未知开」才放行 |
| 另一端是否复现 | 必须有确定值。两端行为差异本身就是常见 bug 类型（<MDX-xxxx> 标题就是 `inconsistent with iOS`）。只验了一端 → 标题只写该端，Regression 行写 `not verified` 且需用户点头 |
| 是否阻塞使用 | 必须有值，直接进优先级依据 |

- 确认本版本新引入的回归 → **优先级上调一档**，依据里写 `Worked on 5.5.50, regression in 5.5.60`。
- 找不到旧包 → 写 `Not verified on 5.5.50 (no build available)`，不要留空、也不要当成正常。

## 6. 回归总票与链接

- 总票命名：**`[QA] JMA <release> Regression Testing`**，issueType `Task`，开在 **MDX**。
  实例：`<MDX-xxxx>`（5.5.60，In Progress）· `<MDX-xxxx>`（5.5.50）· `<MDX-xxxx>`（5.5.40）· `<MDX-xxxx>`（5.5.30）。
  也有非版本型的专项回归：`[QA] Regression testing for 原産国→原料原産地 changes`（<MDX-xxxx>）。
- **新 bug → `Blocks` → 回归总票**（已在 <MDX-xxxx> 上读回校验：18 张 bug 均为 `<bug> blocks <MDX-xxxx>`）。这就是 SKILL.md 4.4 的默认方向，直接用。
- 只是回归中"顺手发现"、不阻塞本次回归的问题，MDX 用 **`Discovery - Connected`** 关联到总票（例 <MDX-xxxx> / 13729 / 13732）。判断：
  **本次改动范围内的问题 → `Blocks`；范围外撞到的 → `Discovery - Connected`**。不确定就问用户。
- 回归执行票在 **`QA` 项目**（`[McD] JMA 5.5.60 Regression <QA-xxxx> MOP` 等，以 `Test` 关系挂总票），bug 票**不需要**挂这些。
- **总票号不要猜**：用这条 curl 现查当前版本的总票，再确认给用户。
  ```bash
  Q='project = MDX AND summary ~ "Regression Testing" ORDER BY created DESC'
  # fields=summary,status,created，取最新那张 In Progress 的
  ```

## 7. 功能区白名单（模块推断只能落在这些里）

**入口 / 导航**：Bottom tab bar · Home · Homepage banner · Hirumac banner · Featured · Footer Navigation · Navigation bar animation
**订购（MOP）**：Menu · Store menu · PLP · PDP · Nutrition information · Customization · Badge · Filter · Cart · Checkout · Order confirm page · Submit order · Order · Order status screen · Mobile Order · DriveThru · Store Finder
**优惠券**：Coupon tab · Coupon list · Coupon detail · Coupon card · MOP Coupon · Use Coupon · Order at the Store · CLR coupon · Kodo coupon · One time coupon
**会员（MMR）**：MMR · Reward detail page · Reward category · Membership card · Point history · Account page · opt-in
**配送（MDS）**：Delivery · McDelivery web · RPOD · Address list / Pin position · Late night extend · Hybrid store · 3pr payment
**活动 / 外部**：Tsukimi（LP / Stamp / Registration）· PLX（Plexure）· Usabilla · Push notification
**账号 / 通用**：Register · Login · Open JMA（启动/闪退）

- 落不进白名单 → **问用户**，不要自造模块名。确认后**回写进本文件**。

## 8. 经办人

**近 100 张 MDX bug 里 78 张是自己指派给自己**（reporter == assignee）。所以：

- **默认 assignee = reporter = 当前用户**（`<your-email>`），在 4.3 关卡里作为默认值一并抛出，用户不改就这么建。
- 要指给开发时才解析姓名。常用 accountId（省一次 lookup）：

| 姓名 | accountId |
|------|-----------|
| Developer A | `<accountId-dev-1>` |
| Developer B | `<accountId-dev-2>` |
| Developer C | `<accountId-dev-3>` |
| Developer D | `<accountId-dev-4>` |
| Developer E | `<accountId-dev-5>` |
| Developer F | `<accountId-dev-6>` |
| Developer G | `<accountId-dev-7>` |

⚠️ `Developer C` / `Developer E` / `Developer D` / `Developer G` 在站点里都有多个近似同名账号（近似同名账号…），**必须用上表的 id**，不要用 `user/search` 的第一条结果。

## 9. 查重关键词（MDX 专用）

`SKILL.md` 4.2 的 curl 照用，JQL 换 `project = MDX`（回归期可加 `OR project = JMA` 覆盖老票）。
- **英日双搜**：日文 UI 原文 + 对应英文各一次，拼进同一条 JQL 的 `OR`。
- 高频误漏词对：`レイアウト崩れ` ↔ `layout is broken` / `overlaps`；`連打 / 複数回` ↔ `rapid taps / multiple times / double-click`；`表示されない` ↔ `not displayed / missing`；`切れる` ↔ `truncated / cut off`；`落ちる / クラッシュ` ↔ `crash`。
- **回归票额外搜一次 release 版本号**（`summary ~ "5.5.50"`），同版本回归问题常已有票。
- 关键词用**功能区 + 现象**，不要带平台段——否则会漏掉标题只写另一端的老票。
- 截断类问题尤其容易重复：`truncated` 在 5.5.60 回归里就出现了 3 次（<MDX-xxxx> / 13731 / 13732），务必先搜。
