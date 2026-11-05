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
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("tintgen", ROOT / "tools" / "tint-gen.py")
tg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tg)

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
         f'<rect x="{wx}" y="{wy}" width="{ww}" height="{tb}" fill="{moods[0]["chrome"]}">'
         + anim("fill", track(lambda m: m["chrome"]), dur, kt) + '</rect>']
    for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        o.append(f'<circle cx="{wx + 20 + i * 20}" cy="{wy + tb / 2}" r="6" fill="{c}"/>')
    o.append(f'<text x="{wx + ww / 2}" y="{wy + tb / 2 + 4.5}" text-anchor="middle" font-family="{SANS}" '
             f'font-size="12.5" fill="{moods[0]["chrome_ink"]}">ghostty — 4 panes'
             + anim("fill", track(lambda m: m["chrome_ink"]), dur, kt) + '</text>')

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


# ---------------------------------------------------------------- spread.svg
def spread(moods: list[dict]) -> str:
    m = moods[0]
    n = len(m["bg"])
    order = tg.spread_order(n)
    k = tg.golden_step(n)
    W, H = 960, 420
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="按顺序取色与黄金角取色的对比">',
         f'<rect width="{W}" height="{H}" rx="22" fill="{PAGE}"/>']

    def row(y, title, sub, idxs, good):
        r = [f'<text x="40" y="{y}" font-family="{SANS}" font-size="19" font-weight="700" fill="{INK}">{e(title)}</text>',
             f'<text x="40" y="{y + 24}" font-family="{SANS}" font-size="14" fill="{INK2}">{e(sub)}</text>']
        for j, idx in enumerate(idxs):
            x = 40 + j * 106
            r.append(f'<rect x="{x}" y="{y + 42}" width="98" height="78" rx="8" fill="{m["bg"][idx]}" '
                     f'stroke="#000" stroke-opacity=".06"/>')
            r.append(f'<text x="{x + 12}" y="{y + 66}" font-family="{MONO}" font-size="13" fill="{INK}" opacity=".5">'
                     f'面板 {j + 1}</text>')
            r.append(f'<text x="{x + 12}" y="{y + 108}" font-family="{SANS}" font-size="14" fill="{INK}">'
                     f'{e(m["names"][idx])}</text>')
        mark = ("✓", "#3E8A5E") if good else ("✗", "#B5584F")
        r.append(f'<text x="{40 + 5 * 106 + 4}" y="{y + 92}" font-family="{SANS}" font-size="30" font-weight="700" '
                 f'fill="{mark[1]}">{mark[0]}</text>')
        return r

    o += row(52, "按顺序取色 1 → 2 → 3", "相邻面板是色轮上的邻居，一眼分不出来", list(range(5)), False)
    o += row(240, f"黄金角取色 1 → {order[1] + 1} → {order[2] + 1}",
             f"每次跳 {k} 格 ≈ 137.5°，相邻面板永远差得够远（包括转完一圈）", order[:5], True)

    # 右侧色轮 + 星形路径
    cx, cy, R = 790, 210, 150
    for i, c in enumerate(m["bg"]):
        a0 = math.radians(-90 + (i - .5) * 360 / n + 1.2)
        a1 = math.radians(-90 + (i + .5) * 360 / n - 1.2)
        r0, r1 = R - 34, R
        p = (f"M{cx + r1 * math.cos(a0):.1f},{cy + r1 * math.sin(a0):.1f} "
             f"A{r1},{r1} 0 0 1 {cx + r1 * math.cos(a1):.1f},{cy + r1 * math.sin(a1):.1f} "
             f"L{cx + r0 * math.cos(a1):.1f},{cy + r0 * math.sin(a1):.1f} "
             f"A{r0},{r0} 0 0 0 {cx + r0 * math.cos(a0):.1f},{cy + r0 * math.sin(a0):.1f}Z")
        o.append(f'<path d="{p}" fill="{c}" stroke="#000" stroke-opacity=".05"/>')
    rp = R - 52

    def pt(i):
        a = math.radians(-90 + i * 360 / n)
        return cx + rp * math.cos(a), cy + rp * math.sin(a)

    pts = [pt(i) for i in order] + [pt(order[0])]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    seglen = 2 * rp * math.sin(math.pi * k / n)
    total = seglen * n
    o.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-opacity=".18" stroke-width="1.5"/>')
    o.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round" '
             f'stroke-dasharray="{total:.1f}" stroke-dashoffset="{total:.1f}">'
             f'<animate attributeName="stroke-dashoffset" values="{total:.1f};0;0;{total:.1f}" '
             f'keyTimes="0;.55;.85;1" dur="7s" repeatCount="indefinite"/></path>')
    for step, i in enumerate(order):
        x, y = pt(i)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="{m["bg"][i]}" stroke="{INK}" stroke-width="1.5"/>')
        o.append(f'<text x="{x:.1f}" y="{y + 4.5:.1f}" text-anchor="middle" font-family="{MONO}" font-size="12" '
                 f'font-weight="700" fill="{INK}">{step + 1}</text>')
    o.append(f'<text x="{cx}" y="{cy + R + 34}" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{INK2}">'
             f'{n} 色 · 步长 {k} · 圆圈里的数字是打开顺序</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- moods.svg
def gallery(moods: list[dict]) -> str:
    cw, ch, gap, pad = 444, 178, 24, 24
    cards = moods + [None]
    rows = math.ceil(len(cards) / 2)
    W, H = 960, pad * 2 + rows * ch + (rows - 1) * 20
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="ghostty-tint 气质图鉴">', f'<rect width="{W}" height="{H}" rx="22" fill="{PAGE}"/>']
    for idx, m in enumerate(cards):
        x = pad + (idx % 2) * (cw + gap)
        y = pad + (idx // 2) * (ch + 20)
        if m is None:
            o.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="14" fill="none" stroke="#BDB8AD" '
                     f'stroke-width="1.5" stroke-dasharray="6 6"/>')
            o.append(f'<text x="{x + 24}" y="{y + 42}" font-family="{SANS}" font-size="21" font-weight="700" fill="{INK}">'
                     f'你的气质<tspan dx="10" font-size="15" font-weight="500" fill="{INK2}">Yours</tspan></text>')
            o.append(f'<text x="{x + 24}" y="{y + 68}" font-family="{SANS}" font-size="14" fill="{INK2}">'
                     f'一句话描述感觉，或给一个喜欢的颜色，任意色数</text>')
            o.append(f'<text x="{x + 24}" y="{y + 98}" font-family="{MONO}" font-size="13" fill="{INK}">'
                     f'tint gen --like paper --count 24</text>')
            cols = [hx for hx, _ in tg.generate(24, .9, .045, 10, 360)]
            sw = (cw - 48) / len(cols)
            o += [f'<rect x="{x + 24 + i * sw:.1f}" y="{y + 118}" width="{sw - 2:.1f}" height="34" rx="3" fill="{c}"/>'
                  for i, c in enumerate(cols)]
            continue
        o.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="14" fill="#FBFAF8" stroke="#E2DED6"/>')
        # 迷你窗口
        mx, my, mw, mh = x + 16, y + 16, 178, 146
        o.append(f'<clipPath id="c{idx}"><rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="8"/></clipPath>')
        o.append(f'<g clip-path="url(#c{idx})"><rect x="{mx}" y="{my}" width="{mw}" height="{mh}" fill="{m["divider"]}"/>')
        o.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="16" fill="{m["chrome"]}"/>')
        for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
            o.append(f'<circle cx="{mx + 10 + i * 9}" cy="{my + 8}" r="3" fill="{c}"/>')
        hw, hh = (mw - 1.5) / 2, (mh - 16 - 1.5) / 2
        for p in range(4):
            px = mx + (p % 2) * (hw + 1.5)
            py = my + 16 + (p // 2) * (hh + 1.5)
            o.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{hw:.1f}" height="{hh:.1f}" fill="{m["spread"][p]}"/>')
            for li, lw in enumerate([46, 64, 38][: 3 - (p % 2)]):
                o.append(f'<rect x="{px + 8:.1f}" y="{py + 10 + li * 11:.1f}" width="{lw}" height="5" rx="2.5" '
                         f'fill="{m["fg"]}" opacity="{.7 if li == 0 else .35}"/>')
        o.append('</g>')
        tx = x + 214
        o.append(f'<text x="{tx}" y="{y + 44}" font-family="{SANS}" font-size="21" font-weight="700" fill="{INK}">'
                 f'{e(m["zh"])}<tspan dx="8" font-size="15" font-weight="500" fill="{INK2}">{e(m["en"])}</tspan></text>')
        o.append(f'<text x="{tx}" y="{y + 70}" font-family="{SANS}" font-size="13.5" fill="{INK2}">{e(m["vibe"])}</text>')
        o.append(f'<text x="{tx}" y="{y + 100}" font-family="{MONO}" font-size="12.5" fill="{INK}">'
                 f'tint mood {e(m["id"])}</text>')
        n = len(m["bg"])
        sw = 212 / n
        o += [f'<rect x="{tx + i * sw:.1f}" y="{y + 116}" width="{sw - 2:.1f}" height="26" rx="3" fill="{c}" '
              f'stroke="#000" stroke-opacity=".05"/>' for i, c in enumerate(m["bg"])]
        o.append(f'<text x="{tx}" y="{y + 160}" font-family="{SANS}" font-size="12.5" fill="{INK2}">'
                 f'{n} 色{" · 深色" if m["dark"] else ""}{" · 默认" if m["id"] == "paper" else ""}</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- how.svg
def how(moods: list[dict]) -> str:
    m = moods[0]
    steps = [
        ("新建面板", "⌘D 分屏 · ⌘T 标签", "Ghostty 启动新 shell"),
        ("source tint.sh", "~/.zshrc 里的一行", "纯 shell 内建，不 fork"),
        ("计数器 +1", "mkdir 原子锁", "同时开 4 个也不撞号"),
        ("黄金角取色", "i · k mod N", "k ≈ 0.382 N，与 N 互质"),
        ("OSC 11 上色", "\\e]11;#D3E5DF\\a", "只改这一个面板"),
    ]
    W, H = 960, 270
    cw, gap, x0 = 166, 20, 27
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="ghostty-tint 工作原理五步">', f'<rect width="{W}" height="{H}" rx="22" fill="{PAGE}"/>']
    for i, (t, code, sub) in enumerate(steps):
        x = x0 + i * (cw + gap)
        c = m["spread"][i]
        o.append(f'<rect x="{x}" y="28" width="{cw}" height="176" rx="14" fill="#FBFAF8" stroke="#E2DED6"/>')
        o.append(f'<path d="M{x},{42} a14,14 0 0 1 14,-14 h{cw - 28} a14,14 0 0 1 14,14 v34 h-{cw}z" fill="{c}"/>')
        o.append(f'<text x="{x + 16}" y="{60}" font-family="{MONO}" font-size="15" font-weight="700" fill="{INK}" '
                 f'opacity=".55">0{i + 1}</text>')
        o.append(f'<text x="{x + 16}" y="{106}" font-family="{SANS}" font-size="17" font-weight="700" fill="{INK}">{e(t)}</text>')
        o.append(f'<text x="{x + 16}" y="{138}" font-family="{MONO}" font-size="12" fill="{INK}">{e(code)}</text>')
        o.append(f'<text x="{x + 16}" y="{176}" font-family="{SANS}" font-size="12.5" fill="{INK2}">{e(sub)}</text>')
        if i < len(steps) - 1:
            ax = x + cw + 3
            o.append(f'<path d="M{ax},{116} h12 m-5,-5 l5,5 l-5,5" fill="none" stroke="{INK2}" stroke-width="1.8" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<text x="{W / 2}" y="{240}" text-anchor="middle" font-family="{SANS}" font-size="14.5" fill="{INK2}">'
             f'不改 Ghostty 配置 · 没有常驻进程 · 删掉那一行就完全还原</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- before-after.svg
def before_after(moods: list[dict]) -> str:
    m = moods[0]
    W, H = 960, 330
    tasks = ["claude · 重构", "claude · 写文档", "codex · 测试", "npm run dev", "ssh prod", "git rebase"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="之前：所有面板同一种颜色；之后：每个面板一种颜色">', f'<rect width="{W}" height="{H}" rx="22" fill="{PAGE}"/>']
    for side in (0, 1):
        x0, y0, ww, wh = 32 + side * 464, 30, 432, 232
        o.append(f'<clipPath id="ba{side}"><rect x="{x0}" y="{y0}" width="{ww}" height="{wh}" rx="10"/></clipPath>')
        o.append(f'<rect x="{x0}" y="{y0 + 6}" width="{ww}" height="{wh}" rx="10" fill="#3A3326" opacity=".08"/>')
        o.append(f'<g clip-path="url(#ba{side})"><rect x="{x0}" y="{y0}" width="{ww}" height="{wh}" fill="{m["divider"]}"/>')
        o.append(f'<rect x="{x0}" y="{y0}" width="{ww}" height="24" fill="{m["chrome"]}"/>')
        for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
            o.append(f'<circle cx="{x0 + 14 + i * 14}" cy="{y0 + 12}" r="4.5" fill="{c}"/>')
        pw, ph = (ww - 4) / 3, (wh - 24 - 2) / 2
        for k in range(6):
            px, py = x0 + (k % 3) * (pw + 2), y0 + 24 + (k // 3) * (ph + 2)
            col = "#FCFBF9" if side == 0 else m["spread"][k]
            o.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="{col}"/>')
            o.append(f'<text x="{px + 12:.1f}" y="{py + 24:.1f}" font-family="{MONO}" font-size="11.5" fill="{INK}" opacity=".45">~ ❯</text>')
            o.append(f'<text x="{px + 40:.1f}" y="{py + 24:.1f}" font-family="{SANS}" font-size="12" fill="{INK}">{e(tasks[k])}</text>')
            for li, lw in enumerate([84, 62, 96][: 2 + k % 2]):
                o.append(f'<rect x="{px + 12:.1f}" y="{py + 38 + li * 12:.1f}" width="{lw}" height="5" rx="2.5" fill="{INK}" opacity=".13"/>')
            if side == 1:
                o.append(f'<text x="{px + pw - 10:.1f}" y="{py + ph - 10:.1f}" text-anchor="end" font-family="{SANS}" '
                         f'font-size="10.5" fill="{INK}" opacity=".5">{e(m["spread_names"][k])}</text>')
        o.append('</g>')
        if side == 0:  # 一个在找 prod 的问号
            o.append(f'<circle cx="{x0 + ww - 26}" cy="{y0 + wh - 30}" r="16" fill="#C25B52"/>'
                     f'<text x="{x0 + ww - 26}" y="{y0 + wh - 23}" text-anchor="middle" font-family="{SANS}" font-size="20" '
                     f'font-weight="700" fill="#fff">?</text>')
        title = ("之前：六个面板长得一模一样", "之后：每个面板一种颜色")[side]
        sub = ("哪个是 prod？刚才那句话发给了谁？", "扫一眼就知道，而且怎么看都顺眼")[side]
        o.append(f'<text x="{x0 + 4}" y="{y0 + wh + 34}" font-family="{SANS}" font-size="17" font-weight="700" fill="{INK}">{e(title)}</text>')
        o.append(f'<text x="{x0 + 4}" y="{y0 + wh + 56}" font-family="{SANS}" font-size="13.5" fill="{INK2}">{e(sub)}</text>')
    o.append('</svg>')
    return "\n".join(o)


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
    o.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{tb}" fill="{m["chrome"]}"/>')
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
    for f in ("tint.sh", "install.sh"):
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
    for name, fn in (("hero", hero), ("spread", spread), ("moods", gallery), ("how", how), ("before-after", before_after), ("social", social)):
        (out / f"{name}.svg").write_text(fn(moods), encoding="utf-8")
        print(f"✓ assets/{name}.svg")
    sync_playground(moods)
    print("✓ docs/index.html 数据")
    sync_skill()
    print("✓ skills/ghostty-tint 文件包")


if __name__ == "__main__":
    main()
