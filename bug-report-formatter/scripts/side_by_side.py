#!/usr/bin/env python3
"""把 2 张或更多证据图拼成一张对比图：卡片样式、平台标签、✕/✓ 小标签、红框圈出问题部位。

对应 SKILL.md 1.7 节。默认样式来自一次「好丑」反馈后被接受的版本（2026-11 团队实测）：
  · 浅灰底 #F4F5F7、外边距 56、图间距 64；每张图是圆角 28 + 柔和阴影的卡片
  · 卡片上方：粗体平台标签（如 `iOS 789`），下面一个小标签：
      红色 `×  <实际>（0:09）`（bug 那一侧） / 绿色 `✓  <预期>（0:06）`（正确行为对照）
  · 顶部一行英文标题；问题部位用红色圆角框（#E53935）圈出
  · 尺寸统一，只缩不放：
      给了 --density（iOS @2x 写 2、Android @1.6x 写 1.6）→ 按密度对齐到最低那档，两端物理尺寸一致
      没给 → 按高度（上下拼时按宽度）对齐到最小那张
    同尺寸同密度的图不会被重采样；要保持原生像素加 --no-equalize
  · 字体：ヒラギノ角ゴシック W6。它没有简体中文字形，图上的文字只用英文和日文；用 `×` 不用 `✗`

用法（任意张数，参数按 --image 的顺序一一对应）:
  python3 side_by_side.py --out combined.png --title "Delivery slot shows wrong date" \\
      --image ios.png     --label "iOS 789"     --density 2   --tag "x:Shows 07/28 (0:09)" \\
      --image android.png --label "Android 491" --density 1.6 --tag "ok:Shows 07/29 (0:06)" \\
      --box 0:120,640,700,760 --box 1:90,500,560,600

两张图的旧写法照旧可用（--left/--right/--left-label/--right-label/--left-box/--right-box）。

坐标是**原生像素**、相对各自那张图的左上角，格式 x1,y1,x2,y2；脚本按缩放比例换算。
--box 前面的数字是图的序号（从 0 开始）。--tag 以 `x:` 开头是红色（实际/有问题），
以 `ok:` 开头是绿色（预期/正确对照），不带前缀是灰色。
"""

import argparse
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("❌ 需要 Pillow：pip3 install Pillow\n"
             "   （不要用 ImageMagick 替代，macOS 上常常没装 —— SKILL.md 1.7）")

BG = (0xF4, 0xF5, 0xF7)
TEXT = (0x1F, 0x23, 0x28)
BOX_RED = (0xE5, 0x39, 0x35)
TAGS = {
    "x": ((0xC6, 0x28, 0x28), (0xFF, 0xEB, 0xEE), "×  "),
    "ok": ((0x2E, 0x7D, 0x32), (0xE8, 0xF5, 0xE9), "✓  "),
    "": ((0x45, 0x4F, 0x5B), (0xE4, 0xE7, 0xEB), ""),
}

# 粗体在前；ヒラギノ角ゴシック 能渲染英文 + 日文
BOLD_FONTS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
REGULAR_FONTS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
] + BOLD_FONTS


def load_font(size, bold=True):
    for path in (BOLD_FONTS if bold else REGULAR_FONTS):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    print("⚠️  找不到ヒラギノ字体，日文可能显示成方块")
    return ImageFont.load_default()


def parse_box(s):
    parts = s.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(f"框坐标要 4 个数 x1,y1,x2,y2，收到 {s!r}")
    try:
        x1, y1, x2, y2 = (int(float(p)) for p in parts)
    except ValueError:
        raise argparse.ArgumentTypeError(f"框坐标必须是数字：{s!r}")
    if x2 <= x1 or y2 <= y1:
        raise argparse.ArgumentTypeError(f"框坐标要求 x2>x1 且 y2>y1，收到 {s!r}")
    return (x1, y1, x2, y2)


def parse_indexed_box(s):
    if ":" not in s:
        raise argparse.ArgumentTypeError(f"--box 要写成 <图序号>:x1,y1,x2,y2，收到 {s!r}")
    idx, rest = s.split(":", 1)
    try:
        idx = int(idx)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--box 的图序号必须是整数：{s!r}")
    return idx, parse_box(rest)


def parse_tag(s):
    for kind in ("x", "ok"):
        if s.startswith(kind + ":"):
            return kind, s[len(kind) + 1:].strip()
    return "", s.strip()


def text_size(draw, text, font):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t, t


def draw_boxes(img, boxes, k):
    """在拼接前的单张图上画红色圆角框（SKILL.md 1.7 C：不要拼完缩放后再画）。"""
    d = ImageDraw.Draw(img)
    width, radius = max(3, round(5 * k)), round(10 * k)
    drawn = []
    for (x1, y1, x2, y2) in boxes:
        cx1, cy1 = max(0, x1), max(0, y1)
        cx2, cy2 = min(img.width - 1, x2), min(img.height - 1, y2)
        if cx2 <= cx1 or cy2 <= cy1:
            print(f"⚠️  框 {(x1, y1, x2, y2)} 完全落在图外（图 {img.width}x{img.height}），已跳过")
            continue
        if (cx1, cy1, cx2, cy2) != (x1, y1, x2, y2):
            print(f"⚠️  框 {(x1, y1, x2, y2)} 超出图边界，已裁到 {(cx1, cy1, cx2, cy2)}")
        d.rounded_rectangle([cx1, cy1, cx2, cy2], radius=radius, outline=BOX_RED, width=width)
        drawn.append((cx1, cy1, cx2, cy2))
    return drawn


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=radius, fill=255)
    return mask


def main():
    ap = argparse.ArgumentParser(
        description="拼接 2 张或更多证据图并圈注（SKILL.md 1.7）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--image", action="append", default=[], help="一张图，按出现顺序排，可重复")
    ap.add_argument("--label", action="append", default=[], help="平台标签，如 \"iOS 789\" / \"Android 12 (Pixel 4 XL) · 491\"")
    ap.add_argument("--tag", action="append", default=[], help="小标签：\"x:<实际>（0:09）\" / \"ok:<预期>（0:06）\"；不需要就传 \"\"")
    ap.add_argument("--density", action="append", type=float, default=[], help="屏幕密度：iOS @2x 写 2、@3x 写 3，Android 按 dpi/160（如 1.6）")
    ap.add_argument("--box", type=parse_indexed_box, action="append", default=[], help="<图序号>:x1,y1,x2,y2（原生像素，可重复）")
    ap.add_argument("--left", help="旧写法：左图")
    ap.add_argument("--right", help="旧写法：右图")
    ap.add_argument("--left-label", default="")
    ap.add_argument("--right-label", default="")
    ap.add_argument("--left-box", type=parse_box, action="append", default=[])
    ap.add_argument("--right-box", type=parse_box, action="append", default=[])
    ap.add_argument("--arrow", action="store_true", help="（旧参数，卡片样式下不再画箭头，保留以免旧命令报错）")
    ap.add_argument("--out", required=True, help="输出文件")
    ap.add_argument("--title", default="", help="顶部一行标题（英文）")
    ap.add_argument("--stack", action="store_true", help="上下排列（默认左右）")
    ap.add_argument("--gap", type=int, default=None, help="图间距像素（默认 64，随尺寸放大）")
    ap.add_argument("--no-equalize", action="store_true", help="保持原生像素、不统一尺寸")
    args = ap.parse_args()

    paths, labels, tags, dens = list(args.image), list(args.label), list(args.tag), list(args.density)
    boxes = {}
    for idx, b in args.box:
        boxes.setdefault(idx, []).append(b)
    if args.left or args.right:
        if paths:
            sys.exit("❌ --image 与 --left/--right 不要混用")
        if not (args.left and args.right):
            sys.exit("❌ 旧写法需要同时给 --left 和 --right")
        paths = [args.left, args.right]
        labels = [args.left_label, args.right_label]
        boxes = {0: args.left_box, 1: args.right_box}
    n = len(paths)
    if n < 2:
        sys.exit("❌ 至少要两张图（--image 重复两次以上，或 --left + --right）")
    for name, lst in (("--label", labels), ("--tag", tags), ("--density", dens)):
        if lst and len(lst) != n:
            sys.exit(f"❌ {name} 有 {len(lst)} 个，--image 有 {n} 张，要一一对应（不需要的传 \"\"）")
    labels = labels or [""] * n
    tags = [parse_tag(t) for t in tags] if tags else [("", "")] * n
    for idx in boxes:
        if not 0 <= idx < n:
            sys.exit(f"❌ --box 的图序号 {idx} 超出范围（共 {n} 张，序号从 0 开始）")

    try:
        imgs = [Image.open(p).convert("RGB") for p in paths]
    except (OSError, IOError) as e:
        sys.exit(f"❌ 打不开图片: {e}")
    native = [(im.width, im.height) for im in imgs]

    # 尺寸统一，只缩不放
    scales = [1.0] * n
    if not args.no_equalize:
        if dens:
            target = min(dens)
            want = [target / d for d in dens]
        else:
            dim = (lambda im: im.width) if args.stack else (lambda im: im.height)
            low = min(dim(im) for im in imgs)
            want = [low / dim(im) for im in imgs]
        for i, s in enumerate(want):
            if s < 0.999:
                imgs[i] = imgs[i].resize((max(1, round(imgs[i].width * s)), max(1, round(imgs[i].height * s))), Image.LANCZOS)
                scales[i] = s

    # 样式尺寸随图大小放大：以约 700px 宽的手机截图为基准
    k = min(3.0, max(1.0, max(im.width for im in imgs) / 700))
    px = lambda v: round(v * k)
    pad, gap = px(56), (args.gap if args.gap is not None else px(64))
    card_r, shadow_blur, shadow_off = px(28), px(18), px(8)
    f_title, f_label, f_tag = load_font(px(32)), load_font(px(36)), load_font(px(24), bold=False)

    drawn = []
    for i, im in enumerate(imgs):
        s = scales[i]
        drawn.append(draw_boxes(im, [tuple(round(v * s) for v in b) for b in boxes.get(i, [])], k))

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    label_h = (text_size(probe, "Ag", f_label)[1] + px(14)) if any(labels) else 0
    tag_h = (text_size(probe, "Ag", f_tag)[1] + px(14) * 2 + px(16)) if any(t for _, t in tags) else 0
    head_h = label_h + tag_h
    title_h = (text_size(probe, "Ag", f_title)[1] + px(32)) if args.title else 0

    if args.stack:
        canvas_w = pad * 2 + max(im.width for im in imgs)
        canvas_h = pad * 2 + title_h + sum(head_h + im.height for im in imgs) + gap * (n - 1)
    else:
        canvas_w = pad * 2 + sum(im.width for im in imgs) + gap * (n - 1)
        canvas_h = pad * 2 + title_h + head_h + max(im.height for im in imgs)

    canvas = Image.new("RGB", (canvas_w, canvas_h), BG)
    d = ImageDraw.Draw(canvas)
    if args.title:
        _, _, top = text_size(d, args.title, f_title)
        d.text((pad, pad - top), args.title, fill=TEXT, font=f_title)

    x, y = pad, pad + title_h
    for im, label, (kind, tag) in zip(imgs, labels, tags):
        cy = y
        if label:
            _, _, top = text_size(d, label, f_label)
            d.text((x, cy - top), label, fill=TEXT, font=f_label)
            cy += label_h
        if tag:
            fg, bg, prefix = TAGS[kind]
            text = prefix + tag
            tw, th, top = text_size(d, text, f_tag)
            ph, pv = px(18), px(14)
            d.rounded_rectangle([x, cy, x + tw + ph * 2, cy + th + pv * 2], radius=(th + pv * 2) // 2, fill=bg)
            d.text((x + ph, cy + pv - top), text, fill=fg, font=f_tag)
        img_y = y + head_h
        # 卡片阴影 + 圆角
        shadow = Image.new("RGBA", (im.width + shadow_blur * 4, im.height + shadow_blur * 4), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle(
            [shadow_blur * 2, shadow_blur * 2, shadow_blur * 2 + im.width, shadow_blur * 2 + im.height],
            radius=card_r, fill=(0, 0, 0, 46))
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        canvas.paste(shadow, (x - shadow_blur * 2, img_y - shadow_blur * 2 + shadow_off), shadow)
        canvas.paste(im, (x, img_y), rounded(im, card_r))
        if args.stack:
            y = img_y + im.height + gap
        else:
            x += im.width + gap

    canvas.save(args.out)
    parts = [f"{w}x{h}" if s == 1.0 else f"{w}x{h}→{im.width}x{im.height}"
             for (w, h), im, s in zip(native, imgs, scales)]
    print(f"✅ {args.out}  {canvas.width}x{canvas.height}  （{' + '.join(parts)}）")
    if any(s != 1.0 for s in scales):
        how = "按 --density 对齐到最低密度" if dens else "按高度对齐到最小那张（给 --density 可按物理尺寸对齐）"
        print(f"   已{how}，只缩不放；要保持原生像素请加 --no-equalize")
    if not any(drawn):
        print("⚠️  没有画任何红框 —— SKILL.md 1.7 要求拼图必须圈出问题部位，请补 --box")
    print("   下一步：走 4.6 上传 + 4.7 内嵌（靠左、内层 media 用真实尺寸），拼图放在视频上方")


if __name__ == "__main__":
    main()
