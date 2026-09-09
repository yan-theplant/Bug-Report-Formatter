#!/usr/bin/env python3
"""解析 iOS .ips 崩溃日志，输出可直接写进 bug 报告的结论。

用法:
    python3 parse_ips.py <crash.ips> [<crash2.ips> ...]

传多份时，除逐份摘要外还会做跨 build 比对（堆栈相同 → 回归性结论可直接写）。

.ips 的结构是「一行 JSON 头 + 紧接一个 JSON 体」，不是单个 JSON 文件。
"""

import json
import re
import sys
from datetime import datetime

# ---- watchdog / 终止原因码 ----------------------------------------------------
EXIT_CODES = {
    "0x8badf00d": ('watchdog kill（"ate bad food"）', "主线程被卡住太久，系统强制杀掉，不是异常崩溃"),
    "0xdead10cc": ('watchdog kill（"dead lock"）', "后台持有系统资源（文件锁 / SQLite）不放被杀"),
    "0xbaaaaaad": ("用户主动触发的堆栈快照", "不是崩溃"),
    "0xc00010ff": ('过热被杀（"cool off"）', "设备过热"),
    "0x2bad45ec": ("安全违规被杀", ""),
}

# 主线程栈里出现即高度可疑的符号 → 卡点性质
STUCK_HINTS = [
    ("__ulock_wait", "在等锁"),
    ("_dispatch_once_wait", "卡在 dispatch_once（另一个线程正在执行该 once 块且未返回）"),
    ("_dispatch_thread_event_wait", "在等 dispatch 事件"),
    ("semaphore_wait", "在等信号量"),
    ("_dispatch_semaphore_wait", "在等 dispatch 信号量"),
    ("__psynch_mutex_wait", "在等 pthread mutex"),
    ("__semwait_signal", "在等信号量"),
    ("nanosleep", "在 sleep"),
    ("mach_msg2_trap", "在等 mach 消息（可能只是正常 runloop）"),
]


def load_ips(path):
    """读 .ips：第一行是 header JSON，其余是 payload JSON。"""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    lines = text.split("\n", 1)
    try:
        header = json.loads(lines[0])
    except (json.JSONDecodeError, IndexError):
        header = {}
    payload = {}
    if len(lines) > 1:
        try:
            payload = json.loads(lines[1])
        except json.JSONDecodeError:
            # 有些导出是单个完整 JSON
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                pass
    if not payload and header:
        payload = header
    return header, payload


def parse_ts(s):
    """'2026-09-02 18:04:45.6190 +0900' → datetime"""
    if not s:
        return None
    m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)", str(s))
    if not m:
        return None
    stamp = m.group(1)
    fmt = "%Y-%m-%d %H:%M:%S.%f" if "." in stamp else "%Y-%m-%d %H:%M:%S"
    try:
        return datetime.strptime(stamp, fmt)
    except ValueError:
        return None


def frames_of(thread, images):
    """把一个 thread 的 frames 解成 ['ImageName symbol+off', ...]"""
    out = []
    for fr in thread.get("frames", []):
        idx = fr.get("imageIndex")
        img = ""
        if isinstance(idx, int) and 0 <= idx < len(images):
            img = images[idx].get("name") or ""
        sym = fr.get("symbol") or ""
        if not sym:
            off = fr.get("imageOffset")
            sym = f"+{off}" if off is not None else "?"
        out.append(f"{img} {sym}".strip())
    return out


def main_thread(payload):
    threads = payload.get("threads") or []
    for t in threads:
        if t.get("triggered"):
            return t
    # 没有 triggered 标记时退回 queue 名为 main 的，或第 0 号线程
    for t in threads:
        if t.get("queue") == "com.apple.main-thread" or t.get("name") == "main":
            return t
    return threads[0] if threads else {}


def summarize(path):
    header, payload = load_ips(path)
    info = {"path": path}

    info["app"] = payload.get("procName") or header.get("app_name") or "?"
    info["version"] = header.get("app_version") or payload.get("bundleInfo", {}).get(
        "CFBundleShortVersionString", "?"
    )
    info["build"] = header.get("build_version") or payload.get("bundleInfo", {}).get(
        "CFBundleVersion", "?"
    )
    info["os"] = header.get("os_version") or payload.get("osVersion", {}).get("train", "?")
    info["model"] = payload.get("modelCode") or header.get("slice_uuid", "?")
    info["visibility"] = payload.get("procRole") or payload.get("ProcessVisibility") or ""

    ex = payload.get("exception", {}) or {}
    info["exc_type"] = ex.get("type", "")
    info["exc_signal"] = ex.get("signal", "")
    info["exc_subtype"] = ex.get("subtype", "")

    term = payload.get("termination", {}) or {}
    info["term_ns"] = term.get("namespace", "")
    info["term_code"] = term.get("code", "")
    info["term_indicator"] = term.get("indicator", "")
    info["term_details"] = term.get("details", []) or []
    info["term_reasons"] = term.get("reasons", []) or []

    # watchdog 码：termination.code 是十进制，也可能出现在 details 文本里
    code_hex = ""
    if isinstance(info["term_code"], int):
        code_hex = hex(info["term_code"] & 0xFFFFFFFF)
    blob = json.dumps(term, ensure_ascii=False).lower() + " " + json.dumps(ex, ensure_ascii=False).lower()
    for known in EXIT_CODES:
        if known in blob or known == code_hex:
            code_hex = known
            break
    info["code_hex"] = code_hex
    info["code_meaning"] = EXIT_CODES.get(code_hex, ("", ""))

    launch = parse_ts(payload.get("procLaunch"))
    exit_ts = parse_ts(payload.get("procExit") or payload.get("captureTime") or header.get("timestamp"))
    info["launch"] = launch
    info["exit"] = exit_ts
    info["alive"] = (exit_ts - launch).total_seconds() if (launch and exit_ts) else None

    images = payload.get("usedImages", []) or []
    mt = main_thread(payload)
    info["stack"] = frames_of(mt, images)
    info["thread_name"] = mt.get("name") or mt.get("queue") or "?"

    stack_blob = " ".join(info["stack"])
    info["hints"] = [(sym, why) for sym, why in STUCK_HINTS if sym in stack_blob]

    # 卡点嫌疑：栈上第一个非系统库的符号
    SYSTEM = ("libsystem", "libdispatch", "libobjc", "libc++", "CoreFoundation", "Foundation", "dyld")
    info["suspect"] = ""
    for fr in info["stack"]:
        if not any(s in fr for s in SYSTEM):
            info["suspect"] = fr
            break
    return info


def is_watchdog(info):
    return bool(info["code_hex"] in ("0x8badf00d", "0xdead10cc")) or "SIGKILL" in str(info["exc_signal"])


def parseable(info):
    """能不能当成一份崩溃日志用 —— 至少要有崩溃性质或者一条栈。"""
    return bool(info["exc_type"] or info["exc_signal"] or info["term_ns"] or info["stack"])


def render(info):
    p = print
    p("=" * 78)
    p(f"文件: {info['path']}")

    if not parseable(info):
        p("⚠️  这个文件里读不到任何崩溃信息 —— 不是 .ips 崩溃日志，或格式不认识。")
        p("   .ips 应当是「一行 JSON 头 + 一个 JSON 体」。请确认取的是")
        p("   设置 > 隐私与安全性 > 分析与改进 > 分析数据 里的 <AppName>-<日期>-<时间>.ips。")
        p("   Android 崩溃请用 `adb logcat -b crash -d`，本脚本只解 iOS .ips。")
        return
    p(f"App : {info['app']}  版本 {info['version']} (build {info['build']})")
    p(f"设备: {info['model']}  OS {info['os']}"
      + (f"  进程角色: {info['visibility']}" if info["visibility"] else ""))
    p("-" * 78)

    if is_watchdog(info):
        p("崩溃性质: ⚠️  不是异常崩溃 —— 主线程卡死，被系统 watchdog 强制杀掉")
    elif info["exc_type"]:
        p(f"崩溃性质: {info['exc_type']} {info['exc_signal']}".rstrip())
    else:
        p("崩溃性质: 未能从日志判定")

    if info["exc_type"] or info["exc_signal"]:
        p(f"  exception : {info['exc_type']} / {info['exc_signal']} {info['exc_subtype']}".rstrip())
    if info["term_ns"]:
        p(f"  termination: {info['term_ns']} {info['term_indicator']} code={info['term_code']}".rstrip())
    if info["code_hex"]:
        name, why = info["code_meaning"]
        p(f"  终止原因码 : {info['code_hex']}" + (f"  = {name}" if name else ""))
        if why:
            p(f"               {why}")
    for d in info["term_details"][:4]:
        p(f"  details    : {d}")
    for r in info["term_reasons"][:4]:
        p(f"  reasons    : {r}")

    p("-" * 78)
    if info["launch"]:
        p(f"进程启动: {info['launch']}  (procLaunch)")
    if info["exit"]:
        p(f"被杀/退出: {info['exit']}")
    if info["alive"] is not None:
        p(f"存活时长: {info['alive']:.1f}s  ← 写进标题和 Actual，如 '~{round(info['alive'])}s after launch'")
        p(f"          反推录屏位置: 崩溃时刻 {info['exit'].strftime('%H:%M:%S.%f')[:-3]} "
          f"− 录屏起始时刻 = 视频内相对秒数（见 SKILL.md 1.5.1 步骤 3）")

    p("-" * 78)
    p(f"触发线程: {info['thread_name']}")
    if info["hints"]:
        p("卡点判读:")
        for sym, why in info["hints"]:
            p(f"  · {sym} → {why}")
    if info["suspect"]:
        p(f"嫌疑点(栈上第一个非系统符号): {info['suspect']}")
        p("  ⚠️ 按 SKILL.md 铁律，归因措辞用「疑似 / 待确认」，不要下结论")
    p("主线程栈顶 15 帧:")
    for i, fr in enumerate(info["stack"][:15]):
        p(f"  {i:2d}  {fr}")
    if len(info["stack"]) > 15:
        p(f"  ... 另有 {len(info['stack']) - 15} 帧")

    # ---- 可直接粘的草稿 ----
    p("-" * 78)
    p("Actual 草稿（英文，按需改写）:")
    if is_watchdog(info):
        alive = f"roughly {round(info['alive'])} seconds after launch" if info["alive"] is not None else "shortly after launch"
        p(f"  The app is terminated by the system watchdog {alive}")
        if info["launch"] and info["exit"]:
            p(f"  (procLaunch {info['launch'].strftime('%H:%M:%S.%f')[:-3]} -> "
              f"killed {info['exit'].strftime('%H:%M:%S.%f')[:-3]}).")
        p(f"  The crash report is not an exception but a watchdog kill on a stuck main thread:")
        p(f"  {info['exc_type']} ({info['exc_signal']}) / {info['term_ns']} {info['code_hex']}".rstrip())
    else:
        p(f"  The app crashes with {info['exc_type']} ({info['exc_signal']}) {info['exc_subtype']}".rstrip())
        if info["suspect"]:
            p(f"  Top non-system frame: {info['suspect']} (suspected, to be confirmed).")
    p("")
    p("别忘了（SKILL.md 1.5.1 步骤 5）:")
    p("  · Steps 里要有崩溃前的操作 + 切后台动作，不能只写 'open the app'")
    p("  · Actual 里附上系统崩溃弹窗的原文（日文照抄不翻译）")
    p("  · .ips 原文件要作为附件上传，说明里写清 build 和日期")


def compare(infos):
    infos = [i for i in infos if parseable(i)]
    if len(infos) < 2:
        return
    print("=" * 78)
    print(f"跨日志比对（{len(infos)} 份）")
    print("=" * 78)
    groups = {}
    for info in infos:
        key = tuple(info["stack"][:8])
        groups.setdefault(key, []).append(info)

    for key, members in groups.items():
        builds = ", ".join(f"{m['version']} (build {m['build']})" for m in members)
        dates = ", ".join(m["exit"].strftime("%Y-%m-%d %H:%M:%S") if m["exit"] else "?" for m in members)
        print(f"\n堆栈组（栈顶 8 帧相同）: {len(members)} 份")
        print(f"  build : {builds}")
        print(f"  时间  : {dates}")
        if len(members) > 1:
            oldest = min((m for m in members if m["exit"]), key=lambda m: m["exit"], default=None)
            print("  ✅ 同一堆栈跨多个 build 复现 → 回归行可直接写确定值，不必写 ⚠️ TBD：")
            if oldest:
                print(f"     『否，{oldest['version']} (build {oldest['build']}) 已存在』"
                      f"（{oldest['exit'].strftime('%Y-%m-%d %H:%M:%S')} 的 .ips 堆栈完全相同）")
            print("     并可省掉「去装旧包复验」那一轮（SKILL.md 1.5.1 步骤 4）")

    if len(groups) > 1:
        print(f"\n⚠️ 检测到 {len(groups)} 组不同堆栈 —— 这是 {len(groups)} 个不同的 bug，"
              "**不要合成一张票**（SKILL.md 1.5.1 步骤 4）")


def main():
    paths = sys.argv[1:]
    if not paths:
        print(__doc__)
        return 2
    infos = []
    for p in paths:
        try:
            info = summarize(p)
        except FileNotFoundError:
            print(f"❌ 找不到文件: {p}")
            continue
        except Exception as e:  # 日志格式千奇百怪，不要因为一份解析失败就全挂
            print(f"❌ 解析失败: {p} ({type(e).__name__}: {e})")
            continue
        infos.append(info)
        render(info)
    if len(infos) > 1:
        compare(infos)
    return 0 if infos else 1


if __name__ == "__main__":
    sys.exit(main())
