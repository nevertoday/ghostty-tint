# 手動セットアップ：インストールスクリプトなしで使う

<a href="manual.md">简体中文</a> · <a href="manual.en.md">English</a> · <strong>日本語</strong> · <a href="manual.ko.md">한국어</a> · <a href="manual.ar.md">العربية</a>

いちばん簡単な方法から完全版まで、合うものをひとつ選んでください。

---

## レベル 0：コマンド一つで、今のペインの色を変える

Ghostty のどのペインでもいいので、次を実行します：

```bash
printf '\e]11;#D7E2EC\a'
```

しくみはこれだけです。`\e]11;色\a` は端末標準の **OSC 11** エスケープシーケンスで、「今のペインの背景をこの色にする」という意味です。影響するのはそのペインだけで、閉じれば元に戻ります。設定ファイルは一切変更しません。

既定の色に戻すには：`printf '\e]111\a'`。

## レベル 1：5 行で、新しいペインを自動で色づける（zsh）

次のコードを `~/.zshrc` の末尾に貼り付けます：

```zsh
# Ghostty の新しいペインを自動で色づける（最小版）
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors} + 1 ))]}"
fi
```

- 色はあらかじめ「黄金角」の順に並べてあります（元の色相順でいうと 1→4→7→2→5→8→3→6）。なので順番に取り出すだけで、似た色が続きません。
- 色を変えたいときは、その行の色の値を書き換えるだけです。何色でも好きなだけ書けます。自分で並び順を決めるときは、**隣り合う二色が色相環でも隣同士にならないように**してください。
- 色の値は必ず引用符で囲んでください。囲まないと zsh が `#` をコメントとして扱ってしまいます。

bash 版（配列は 0 始まり）：

```bash
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors[@]} ))]}"
fi
```

この版の制限：複数のウィンドウを同時に復元すると、ときどき二つのペインが同じ色になります（ロックをかけていないため）。同じペインでサブシェルを開くと、もう一度色が変わります。サブプロセス（`cat`）を二つ使うので、起動が 1–2ms 遅くなります。とはいえ、普段使いにはこれで十分です。

## レベル 2：完全版を手動でインストール

完全版の `tint.sh` は上の制限をすべて解消していて、`tint` コマンド、7 つのムード、ジェネレーターも付いています。手動インストールは、ファイルを所定の場所に置いて source を一行加えるだけです：

```bash
git clone --depth 1 https://github.com/nevertoday/ghostty-tint ~/ghostty-tint
mkdir -p ~/.config/ghostty-tint/moods
cp ~/ghostty-tint/tint.sh ~/.config/ghostty-tint/
cp ~/ghostty-tint/tools/tint-gen.py ~/.config/ghostty-tint/
cp ~/ghostty-tint/moods/*.tint ~/.config/ghostty-tint/moods/
echo 'source ~/.config/ghostty-tint/tint.sh' >> ~/.zshrc     # bash の場合は ~/.bashrc に書く
```

新しい分割ペインを開けば完了です。

### 既定のムードを変える

```bash
echo mist > ~/.config/ghostty-tint/mood      # tint mood mist と同じ
```

または rc で source する前に `export TINT_MOOD=mist` と書いておきます（こちらのほうが優先されます）。

### 自分でムードを書く

`~/.config/ghostty-tint/moods/mine.tint` を新しく作ります：

```text
name  マイムード Mine
vibe  ひとことで説明
fg    #1A1A1A

bg    #EBD6D3  コーラル  red
bg    #ECE5C6  サンドゴールド  yellow
bg    #D3E5DF  青磁  teal
bg    #E0DAEA  スモークパープル  purple
```

- `bg` 行：色の値と、好きな数の名前を書きます。名前はそのまま指定に使えます：`tint コーラル`、`tint red`。
- **色相の順に書いてください**（赤→橙→黄→緑→青緑→青→紫→ピンク）。tint が自動で黄金角に沿って散らしてくれます。
- `fg`：文字の色。省略できます。ダーク系のムードでは明るい文字色を忘れずに指定してください。例：`fg #E6E4DC`。
- 必要に応じて `cursor #RRGGBB`（カーソルの色）、`ansi 0 #RRGGBB` … `ansi 15 #RRGGBB`（ANSI 16 色）も指定できます。

あとは `tint mood mine` を実行します。

### 色選びのコツ

きれいなペイン用パレットのルールはひとつだけです：**明度と彩度をそろえて、色相だけを変える**。手作業で合わせるのは難しいので、ジェネレーターを使うのがおすすめです：

```bash
python3 ~/.config/ghostty-tint/tint-gen.py --l 0.91 --c 0.03 --hue 20 --count 8 --name mine \
  -o ~/.config/ghostty-tint/moods/mine.tint
python3 ~/.config/ghostty-tint/tint-gen.py --check ~/.config/ghostty-tint/moods/mine.tint
```

または[オンライン調色台](https://nevertoday.github.io/ghostty-tint/)を開いてスライダーを動かせば、見たままの色で調整できます。

## アンインストール

rc に加えた source の一行を消して、`rm -rf ~/.config/ghostty-tint` を実行すれば完了です。
