#!/usr/bin/env python3
"""make_gifs · 逐帧渲染 tools/gif/stage.html，合成 assets/*.gif（含多语言版本）

    python3 tools/make_gifs.py              # 全部语言：zh → assets/，其余 → assets/<lang>/
    python3 tools/make_gifs.py en ja        # 只做指定语言

需要 Google Chrome 与 ffmpeg。颜色来自 moods/*.tint，文字来自 tools/i18n.py。
设 TINT_GIF_DIR=某目录 可以保留帧，再次运行只重新编码。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FPS = 15
SCENES = {"split": 12.6, "skill": 11.2}
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
KYOTO = dict(l=0.89, c=0.045, hue=20, span=110, count=8)
# 全局调色板 + 不抖动：纯色面板保持干净，帧差压缩依然有效
VF = ("scale=900:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=256:stats_mode=full:reserve_transparent=0[p];"
      "[b][p]paletteuse=dither=none:diff_mode=rectangle")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render(tmp: Path, page: Path, outdir: Path, keep: bool) -> bool:
    def shot(scene, i):
        out = tmp / scene / f"f{i:04d}.png"
        if keep and out.exists():
            return True
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--user-data-dir={tmp / 'profile' / f'{scene}{i % 8}'}", "--window-size=900,540",
                        f"--screenshot={out}", f"file://{page}#scene={scene}&t={i / FPS:.4f}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return out.exists()

    for scene, dur in SCENES.items():
        (tmp / scene).mkdir(parents=True, exist_ok=True)
        n = int(dur * FPS)
        # 同一个 Chrome profile 不能同时被两个进程使用：按 i % 8 分 8 组，组内串行
        groups = [[i for i in range(n) if i % 8 == g] for g in range(8)]
        with ThreadPoolExecutor(8) as ex:
            ok = list(ex.map(lambda grp: all(shot(scene, i) for i in grp), groups))
        if not all(ok):
            print(f"✗ {outdir.name}/{scene} 有帧渲染失败", file=sys.stderr)
            return False
        out = outdir / f"{scene}.gif"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / scene / "f%04d.png"),
                        "-vf", os.environ.get("TINT_GIF_VF", VF), "-loop", "0", str(out)], check=True)
        print(f"✓ {out.relative_to(ROOT)}  {n} 帧  {out.stat().st_size / 1024:.0f} KB")
    return True


def main() -> int:
    if not Path(CHROME).exists() or not shutil.which("ffmpeg"):
        print("需要 Google Chrome 和 ffmpeg（brew install ffmpeg）", file=sys.stderr)
        return 1
    build = load("build", ROOT / "tools" / "build.py")
    tg, i18n = build.tg, build.i18n
    langs = [a for a in sys.argv[1:] if a in i18n.LANGS] or i18n.LANGS
    moods = build.load_moods()
    bgs = [hx for hx, _ in tg.generate(KYOTO["count"], KYOTO["l"], KYOTO["c"], KYOTO["hue"], KYOTO["span"])]
    order = tg.spread_order(len(bgs))
    keep = os.environ.get("TINT_GIF_DIR")
    root_tmp = Path(keep) if keep else Path(tempfile.mkdtemp(prefix="tint-gif-"))
    template = (ROOT / "tools" / "gif" / "stage.html").read_text(encoding="utf-8")

    for lang in langs:
        G = dict(i18n.GIF[lang], count8=i18n.STR[lang]["count"].format(n=8))
        names = G["kyoto_names"]
        ms = moods + [dict(moods[0], id="kyoto", bg=bgs, names=names,
                           spread=[bgs[i] for i in order], spread_names=[names[i] for i in order])]
        tmp = root_tmp / lang
        tmp.mkdir(parents=True, exist_ok=True)
        page = tmp / "stage.html"
        data = json.dumps({"moods": ms, "str": G, "lang": lang, "font": i18n.FONTS[lang]}, ensure_ascii=False)
        page.write_text(template.replace("/*@data*/null/*@end*/", "/*@data*/" + data + "/*@end*/"), encoding="utf-8")
        outdir = ROOT / "assets" if lang == "zh" else ROOT / "assets" / lang
        outdir.mkdir(exist_ok=True)
        if not render(tmp, page, outdir, bool(keep)):
            return 1
    if not keep:
        shutil.rmtree(root_tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
