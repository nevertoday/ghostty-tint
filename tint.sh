# shellcheck shell=bash
# ghostty-tint · 每开一个面板，换一种安静的颜色
# https://github.com/nevertoday/ghostty-tint
# Copyright (c) 2026 小小东 Xiaoxiaodong · PolyForm Noncommercial 1.0.0（非商用免费，商用见 COMMERCIAL.md）
#
# 在 ~/.zshrc 或 ~/.bashrc 里 source 这个文件即可：
#   source ~/.config/ghostty-tint/tint.sh
#
# 原理只有三步：
#   1. 新面板的 shell 启动 → 全局计数器 +1（mkdir 原子锁，同时开 4 个面板也不撞号）
#   2. 第 i 个面板取第 (i·k mod N) 个颜色，k ≈ 0.382·N（黄金角），相邻面板永远差得够远
#   3. printf '\e]11;#RRGGBB\a'（OSC 11）只改当前面板的背景，不动全局配置
#
# 可选环境变量（写在 source 之前）：
#   TINT_MOOD=mist        临时指定气质（否则读 ~/.config/ghostty-tint/mood，默认 paper）
#   TINT_ORDER=spread     spread 黄金角分散（默认）· seq 按顺序 · random 随机
#   TINT_AUTO=0           不在新面板自动换色，只保留 tint 命令
#   TINT_ANY_TERM=1       不只是 Ghostty，任何支持 OSC 11 的终端都换色
#   TINT_WASH=1           用单元格底色铺满（给不支持分屏独立 OSC 11 的宿主，如旧版 cmux）

: "${TINT_HOME:=$HOME/.config/ghostty-tint}"
: "${TINT_ORDER:=spread}"
: "${TINT_AUTO:=1}"

# ---------------------------------------------------------------- 小工具
# 所有内部函数都把结果放进 _tint_ret，避免 $(...) 子进程，shell 启动更快。

_tint_is_hex() {
  case "$1" in
    \#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) return 0 ;;
  esac
  return 1
}

_tint_state_dir() {
  _tint_ret="${TMPDIR:-/tmp}"
  _tint_ret="${_tint_ret%/}/ghostty-tint-${UID:-0}"
}

# 第 $1 个（从 1 开始）空格分隔的词 → _tint_ret
_tint_nth() {
  local i=1 s="$2" w
  while [[ -n $s ]]; do
    w="${s%% *}"
    s="${s#* }"
    if (( i == $1 )); then
      _tint_ret="$w"
      return 0
    fi
    i=$((i + 1))
  done
  return 1
}

# 气质名或路径 → 文件路径
_tint_mood_path() {
  local m="${1:-}"
  if [[ -z $m ]]; then
    m="${TINT_MOOD:-}"
    if [[ -z $m && -r "$TINT_HOME/mood" ]]; then
      read -r m < "$TINT_HOME/mood" || :
    fi
    m="${m:-paper}"
  fi
  case "$m" in
    */* | *.tint) _tint_ret="$m" ;;
    *) _tint_ret="$TINT_HOME/moods/$m.tint" ;;
  esac
  [[ -r $_tint_ret ]]
}

# 读取 .tint 文件（纯内建命令，不 fork）
_tint_load() {
  local key v1 rest
  _TINT_BG="" _TINT_N=0 _TINT_FG="" _TINT_CURSOR="" _TINT_ANSI="" _TINT_NAME="" _TINT_VIBE=""
  while read -r key v1 rest || [[ -n $key ]]; do
    case "$key" in
      bg)
        _tint_is_hex "$v1" || continue
        _TINT_BG="$_TINT_BG$v1 "
        _TINT_N=$((_TINT_N + 1))
        ;;
      fg) _TINT_FG="$v1" ;;
      cursor) _TINT_CURSOR="$v1" ;;
      ansi) _tint_is_hex "${rest%% *}" && _TINT_ANSI="$_TINT_ANSI$v1=${rest%% *} " ;;
      name) _TINT_NAME="$v1${rest:+ $rest}" ;;
      vibe) _TINT_VIBE="$v1${rest:+ $rest}" ;;
    esac
  done < "$1"
  (( _TINT_N > 0 ))
}

# 按名字/别名找颜色：tint red、tint 后端、tint prod
_tint_lookup() {
  local key v1 rest s w
  while read -r key v1 rest || [[ -n $key ]]; do
    [[ $key == bg ]] || continue
    s="$rest "
    while [[ -n $s ]]; do
      w="${s%% *}"
      s="${s#* }"
      if [[ -n $w && $w == "$2" ]]; then
        _tint_ret="$v1"
        return 0
      fi
    done
  done < "$1"
  return 1
}

# ---------------------------------------------------------------- 取色顺序

# 黄金角步长：最接近 0.382·N、且与 N 互质的 k（N=8→3，12→5，16→7）
_tint_step() {
  local n=$1 k a b g best=1 bestd=-1 d
  for (( k = 1; k < n; k++ )); do
    a=$n b=$k
    while (( b )); do g=$((a % b)); a=$b; b=$g; done
    (( a == 1 )) || continue
    d=$(( k * 1000000 - n * 381966 ))
    (( d < 0 )) && d=$(( -d ))
    if (( bestd < 0 || d <= bestd )); then best=$k bestd=$d; fi
  done
  _tint_ret=$best
}

# 第 $1 个面板（从 0 开始）、共 $2 色 → 颜色序号（从 1 开始）
_tint_spread() {
  local pos=$1 n=$2 half
  _tint_step "$n"
  if (( _tint_ret == 1 && n >= 4 )); then
    # 4、6 色找不到好步长：先隔一个取，再回头补
    half=$(( (n + 1) / 2 ))
    if (( pos < half )); then _tint_ret=$(( 2 * pos + 1 )); else _tint_ret=$(( 2 * (pos - half) + 2 )); fi
    return 0
  fi
  _tint_ret=$(( (pos * _tint_ret) % n + 1 ))
}

# 全局计数器 +1，mkdir 是原子操作，充当跨进程锁 → _tint_ret = 本面板的序号（从 0 开始）
_tint_counter() {
  local dir file lock tries=0 got=1 c=0
  _tint_state_dir
  dir=$_tint_ret file="$_tint_ret/counter" lock="$_tint_ret/lock"
  [[ -d $dir ]] || mkdir -p "$dir" 2>/dev/null || return 1
  while ! mkdir "$lock" 2>/dev/null; do
    tries=$((tries + 1))
    if (( tries > 50 )); then # 1 秒还拿不到，多半是残留锁
      rmdir "$lock" 2>/dev/null
      got=0
      break
    fi
    sleep 0.02
  done
  if [[ -r $file ]]; then read -r c < "$file" || :; fi
  case "$c" in '' | *[!0-9]*) c=0 ;; esac
  printf '%s\n' $((c + 1)) > "$file"
  (( got )) && rmdir "$lock" 2>/dev/null
  _tint_ret=$c
}

# 随机取一个，且不与上一次随机结果相同 → _tint_ret（从 1 开始）
_tint_random() {
  local n=$1 last=0 idx dir
  _tint_state_dir
  dir=$_tint_ret
  if [[ -r $dir/last ]]; then read -r last < "$dir/last" || :; fi
  idx=$(( RANDOM % n + 1 ))
  if (( n > 1 && idx == last )); then idx=$(( idx % n + 1 )); fi
  mkdir -p "$dir" 2>/dev/null && printf '%s\n' "$idx" > "$dir/last"
  _tint_ret=$idx
}

# ---------------------------------------------------------------- 上色

_tint_osc() {
  if [[ -n ${TMUX:-} ]]; then
    printf '\033Ptmux;\033\033]%s\007\033\\' "$1" # tmux 里需要透传
  else
    printf '\033]%s\007' "$1"
  fi
}

_tint_paint() {
  local bg="$1" h s pair
  if [[ ${TINT_WASH:-0} == 1 ]]; then
    h="${bg#\#}"
    printf '\033[48;2;%d;%d;%dm\033[2J\033[H' "0x${h:0:2}" "0x${h:2:2}" "0x${h:4:2}"
  fi
  _tint_osc "11;$bg"
  if [[ -n $_TINT_FG ]]; then _tint_osc "10;$_TINT_FG"; else _tint_osc 110; fi
  if [[ -n $_TINT_CURSOR ]]; then _tint_osc "12;$_TINT_CURSOR"; else _tint_osc 112; fi
  if [[ -n $_TINT_ANSI ]]; then
    s="$_TINT_ANSI"
    while [[ -n $s ]]; do
      pair="${s%% *}"
      s="${s#* }"
      _tint_osc "4;${pair%%=*};${pair#*=}"
    done
  else
    _tint_osc 104
  fi
  TINT_CURRENT="$bg"
}

# 打印一个色块：$1 背景 $2 文字 $3 前景色
_tint_swatch() {
  local b="${1#\#}" f="${3:-#1A1A1A}"
  f="${f#\#}"
  printf '\033[48;2;%d;%d;%dm\033[38;2;%d;%d;%dm%s\033[0m' \
    "0x${b:0:2}" "0x${b:2:2}" "0x${b:4:2}" "0x${f:0:2}" "0x${f:2:2}" "0x${f:4:2}" "$2"
}

# ---------------------------------------------------------------- 命令

_tint_help() {
  cat <<'EOF'
tint · 每开一个面板，换一种安静的颜色

  tint                 换下一个颜色（新面板会自动执行）
  tint random          随机换一个
  tint 3               用当前气质的第 3 色
  tint red | 后端      按名字/别名取色（见 tint ls）
  tint '#D7E2EC'       任意颜色
  tint reset           恢复主题默认

  tint ls              查看当前气质的所有颜色
  tint mood            列出所有气质
  tint mood mist       切换气质（之后的新面板都用它）
  tint gen …           生成新气质，如：tint gen --like paper --count 16 --name paper16

  配置目录：~/.config/ghostty-tint    文档：github.com/nevertoday/ghostty-tint
EOF
}

_tint_cmd_list() {
  local f key v1 rest i=0 mark
  _tint_mood_path "${1:-}" || { echo "tint: 找不到气质文件 $_tint_ret" >&2; return 1; }
  f=$_tint_ret
  _tint_load "$f" || return 1
  printf '\n  %s · %s 色 · %s\n\n' "$_TINT_NAME" "$_TINT_N" "$_TINT_VIBE"
  while read -r key v1 rest || [[ -n $key ]]; do
    [[ $key == bg ]] && _tint_is_hex "$v1" || continue
    i=$((i + 1))
    mark="  "
    [[ $v1 == "${TINT_CURRENT:-}" ]] && mark="▶ "
    printf '  %s%2d ' "$mark" "$i"
    _tint_swatch "$v1" "   $v1   " "${_TINT_FG:-#1A1A1A}"
    printf '  %s\n' "$rest"
  done < "$f"
  echo
}

_tint_cmd_mood() {
  local name="${1:-}" f id cur strip s c
  if [[ -z $name ]]; then
    [[ -n ${ZSH_VERSION:-} ]] && setopt localoptions nullglob
    _tint_mood_path
    cur="${_tint_ret##*/}"
    echo
    for f in "$TINT_HOME"/moods/*.tint; do
      [[ -r $f ]] || continue
      id="${f##*/}"
      id="${id%.tint}"
      _tint_load "$f" || continue
      if [[ "$id.tint" == "$cur" ]]; then printf '  ▶ '; else printf '    '; fi
      printf '%-10s' "$id"
      s="$_TINT_BG"
      while [[ -n $s ]]; do
        c="${s%% *}"
        s="${s#* }"
        _tint_swatch "$c" "  "
      done
      printf '  %s · %s 色\n' "$_TINT_NAME" "$_TINT_N"
    done
    echo
    echo "  切换：tint mood <名字>    生成新的：tint gen --help"
    echo
    return 0
  fi
  _tint_mood_path "$name" || { echo "tint: 没有气质 \"$name\"（tint mood 查看全部）" >&2; return 1; }
  mkdir -p "$TINT_HOME" && printf '%s\n' "$name" > "$TINT_HOME/mood"
  if [[ -n ${TINT_MOOD:-} && $TINT_MOOD != "$name" ]]; then
    echo "tint: 注意，环境变量 TINT_MOOD=$TINT_MOOD 会覆盖这个设置" >&2
  fi
  TINT_MOOD="$name" tint next || return 1
  printf '  已切换到 %s · 之后打开的面板都会用它\n' "$name"
}

tint() {
  local cmd="${1:-next}" f
  case "$cmd" in
    -h | --help | help) _tint_help; return 0 ;;
    ls | list | l) shift; _tint_cmd_list "$@"; return ;;
    mood | moods | m) shift; _tint_cmd_mood "$@"; return ;;
    gen | generate)
      shift
      if [[ -r "$TINT_HOME/tint-gen.py" ]]; then
        python3 "$TINT_HOME/tint-gen.py" "$@"
      else
        echo "tint: 没找到 $TINT_HOME/tint-gen.py，请重新运行 install.sh" >&2
        return 1
      fi
      return
      ;;
    reset | r | default | 重置)
      _tint_osc 111; _tint_osc 110; _tint_osc 112; _tint_osc 104
      TINT_CURRENT=""
      return 0
      ;;
  esac

  _tint_mood_path || { echo "tint: 找不到气质文件 $_tint_ret（tint mood 查看全部）" >&2; return 1; }
  f=$_tint_ret
  _tint_load "$f" || { echo "tint: $f 里没有 bg 颜色" >&2; return 1; }

  case "$cmd" in
    next | n)
      if [[ $TINT_ORDER == random ]]; then
        _tint_random "$_TINT_N"
      else
        _tint_counter || return 1
        if [[ $TINT_ORDER == seq ]]; then
          _tint_ret=$(( _tint_ret % _TINT_N + 1 ))
        else
          _tint_spread $(( _tint_ret % _TINT_N )) "$_TINT_N"
        fi
      fi
      _tint_nth "$_tint_ret" "$_TINT_BG"
      ;;
    random | rand | shuffle | 随机)
      _tint_random "$_TINT_N"
      _tint_nth "$_tint_ret" "$_TINT_BG"
      ;;
    \#*)
      _tint_is_hex "$cmd" || { echo "tint: 颜色要写成 #RRGGBB" >&2; return 1; }
      _tint_ret=$cmd
      ;;
    *[!0-9]*)
      _tint_lookup "$f" "$cmd" || { echo "tint: 不认识 \"$cmd\"，试试 tint ls 或 tint help" >&2; return 1; }
      ;;
    *)
      _tint_nth "$cmd" "$_TINT_BG" || { echo "tint: 当前气质只有 $_TINT_N 色" >&2; return 1; }
      ;;
  esac
  _tint_paint "$_tint_ret"
}

# ---------------------------------------------------------------- 新面板自动换色
# 每个面板有自己的 tty；同一个面板里再开子 shell（exec zsh、source ~/.zshrc）不会重复换色。

if [[ $TINT_AUTO == 1 && $- == *i* && -t 1 ]]; then
  if [[ ${TERM_PROGRAM:-} == ghostty || -n ${GHOSTTY_RESOURCES_DIR:-} || ${TINT_ANY_TERM:-0} == 1 ]]; then
    _tint_tty="${TTY:-}"
    [[ -z $_tint_tty ]] && _tint_tty="$(tty 2>/dev/null)"
    if [[ ${_TINT_DONE:-} != "$_tint_tty" ]]; then
      export _TINT_DONE="$_tint_tty"
      tint next 2>/dev/null
    fi
    unset _tint_tty
  fi
fi
