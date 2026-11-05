# 수동 설치: 설치 스크립트 없이 쓰기

<a href="manual.md">简体中文</a> · <a href="manual.en.md">English</a> · <a href="manual.ja.md">日本語</a> · <strong>한국어</strong> · <a href="manual.ar.md">العربية</a>

가장 간단한 방법부터 가장 완전한 방법까지 정리했습니다. 필요에 맞는 것 하나를 고르면 됩니다.

---

## 0단계: 명령 하나로 현재 패널 색 바꾸기

아무 Ghostty 패널에서 실행해 보세요:

```bash
printf '\e]11;#D7E2EC\a'
```

원리는 이게 전부입니다. `\e]11;색\a`는 터미널 표준 **OSC 11** 이스케이프 시퀀스로, "현재 패널의 배경을 이 색으로 바꿔라"라는 뜻입니다. 이 패널 하나에만 적용되고, 패널을 닫으면 사라지며, 설정은 전혀 건드리지 않습니다.

기본값으로 되돌리려면 `printf '\e]111\a'`를 실행합니다.

## 1단계: 5줄로 새 패널에 자동으로 색 입히기 (zsh)

아래 코드를 `~/.zshrc` 맨 끝에 붙여 넣습니다:

```zsh
# Ghostty 새 패널 자동 배경색 (최소 버전)
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors} + 1 ))]}"
fi
```

- 색은 이미 "황금각" 순서로 정렬되어 있습니다(원래 색상 순서로는 1→4→7→2→5→8→3→6). 그래서 앞에서부터 차례로 꺼내 써도 비슷한 색이 이어지지 않습니다.
- 색을 바꾸려면 그 줄의 색상값만 고치면 됩니다. 원하는 만큼 몇 개든 넣을 수 있습니다. 순서를 직접 정할 때는 **이웃한 두 색이 색상환에서도 이웃하지 않게** 하세요.
- 색상값은 반드시 따옴표로 감싸야 합니다. 그렇지 않으면 zsh가 `#`을 주석으로 처리합니다.

bash 버전(배열 인덱스가 0부터 시작):

```bash
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors[@]} ))]}"
fi
```

이 버전의 한계: 창 여러 개를 동시에 복원하면 가끔 두 패널이 같은 색이 됩니다(잠금이 없기 때문). 같은 패널에서 서브셸을 열면 색이 한 번 더 바뀝니다. 자식 프로세스(`cat`)를 두 번 띄우므로 시작이 1–2ms 느려집니다. 그래도 일상적으로 쓰기에는 충분합니다.

## 2단계: 완전판 수동 설치

완전판 `tint.sh`는 위의 한계를 모두 해결했고, `tint` 명령, 7가지 무드, 생성기까지 들어 있습니다. 수동 설치는 파일을 제자리에 두고 source 한 줄을 추가하는 것이 전부입니다:

```bash
git clone --depth 1 https://github.com/nevertoday/ghostty-tint ~/ghostty-tint
mkdir -p ~/.config/ghostty-tint/moods
cp ~/ghostty-tint/tint.sh ~/.config/ghostty-tint/
cp ~/ghostty-tint/tools/tint-gen.py ~/.config/ghostty-tint/
cp ~/ghostty-tint/moods/*.tint ~/.config/ghostty-tint/moods/
echo 'source ~/.config/ghostty-tint/tint.sh' >> ~/.zshrc     # bash 사용자는 ~/.bashrc에 추가
```

분할 패널을 새로 하나 열면 끝입니다.

### 기본 무드 바꾸기

```bash
echo mist > ~/.config/ghostty-tint/mood      # tint mood mist와 같음
```

또는 rc 파일에서 source 줄보다 앞에 `export TINT_MOOD=mist`를 적어도 됩니다(이쪽이 우선합니다).

### 무드 직접 만들기

`~/.config/ghostty-tint/moods/mine.tint` 파일을 새로 만듭니다:

```text
name  나의 무드 Mine
vibe  한 줄 설명
fg    #1A1A1A

bg    #EBD6D3  코랄    red
bg    #ECE5C6  사금    yellow
bg    #D3E5DF  청자    teal
bg    #E0DAEA  연보라  purple
```

- `bg` 줄: 색상값 뒤에 이름을 몇 개든 붙일 수 있고, 그 이름으로 바로 지정할 수 있습니다: `tint 코랄`, `tint red`.
- **색상 순서대로 적으세요**(빨강→주황→노랑→초록→청록→파랑→보라→분홍). tint가 황금각으로 알아서 흩어 줍니다.
- `fg`: 글자색이며 생략할 수 있습니다. 어두운 무드라면 밝은 글자색을 꼭 지정하세요. 예: `fg #E6E4DC`.
- 선택 항목으로 `cursor #RRGGBB`(커서 색), `ansi 0 #RRGGBB` … `ansi 15 #RRGGBB`(ANSI 16색)도 쓸 수 있습니다.

그다음 `tint mood mine`을 실행합니다.

### 색 고르는 요령

보기 좋은 패널 팔레트의 규칙은 하나뿐입니다: **명도와 채도는 같게, 색상만 바꾼다.** 손으로 맞추기는 어려우니 생성기를 쓰는 것을 권합니다:

```bash
python3 ~/.config/ghostty-tint/tint-gen.py --l 0.91 --c 0.03 --hue 20 --count 8 --name mine \
  -o ~/.config/ghostty-tint/moods/mine.tint
python3 ~/.config/ghostty-tint/tint-gen.py --check ~/.config/ghostty-tint/moods/mine.tint
```

또는 [온라인 팔레트](https://nevertoday.github.io/ghostty-tint/)를 열어 슬라이더를 움직이면서 보이는 그대로 조정할 수 있습니다.

## 제거

rc 파일에서 source 줄을 지우고 `rm -rf ~/.config/ghostty-tint`를 실행하면 됩니다.
