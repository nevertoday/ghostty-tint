# Manual setup: no install script needed

<a href="manual.md">简体中文</a> · <strong>English</strong> · <a href="manual.ja.md">日本語</a> · <a href="manual.ko.md">한국어</a> · <a href="manual.ar.md">العربية</a>

The levels go from simplest to most complete. Pick the one that suits you.

---

## Level 0: one command, recolor the current pane

Run this in any Ghostty pane:

```bash
printf '\e]11;#D7E2EC\a'
```

That's the whole trick. `\e]11;color\a` is the standard **OSC 11** escape sequence, and it means "set this pane's background to this color". It only affects this one pane, goes away when you close it, and touches no config.

To go back to the default: `printf '\e]111\a'`.

## Level 1: 5 lines, new panes recolor themselves (zsh)

Paste this at the end of `~/.zshrc`:

```zsh
# Ghostty: auto-color new panes (minimal version)
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors} + 1 ))]}"
fi
```

- The colors are already in golden-angle order (by hue they go 1→4→7→2→5→8→3→6), so taking them in sequence never puts similar colors side by side.
- To change the colors, edit the values on that line. Use as many as you like. If you order them yourself, **don't put two hue-wheel neighbors next to each other**.
- Keep the quotes around each color, or zsh will treat `#` as the start of a comment.

bash version (arrays start at 0):

```bash
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors[@]} ))]}"
fi
```

Limits of this version: when several windows are restored at once, two panes can occasionally get the same color (there's no lock). Starting a subshell in the same pane recolors it again. It spawns two child processes (`cat`), which adds 1–2ms to startup. For everyday use, it's plenty.

## Level 2: the full version, installed by hand

The full `tint.sh` fixes all of the limits above, and adds the `tint` command, 7 moods and the generator. Installing it by hand just means putting the files in place and adding one source line:

```bash
git clone --depth 1 https://github.com/nevertoday/ghostty-tint ~/ghostty-tint
mkdir -p ~/.config/ghostty-tint/moods
cp ~/ghostty-tint/tint.sh ~/.config/ghostty-tint/
cp ~/ghostty-tint/tools/tint-gen.py ~/.config/ghostty-tint/
cp ~/ghostty-tint/moods/*.tint ~/.config/ghostty-tint/moods/
echo 'source ~/.config/ghostty-tint/tint.sh' >> ~/.zshrc     # bash users: put it in ~/.bashrc
```

Open a new split. Done.

### Change the default mood

```bash
echo mist > ~/.config/ghostty-tint/mood      # same as tint mood mist
```

Or set `export TINT_MOOD=mist` in your rc before the source line (this takes priority).

### Write your own mood

Create `~/.config/ghostty-tint/moods/mine.tint`:

```text
name  My mood
vibe  A one-line description
fg    #1A1A1A

bg    #EBD6D3  coral  red
bg    #ECE5C6  sand  yellow
bg    #D3E5DF  celadon  teal
bg    #E0DAEA  smoke  purple
```

- `bg` lines: a color value plus any number of names. You can use the names directly: `tint coral`, `tint red`.
- **Write them in hue order** (red → orange → yellow → green → teal → blue → purple → pink). tint spreads them out by the golden angle for you.
- `fg`: text color, optional. For a dark mood, remember to set a light text color, e.g. `fg #E6E4DC`.
- Optional: `cursor #RRGGBB` (cursor color) and `ansi 0 #RRGGBB` … `ansi 15 #RRGGBB` (the 16 ANSI colors).

Then run `tint mood mine`.

### Tips for picking colors

A good pane palette has one rule: **same lightness and chroma, only the hue changes**. That's hard to get right by hand, so use the generator:

```bash
python3 ~/.config/ghostty-tint/tint-gen.py --l 0.91 --c 0.03 --hue 20 --count 8 --name mine \
  -o ~/.config/ghostty-tint/moods/mine.tint
python3 ~/.config/ghostty-tint/tint-gen.py --check ~/.config/ghostty-tint/moods/mine.tint
```

Or open the [playground](https://nevertoday.github.io/ghostty-tint/) and drag the sliders. What you see is what you get.

## Uninstall

Remove the source line from your rc, then run `rm -rf ~/.config/ghostty-tint`.
