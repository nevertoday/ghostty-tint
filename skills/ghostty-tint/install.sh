#!/usr/bin/env bash
# ghostty-tint 安装脚本
#   bash install.sh                 安装到 ~/.config/ghostty-tint，并在 ~/.zshrc / ~/.bashrc 里加一行 source
#   bash install.sh --mood mist     安装并把默认气质设为 mist
#   bash install.sh --skill         同时安装 AI Skill（Claude Code / Codex）
#   bash install.sh --uninstall     卸载（删除配置目录和 rc 里的那几行）
#
# 远程一键：curl -fsSL https://raw.githubusercontent.com/nevertoday/ghostty-tint/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/nevertoday/ghostty-tint"
DEST="${TINT_HOME:-$HOME/.config/ghostty-tint}"
MARK_BEGIN="# >>> ghostty-tint >>>"
MARK_END="# <<< ghostty-tint <<<"

mood="" skill=0 uninstall=0
while (( $# )); do
  case "$1" in
    --mood) mood="${2:-}"; shift ;;
    --skill) skill=1 ;;
    --uninstall) uninstall=1 ;;
    -h | --help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 1 ;;
  esac
  shift
done

say() { printf '  \033[38;2;120;150;140m●\033[0m %s\n' "$*"; }

rc_files() {
  local f
  for f in "$HOME/.zshrc" "$HOME/.bashrc"; do
    [[ -f $f ]] && echo "$f"
  done
  # 一个都没有时，按当前 shell 新建
  if [[ ! -f $HOME/.zshrc && ! -f $HOME/.bashrc ]]; then
    case "${SHELL:-}" in */bash) echo "$HOME/.bashrc" ;; *) echo "$HOME/.zshrc" ;; esac
  fi
}

strip_block() { # 删除 rc 文件里的 ghostty-tint 段落
  local f="$1" tmp
  grep -qF "$MARK_BEGIN" "$f" 2>/dev/null || return 0
  tmp="$(mktemp)"
  awk -v b="$MARK_BEGIN" -v e="$MARK_END" '$0==b{skip=1;next} $0==e{skip=0;next} !skip' "$f" > "$tmp"
  cat "$tmp" > "$f" && rm -f "$tmp"
}

if (( uninstall )); then
  while read -r f; do strip_block "$f" && say "已从 ${f/#$HOME/~} 移除"; done < <(rc_files)
  rm -rf "$DEST" && say "已删除 ${DEST/#$HOME/~}"
  for d in "$HOME/.claude/skills/ghostty-tint" "$HOME/.codex/skills/ghostty-tint"; do
    [[ -d $d ]] && rm -rf "$d" && say "已删除 ${d/#$HOME/~}"
  done
  echo; echo "  已卸载。新开的面板会回到主题默认颜色。"; exit 0
fi

# 找到源文件：本地仓库 / skill 目录，或者远程克隆
SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
if [[ -z $SRC || ! -r $SRC/tint.sh ]]; then
  SRC="$(mktemp -d)/ghostty-tint"
  say "下载 $REPO"
  git clone --depth 1 -q "$REPO" "$SRC"
fi

echo
echo "  ghostty-tint · 每开一个面板，换一种安静的颜色"
echo

mkdir -p "$DEST/moods"
cp "$SRC/tint.sh" "$DEST/tint.sh"
cp "$SRC/tools/tint-gen.py" "$DEST/tint-gen.py"
cp "$SRC/install.sh" "$DEST/install.sh" # 方便以后 bash ~/.config/ghostty-tint/install.sh --uninstall
cp "$SRC/LICENSE" "$SRC/COMMERCIAL.md" "$DEST/" 2>/dev/null || true
# 内置气质每次覆盖更新；你自己生成的 .tint 文件不会被动到
cp "$SRC"/moods/*.tint "$DEST/moods/"
say "核心文件 → ${DEST/#$HOME/~}（$(ls "$SRC"/moods/*.tint | wc -l | tr -d ' ') 种内置气质）"

if [[ -n $mood ]]; then
  [[ -r $DEST/moods/$mood.tint ]] || { echo "没有气质 $mood" >&2; exit 1; }
  echo "$mood" > "$DEST/mood"
  say "默认气质 → $mood"
fi

line='[ -r "$HOME/.config/ghostty-tint/tint.sh" ] && source "$HOME/.config/ghostty-tint/tint.sh"'
[[ $DEST != "$HOME/.config/ghostty-tint" ]] && line="export TINT_HOME=\"$DEST\"; [ -r \"$DEST/tint.sh\" ] && source \"$DEST/tint.sh\""
while read -r f; do
  strip_block "$f" 2>/dev/null || true
  [[ -s $f && -n "$(tail -n 1 "$f")" ]] && echo >> "$f"
  printf '%s\n%s\n%s\n' "$MARK_BEGIN" "$line" "$MARK_END" >> "$f"
  say "已写入 ${f/#$HOME/~}"
done < <(rc_files)

if (( skill )); then
  targets=()
  [[ -d $HOME/.claude ]] && targets+=("$HOME/.claude/skills/ghostty-tint")
  [[ -d $HOME/.codex ]] && targets+=("$HOME/.codex/skills/ghostty-tint")
  (( ${#targets[@]} )) || targets=("$HOME/.claude/skills/ghostty-tint")
  skill_md="$SRC/skills/ghostty-tint/SKILL.md"
  [[ -r $skill_md ]] || skill_md="$SRC/SKILL.md" # 从 skill 目录自身运行时
  for t in "${targets[@]}"; do
    mkdir -p "$t/moods" "$t/tools"
    [[ $t -ef $SRC ]] && { say "Skill 已在 ${t/#$HOME/~}"; continue; }
    cp "$skill_md" "$t/SKILL.md"
    cp "$SRC/tint.sh" "$SRC/install.sh" "$t/"
    cp "$SRC/LICENSE" "$SRC/COMMERCIAL.md" "$t/" 2>/dev/null || true
    cp "$SRC/tools/tint-gen.py" "$t/tools/"
    cp "$SRC"/moods/*.tint "$t/moods/"
    say "Skill → ${t/#$HOME/~}"
  done
fi

# 提醒：已有的其他自动换色脚本会和它打架
if grep -qsE '\]11;|ghostty_bg_apply' "$HOME/.zshrc" "$HOME/.bashrc" 2>/dev/null; then
  echo
  echo "  ⚠️  你的 rc 文件里似乎已有别的 OSC 11 换色逻辑，两个同时运行会互相覆盖，建议注释掉旧的。"
fi

echo
echo "  完成！新开一个 Ghostty 面板（⌘D / ⌘T）就能看到颜色。"
echo "  当前面板立即生效：source ${DEST/#$HOME/~}/tint.sh && tint"
echo "  看看全部气质：    tint mood"
echo "  授权：非商用免费，商用请见 COMMERCIAL.md（PolyForm Noncommercial 1.0.0）"
echo
