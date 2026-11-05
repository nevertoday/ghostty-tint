#!/usr/bin/env python3
"""tint-gen · 把一种「气质」变成 N 色面板色板（ghostty-tint）

原理：在 OKLCH 色彩空间里固定「亮度 L」和「彩度 C」，只转动「色相 h」。
亮度一致 = 每个面板的文字一样好读；彩度一致 = 所有颜色属于同一种气质。

常用：
  tint-gen.py --like paper --count 16            # 默认纸感，扩成 16 色
  tint-gen.py --like mist --count 12 -o ~/.config/ghostty-tint/moods/mist12.tint
  tint-gen.py --seed '#D7E2EC' --count 8         # 从你喜欢的一个颜色出发
  tint-gen.py --l 0.9 --c 0.04 --hue 20 --span 120 --count 6   # 完全自定义
  tint-gen.py --check paper                      # 体检：对比度 + 相邻差异（可写气质名或路径）
  tint-gen.py --preview moods/macaron.tint       # 在终端里预览色块

只用 Python 标准库，无需安装任何依赖。
"""
from __future__ import annotations

import argparse
import math
import re
import sys

# ---------- 气质预设：L 亮度 · C 彩度 · hue 起始色相 · span 色相跨度 ----------
PRESETS = {
    "paper":    dict(l=0.908, c=0.027, hue=27,  span=360, dark=False, title="纸感 Paper",    vibe="低饱和暖纸色，像一桌便签"),
    "mist":     dict(l=0.930, c=0.030, hue=170, span=150, dark=False, title="晨雾 Mist",     vibe="冷调雾色，安静专注不累眼"),
    "macaron":  dict(l=0.905, c=0.052, hue=15,  span=360, dark=False, title="马卡龙 Macaron", vibe="甜而不腻，开再多也不撞色"),
    "matcha":   dict(l=0.905, c=0.040, hue=50,  span=125, dark=False, title="茶室 Matcha",   vibe="抹茶麦秆苔藓，木质温润"),
    "morandi":  dict(l=0.855, c=0.026, hue=20,  span=360, dark=False, title="莫兰迪 Morandi", vibe="灰调高级，16 色依旧克制"),
    "midnight": dict(l=0.265, c=0.028, hue=200, span=360, dark=True,  title="夜航 Midnight",  vibe="深夜舷窗，暗色也有温度"),
    "neon":     dict(l=0.250, c=0.058, hue=280, span=360, dark=True,  title="霓虹 Neon",     vibe="赛博夜市，深底高彩适合演示"),
}

LIGHT_FG = "#1A1A1A"
DARK_FG = "#E6E4DC"
DARK_ANSI = [
    "#2A2D33", "#E07A7A", "#8CC79A", "#E3B66F", "#7FA8E0", "#C49BE0", "#74C7C2", "#D9D7CF",
    "#6B6F78", "#F09A9A", "#A8DDB4", "#F0CB8A", "#A1C2F0", "#D8B6F0", "#98DDD8", "#F2F0EA",
]

# 色相 → 名字（用于 `tint red` 这类按名字取色）
HUE_NAMES = [
    (40, "红", "red"), (65, "橙", "orange"), (90, "杏", "amber"), (115, "黄", "yellow"),
    (135, "黄绿", "lime"), (165, "绿", "green"), (190, "青", "teal"), (225, "湖蓝", "cyan"),
    (260, "蓝", "blue"), (290, "靛", "indigo"), (320, "紫", "purple"), (355, "粉", "pink"),
    (400, "红", "red"),
]


# ---------- 色彩数学（Björn Ottosson 的 OKLab） ----------
def _lin_to_srgb(x: float) -> float:
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055


def _srgb_to_lin(x: float) -> float:
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def oklch_to_rgb(L: float, C: float, h: float) -> tuple[float, float, float]:
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return r, g, bb


def in_gamut(rgb) -> bool:
    return all(-1e-6 <= v <= 1 + 1e-6 for v in rgb)


def oklch_to_hex(L: float, C: float, h: float) -> str:
    rgb = oklch_to_rgb(L, C, h)
    if not in_gamut(rgb):  # 超出 sRGB 时降彩度，保持亮度与色相
        lo, hi = 0.0, C
        for _ in range(30):
            mid = (lo + hi) / 2
            if in_gamut(oklch_to_rgb(L, mid, h)):
                lo = mid
            else:
                hi = mid
        rgb = oklch_to_rgb(L, lo, h)
    return "#" + "".join(f"{round(max(0, min(1, _lin_to_srgb(max(0, v)))) * 255):02X}" for v in rgb)


def hex_to_oklab(hx: str) -> tuple[float, float, float]:
    r, g, b = (_srgb_to_lin(int(hx[i:i + 2], 16) / 255) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def hex_to_oklch(hx: str) -> tuple[float, float, float]:
    L, a, b = hex_to_oklab(hx)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def luminance(hx: str) -> float:
    r, g, b = (_srgb_to_lin(int(hx[i:i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def golden_step(n: int) -> int:
    """黄金角步长：最接近 0.382·n 且与 n 互质的整数。n=8 → 3，n=12 → 5，n=16 → 7"""
    target = n * 0.381966
    for k in sorted(range(1, max(n, 2)), key=lambda k: (abs(k - target), -k)):
        if math.gcd(k, n) == 1:
            return k
    return 1


def spread_order(n: int) -> list[int]:
    """与 tint.sh 完全相同的分散顺序：第 i 个面板取第 (i·k mod n) 个颜色。
    相邻面板（包括第 n 个和下一轮第 1 个）在色轮上永远相隔 k 格 ≈ 137.5°。"""
    k = golden_step(n)
    if k == 1 and n >= 4:  # 4、6 色找不到好步长：先隔一个取，再回头补
        half = (n + 1) // 2
        return [2 * i if i < half else 2 * (i - half) + 1 for i in range(n)]
    return [(i * k) % n for i in range(n)]


def hue_name(h: float) -> tuple[str, str]:
    h = h % 360
    if h < 5:
        h += 360
    for limit, zh, en in HUE_NAMES:
        if h <= limit:
            return zh, en
    return "红", "red"


# ---------- 生成 ----------
def generate(count: int, l: float, c: float, hue: float, span: float) -> list[tuple[str, float]]:
    if span >= 360:
        hues = [hue + i * 360 / count for i in range(count)]
    elif count == 1:
        hues = [hue]
    else:
        hues = [hue + i * span / (count - 1) for i in range(count)]
    return [(oklch_to_hex(l, c, h), h % 360) for h in hues]


def render_tint(name, title, vibe, fg, colors, dark, params) -> str:
    lines = [
        "# ghostty-tint mood · 由 tools/tint-gen.py 生成，可随意手改",
        f"# 参数：L={params['l']} C={params['c']} hue={params['hue']} span={params['span']} count={len(colors)}",
        "# 格式：bg  #RRGGBB  名字  别名…   （按色相顺序排列，tint 会自动分散取色）",
        "",
        f"name  {title or name}",
        f"vibe  {vibe}",
        f"fg    {fg}",
    ]
    if dark:
        lines.append(f"cursor {fg}")
    lines.append("")
    used: dict[str, int] = {}
    for hx, h in colors:
        zh, en = hue_name(h)
        used[en] = used.get(en, 0) + 1
        tag = en if used[en] == 1 else f"{en}{used[en]}"
        lines.append(f"bg    {hx}  {zh}  {tag}")
    if dark:
        lines += ["", "# 深色气质顺带换一套亮一点的 ANSI 16 色，保证 ls/git 输出看得清"]
        lines += [f"ansi  {i:<2} {hx}" for i, hx in enumerate(DARK_ANSI)]
    return "\n".join(lines) + "\n"


# ---------- 读取 / 体检 / 预览 ----------
def parse_tint(path: str) -> dict:
    data = {"name": "", "vibe": "", "fg": "", "bg": [], "ansi": []}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            parts = raw.strip().split()
            if not parts or parts[0].startswith("#"):
                continue
            key, rest = parts[0], parts[1:]
            if key == "bg" and rest and re.fullmatch(r"#[0-9A-Fa-f]{6}", rest[0]):
                data["bg"].append((rest[0].upper(), rest[1:]))
            elif key in ("name", "vibe"):
                data[key] = " ".join(rest)
            elif key in ("fg", "cursor") and rest:
                data[key] = rest[0].upper()
            elif key == "ansi" and len(rest) >= 2:
                data["ansi"].append((int(rest[0]), rest[1].upper()))
    return data


def swatch(hx: str, text: str, fg: str) -> str:
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    fr, fgc, fb = (int(fg[i:i + 2], 16) for i in (1, 3, 5))
    return f"\033[48;2;{r};{g};{b}m\033[38;2;{fr};{fgc};{fb}m {text} \033[0m"


def resolve(path: str) -> str:
    """--check kyoto 也行：不是文件路径时去气质目录里找"""
    import os
    if os.path.exists(path) or "/" in path:
        return path
    home = os.environ.get("TINT_HOME") or os.path.expanduser("~/.config/ghostty-tint")
    return os.path.join(home, "moods", path if path.endswith(".tint") else f"{path}.tint")


def check(path: str) -> int:
    path = resolve(path)
    d = parse_tint(path)
    bgs = [hx for hx, _ in d["bg"]]
    if not bgs:
        print(f"✗ {path} 里没有 bg 行")
        return 1
    fg = d["fg"] or (LIGHT_FG if luminance(bgs[0]) > 0.18 else DARK_FG)
    ratios = [contrast(fg, hx) for hx in bgs]
    order = spread_order(len(bgs))
    dists = []
    for i in range(len(order)):
        a, b = hex_to_oklab(bgs[order[i]]), hex_to_oklab(bgs[order[(i + 1) % len(order)]])
        dists.append(math.dist(a, b) * 100)
    worst = min(ratios)
    print(f"{d['name'] or path} · {len(bgs)} 色 · 文字 {fg}")
    for i, hx in enumerate(bgs):
        L, C, h = hex_to_oklch(hx)
        print(f"  {i + 1:>2} {swatch(hx, hx, fg)}  对比度 {ratios[i]:5.1f}  L={L:.3f} C={C:.3f} h={h:5.1f}")
    level = "AAA 舒适" if worst >= 7 else ("AA 可用" if worst >= 4.5 else "偏低，建议调整 L")
    print(f"  最低对比度 {worst:.1f}（{level}）")
    print(f"  相邻面板最小色差 ΔE {min(dists):.1f}（≥3 一眼可分，≥5 很清楚）")
    if len(bgs) > 1:
        print("  打开顺序 " + " → ".join(str(i + 1) for i in order))
    return 0 if worst >= 4.5 else 1


def preview(path: str) -> None:
    d = parse_tint(resolve(path))
    fg = d["fg"] or LIGHT_FG
    print(f"{d['name']} — {d['vibe']}")
    row = [swatch(hx, f"{i + 1:>2}", fg) for i, (hx, _) in enumerate(d["bg"])]
    print("".join(row))


def main() -> int:
    ap = argparse.ArgumentParser(description="ghostty-tint 气质色板生成器（OKLCH）")
    ap.add_argument("--like", choices=sorted(PRESETS), help="以某个内置气质为基础")
    ap.add_argument("--seed", help="从一个你喜欢的颜色出发，如 '#D7E2EC'")
    ap.add_argument("--count", "-n", type=int, default=8, help="颜色数量（默认 8，任意 ≥1）")
    ap.add_argument("--l", type=float, help="亮度 0–1：浅色 0.86–0.94，深色 0.20–0.30")
    ap.add_argument("--c", type=float, help="彩度：0.015 很灰 · 0.03 低饱和 · 0.06 明显")
    ap.add_argument("--hue", type=float, help="起始色相 0–360（0 红 · 90 黄 · 150 绿 · 250 蓝 · 320 紫）")
    ap.add_argument("--span", type=float, help="色相跨度：360 全色轮，120 只取一段（更统一）")
    ap.add_argument("--dark", action="store_true", help="深色气质（浅色文字 + 亮 ANSI）")
    ap.add_argument("--fg", help="文字颜色，默认自动")
    ap.add_argument("--name", default="custom", help="气质 id（文件名）")
    ap.add_argument("--title", help="显示名，如 '京都秋 Kyoto'")
    ap.add_argument("--vibe", help="一句话气质描述")
    ap.add_argument("-o", "--out", help="写入文件（默认输出到屏幕）")
    ap.add_argument("--check", metavar="FILE", help="体检一个 .tint 文件")
    ap.add_argument("--preview", metavar="FILE", help="在终端预览一个 .tint 文件")
    a = ap.parse_args()

    if a.check:
        return check(a.check)
    if a.preview:
        preview(a.preview)
        return 0
    if a.count < 1:
        ap.error("--count 至少为 1")

    p = dict(PRESETS.get(a.like or "paper"))
    if a.seed:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", a.seed):
            ap.error("--seed 需要 #RRGGBB")
        L, C, h = hex_to_oklch(a.seed)
        p.update(l=round(L, 3), c=round(C, 3), hue=round(h, 1), span=360 if not a.like else p["span"],
                 dark=L < 0.5, title=None, vibe=f"从 {a.seed.upper()} 长出来的一组颜色")
    for k in ("l", "c", "hue", "span"):
        if getattr(a, k) is not None:
            p[k] = getattr(a, k)
    if a.dark:
        p["dark"] = True
    dark = p["dark"]
    fg = (a.fg or (DARK_FG if dark else LIGHT_FG)).upper()
    colors = generate(a.count, p["l"], p["c"], p["hue"], p["span"])
    title = a.title or (p.get("title") if a.like and not a.seed else None) or a.name
    vibe = a.vibe or p.get("vibe") or "我的气质"
    text = render_tint(a.name, title, vibe, fg, colors, dark,
                       {k: p[k] for k in ("l", "c", "hue", "span")})
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        import os
        shown = a.out.replace(os.path.expanduser("~"), "~", 1)
        print(f"✓ 已写入 {shown}（{a.count} 色）。在 Ghostty 里运行：tint mood {a.name}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
