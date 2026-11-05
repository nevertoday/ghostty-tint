#!/usr/bin/env python3
"""make_gifs · 逐帧渲染 tools/gif/stage.html，合成 assets/*.gif

    python3 tools/make_gifs.py            # 需要 Google Chrome 与 ffmpeg

颜色直接来自 moods/*.tint，改了气质再跑一次，GIF 就和代码保持一致。
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
# 全局调色板 + 不抖动：纯色面板保持干净，帧差压缩依然有效
VF = ("scale=900:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=256:stats_mode=full:reserve_transparent=0[p];"
      "[b][p]paletteuse=dither=none:diff_mode=rectangle")
SCENES = {"split": 12.6, "skill": 11.2}
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
KYOTO = dict(l=0.89, c=0.045, hue=20, span=110, count=8,
             names=["枫红", "朱鹭", "柿色", "香木", "金阁", "稻穗", "抹茶", "苔庭"])


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not Path(CHROME).exists() or not shutil.which("ffmpeg"):
        print("需要 Google Chrome 和 ffmpeg（brew install ffmpeg）", file=sys.stderr)
        return 1
    build = load("build", ROOT / "tools" / "build.py")
    tg = build.tg
    moods = build.load_moods()
    bgs = [hx for hx, _ in tg.generate(KYOTO["count"], KYOTO["l"], KYOTO["c"], KYOTO["hue"], KYOTO["span"])]
    order = tg.spread_order(len(bgs))
    base = moods[0]
    moods.append(dict(base, id="kyoto", zh="京都秋", en="Kyoto", bg=bgs, names=KYOTO["names"],
                      spread=[bgs[i] for i in order], spread_names=[KYOTO["names"][i] for i in order]))

    keep = os.environ.get("TINT_GIF_DIR")  # 指定后会保留帧，重复运行只重新编码
    tmp = Path(keep) if keep else Path(tempfile.mkdtemp(prefix="tint-gif-"))
    tmp.mkdir(parents=True, exist_ok=True)
    stage = (ROOT / "tools" / "gif" / "stage.html").read_text(encoding="utf-8")
    stage = stage.replace("/*@data*/null/*@end*/", "/*@data*/" + json.dumps({"moods": moods}, ensure_ascii=False) + "/*@end*/")
    page = tmp / "stage.html"
    page.write_text(stage, encoding="utf-8")

    def shot(job):
        scene, i = job
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
        jobs = [(scene, i) for i in range(int(dur * FPS))]
        # 同一个 profile 不能被两个 Chrome 同时使用：按 i % 8 分组，每组串行
        groups = [[j for j in jobs if j[1] % 8 == g] for g in range(8)]
        with ThreadPoolExecutor(8) as ex:
            results = list(ex.map(lambda grp: all(shot(j) for j in grp), groups))
        if not all(results):
            print(f"✗ {scene} 有帧渲染失败", file=sys.stderr)
            return 1
        out = ROOT / "assets" / f"{scene}.gif"
        vf = os.environ.get("TINT_GIF_VF", VF)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / scene / "f%04d.png"),
                        "-vf", vf, "-loop", "0", str(out)], check=True)
        print(f"✓ assets/{scene}.gif  {len(jobs)} 帧  {out.stat().st_size / 1024:.0f} KB")
    if not keep:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
