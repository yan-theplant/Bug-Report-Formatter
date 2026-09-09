# 崩溃 / 闪退类 bug 的处理捷径

> `bug-report-formatter` 的参考文件。**只在 bug 是崩溃 / 闪退时读它**，由 `SKILL.md` 1.5 节触发。

## 总原则

崩溃类 bug 不要从录屏画面去找"哪一帧崩的" —— 崩溃日志里有**精确到毫秒**的时间戳，拿它反推录屏里的位置，抽帧量能从几十帧降到 5 帧以内。

⚠️ 实测代价（<MDX-xxxx>，2026-09-03）：先解 `.ips` 已经拿到了完整死锁链和 `procLaunch 18:04:32.325 → killed 18:04:45.619`，进 skill 后却又把 186s 录屏盲扫了一遍 47 帧，思考 11m42s。**日志已经给了答案，就不要再问画面。**

### 步骤 1：先要崩溃日志，再看录屏
| 平台 | 去哪拿 |
|------|--------|
| **iOS 真机** | 设置 > 隐私与安全性 > 分析与改进 > 分析数据，找 `<AppName>-<日期>-<时间>.ips`（**watchdog 杀掉的还会有一份 `UIKit-runloop-<AppName>-*.ips`**，一并取）；TestFlight 崩溃后弹的「共享给开发者」也是这份 |
| **iOS 模拟器 / 已同步的机** | `~/Library/Logs/DiagnosticReports/`、`~/Library/Logs/CrashReporter/MobileDevice/<设备名>/` |
| **Android** | `adb logcat -b crash -d`；或 `adb bugreport`；Play Console / Firebase Crashlytics 的堆栈 |

用户只给了录屏没给日志 → **先问日志**（一句话，跟其它追问合并抛出），别直接开始抽帧。日志确实拿不到才退回画面定位，并在附件说明里标 `⚠️ TBD 无崩溃日志`。

### 步骤 2：解析 `.ips`
本 skill 自带脚本，直接跑：
```bash
python3 ~/.claude/skills/bug-report-formatter/scripts/parse_ips.py <crash>.ips
```
它输出：崩溃性质（异常 / watchdog kill）、终止原因码、进程启动与被杀时间戳、存活时长、主线程栈顶若干帧、以及可直接粘进报告的 `Actual` 草稿。多份日志一起传可做跨 build 比对（见步骤 4）。

`.ips` 是「一行 JSON 头 + 一个 JSON 体」的两段结构，脚本已处理。手动看时的判读要点：

| 看什么 | 含义 |
|--------|------|
| `EXC_CRASH (SIGKILL)` + `FRONTBOARD 0x8BADF00D` | **不是崩溃，是主线程卡死被系统 watchdog 杀掉**（`0x8BADF00D` = "ate bad food"，苹果的经典标记）。Actual 里必须写清这个区别 |
| `EXC_BAD_ACCESS` / `SIGSEGV` | 真的野指针 / 空指针崩溃 |
| `termination.details` 里的 `"...is stuck (deadlock)"` | 死锁，配合主线程栈能指出卡在哪个锁 |
| `procLaunch` → `procExit` / 被杀时刻 | **启动后存活多少秒**，直接进标题和 Actual（如 `~13s after launch`） |
| 主线程栈里 `__ulock_wait` / `_dispatch_once_wait` | 卡在 `dispatch_once`，栈上紧邻的那个符号就是嫌疑点 |
| `ProcessVisibility: Background` | 崩的时候 app 已在后台 —— 复现步骤里必须有「切后台」这一步 |

### 步骤 3：用时间戳反推录屏位置，只抽 ±5s
```bash
# 1. 录屏文件的开始时间（拍摄时刻）
ffprobe -v error -show_entries format_tags=creation_time -of csv=p=0 "<video>"
# 文件名里常常直接带：ScreenRecording_09-02-2026 18-02-33.MP4 → 18:02:33 开始

# 2. 崩溃时刻 − 录屏起始时刻 = 视频内相对秒数
#    例：崩溃 18:04:45.619 − 起始 18:02:33 = 132.6s

# 3. 只抽这个点前后 ±5s，批量一次抽完
for t in 122 127 130 132.6 134; do
  ffmpeg -v error -ss $t -i "<video>" -frames:v 1 <scratchpad>/crash_$t.png
done
```
- 5 帧足够写出 `切后台 → 黑屏 → 崩溃弹窗` 这条时间线，**不需要跑 1.5 节的阶段 A 粗扫**。
- 🔴 **时区必须先对齐再相减**（2026-09-09 实测的坑）：`ffprobe` 读出的 `creation_time` 是 **UTC**（形如 `2026-09-02T18:02:33.000000Z`），而 `.ips` 里的 `procLaunch` / `procExit` 带**本地时区**（形如 `2026-09-02 18:04:45.6190 +0900`）。直接相减会差整 9 小时，反推结果必然落到视频范围外。
  - **文件名里的时间是本地时间**（`ScreenRecording_09-02-2026 18-02-33.MP4` → 18:02:33 JST），跟 `.ips` 同一时区，**优先用文件名**，最省事。
  - 只能用 `creation_time` 时，先按 `.ips` 的偏移量换算（`+0900` → UTC 时刻加 9h），再相减。
  - 自检：算出来的相对秒数应落在 `[0, 视频时长]` 内、且接近末段。**偏出正好 ±9h（或其它整小时）→ 是时区没对齐，不是录屏拍错了**，先换算再说。
- 录屏没有 `creation_time`、文件名也不带时间 → 退回 1.5 阶段 A，但**只粗扫视频最后 1/3**（崩溃几乎总在末段）。
- 反推出的秒数落在视频长度之外、**且已排除上面那条时区问题** → 说明这支录屏拍的不是这次崩溃，**先跟用户对齐是哪一次**，别硬凑。

### 步骤 4：多份日志 = 免费的回归结论
同设备上往往存着**多个 build 的同类崩溃**。把它们一起解，堆栈相同就直接得出回归性结论，省掉「去装旧包复验」那一轮：

- 实测：`<AppName>-UAT-2026-08-31-150941.ips`（build 1761）与 `-2026-09-02-180446.ips`（build 1764）堆栈完全相同（同为 `SIGKILL` + `LocationSource sharedInstance` 的 `dispatch_once` 卡死）→ 回归行可以直接写 `否，5.5.70 (build 1761) 已存在`，不再是 `⚠️ TBD`。
- 堆栈**不同**的两份日志是两个 bug，**不要合成一张票**（同上那次，`JWTToken.isExpired` 的 `EXC_BAD_ACCESS` 是另一个问题，与 watchdog kill 无关）。

### 步骤 5：崩溃票的字段落位
- **标题**：`<环境> > <平台(build)> > <功能区> > <崩溃性质>`，把存活时长写进去。
  例：`UAT > iOS(1764) > Open JMA > App killed by watchdog (0x8BADF00D): main thread deadlocks in LocationSource dispatch_once ~13s after launch`
- **Actual**：写清「不是异常崩溃而是 watchdog kill」+ 两个时间戳 + 系统弹窗**原文**（如 `"[UAT] <アプリ名>" 已崩溃 / 你要将更多信息共享给开发者吗？`）。
- **Steps**：必须包含崩溃前的操作和切后台动作（见 1.5 步骤 5）。
- **附件**：`.ips` 原文件一律作为附件上传（它是最有价值的证据），附件说明里写清是哪个 build、哪一天的。
- **归因措辞**：堆栈指向第三方 SDK 时按第 1 节铁律用「疑似 / 待确认」，不要下结论。
