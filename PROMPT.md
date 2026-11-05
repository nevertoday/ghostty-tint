# AI 话术：复制给 AI，让它帮你实现

下面每一段都可以**原样复制**给 Claude Code、Codex、Cursor、Gemini CLI 等能操作终端的 AI。按需要挑一段就行。

> 小提示：AI 的命令行不是你正在看的那个 Ghostty 面板，它运行 `tint` 你看不到颜色。装好以后，你自己按 <kbd>⌘</kbd><kbd>D</kbd> 新开一个分屏看效果。

---

## ① 一键安装（最常用）

```text
帮我安装 ghostty-tint（https://github.com/nevertoday/ghostty-tint），让 Ghostty 每个新面板自动换一种低饱和背景色。

步骤：
1. 把仓库克隆到临时目录，运行 bash install.sh --skill
2. 如果安装器提示我的 rc 文件里已经有别的 OSC 11 换色逻辑，先把那几行给我看，问我要不要注释掉，不要直接删
3. 装完用一张表告诉我有哪些内置气质（名字、一句话气质、色数），并推荐 3 个适合长时间写代码的
4. 告诉我在 Ghostty 里切换气质的命令
```

## ② 我想要某种感觉

```text
我用 ghostty-tint 给 Ghostty 面板配色。帮我做一个新气质：

感觉：【例如：京都秋天的寺庙 / 雨后的江南 / 北欧极简 / 深夜咖啡馆 / 赛博朋克】
颜色数量：【例如：12】
浅色还是深色：【浅色 / 深色 / 你决定】

要求：
- 用 ~/.config/ghostty-tint/tint-gen.py 在 OKLCH 里生成（所有颜色亮度、彩度相同，只转色相）
- 把我的描述翻译成 --l --c --hue --span 参数，并说明你为什么这样选
- 给每个颜色起一个和这个气质同一个世界观的中文名，保留英文色相词做别名
- 用 tint-gen.py --check 体检：文字对比度 ≥ 7，相邻面板色差 ΔE ≥ 3，不过就调参重来
- 保存到 ~/.config/ghostty-tint/moods/<id>.tint，最后给我一张色板表和一行 tint mood <id>
- 再给我 3 个相近或互补的备选气质
```

## ③ 改颜色数量

```text
我在用 ghostty-tint 的【paper】气质，想把它扩展成【16】色，气质保持不变。
用 tint gen --like paper --count 16 生成到 ~/.config/ghostty-tint/moods/paper16.tint，
给新增的颜色起名（沿用原来的命名风格），体检通过后告诉我怎么切换。
```

## ④ 从一个颜色出发

```text
我很喜欢这个颜色：【#D7E2EC】。用 ghostty-tint 的 tint gen --seed 从它出发，
帮我生成一套【8】色的面板配色，保持同样的亮度和彩度，起好名字，体检后告诉我怎么切换。
```

## ⑤ 不用这个仓库，从零实现（适合想自己掌握原理的人）

```text
帮我在 ~/.zshrc 里实现「Ghostty 每个新面板自动换一种背景色」，要求：

1. 色板：用户可自定义 N 个颜色（N 任意），默认 8 个低饱和浅色：
   #EBD6D3 #EFDFC9 #ECE5C6 #DDE7D3 #D3E5DF #D7E2EC #E0DAEA #EFDCE6（按色相顺序）
2. 只在 Ghostty 里生效（TERM_PROGRAM=ghostty），只在交互式 shell 里运行；
   同一个面板里再开子 shell 不重复换色（可以记住当前 tty 判断）
3. 全局计数器放在 $TMPDIR，用 mkdir 当原子锁，避免同时打开多个面板时拿到同一个序号；锁超过 1 秒视为残留，直接清掉
4. 取色顺序用「黄金角」：第 i 个面板取第 (i*k mod N) 个颜色，k 为最接近 0.382*N 且与 N 互质的整数；
   4 色、6 色这种找不到好 k 的情况，先取奇数位再取偶数位
5. 用 OSC 11 设置背景：printf '\e]11;%s\a' "$color"；在 tmux 里要包成 DCS 透传
6. 再提供一个 tint 函数：tint（下一个）、tint random（随机且不与上次相同）、tint 3（第 3 色）、tint '#RRGGBB'、tint reset（OSC 111 恢复默认）
7. 全部用 shell 内建命令，不要用 $(...) 子进程，shell 启动要快
8. 同时兼容 zsh 和 bash（注意 zsh 数组从 1 开始、unquoted 变量不分词）

写好后告诉我新开一个分屏验证，并解释每一步为什么这样做。
```

## ⑥ 颜色没变，帮我排查

```text
我装了 ghostty-tint，但新开的 Ghostty 面板背景色没变。请按顺序排查，找到原因就停：
1. grep -n ghostty-tint ~/.zshrc ~/.bashrc，确认 source 行存在且在文件靠后的位置
2. 在一个新 shell 里检查 echo $TERM_PROGRAM 是不是 ghostty（不是就建议 TINT_ANY_TERM=1）
3. 看 rc 里 source 之后是否还有别的脚本发了 OSC 11、clear 或切主题，把颜色盖掉
4. 如果在 tmux 里，检查 ~/.tmux.conf 是否有 set -g allow-passthrough on
5. 检查 Ghostty 配置里的 background-opacity 是否小于 1
6. 如果是 cmux 等嵌入 Ghostty 的应用，所有分屏同色，就建议 TINT_WASH=1
最后告诉我改了什么、怎么验证。
```

## ⑦ 装 Skill 之后，一句话就够了

装了 Skill（`bash install.sh --skill`）以后，上面这些都不用复制，直接说：

```text
我想要雨后江南的感觉，12 个颜色
```

```text
给我一个适合晚上直播演示的深色面板配色
```

```text
把现在的配色改成 24 色
```
