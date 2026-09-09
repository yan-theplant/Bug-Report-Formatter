#!/usr/bin/env python3
"""按原生像素左右/上下拼接两张证据图，加标注，并用红框圈出有问题的部位。

对应 SKILL.md 1.7 节 A / B / C：
  · 原生像素粘贴，绝不为了等高而缩放（不重采样）
  · 每侧标注「OS(设备) · build · 时间点」
  · 红框圈出问题部位，框线宽度随分辨率自适应

用法:
  python3 side_by_side.py --out combined.png \
      --left ios.png     --left-label  "iOS 1766 · 0:49" \
      --right android.png --right-label "Android 1373 · 0:49" \
      --left-box  1085,240,1470,320 \
      --right-box 1740,205,1900,255 \
      --arrow

坐标是**原生像素**、相对各自那张图的左上角，格式 x1,y1,x2,y2。
--left-box / --right-box 可重复多次。
"""

import argparse
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


def stroke_width(img_w):
    """框线宽度随原图宽度自适应：手机 ~1170px 出 4px，桌面 ~3000px 出 10px。"""
    return max(3, round(img_w / 300))


def text_size(draw, text, font):
    try:
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        return r - l, b - t
    except AttributeError:  # 老版本 Pillow
        return draw.textsize(text, font=font)


def draw_boxes(img, boxes):
    """在**原生尺寸**的图上画红框（SKILL.md 1.7 C：不要拼完缩放后再画）。"""
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
    import math
    d.line([start, end], fill=RED, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = width * 4
    p1 = end
    p2 = (end[0] - size * math.cos(ang - math.pi / 7), end[1] - size * math.sin(ang - math.pi / 7))
    p3 = (end[0] - size * math.cos(ang + math.pi / 7), end[1] - size * math.sin(ang + math.pi / 7))
    d.polygon([p1, p2, p3], fill=RED)


def main():
    ap = argparse.ArgumentParser(
        description="拼接两张证据图并圈注（SKILL.md 1.7 A/B/C）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--left", required=True, help="左图（双端 bug 惯例：iOS 放左）")
    ap.add_argument("--right", required=True, help="右图（Android 放右）")
    ap.add_argument("--out", required=True, help="输出文件")
    ap.add_argument("--left-label", default="", help='如 "iOS 1766 · 0:49" 或 "Android 12 (Pixel 4 XL) · 462 · 0:07"')
    ap.add_argument("--right-label", default="")
    ap.add_argument("--title", default="", help="顶部场景小标题（1.7 B）")
    ap.add_argument("--left-box", type=parse_box, action="append", default=[],
                    help="左图上的红框 x1,y1,x2,y2（原生像素，可重复）")
    ap.add_argument("--right-box", type=parse_box, action="append", default=[],
                    help="右图上的红框（可重复）")
    ap.add_argument("--arrow", action="store_true",
                    help="从左图第一个框指向右图第一个框，画一条箭头")
    ap.add_argument("--stack", action="store_true", help="上下拼接（默认左右）")
    ap.add_argument("--gap", type=int, default=0, help="两图之间的留白像素（默认 0）")
    args = ap.parse_args()

    try:
        left = Image.open(args.left).convert("RGB")
        right = Image.open(args.right).convert("RGB")
    except (OSError, IOError) as e:
        sys.exit(f"❌ 打不开图片: {e}")

    # 1.7 C：圈注画在原生尺寸的图上，再拼接
    lboxes = draw_boxes(left, args.left_box)
    rboxes = draw_boxes(right, args.right_box)

    # 标注区高度：按较大那张图的宽度定字号
    base_w = max(left.width, right.width)
    fsize = max(16, round(base_w / 45))
    font = load_font(fsize)
    title_font = load_font(round(fsize * 1.15))
    pad = max(8, round(fsize * 0.5))
    label_h = (fsize + pad * 2) if (args.left_label or args.right_label) else 0
    title_h = (round(fsize * 1.15) + pad * 2) if args.title else 0

    # 1.7 A/B 铁律：原生像素粘贴、顶部对齐、绝不为了等高而缩放
    if args.stack:
        canvas_w = max(left.width, right.width)
        canvas_h = title_h + (label_h + left.height) + args.gap + (label_h + right.height)
    else:
        canvas_w = left.width + args.gap + right.width
        canvas_h = title_h + label_h + max(left.height, right.height)

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

    if args.stack:
        ly = title_h
        put_label(args.left_label, 0, ly, canvas_w)
        canvas.paste(left, (0, ly + label_h))
        ry = ly + label_h + left.height + args.gap
        put_label(args.right_label, 0, ry, canvas_w)
        canvas.paste(right, (0, ry + label_h))
        loff = (0, ly + label_h)
        roff = (0, ry + label_h)
    else:
        ly = title_h
        put_label(args.left_label, 0, ly, left.width)
        put_label(args.right_label, left.width + args.gap, ly, right.width)
        canvas.paste(left, (0, ly + label_h))
        canvas.paste(right, (left.width + args.gap, ly + label_h))
        loff = (0, ly + label_h)
        roff = (left.width + args.gap, ly + label_h)

    if args.arrow:
        if lboxes and rboxes:
            lb, rb = lboxes[0], rboxes[0]
            start = (loff[0] + lb[2], loff[1] + (lb[1] + lb[3]) // 2)
            end = (roff[0] + rb[0], roff[1] + (rb[1] + rb[3]) // 2)
            draw_arrow(ImageDraw.Draw(canvas), start, end, stroke_width(base_w))
        else:
            print("⚠️  --arrow 需要左右两侧各至少一个框（--left-box / --right-box），已跳过箭头")

    canvas.save(args.out)
    print(f"✅ {args.out}  {canvas.width}x{canvas.height}"
          f"  （左 {left.width}x{left.height} + 右 {right.width}x{right.height}，未缩放）")
    if not (lboxes or rboxes):
        print("⚠️  没有画任何红框 —— SKILL.md 1.7 C 要求拼图必须圈出问题部位，"
              "请补 --left-box / --right-box")
    print("   下一步：走 4.6 上传 + 4.7 内嵌（靠左、内层 media 用真实尺寸），拼图放在视频上方")


if __name__ == "__main__":
    main()
