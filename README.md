<div align="center">

# ghostty-tint

**每开一个面板，换一种安静的颜色。**

给 Ghostty 的每个分屏和标签自动配一块低饱和背景色，扫一眼就知道哪个面板在干嘛。

![zero deps](https://img.shields.io/badge/依赖-0-8A9A8C?style=flat-square)
![shell](https://img.shields.io/badge/zsh%20%7C%20bash-✓-8A9A8C?style=flat-square)
![colors](https://img.shields.io/badge/颜色数量-随你-D7B9C8?style=flat-square)
![license](https://img.shields.io/badge/license-PolyForm%20Noncommercial-8A9A8C?style=flat-square)

</div>

<p align="center">
  <img src="assets/split.gif" width="100%" alt="按 ⌘D 开分屏，每个新面板自动换一种低饱和颜色；再用 tint mood 一键切换气质">
</p>

<p align="center">
  <a href="#-安装">安装</a> ·
  <a href="#-用法">用法</a> ·
  <a href="#-七种气质">气质</a> ·
  <a href="#-定制你的气质">定制</a> ·
  <a href="#-ai-skill">AI Skill</a> ·
  <a href="#-原理">原理</a> ·
  <a href="https://nevertoday.github.io/ghostty-tint/">在线调色台</a> ·
  <a href="README.en.md">English</a>
</p>

## 😵 为什么需要它

同时开着三个 Claude、一个 Codex、一个 dev server，外加一个连着生产环境的 ssh，全是一模一样的白底黑字。然后你把「删掉这张表」发了出去……等等，这是哪个面板？

<p align="center">
  <img src="assets/before-after.svg" width="100%" alt="之前：六个面板同一种颜色；之后：每个面板一种颜色">
</p>

颜色是最快的标签：不用读标题，余光一扫就知道。但随便随机换色并不好看，ghostty-tint 做了这几件事：

| | 随便随机 | ghostty-tint |
|---|---|---|
| 协调 | 撞上荧光绿就很刺眼 | 亮度、彩度完全一致，只换色相，怎么组合都顺眼 |
| 可读 | 看运气 | 文字对比度 ≥ 12 : 1，每个面板一样清楚 |
| 不撞色 | 常有两个差不多的挨着 | 按黄金角 137.5° 取色，转完一圈也不撞 |
| 色数 | 写死 | 8 / 12 / 16 / 24…… 一条命令随你定 |
| 体积 | 插件、守护进程 | 一个 shell 文件，零依赖，删一行就还原 |

## ⚡ 安装

### 让 AI 帮你装（推荐）

把下面这段话发给 Claude Code、Codex 或 Cursor：

```text
帮我安装 ghostty-tint：https://github.com/nevertoday/ghostty-tint
克隆仓库后运行 bash install.sh --skill，然后告诉我有哪些气质可以选。
如果我的 ~/.zshrc 里已经有别的改背景色的逻辑，先问我要不要注释掉。
```

### 一行命令

```bash
curl -fsSL https://raw.githubusercontent.com/nevertoday/ghostty-tint/main/install.sh | bash
```

装完按 <kbd>⌘</kbd> <kbd>D</kbd> 开一个分屏，颜色就来了。

### 手动安装

不想跑脚本的话，[docs/manual.md](docs/manual.md) 从「一条 printf 换色」讲到「5 行 zshrc 极简版」，复制粘贴就能用。

> [!TIP]
> 想让 AI 从零实现、定制气质、改颜色数量或排查问题？[PROMPT.md](PROMPT.md) 里有 7 段现成话术。

## 🧭 用法

装好以后什么都不用做，新面板会自动换色。想手动控制：

| 命令 | 作用 |
|---|---|
| `tint` | 换下一个颜色 |
| `tint random` | 随机换一个，不会连续两次同色 |
| `tint 3` · `tint red` · `tint 后端` | 按序号、颜色名或别名取色 |
| `tint '#D7E2EC'` | 任意颜色 |
| `tint reset` | 恢复主题默认 |
| `tint ls` | 查看当前气质的所有颜色 |
| `tint mood` · `tint mood mist` | 列出全部气质 · 切换气质 |
| `tint gen …` | 生成新气质，见[定制你的气质](#-定制你的气质) |

默认的「纸感」还给每个颜色配了任务别名，正好用来标记面板用途：`tint prod` 珊瑚粉、`tint dev` 鼠尾草、`tint api` 青瓷灰、`tint test` 雾蓝灰、`tint doc` 烟紫灰、`tint ui` 梅子粉。

## 🌈 七种气质

<p align="center">
  <img src="assets/moods.svg" width="100%" alt="七种内置气质：纸感、晨雾、茶室、马卡龙、莫兰迪、夜航、霓虹">
</p>

用 `tint mood <名字>` 切换，之后打开的面板都会用新气质：

`paper` 纸感（默认）· `mist` 晨雾 · `matcha` 茶室 · `macaron` 马卡龙 · `morandi` 莫兰迪 · `midnight` 夜航 · `neon` 霓虹

两种深色气质会顺带换上一套更亮的 ANSI 16 色，`ls` 和 `git diff` 在深底上照样清楚。

## 🎨 定制你的气质

### 在线调色台

打开 [nevertoday.github.io/ghostty-tint](https://nevertoday.github.io/ghostty-tint/)，拖滑杆调色，点「开新面板」看效果。满意了复制一段命令，粘贴进终端就装好了。

### 一条命令生成

```bash
tint gen --like morandi --count 24 --name morandi24   # 把任何气质扩成任意色数
tint gen --seed '#D7E2EC' --count 12 --name sky        # 从一个喜欢的颜色出发
tint gen --l 0.89 --c 0.045 --hue 20 --span 110 --name kyoto
tint gen --check kyoto                                 # 体检：对比度和相邻色差
tint mood kyoto
```

写了 `--name` 就会自动存进 `~/.config/ghostty-tint/moods/`，生成完直接 `tint mood` 切过去。

| 参数 | 含义 | 参考值 |
|---|---|---|
| `--l` | 亮度，越高越轻盈 | 浅色 0.86–0.94，深色 0.20–0.30 |
| `--c` | 彩度，越高越鲜艳 | 0.015 近灰，0.027 纸感，0.05 糖果 |
| `--hue` | 起始色相 | 0 粉红，60 杏，150 绿，240 蓝，310 紫 |
| `--span` | 绕色轮多少度 | 360 最好区分，120 更有主题感 |

### 手写 .tint 文件

`.tint` 是纯文本，一行一个颜色，想写几个写几个，按色相顺序排好就行，tint 会自动打散：

```text
name  京都秋 Kyoto
vibe  旧木与枫叶，暖而不燥
fg    #1A1A1A

bg    #F7D0CE  枫红  maple red
bg    #F0D6BC  柿色  persimmon orange
bg    #E2DCBA  金阁  gold yellow
```

## 🤖 AI Skill

<p align="center">
  <img src="assets/skill.gif" width="100%" alt="对 AI 说「我想要京都秋天寺庙的感觉」，它生成八色京都秋气质并应用到所有面板">
</p>

运行 `bash install.sh --skill`，Skill 会装进 `~/.claude/skills/`（装了 Codex 的话也会装进 `~/.codex/skills/`）。之后直接说你想要的感觉：

- 「我想要京都秋天寺庙的感觉，8 个颜色」
- 「来一套雨后江南，12 色」
- 「给我一个适合晚上直播演示的深色配色」
- 「把现在的配色改成 24 色」

AI 会把描述翻译成 OKLCH 参数，生成色板，给每个颜色起一个同一世界观的名字，跑完对比度和色差体检，最后给你一行 `tint mood`，外加 3 个备选气质。Skill 原文在 [skills/ghostty-tint/SKILL.md](skills/ghostty-tint/SKILL.md)。

## 🔬 原理

<p align="center">
  <img src="assets/how.svg" width="100%" alt="五步：新建面板 → source tint.sh → 计数器加一 → 黄金角取色 → OSC 11 上色">
</p>

1. **每个面板都是一个新 shell。** `~/.zshrc` 里 source 了 `tint.sh`，它在 shell 启动时运行一次。同一个面板里再开子 shell 不会重复换色。
2. **全局计数器加一。** 计数器放在 `$TMPDIR`，用 `mkdir` 当原子锁，同时恢复 4 个窗口也不会有两个面板拿到同一个号。
3. **黄金角取色。** 第 i 个面板取第 `(i × k) mod N` 个颜色，k 是最接近 0.382 × N 且与 N 互质的整数（8 色时 k=3，12 色 k=5，16 色 k=7）。互质保证转一圈每个颜色正好用一次；k/N ≈ 0.382 让相邻面板在色轮上相差约 137.5°，也就是向日葵种子的排列角度。
4. **OSC 11 上色。** `printf '\e]11;#D3E5DF\a'` 是终端的标准转义序列，只改当前面板的背景，不碰全局配置，也不需要重载。

<p align="center">
  <img src="assets/spread.svg" width="100%" alt="按顺序取色与黄金角取色对比，以及八角星形的取色路径">
</p>
<p align="center"><sub>8 色时，取色路径正好画出一颗八角星</sub></p>

## ❓ 常见问题

<details>
<summary><b>已经打开的面板没变色？</b></summary>
<br>

只有新面板会自动换。当前面板想立刻试：`source ~/.zshrc && tint`。

</details>

<details>
<summary><b>不用 Ghostty 可以吗？</b></summary>
<br>

可以。iTerm2、WezTerm、kitty、Alacritty、foot 等支持 OSC 11 的终端都行，在 source 之前加一行 `export TINT_ANY_TERM=1`。

</details>

<details>
<summary><b>tmux 里能用吗？</b></summary>
<br>

能，tint 会自动使用 tmux 透传序列。如果没效果，在 `~/.tmux.conf` 里加 `set -g allow-passthrough on`。

</details>

<details>
<summary><b>想要纯随机，或者按顺序取色？</b></summary>
<br>

`export TINT_ORDER=random`（随机，但不会连续两次同色）或 `TINT_ORDER=seq`。默认是 `spread`（黄金角）。

</details>

<details>
<summary><b>不想自动换色，只想要 tint 命令？</b></summary>
<br>

`export TINT_AUTO=0`。

</details>

<details>
<summary><b>在 cmux 等嵌入 Ghostty 的应用里，所有分屏变成了同一个颜色？</b></summary>
<br>

部分旧版本不能给每个分屏单独设置 OSC 11 背景。设 `export TINT_WASH=1`，tint 会改用单元格底色铺满面板。

</details>

<details>
<summary><b>颜色看起来很淡？</b></summary>
<br>

先检查 Ghostty 的 `background-opacity`，小于 1 时颜色会被透明度冲淡。想要更明显的颜色，可以换 `macaron`，或者用 `tint gen --c 0.05` 提高彩度。

</details>

<details>
<summary><b>怎么卸载？</b></summary>
<br>

`bash ~/.config/ghostty-tint/install.sh --uninstall`。它会删掉配置目录、rc 里的那几行和 Skill。

</details>

## 📦 项目结构

```text
tint.sh                核心，被 source 进 rc，纯 shell
moods/*.tint           7 种内置气质
tools/tint-gen.py      气质生成、体检、预览，只用 Python 标准库
tools/build.py         从 moods/ 生成 SVG，同步调色台和 Skill
tools/make_gifs.py     逐帧渲染 tools/gif/stage.html，合成 GIF
install.sh             安装与卸载
skills/ghostty-tint/   AI Skill，自带完整文件，可单独拷走
docs/                  在线调色台与手动方案
PROMPT.md              AI 话术
```

所有图片都从 `moods/` 生成。改了气质后运行 `python3 tools/build.py` 和 `python3 tools/make_gifs.py`，文档就会同步更新。

## 🙌 致谢

默认的「纸感」八色来自作者日常使用的 Otty Paper 浅色主题。欢迎提交你调出来的气质：放进 `moods/`，运行一次 `build.py`，它就会出现在图鉴里。

## 📄 License

**非商用免费，商用必须单独授权。** 本项目（脚本、气质、Skill、话术和文档）采用 [PolyForm Noncommercial 1.0.0](LICENSE)，源码公开，但不属于 OSI 定义的开源软件。

- **免费：** 个人学习和兴趣项目，在自己的电脑上给自己的终端配色；截图、录屏发在个人账号上分享（广告、商单、带货除外）；非商用地修改和转发，须附上 LICENSE。
- **需要授权：** 在收费工作、公司或团队内部使用，集成进商业产品，或用于付费课程和社群。个人小范围商用一般可以谈，机构使用须签书面协议。

详见 [COMMERCIAL.md](COMMERCIAL.md)。Copyright (c) 2026 [小小东 Xiaoxiaodong](https://x.com/xiaoxiaodong01)。
