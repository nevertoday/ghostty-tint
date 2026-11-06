#!/usr/bin/env python3
"""build · 从 moods/*.tint 生成所有演示图，并同步 Skill 文件包与在线调色页

    python3 tools/build.py

改了任何气质文件后运行一次，README 里的图、docs/index.html、skills/ 都会更新。
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import shutil
import sys
from contextlib import contextmanager
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("tintgen", ROOT / "tools" / "tint-gen.py")
tg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tg)
sys.path.insert(0, str(ROOT / "tools"))
import i18n  # noqa: E402

ORDER = ["paper", "mist", "matcha", "macaron", "morandi", "midnight", "neon"]
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
INK, INK2, PAGE = "#2B2A27", "#8A867D", "#F1EFEA"


def load_moods() -> list[dict]:
    out = []
    for mid in ORDER:
        d = tg.parse_tint(str(ROOT / "moods" / f"{mid}.tint"))
        bgs = [hx for hx, _ in d["bg"]]
        names = [(lab[0] if lab else "") for _, lab in d["bg"]]
        zh, _, en = d["name"].partition(" ")
        dark = tg.luminance(bgs[0]) < 0.18
        order = tg.spread_order(len(bgs))
        out.append(dict(
            id=mid, zh=zh, en=en, vibe=d["vibe"], fg=d["fg"] or tg.LIGHT_FG, dark=dark,
            bg=bgs, names=names, spread=[bgs[i] for i in order], spread_names=[names[i] for i in order],
            chrome="#1B1C20" if dark else "#F8F7F4", chrome_ink="#8E9097" if dark else "#9A968C",
            divider="#0E0F12" if dark else "#D9D6CE",
        ))
    return out


def mixhex(a: str, b: str, p: float) -> str:
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - p) + int(b[i:i + 2], 16) * p):02X}" for i in (1, 3, 5))


def bar_ink(m: dict, bg: str) -> str:
    """标题栏文字：前景色和标题栏底色各一半"""
    return mixhex(bg, m["fg"], .5)


def tw(s: str, size: float = 13.5) -> float:
    """等宽字体下的大致文字宽度：ASCII 0.6em，中日韩 1em"""
    return sum(size if ord(ch) > 0x2E80 else size * 0.602 for ch in s)


def e(s: str) -> str:
    return escape(str(s), quote=True)


# ---------------------------------------------------------------- 动画时间轴
def timeline(m: int, hold: float, fade: float):
    """m 段循环：每段停留 hold 秒、渐变 fade 秒。返回 (总时长, keyTimes, 每个点对应的段号)"""
    total = m * hold
    pts, seg = [], []
    for j in range(m):
        pts += [j * hold / total, ((j + 1) * hold - fade) / total]
        seg += [j, j]
    pts.append(1.0)
    seg.append(0)
    return total, ";".join(f"{t:.4f}" for t in pts), seg


def anim(attr: str, values: list[str], dur: float, kt: str) -> str:
    return (f'<animate attributeName="{attr}" dur="{dur:.1f}s" repeatCount="indefinite" '
            f'keyTimes="{kt}" values="{";".join(values)}"/>')


# ---------------------------------------------------------------- hero.svg
def hero(moods: list[dict]) -> str:
    W, H = 960, 600
    wx, wy, ww, wh = 48, 36, 864, 444
    tb = 34
    M = len(moods)
    dur, kt, seg = timeline(M, 3.4, 0.7)

    def track(fn):
        return [fn(moods[s]) for s in seg]

    def fade_in(k):  # 第 k 段可见
        return ["1" if s == k else "0" for s in seg]

    px, py, pw, ph = wx, wy + tb, ww, wh - tb
    lw = 430
    rw = pw - lw - 2
    th = 202
    panes = [  # x, y, w, h
        (px, py, lw, ph),
        (px + lw + 2, py, rw, th),
        (px + lw + 2, py + th + 2, (rw - 2) // 2, ph - th - 2),
        (px + lw + 2 + (rw - 2) // 2 + 2, py + th + 2, rw - (rw - 2) // 2 - 2, ph - th - 2),
    ]
    texts = [
        [("~/app", "❯ claude", 1), ("", "", 0), ("✻", "重构 auth 模块", 1), ("  ⎿", "读取 src/auth/session.ts", .6),
         ("  ⎿", "修改 3 个文件 +128 −41", .6), ("  ⎿", "运行测试 · 42 passed", .6), ("", "", 0),
         (">", "顺便把 README 也更新一下", 1)],
        [("~/api", "❯ npm run dev", 1), ("", "ready on http://localhost:3000", .6),
         ("", "GET  /health   200   3ms", .6), ("", "GET  /users    200  12ms", .6),
         ("", "POST /login    201  48ms", .6)],
        [("~/web", "❯ git log", 1), ("", "a1f3c feat: tint", .6), ("", "9be20 fix: lock", .6),
         ("", "4c7d1 docs: moods", .6)],
        [("~", "❯ tint mood", 1)],
    ]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'role="img" aria-label="ghostty-tint：每个面板自动换一种颜色，七种气质循环演示">',
         '<defs>',
         f'<clipPath id="win"><rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="12"/></clipPath>',
         '<filter id="sh" x="-10%" y="-10%" width="120%" height="130%">'
         '<feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="#3A3326" flood-opacity=".16"/></filter>',
         '</defs>',
         f'<rect width="{W}" height="{H}" rx="22" fill="{PAGE}"/>',
         f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="12" fill="#000" filter="url(#sh)" opacity=".9"/>',
         f'<g clip-path="url(#win)">',
         f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="{moods[0]["divider"]}">'
         + anim("fill", track(lambda m: m["divider"]), dur, kt) + '</rect>',
         f'<rect x="{wx}" y="{wy}" width="{ww}" height="{tb}" fill="{moods[0]["spread"][0]}">'
         + anim("fill", track(lambda m: m["spread"][0]), dur, kt) + '</rect>']  # 标题栏跟随聚焦面板（左侧大面板）
    for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        o.append(f'<circle cx="{wx + 20 + i * 20}" cy="{wy + tb / 2}" r="6" fill="{c}"/>')
    o.append(f'<text x="{wx + ww / 2}" y="{wy + tb / 2 + 4.5}" text-anchor="middle" font-family="{SANS}" '
             f'font-size="12.5" fill="{bar_ink(moods[0], moods[0]["spread"][0])}">ghostty — 4 panes'
             + anim("fill", track(lambda m: bar_ink(m, m["spread"][0])), dur, kt) + '</text>')

    for pi, (x, y, w, h) in enumerate(panes):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{moods[0]["spread"][pi]}">'
                 + anim("fill", track(lambda m, pi=pi: m["spread"][pi % len(m["spread"])]), dur, kt) + '</rect>')
        g = [f'<g font-family="{MONO}" font-size="13.5" fill="{moods[0]["fg"]}" xml:space="preserve" style="white-space:pre">'
             + anim("fill", track(lambda m: m["fg"]), dur, kt)]
        for li, (pre, body, op) in enumerate(texts[pi]):
            if not (pre or body):
                continue
            ty = y + 30 + li * 23
            if pre:
                g.append(f'<text x="{x + 18}" y="{ty}" opacity="{.5 if pre.startswith("~") else op}">{e(pre)}</text>')
            off = (tw(pre) + 8.1) if pre else 0
            g.append(f'<text x="{x + 18 + off}" y="{ty}" opacity="{op}">{e(body)}</text>')
        if pi == 0:  # 光标
            pre, body, _ = texts[0][-1]
            g.append(f'<rect x="{x + 18 + tw(pre) + 8.1 + tw(body) + 3:.1f}" y="{y + 30 + 7 * 23 - 13}" width="8" height="17" opacity=".7">'
                     f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')
        g.append('</g>')
        o += g
        # 角标：色名 + 色值
        for k, m in enumerate(moods):
            col = m["spread"][pi % len(m["spread"])]
            name = m["spread_names"][pi % len(m["spread"])]
            o.append(f'<g opacity="{1 if k == 0 else 0}">' + anim("opacity", fade_in(k), dur, kt)
                     + f'<text x="{x + w - 16}" y="{y + h - 16}" text-anchor="end" font-family="{SANS}" '
                       f'font-size="12" fill="{m["fg"]}" opacity=".55">{e(name)} · {col}</text></g>')

    # 面板 D：tint mood 输出（迷你色条）
    dx, dy, dw, dh = panes[3]
    for k, m in enumerate(moods):
        n = len(m["bg"])
        cw = min(14, (dw - 36) / n)
        cells = "".join(
            f'<rect x="{dx + 18 + i * cw:.1f}" y="{dy + 46}" width="{cw - 1.5:.1f}" height="22" rx="2" fill="{c}" '
            f'stroke="{m["fg"]}" stroke-opacity=".12"/>' for i, c in enumerate(m["bg"]))
        o.append(f'<g opacity="{1 if k == 0 else 0}">' + anim("opacity", fade_in(k), dur, kt) + cells
                 + f'<text x="{dx + 18}" y="{dy + 94}" font-family="{MONO}" font-size="13" fill="{m["fg"]}">'
                   f'▶ {e(m["id"])} · {n} 色</text></g>')
    o.append('</g>')

    # 下方：气质名 + 色板
    for k, m in enumerate(moods):
        n = len(m["bg"])
        sw = 300 / n
        cells = "".join(f'<rect x="{612 + i * sw:.1f}" y="{528}" width="{sw - 3:.1f}" height="34" rx="5" fill="{c}"/>'
                        for i, c in enumerate(m["bg"]))
        o.append(f'<g opacity="{1 if k == 0 else 0}">' + anim("opacity", fade_in(k), dur, kt)
                 + f'<text x="{wx + 4}" y="{540}" font-family="{SANS}" font-size="26" font-weight="700" fill="{INK}">'
                   f'{e(m["zh"])}<tspan dx="10" font-size="17" font-weight="500" fill="{INK2}">{e(m["en"])}</tspan></text>'
                 + f'<text x="{wx + 4}" y="{568}" font-family="{SANS}" font-size="15" fill="{INK2}">'
                   f'{e(m["vibe"])} · {n} 色 · tint mood {e(m["id"])}</text>' + cells + '</g>')
    o.append('</svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- 多语言画布
ARABIC = re.compile(r"[؀-ۿ]")


class Canvas:
    """简单的 SVG 画布。rtl=True 时整个版面左右镜像（阿拉伯语），文字按书写方向对齐。
    with c.unmirrored(x, w): 里面画的东西保持左到右（比如终端窗口）。"""

    def __init__(self, W, H, lang, aria):
        self.W, self.H, self.lang, self.rtl = W, H, lang, lang == "ar"
        self.sans = i18n.FONTS[lang]
        self.flip = self.rtl
        self.dx = 0.0
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
                  f'role="img" aria-label="{e(aria)}">', f'<rect width="{W}" height="{H}" rx="22" fill="{PAGE}"/>']

    def X(self, x, w=0.0):
        return self.W - x - w if self.flip else x + self.dx

    @contextmanager
    def unmirrored(self, x, w):
        saved = self.flip, self.dx
        if self.flip:
            self.flip, self.dx = False, (self.W - x - w) - x
        try:
            yield
        finally:
            self.flip, self.dx = saved

    @staticmethod
    def _a(attrs):
        return "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items() if v is not None)

    def raw(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, **a):
        self.o.append(f'<rect x="{self.X(x, w):.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{self._a(a)}/>')

    def circle(self, cx, cy, r, **a):
        self.o.append(f'<circle cx="{self.X(cx):.1f}" cy="{cy:.1f}" r="{r}"{self._a(a)}/>')

    def path(self, pts, close=False, **a):
        d = "M" + " L".join(f"{self.X(x):.1f},{y:.1f}" for x, y in pts) + ("Z" if close else "")
        self.o.append(f'<path d="{d}"{self._a(a)}/>')
        return d

    def text(self, x, y, s, size, fill=INK, weight=None, mono=False, anchor="start", opacity=None, extra=""):
        xx = self.X(x)
        is_rtl_text = bool(ARABIC.search(s)) and not mono
        direction = None
        if self.flip and anchor != "middle":
            # 镜像后：原来的「左对齐」变成「右对齐」
            if is_rtl_text:
                direction = "rtl"  # rtl 下 start 就是右端
            else:
                anchor = "end" if anchor == "start" else "start"
        elif is_rtl_text:
            direction = "rtl"
            anchor = {"start": "end", "end": "start"}.get(anchor, anchor)
        self.o.append(f'<text x="{xx:.1f}" y="{y:.1f}"{self._a(dict(text_anchor=None if anchor == "start" else anchor, direction=direction, font_family=MONO if mono else self.sans, font_size=size, font_weight=weight, fill=fill, opacity=opacity))}{extra}>{e(s)}</text>')

    def done(self):
        return "\n".join(self.o + ["</svg>"])


def mood_label(lang, mid):
    return i18n.MOODS[lang][mid]


def lights(c, x, y, r, gap):
    for i, col in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        c.circle(x + i * gap, y, r, fill=col)


# ---------------------------------------------------------------- spread.svg
def spread(moods: list[dict], lang: str = "zh") -> str:
    m, S = moods[0], i18n.STR[lang]
    n = len(m["bg"])
    order = tg.spread_order(n)
    k = tg.golden_step(n)
    c = Canvas(960, 420, lang, S["aria_spread"])

    def row(y, title, sub, idxs, good):
        c.text(40, y, title, 19, weight=700)
        c.text(40, y + 24, sub, 14, fill=INK2)
        for j, idx in enumerate(idxs):
            x = 40 + j * 106
            c.rect(x, y + 42, 98, 78, rx=8, fill=m["bg"][idx], stroke="#000", stroke_opacity=".06")
            c.text(x + 12, y + 66, S["pane"].format(j=j + 1), 13, opacity=".5")
            c.text(x + 12, y + 108, m["names"][idx] if lang == "zh" else m["bg"][idx], 14 if lang == "zh" else 12.5,
                   mono=lang != "zh")
        mark = ("✓", "#3E8A5E") if good else ("✗", "#B5584F")
        c.text(40 + 5 * 106 + 4, y + 92, mark[0], 30, fill=mark[1], weight=700)

    row(52, S["seq_title"], S["seq_sub"], list(range(5)), False)
    row(240, S["gold_title"].format(a=order[1] + 1, b=order[2] + 1), S["gold_sub"].format(k=k), order[:5], True)

    cx, cy, R = 790, 210, 150
    for i, col in enumerate(m["bg"]):
        a0 = math.radians(-90 + (i - .5) * 360 / n + 1.2)
        a1 = math.radians(-90 + (i + .5) * 360 / n - 1.2)
        r0, r1 = R - 34, R
        X = c.X
        sweep_o, sweep_i = (0, 1) if c.flip else (1, 0)
        p = (f"M{X(cx + r1 * math.cos(a0)):.1f},{cy + r1 * math.sin(a0):.1f} "
             f"A{r1},{r1} 0 0 {sweep_o} {X(cx + r1 * math.cos(a1)):.1f},{cy + r1 * math.sin(a1):.1f} "
             f"L{X(cx + r0 * math.cos(a1)):.1f},{cy + r0 * math.sin(a1):.1f} "
             f"A{r0},{r0} 0 0 {sweep_i} {X(cx + r0 * math.cos(a0)):.1f},{cy + r0 * math.sin(a0):.1f}Z")
        c.raw(f'<path d="{p}" fill="{col}" stroke="#000" stroke-opacity=".05"/>')
    rp = R - 52

    def pt(i):
        a = math.radians(-90 + i * 360 / n)
        return cx + rp * math.cos(a), cy + rp * math.sin(a)

    pts = [pt(i) for i in order] + [pt(order[0])]
    total = 2 * rp * math.sin(math.pi * k / n) * n
    c.path(pts, fill="none", stroke=INK, stroke_opacity=".18", stroke_width="1.5")
    d = "M" + " L".join(f"{c.X(x):.1f},{y:.1f}" for x, y in pts)
    c.raw(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round" '
          f'stroke-dasharray="{total:.1f}" stroke-dashoffset="{total:.1f}">'
          f'<animate attributeName="stroke-dashoffset" values="{total:.1f};0;0;{total:.1f}" '
          f'keyTimes="0;.55;.85;1" dur="7s" repeatCount="indefinite"/></path>')
    for step, i in enumerate(order):
        x, y = pt(i)
        c.circle(x, y, 12, fill=m["bg"][i], stroke=INK, stroke_width="1.5")
        c.text(x, y + 4.5, str(step + 1), 12, weight=700, mono=True, anchor="middle")
    c.text(cx, cy + R + 34, S["wheel"].format(n=n, k=k), 14, fill=INK2, anchor="middle")
    return c.done()


# ---------------------------------------------------------------- moods.svg
def gallery(moods: list[dict], lang: str = "zh") -> str:
    S = i18n.STR[lang]
    cw, ch, gap, pad = 444, 178, 24, 24
    cards = moods + [None]
    rows = math.ceil(len(cards) / 2)
    c = Canvas(960, pad * 2 + rows * ch + (rows - 1) * 20, lang, S["aria_moods"])
    for idx, m in enumerate(cards):
        x = pad + (idx % 2) * (cw + gap)
        y = pad + (idx // 2) * (ch + 20)
        if m is None:
            title, sub, desc = S["yours"]
            c.rect(x, y, cw, ch, rx=14, fill="none", stroke="#BDB8AD", stroke_width="1.5", stroke_dasharray="6 6")
            c.text(x + 24, y + 42, title, 21, weight=700)
            c.text(x + 24, y + 68, desc, 14, fill=INK2)
            c.text(x + 24, y + 98, "tint gen --like paper --count 24", 13, mono=True)
            cols = [hx for hx, _ in tg.generate(24, .9, .045, 10, 360)]
            sw = (cw - 48) / len(cols)
            for i, col in enumerate(cols):
                c.rect(x + 24 + i * sw, y + 118, sw - 2, 34, rx=3, fill=col)
            continue
        c.rect(x, y, cw, ch, rx=14, fill="#FBFAF8", stroke="#E2DED6")
        mx, my, mw, mh = x + 16, y + 16, 178, 146
        cid = f"c{idx}"
        with c.unmirrored(mx, mw):
            c.raw(f'<clipPath id="{cid}"><rect x="{c.X(mx):.1f}" y="{my}" width="{mw}" height="{mh}" rx="8"/></clipPath>')
            c.raw(f'<g clip-path="url(#{cid})">')
            c.rect(mx, my, mw, mh, fill=m["divider"])
            c.rect(mx, my, mw, 16, fill=m["spread"][0])  # 标题栏跟随聚焦面板
            lights(c, mx + 10, my + 8, 3, 9)
            hw, hh = (mw - 1.5) / 2, (mh - 16 - 1.5) / 2
            for p in range(4):
                px = mx + (p % 2) * (hw + 1.5)
                py = my + 16 + (p // 2) * (hh + 1.5)
                c.rect(px, py, hw, hh, fill=m["spread"][p])
                for li, lw in enumerate([46, 64, 38][: 3 - (p % 2)]):
                    c.rect(px + 8, py + 10 + li * 11, lw, 5, rx=2.5, fill=m["fg"], opacity=.7 if li == 0 else .35)
            c.raw('</g>')
        name, sub, vibe = mood_label(lang, m["id"])
        tx = x + 214
        c.text(tx, y + 44, name, 21, weight=700)
        if sub and lang != "ar":
            # 副名跟在主名后面（镜像时在左边）
            off = tw(name, 21) * (0.62 if lang == "ar" else 1) + 10 if lang != "en" else 0
            c.text(tx + off, y + 44, sub, 15, fill=INK2, weight=500)
        c.text(tx, y + 70, vibe, 13.5, fill=INK2)
        c.text(tx, y + 100, f"tint mood {m['id']}", 12.5, mono=True)
        n = len(m["bg"])
        sw = 212 / n
        for i, col in enumerate(m["bg"]):
            c.rect(tx + i * sw, y + 116, sw - 2, 26, rx=3, fill=col, stroke="#000", stroke_opacity=".05")
        tags = [S["count"].format(n=n)] + ([S["dark"]] if m["dark"] else []) + ([S["default"]] if m["id"] == "paper" else [])
        c.text(tx, y + 160, " · ".join(tags), 12.5, fill=INK2)
    return c.done()


# ---------------------------------------------------------------- how.svg
def how(moods: list[dict], lang: str = "zh") -> str:
    m, S = moods[0], i18n.STR[lang]
    c = Canvas(960, 270, lang, S["aria_how"])
    cw, gap, x0 = 166, 20, 27
    steps = S["steps"]
    for i, (t, code, sub) in enumerate(steps):
        x = x0 + i * (cw + gap)
        cid = f"h{i}"
        c.raw(f'<clipPath id="{cid}"><rect x="{c.X(x, cw):.1f}" y="28" width="{cw}" height="176" rx="14"/></clipPath>')
        c.rect(x, 28, cw, 176, rx=14, fill="#FBFAF8", stroke="#E2DED6")
        c.raw(f'<g clip-path="url(#{cid})">')
        c.rect(x, 28, cw, 48, fill=m["spread"][i])
        c.raw('</g>')
        c.text(x + 16, 60, f"0{i + 1}", 15, weight=700, mono=True, opacity=".55")
        c.text(x + 16, 106, t, 17, weight=700)
        c.text(x + 16, 138, code, 12, mono=True)
        c.text(x + 16, 176, sub, 12.5, fill=INK2)
        if i < len(steps) - 1:
            ax = x + cw + 3
            c.path([(ax, 116), (ax + 12, 116)], fill="none", stroke=INK2, stroke_width="1.8", stroke_linecap="round")
            c.path([(ax + 7, 111), (ax + 12, 116), (ax + 7, 121)], fill="none", stroke=INK2, stroke_width="1.8",
                   stroke_linecap="round", stroke_linejoin="round")
    c.text(480, 240, S["how_foot"], 14.5, fill=INK2, anchor="middle")
    return c.done()


# ---------------------------------------------------------------- before-after.svg
def before_after(moods: list[dict], lang: str = "zh") -> str:
    m, S = moods[0], i18n.STR[lang]
    c = Canvas(960, 330, lang, S["aria_ba"])
    tasks = S["tasks"]
    for side in (0, 1):
        x0, y0, ww, wh = 32 + side * 464, 30, 432, 232
        with c.unmirrored(x0, ww):  # 终端窗口本身不镜像
            cid = f"ba{side}"
            c.raw(f'<clipPath id="{cid}"><rect x="{c.X(x0):.1f}" y="{y0}" width="{ww}" height="{wh}" rx="10"/></clipPath>')
            c.rect(x0, y0 + 6, ww, wh, rx=10, fill="#3A3326", opacity=".08")
            c.raw(f'<g clip-path="url(#{cid})">')
            c.rect(x0, y0, ww, wh, fill=m["divider"])
            c.rect(x0, y0, ww, 24, fill="#FCFBF9" if side == 0 else m["spread"][0])  # 标题栏跟随聚焦面板
            lights(c, x0 + 14, y0 + 12, 4.5, 14)
            pw, ph = (ww - 4) / 3, (wh - 24 - 2) / 2
            for k in range(6):
                px, py = x0 + (k % 3) * (pw + 2), y0 + 24 + (k // 3) * (ph + 2)
                c.rect(px, py, pw, ph, fill="#FCFBF9" if side == 0 else m["spread"][k])
                c.text(px + 12, py + 24, "~ ❯", 11.5, mono=True, opacity=".45")
                c.text(px + 40, py + 24, tasks[k], 12)
                for li, lw in enumerate([84, 62, 96][: 2 + k % 2]):
                    c.rect(px + 12, py + 38 + li * 12, lw, 5, rx=2.5, fill=INK, opacity=".13")
                if side == 1:
                    tag = m["spread_names"][k] if lang == "zh" else m["spread"][k]
                    c.text(px + pw - 10, py + ph - 10, tag, 10.5, anchor="end", opacity=".5", mono=lang != "zh")
            c.raw('</g>')
            if side == 0:
                c.circle(x0 + ww - 26, y0 + wh - 30, 16, fill="#C25B52")
                c.text(x0 + ww - 26, y0 + wh - 23, "?", 20, fill="#fff", weight=700, anchor="middle")
        title, sub = S["before"] if side == 0 else S["after"]
        c.text(x0 + 4, y0 + wh + 34, title, 17, weight=700)
        c.text(x0 + 4, y0 + wh + 56, sub, 13.5, fill=INK2)
    return c.done()


# ---------------------------------------------------------------- social.svg（GitHub 分享封面 1280×640）
def social(moods: list[dict]) -> str:
    m = moods[0]
    W, H = 1280, 640
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<defs><filter id="ssh" x="-20%" y="-20%" width="140%" height="150%">'
         '<feDropShadow dx="0" dy="22" stdDeviation="26" flood-color="#3A3326" flood-opacity=".20"/></filter></defs>',
         f'<rect width="{W}" height="{H}" fill="{PAGE}"/>']
    # 左侧文字
    x = 84
    o.append(f'<text x="{x}" y="200" font-family="{MONO}" font-size="76" font-weight="700" fill="{INK}" letter-spacing="-1">ghostty-tint</text>')
    o.append(f'<text x="{x}" y="270" font-family="{SANS}" font-size="38" font-weight="700" fill="{INK}">每开一个面板，</text>')
    o.append(f'<text x="{x}" y="322" font-family="{SANS}" font-size="38" font-weight="700" fill="{INK}">换一种安静的颜色。</text>')
    o.append(f'<text x="{x}" y="370" font-family="{SANS}" font-size="21" fill="{INK2}">Every new Ghostty pane gets its own quiet color.</text>')
    sw = 54
    for i, c in enumerate(m["bg"]):
        o.append(f'<rect x="{x + i * (sw + 6)}" y="408" width="{sw}" height="54" rx="9" fill="{c}" stroke="#000" stroke-opacity=".05"/>')
    chips = ["零依赖", "zsh · bash", "7 种气质", "任意色数", "AI Skill"]
    cx = x
    for t in chips:
        w = tw(t, 17) + 30
        o.append(f'<rect x="{cx}" y="500" width="{w:.0f}" height="38" rx="19" fill="#FBFAF8" stroke="#DDD9D0"/>')
        o.append(f'<text x="{cx + w / 2:.0f}" y="525" text-anchor="middle" font-family="{SANS}" font-size="17" fill="{INK}">{e(t)}</text>')
        cx += w + 10
    # 右侧窗口：左一大格 + 右侧四格，五种颜色 + 一块深色霓虹点缀
    wx, wy, ww, wh, tb = 700, 96, 500, 448, 34
    o.append(f'<clipPath id="sw"><rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="14"/></clipPath>')
    o.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="14" fill="#000" filter="url(#ssh)" opacity=".85"/>')
    o.append(f'<g clip-path="url(#sw)"><rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="{m["divider"]}"/>')
    o.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{tb}" fill="{m["spread"][0]}"/>')  # 标题栏跟随聚焦面板
    for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        o.append(f'<circle cx="{wx + 20 + i * 20}" cy="{wy + tb / 2}" r="6.5" fill="{c}"/>')
    py0, ph = wy + tb, wh - tb
    lw = 248
    rw = ww - lw - 2
    hh = (ph - 4) / 3
    panes = [(wx, py0, lw, ph)] + [(wx + lw + 2, py0 + k * (hh + 2), rw, hh) for k in range(3)]
    texts = [["~/app ❯ claude", "", "✻ 重构 auth 模块", "  ⎿ 42 tests passed"], ["~/api ❯ npm run dev"],
             ["~/web ❯ git log"], ["~ ❯ tint mood"]]
    for k, (px, py, pw, phh) in enumerate(panes):
        o.append(f'<rect x="{px}" y="{py:.1f}" width="{pw}" height="{phh:.1f}" fill="{m["spread"][k]}"/>')
        for li, line in enumerate(texts[k]):
            if line:
                o.append(f'<text x="{px + 18}" y="{py + 32 + li * 25:.1f}" font-family="{MONO}" font-size="15" '
                         f'fill="{INK}" opacity="{.9 if li == 0 or k == 0 and li == 2 else .55}" style="white-space:pre">{e(line)}</text>')
        o.append(f'<text x="{px + pw - 14}" y="{py + phh - 14:.1f}" text-anchor="end" font-family="{SANS}" font-size="13" '
                 f'fill="{INK}" opacity=".5">{e(m["spread_names"][k])}</text>')
    o.append('</g>')
    o.append(f'<text x="{wx + ww}" y="{wy + wh + 44}" text-anchor="end" font-family="{SANS}" font-size="17" fill="{INK2}">'
             f'github.com/nevertoday/ghostty-tint</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- 同步
def sync_playground(moods: list[dict]) -> None:
    p = ROOT / "docs" / "index.html"
    if not p.exists():
        return
    data = [dict(id=m["id"], zh=m["zh"], en=m["en"], vibe=m["vibe"], fg=m["fg"], dark=m["dark"],
                 bg=m["bg"], names=m["names"], params=tg.PRESETS.get(m["id"], {})) for m in moods]
    for d in data:
        d["params"] = {k: v for k, v in d["params"].items() if k in ("l", "c", "hue", "span", "dark")}
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"/\*@moods\*/.*?/\*@end\*/",
               lambda _: "/*@moods*/" + json.dumps(data, ensure_ascii=False) + "/*@end*/", s, flags=re.S)
    p.write_text(s, encoding="utf-8")


def sync_skill() -> None:
    sk = ROOT / "skills" / "ghostty-tint"
    (sk / "tools").mkdir(parents=True, exist_ok=True)
    (sk / "moods").mkdir(exist_ok=True)
    for f in ("tint.sh", "install.sh", "LICENSE", "COMMERCIAL.md"):
        shutil.copy2(ROOT / f, sk / f)
    shutil.copy2(ROOT / "tools" / "tint-gen.py", sk / "tools" / "tint-gen.py")
    for f in (sk / "moods").glob("*.tint"):
        f.unlink()
    for f in (ROOT / "moods").glob("*.tint"):
        shutil.copy2(f, sk / "moods" / f.name)


def main() -> None:
    moods = load_moods()
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    for name, fn in (("hero", hero), ("social", social)):  # 只有中文版
        (out / f"{name}.svg").write_text(fn(moods), encoding="utf-8")
        print(f"✓ assets/{name}.svg")
    for lang in i18n.LANGS:
        d = out if lang == "zh" else out / lang
        d.mkdir(exist_ok=True)
        for name, fn in (("spread", spread), ("moods", gallery), ("how", how), ("before-after", before_after)):
            (d / f"{name}.svg").write_text(fn(moods, lang), encoding="utf-8")
        print(f"✓ {d.relative_to(ROOT)}/ spread · moods · how · before-after")
    sync_playground(moods)
    print("✓ docs/index.html 数据")
    sync_skill()
    print("✓ skills/ghostty-tint 文件包")


if __name__ == "__main__":
    main()
