<div align="center" dir="rtl">

# الطريقة اليدوية: استخدامه دون تشغيل سكربت التثبيت

<a href="manual.md">简体中文</a> · <a href="manual.en.md">English</a> · <a href="manual.ja.md">日本語</a> · <a href="manual.ko.md">한국어</a> · <strong>العربية</strong>

</div>

<div dir="rtl">

من الأبسط إلى الأكمل، اختر المستوى الذي يناسبك.

---

## المستوى 0: أمر واحد يغيّر لون اللوحة الحالية

شغّل هذا الأمر في أي لوحة من لوحات Ghostty:

<div dir="ltr">

```bash
printf '\e]11;#D7E2EC\a'
```

</div>

هذا هو المبدأ كله: ⁦`\e]11;اللون\a`⁩ هو تسلسل الهروب **OSC 11** القياسي في الطرفيات، ومعناه «اجعل خلفية اللوحة الحالية بهذا اللون». لا يؤثر إلا في هذه اللوحة وحدها، ويزول بإغلاقها، ولا يغيّر أي إعداد.

للعودة إلى اللون الافتراضي: ⁦`printf '\e]111\a'`⁩.

## المستوى 1: خمسة أسطر تلوّن كل لوحة جديدة تلقائياً (zsh)

ألصق المقطع التالي في آخر ⁦`~/.zshrc`⁩:

<div dir="ltr">

```zsh
# Ghostty: auto-tint every new pane (minimal version)
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors} + 1 ))]}"
fi
```

</div>

- الألوان مرتّبة مسبقاً وفق «الزاوية الذهبية» (ترتيبها الأصلي حسب تدرّج اللون هو ⁦1→4→7→2→5→8→3→6⁩)، لذا يكفي أخذها بالتسلسل دون أن يتكرر لونان متشابهان.
- لتغيير الألوان عدّل القيم في ذلك السطر، وضع منها العدد الذي تريده. وإن رتّبتها بنفسك فتذكّر: **لا تجعل لونين متتاليين متجاورين على دائرة الألوان**.
- يجب وضع قيم الألوان بين علامتي اقتباس، وإلا عدّ zsh الرمز ⁦`#`⁩ بداية تعليق.

نسخة bash (تبدأ فهارس المصفوفات فيها من 0):

<div dir="ltr">

```bash
if [[ $TERM_PROGRAM == ghostty && $- == *i* ]]; then
  tint_colors=('#EBD6D3' '#DDE7D3' '#E0DAEA' '#EFDFC9' '#D3E5DF' '#EFDCE6' '#ECE5C6' '#D7E2EC')
  f="${TMPDIR:-/tmp}/tint-counter"; n=$(( $(cat "$f" 2>/dev/null || echo 0) + 1 )); echo $n > "$f"
  printf '\e]11;%s\a' "${tint_colors[$(( (n - 1) % ${#tint_colors[@]} ))]}"
fi
```

</div>

حدود هذه النسخة: عند استعادة عدة نوافذ في وقت واحد قد تحصل لوحتان أحياناً على اللون نفسه (لعدم وجود قفل)، وفتح shell فرعي داخل اللوحة نفسها يغيّر لونها مرة أخرى، كما أنها تستدعي عمليتين فرعيتين (⁦`cat`⁩) فيتأخر بدء الـ shell بمقدار 1–2 ملّي ثانية. وهي مع ذلك كافية تماماً للاستخدام اليومي.

## المستوى 2: النسخة الكاملة بتثبيت يدوي

تعالج النسخة الكاملة ⁦`tint.sh`⁩ كل الحدود المذكورة أعلاه، ومعها الأمر ⁦`tint`⁩ وسبعة طوابع والمولّد. والتثبيت اليدوي ليس إلا وضع الملفات في أماكنها وإضافة سطر source واحد:

<div dir="ltr">

```bash
git clone --depth 1 https://github.com/nevertoday/ghostty-tint ~/ghostty-tint
mkdir -p ~/.config/ghostty-tint/moods
cp ~/ghostty-tint/tint.sh ~/.config/ghostty-tint/
cp ~/ghostty-tint/tools/tint-gen.py ~/.config/ghostty-tint/
cp ~/ghostty-tint/moods/*.tint ~/.config/ghostty-tint/moods/
echo 'source ~/.config/ghostty-tint/tint.sh' >> ~/.zshrc     # bash users: write it to ~/.bashrc instead
```

</div>

افتح لوحة مقسومة جديدة، وانتهى الأمر.

### تغيير الطابع الافتراضي

<div dir="ltr">

```bash
echo mist > ~/.config/ghostty-tint/mood      # same as: tint mood mist
```

</div>

أو اكتب ⁦`export TINT_MOOD=mist`⁩ في ملف rc قبل سطر source (وله أولوية أعلى).

### اصنع طابعك بنفسك

أنشئ الملف ⁦`~/.config/ghostty-tint/moods/mine.tint`⁩:

<div dir="ltr">

```text
name  طابعي Mine
vibe  وصف في جملة واحدة
fg    #1A1A1A

bg    #EBD6D3  مرجاني  red
bg    #ECE5C6  رملي  yellow
bg    #D3E5DF  يشمي  teal
bg    #E0DAEA  ليلكي  purple
```

</div>

- سطر ⁦`bg`⁩: قيمة اللون يليها أي عدد من الأسماء، ويمكنك استخدام هذه الأسماء مباشرة: ⁦`tint مرجاني`⁩ أو ⁦`tint red`⁩.
- **اكتب الألوان بترتيب تدرّج اللون** (أحمر ← برتقالي ← أصفر ← أخضر ← فيروزي ← أزرق ← بنفسجي ← وردي)، وسيتولى tint بعثرتها تلقائياً بالزاوية الذهبية.
- ⁦`fg`⁩: لون النص، ويمكن حذفه. وفي الطوابع الداكنة لا تنسَ تحديد لون نص فاتح، مثل ⁦`fg #E6E4DC`⁩.
- اختيارياً: ⁦`cursor #RRGGBB`⁩ (لون المؤشر)، و⁦`ansi 0 #RRGGBB`⁩ … ⁦`ansi 15 #RRGGBB`⁩ (ألوان ANSI الستة عشر).

ثم شغّل ⁦`tint mood mine`⁩.

### نصيحة لاختيار الألوان

لمجموعة ألوان اللوحات الجميلة قاعدة واحدة فقط: **السطوع والتشبّع ثابتان، ولا يتغيّر إلا تدرّج اللون**. وهذا صعب الضبط يدوياً، لذا ننصح باستخدام المولّد:

<div dir="ltr">

```bash
python3 ~/.config/ghostty-tint/tint-gen.py --l 0.91 --c 0.03 --hue 20 --count 8 --name mine \
  -o ~/.config/ghostty-tint/moods/mine.tint
python3 ~/.config/ghostty-tint/tint-gen.py --check ~/.config/ghostty-tint/moods/mine.tint
```

</div>

أو افتح [لوحة الألوان على الويب](https://nevertoday.github.io/ghostty-tint/) وحرّك المنزلقات، فترى النتيجة فوراً كما ستظهر.

## إلغاء التثبيت

احذف سطر source ذاك من ملف rc، ثم شغّل ⁦`rm -rf ~/.config/ghostty-tint`⁩، وهذا كل شيء.

</div>
