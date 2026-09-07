# Builds part2.html by reusing Part 1's shell (head, styles, chrome, engine)
# so both decks are visually and behaviourally identical.
import io, re, sys

SRC = 'index.html'
OUT = 'part2.html'
SLIDES_FILE = 'part2_slides.html'

src = io.open(SRC, encoding='utf-8').read()

open_marker = '<div class="slides" id="slides">'
close_marker = '\n  </div>\n\n  <div class="menu-overlay" id="menuOverlay">'
i = src.index(open_marker) + len(open_marker)
j = src.index(close_marker)

shell_head = src[:i]
shell_tail = src[j:]

# Part 2 branding
shell_head = shell_head.replace('<span class="part-tag en">PART 1</span>',
                                '<span class="part-tag en">PART 2</span>')
shell_head = shell_head.replace('<title>طبيب PRIME</title>',
                                '<title>طبيب PRIME — الجزء الثاني</title>')
shell_head = shell_head.replace(
    'content="الذكاء الاصطناعي × الطبيب — إطار PRIME للأطباء ، الجزء الأول."',
    'content="الذكاء الاصطناعي × الطبيب — الجزء الثاني: أدوات الذكاء الاصطناعي في الأمراض الجلدية."')
shell_head = shell_head.replace('<div class="act-chip" id="actChip">افتتاحية</div>',
                                '<div class="act-chip" id="actChip">افتتاحية</div>')

blob = io.open(SLIDES_FILE, encoding='utf-8').read()

# Each slide is delimited by:  <!--SLIDE|act|title-->
parts = re.split(r'<!--SLIDE\|(.*?)\|(.*?)-->', blob)
if parts[0].strip():
    sys.exit('content before first slide marker')
acts, titles, bodies = [], [], []
for k in range(1, len(parts), 3):
    acts.append(parts[k].strip())
    titles.append(parts[k+1].strip())
    bodies.append(parts[k+2].rstrip())

slides_html = []
for n, (a, body) in enumerate(zip(acts, bodies), 1):
    slides_html.append('\n    <!-- %d -->\n    <section class="slide" data-act="%s">%s\n    </section>\n'
                       % (n, a, body))

# Part 1's engine also wires up widgets that live inside Part 1's own slides and bind by
# element id (su-*, dr-*, sp-*, sqdt-*). Those ids do not exist here, so the binding throws
# and takes render() down with it. Drop those sections; everything class-based is generic
# and no-ops safely on an empty NodeList.
PART1_ONLY = [
    ('  // system setup builder', '  // generalized matcher'),
    ('  // same question, different tool', '  // generic checklist persistence'),
]
for start_marker, end_marker in PART1_ONLY:
    a = shell_tail.index(start_marker)
    b = shell_tail.index(end_marker)
    assert a < b, (start_marker, end_marker)
    shell_tail = shell_tail[:a] + shell_tail[b:]

# ...and the one-off init call for those same widgets.
kickoff = '  buildSetup(); buildDeepResearch(); buildStudyPlan();\n'
assert kickoff in shell_tail
shell_tail = shell_tail.replace(kickoff, '')


def js_arr(name, items):
    inner = ',\n    '.join('"%s"' % s.replace('"', '\\"') for s in items)
    return 'var %s = [\n    %s\n  ];' % (name, inner)

tail = shell_tail
tail = re.sub(r'var titles = \[.*?\];', lambda m: js_arr('titles', titles), tail, count=1, flags=re.S)
tail = re.sub(r'var acts = \[.*?\];',   lambda m: js_arr('acts', acts),     tail, count=1, flags=re.S)

out = shell_head + ''.join(slides_html) + tail
io.open(OUT, 'w', encoding='utf-8').write(out)
print('part2.html written — %d slides' % len(acts))
for n, (a, t) in enumerate(zip(acts, titles), 1):
    print('%3d  [%s] %s' % (n, a, t))
