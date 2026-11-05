<div align="center">

# ghostty-tint

**Every new pane gets its own quiet color.**

Each Ghostty split and tab gets a soft background of its own, so you can tell your panes apart at a glance.

![zero deps](https://img.shields.io/badge/deps-0-8A9A8C?style=flat-square)
![shell](https://img.shields.io/badge/zsh%20%7C%20bash-✓-8A9A8C?style=flat-square)
![colors](https://img.shields.io/badge/colors-any%20number-D7B9C8?style=flat-square)
![license](https://img.shields.io/badge/license-PolyForm%20Noncommercial-8A9A8C?style=flat-square)

</div>

<p align="center">
  <img src="assets/split.gif" width="100%" alt="Press ⌘D: each new pane picks up its own soft color; tint mood switches the whole mood">
</p>

<p align="center">
  <a href="#-install">Install</a> ·
  <a href="#-usage">Usage</a> ·
  <a href="#-moods">Moods</a> ·
  <a href="#-make-your-own">Make your own</a> ·
  <a href="#-ai-skill">AI Skill</a> ·
  <a href="#-how-it-works">How it works</a> ·
  <a href="https://nevertoday.github.io/ghostty-tint/">Playground</a> ·
  <a href="README.md">中文</a>
</p>

## 😵 Why

Three Claude sessions, a Codex, a dev server and an ssh into production, all in identical white-on-black panes. Then you send "drop this table"… wait, which pane was that?

<p align="center">
  <img src="assets/before-after.svg" width="100%" alt="Before: six identical panes. After: one color per pane.">
</p>

- **Harmonious.** Every color shares the same OKLCH lightness and chroma; only the hue changes.
- **Readable.** Text contrast is at least 12:1 on every pane.
- **No clashes.** New panes step around the hue wheel by the golden angle (~137.5°), even when the cycle wraps.
- **Any number of colors.** 8, 12, 16, 24… one command.
- **Tiny.** One shell file, no dependencies, no daemon. Delete one line to undo it.

## ⚡ Install

```bash
curl -fsSL https://raw.githubusercontent.com/nevertoday/ghostty-tint/main/install.sh | bash
```

Then press <kbd>⌘</kbd> <kbd>D</kbd>. Or hand it to Claude Code, Codex or Cursor:

```text
Install ghostty-tint: https://github.com/nevertoday/ghostty-tint
Clone it, run `bash install.sh --skill`, then list the built-in moods.
If my ~/.zshrc already changes the background color, ask me before touching it.
```

Prefer doing it by hand? [docs/manual.md](docs/manual.md) (Chinese, the code is universal) goes from a one-line `printf` to a 5-line zshrc version.

## 🧭 Usage

| Command | What it does |
|---|---|
| `tint` | next color (runs automatically in new panes) |
| `tint random` | random, never the same twice in a row |
| `tint 3` · `tint red` · `tint api` | by index, hue name or alias |
| `tint '#D7E2EC'` | any color |
| `tint reset` | back to the theme default |
| `tint ls` · `tint mood` | list colors · list moods |
| `tint mood mist` | switch mood for future panes |
| `tint gen …` | generate a new mood |

## 🌈 Moods

<p align="center">
  <img src="assets/moods.svg" width="100%" alt="Seven built-in moods">
</p>

`paper` (default) · `mist` · `matcha` · `macaron` · `morandi` · `midnight` · `neon`. The two dark moods also bring a brighter ANSI palette.

## 🎨 Make your own

```bash
tint gen --like morandi --count 24 --name morandi24   # any mood, any number of colors
tint gen --seed '#D7E2EC' --count 12 --name sky        # grow a palette from one color
tint gen --l 0.89 --c 0.045 --hue 20 --span 110 --name kyoto
tint gen --check kyoto                                 # contrast and neighbor ΔE
tint mood kyoto
```

`--l` lightness (light 0.86–0.94, dark 0.20–0.30) · `--c` chroma (0.015 greyish, 0.027 paper, 0.05 candy) · `--hue` start hue · `--span` degrees of the wheel (360 is the most distinct). With `--name`, the mood is saved straight into `~/.config/ghostty-tint/moods/`.

Or use the [playground](https://nevertoday.github.io/ghostty-tint/): drag the sliders, open fake panes, and copy one command that installs the mood.

## 🤖 AI Skill

<p align="center">
  <img src="assets/skill.gif" width="100%" alt="Asking the AI for a Kyoto-autumn mood">
</p>

Run `bash install.sh --skill`, then just say *"I want the feeling of an autumn temple in Kyoto, 12 colors"*. The agent turns that into OKLCH parameters, names each color, checks contrast and ΔE, and hands you a `tint mood` line plus three alternative moods.

## 🔬 How it works

<p align="center">
  <img src="assets/how.svg" width="100%" alt="How it works">
</p>

1. `tint.sh` is sourced by your shell and runs once per pane. It tracks the tty, so subshells don't recolor.
2. A global counter in `$TMPDIR` is incremented under a `mkdir` lock, so panes restored at the same moment never share a number.
3. Pane *i* takes color `(i × k) mod N`, where *k* is the integer closest to 0.382 × N that is coprime with N. Coprime means every color is used once per cycle; k/N ≈ 0.382 puts neighbors about 137.5° apart, the angle sunflower seeds use.
4. `printf '\e]11;#D3E5DF\a'` (OSC 11) recolors just that pane.

<p align="center">
  <img src="assets/spread.svg" width="100%" alt="Sequential vs golden-angle order">
</p>

Works in any terminal with OSC 11 support via `TINT_ANY_TERM=1`. tmux passthrough is handled for you (you may need `set -g allow-passthrough on`). Other options: `TINT_ORDER=random|seq|spread`, `TINT_AUTO=0`, and `TINT_WASH=1` for hosts that can't color splits separately.

## 📄 License

**Free for noncommercial use; commercial use needs separate written permission.** ghostty-tint is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE). The source is public, but it is not OSI open source. Personal and hobby use on your own machine is free. Using it in paid work, inside a company or team, in a commercial product, or in paid courses needs a licence. See [COMMERCIAL.md](COMMERCIAL.md).

Copyright (c) 2026 [小小东 Xiaoxiaodong](https://x.com/xiaoxiaodong01)
