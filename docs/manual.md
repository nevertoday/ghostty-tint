# 手动方案：不跑安装脚本也能用

<strong>简体中文</strong> · <a href="manual.en.md">English</a> · <a href="manual.ja.md">日本語</a> · <a href="manual.ko.md">한국어</a> · <a href="manual.ar.md">العربية</a>

从最简单到最完整，挑一个适合你的就行。

---

## 第 0 级：一条命令，给当前面板换色

在任意 Ghostty 面板里运行：

```bash
printf '\e]11;#D7E2EC\a'
```

这就是全部原理：`\e]11;颜色\a` 是终端标准的 **OSC 11** 转义序列，作用是「把当前面板的背景改成这个颜色」。它只影响这一个面板，关掉就没了，不改任何配置。

想恢复默认：`printf '\e]111\a'`。

## 第 1 级：5 行，新面板自动换色（zsh）

把下面这段贴到 `~/.zshrc` 末尾：

```zsh
# Ghostty 新面板自动换色（极简版）
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors} + 1 ))]}"
fi
```

- 颜色已经按「黄金角」顺序排好（原本的色相顺序是 1→4→7→2→5→8→3→6），所以直接按顺序取就不撞色。
- 想换颜色，改那一行的色值即可；想要几个就写几个。自己排顺序时，记住**相邻两个不要是色轮上的邻居**。
- 颜色值必须加引号，否则 zsh 会把 `#` 当成注释。

bash 版（数组从 0 开始）：

```bash
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors[@]} ))]}"
fi
```

这个版本的局限：同时恢复多个窗口时偶尔会有两个面板同色（没有加锁）；在同一面板里再开子 shell 会再换一次色；用了两个子进程（`cat`），启动慢 1–2ms。日常完全够用。

## 第 2 级：完整版，手动安装

完整版 `tint.sh` 解决了上面所有局限，还带 `tint` 命令、7 种气质和生成器。手动安装就是把文件放好、加一行 source：

```bash
git clone --depth 1 https://github.com/nevertoday/ghostty-tint ~/ghostty-tint
mkdir -p ~/.config/ghostty-tint/moods
cp ~/ghostty-tint/tint.sh ~/.config/ghostty-tint/
cp ~/ghostty-tint/tools/tint-gen.py ~/.config/ghostty-tint/
cp ~/ghostty-tint/moods/*.tint ~/.config/ghostty-tint/moods/
echo 'source ~/.config/ghostty-tint/tint.sh' >> ~/.zshrc     # bash 用户写进 ~/.bashrc
```

新开一个分屏，完成。

### 换默认气质

```bash
echo mist > ~/.config/ghostty-tint/mood      # 等同于 tint mood mist
```

或者在 rc 里 source 之前写 `export TINT_MOOD=mist`（优先级更高）。

### 自己写一个气质

新建 `~/.config/ghostty-tint/moods/mine.tint`：

```text
name  我的气质 Mine
vibe  一句话描述
fg    #1A1A1A

bg    #EBD6D3  珊瑚  red
bg    #ECE5C6  沙金  yellow
bg    #D3E5DF  青瓷  teal
bg    #E0DAEA  烟紫  purple
```

- `bg` 行：色值 + 任意多个名字，名字可以直接用：`tint 珊瑚`、`tint red`。
- **按色相顺序写**（红→橙→黄→绿→青→蓝→紫→粉），tint 会自动用黄金角打散。
- `fg`：文字颜色，可省略。深色气质记得写浅色文字，例如 `fg #E6E4DC`。
- 可选 `cursor #RRGGBB`（光标色）、`ansi 0 #RRGGBB` … `ansi 15 #RRGGBB`（ANSI 16 色）。

然后 `tint mood mine`。

### 选颜色的小窍门

好看的面板色板只有一条规则：**亮度和彩度一样，只换色相**。手调很难做到，所以推荐用生成器：

```bash
python3 ~/.config/ghostty-tint/tint-gen.py --l 0.91 --c 0.03 --hue 20 --count 8 --name mine \
  -o ~/.config/ghostty-tint/moods/mine.tint
python3 ~/.config/ghostty-tint/tint-gen.py --check ~/.config/ghostty-tint/moods/mine.tint
```

或者打开[在线调色台](https://nevertoday.github.io/ghostty-tint/)拖滑杆，所见即所得。

## 卸载

删掉 rc 里那一行 source，再 `rm -rf ~/.config/ghostty-tint` 即可。
