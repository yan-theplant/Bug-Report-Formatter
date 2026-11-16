#!/usr/bin/env python3
"""把 2 张或更多证据图左右/上下拼成一张，加标注，并用红框圈出有问题的部位。

对应 SKILL.md 1.7 节 A / B / C：
  · 尺寸统一：各图高度（上下拼时是宽度）不一致时，把较大的**缩小**到最小那张，只缩不放
    （2026-10 团队反馈：三张截图原生拼接后大小不一，又得追加一次指令）。
    同一台设备的截图本来就一样大，不会被重采样；要保持原生像素就加 --no-equalize
  · 每张图上方标注「OS(设备) · build · 时间点」
  · 红框圈出问题部位：坐标按原生像素给，脚本按缩放比例换算，框画在缩放后、拼接前的图上，
    线宽按最终尺寸自适应

用法（任意张数）:
  python3 side_by_side.py --out combined.png \\
      --image a.png --label "iOS 1766 · 0:03" \\
      --image b.png --label "iOS 1766 · 0:11" \\
      --image c.png --label "Android 1373 · 0:11" \\
      --box 1:1085,240,1470,320 --box 2:1740,205,1900,255 --arrow

两张图的旧写法照旧可用:
  python3 side_by_side.py --out combined.png \\
      --left ios.png --left-label "iOS 1766 · 0:49" \\
      --right android.png --right-label "Android 1373 · 0:49" \\
      --left-box 1085,240,1470,320 --right-box 1740,205,1900,255 --arrow

坐标是**原生像素**、相对各自那张图的左上角，格式 x1,y1,x2,y2。
--box 前面的数字是图的序号（从 0 开始，按 --image 出现的顺序），可重复多次。
"""

import argparse
import math
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("❌ 需要 Pillow：pip3 install Pillow\n"
             "   （不要用 ImageMagick 替代，macOS 上常常没装 —— SKILL.md 1.7）")

RED = (255, 0, 0)
BG = (255, 255, 255)
LABEL_FG = (20, 20, 20)

# 能渲染中日文的字体，按优先级找
FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
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


def stroke_width(img_w):
    """框线宽度随图宽自适应：手机 ~1170px 出 4px，桌面 ~3000px 出 10px。"""
    return max(3, round(img_w / 300))


def text_size(draw, text, font):
    try:
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        return r - l, b - t
    except AttributeError:  # 老版本 Pillow
        return draw.textsize(text, font=font)


def draw_boxes(img, boxes):
    """在拼接前的单张图上画红框（SKILL.md 1.7 C：不要拼完缩放后再画）。"""
    if not boxes:
        return []
    d = ImageDraw.Draw(img)
    w = stroke_width(img.width)
    clipped = []
    for (x1, y1, x2, y2) in boxes:
        cx1, cy1 = max(0, x1), max(0, y1)
        cx2, cy2 = min(img.width - 1, x2), min(img.height - 1, y2)
        if cx2 <= cx1 or cy2 <= cy1:
            print(f"⚠️  框 {(x1, y1, x2, y2)} 完全落在图外（图 {img.width}x{img.height}），已跳过")
            continue
        if (cx1, cy1, cx2, cy2) != (x1, y1, x2, y2):
            print(f"⚠️  框 {(x1, y1, x2, y2)} 超出图边界，已裁到 {(cx1, cy1, cx2, cy2)}")
        d.rectangle([cx1, cy1, cx2, cy2], outline=RED, width=w)
        clipped.append((cx1, cy1, cx2, cy2))
    return clipped


def draw_arrow(d, start, end, width):
    """从 start 指向 end 的直线 + 实心三角箭头。"""
    d.line([start, end], fill=RED, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = width * 4
    p1 = end
    p2 = (end[0] - size * math.cos(ang - math.pi / 7), end[1] - size * math.sin(ang - math.pi / 7))
    p3 = (end[0] - size * math.cos(ang + math.pi / 7), end[1] - size * math.sin(ang + math.pi / 7))
    d.polygon([p1, p2, p3], fill=RED)


def main():
    ap = argparse.ArgumentParser(
        description="拼接 2 张或更多证据图并圈注（SKILL.md 1.7 A/B/C）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--image", action="append", default=[], help="一张图，按出现顺序从左到右（或从上到下）排，可重复")
    ap.add_argument("--label", action="append", default=[], help="与 --image 一一对应的标注，如 \"iOS 1766 · 0:49\"")
    ap.add_argument("--box", type=parse_indexed_box, action="append", default=[],
                    help="<图序号>:x1,y1,x2,y2（原生像素，可重复）")
    ap.add_argument("--left", help="旧写法：左图（双端 bug 惯例：iOS 放左）")
    ap.add_argument("--right", help="旧写法：右图（Android 放右）")
    ap.add_argument("--left-label", default="")
    ap.add_argument("--right-label", default="")
    ap.add_argument("--left-box", type=parse_box, action="append", default=[])
    ap.add_argument("--right-box", type=parse_box, action="append", default=[])
    ap.add_argument("--out", required=True, help="输出文件")
    ap.add_argument("--title", default="", help="顶部场景小标题（1.7 B）")
    ap.add_argument("--arrow", action="store_true",
                    help="从第 0 张图的第一个框指向第 1 张图的第一个框，画一条箭头")
    ap.add_argument("--stack", action="store_true", help="上下拼接（默认左右）")
    ap.add_argument("--gap", type=int, default=0, help="图与图之间的留白像素（默认 0）")
    ap.add_argument("--no-equalize", action="store_true",
                    help="保持原生像素、不统一尺寸（默认把较大的图缩小到与最小那张同高/同宽）")
    args = ap.parse_args()

    paths, labels = list(args.image), list(args.label)
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
    if len(paths) < 2:
        sys.exit("❌ 至少要两张图（--image 重复两次以上，或 --left + --right）")
    if labels and len(labels) != len(paths):
        sys.exit(f"❌ --label 有 {len(labels)} 个，--image 有 {len(paths)} 张，要一一对应（没有标注就传 \"\"）")
    labels = labels or [""] * len(paths)
    for idx in boxes:
        if not 0 <= idx < len(paths):
            sys.exit(f"❌ --box 的图序号 {idx} 超出范围（共 {len(paths)} 张，序号从 0 开始）")

    try:
        imgs = [Image.open(p).convert("RGB") for p in paths]
    except (OSError, IOError) as e:
        sys.exit(f"❌ 打不开图片: {e}")
    native = [(im.width, im.height) for im in imgs]

    # 尺寸统一：左右拼看高度、上下拼看宽度，较大的缩小到最小那张，只缩不放
    scales = [1.0] * len(imgs)
    if not args.no_equalize:
        dim = (lambda im: im.width) if args.stack else (lambda im: im.height)
        target = min(dim(im) for im in imgs)
        for i, im in enumerate(imgs):
            if dim(im) > target:
                s = target / dim(im)
                imgs[i] = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
                scales[i] = s

    # 1.7 C：框坐标按原生像素给，换算到缩放后的图上再画，然后才拼接
    drawn = []
    for i, im in enumerate(imgs):
        s = scales[i]
        scaled = [tuple(round(v * s) for v in b) for b in boxes.get(i, [])]
        drawn.append(draw_boxes(im, scaled))

    base_w = max(im.width for im in imgs)
    fsize = max(16, round(base_w / 45))
    font = load_font(fsize)
    title_font = load_font(round(fsize * 1.15))
    pad = max(8, round(fsize * 0.5))
    label_h = (fsize + pad * 2) if any(labels) else 0
    title_h = (round(fsize * 1.15) + pad * 2) if args.title else 0
    gaps = args.gap * (len(imgs) - 1)

    if args.stack:
        canvas_w = base_w
        canvas_h = title_h + sum(label_h + im.height for im in imgs) + gaps
    else:
        canvas_w = sum(im.width for im in imgs) + gaps
        canvas_h = title_h + label_h + max(im.height for im in imgs)

    canvas = Image.new("RGB", (canvas_w, canvas_h), BG)
    d = ImageDraw.Draw(canvas)

    if args.title:
        tw, _ = text_size(d, args.title, title_font)
        d.text(((canvas_w - tw) // 2, pad), args.title, fill=LABEL_FG, font=title_font)

    def put_label(text, x, y, width):
        if not text:
            return
        tw, _ = text_size(d, text, font)
        d.text((x + max(0, (width - tw) // 2), y + pad), text, fill=LABEL_FG, font=font)

    offsets = []
    x, y = 0, title_h
    for im, text in zip(imgs, labels):
        if args.stack:
            put_label(text, 0, y, canvas_w)
            canvas.paste(im, (0, y + label_h))
            offsets.append((0, y + label_h))
            y += label_h + im.height + args.gap
        else:
            put_label(text, x, y, im.width)
            canvas.paste(im, (x, y + label_h))
            offsets.append((x, y + label_h))
            x += im.width + args.gap

    if args.arrow:
        if drawn[0] and drawn[1]:
            lb, rb = drawn[0][0], drawn[1][0]
            lo, ro = offsets[0], offsets[1]
            start = (lo[0] + lb[2], lo[1] + (lb[1] + lb[3]) // 2)
            end = (ro[0] + rb[0], ro[1] + (rb[1] + rb[3]) // 2)
            draw_arrow(ImageDraw.Draw(canvas), start, end, stroke_width(base_w))
        else:
            print("⚠️  --arrow 需要第 0 张和第 1 张图上各至少一个框，已跳过箭头")

    canvas.save(args.out)
    parts = []
    for (w0, h0), im, s in zip(native, imgs, scales):
        parts.append(f"{w0}x{h0}" if s == 1.0 else f"{w0}x{h0}→{im.width}x{im.height}")
    print(f"✅ {args.out}  {canvas.width}x{canvas.height}  （{' + '.join(parts)}）")
    if any(s != 1.0 for s in scales):
        print("   已把较大的图缩小到统一尺寸（只缩不放）；要保持原生像素请加 --no-equalize")
    if not any(drawn):
        print("⚠️  没有画任何红框 —— SKILL.md 1.7 C 要求拼图必须圈出问题部位，请补 --box")
    print("   下一步：走 4.6 上传 + 4.7 内嵌（靠左、内层 media 用真实尺寸），拼图放在视频上方")


if __name__ == "__main__":
    main()
