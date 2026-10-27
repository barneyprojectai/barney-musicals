"""Guitar Scales: 6 Ways to Play Every Scale — printable/on-screen PDF book.

Usage: python3 tools/make_guitar_scales_book.py books/guitar-scales-6-ways.pdf logo.png
"""
import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white

FD = '/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('Sans', FD + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('SansB', FD + 'DejaVuSans-Bold.ttf'))

INK = HexColor('#2A1A10'); MUTED = HexColor('#6E5A4C'); LINE = HexColor('#F3D9C2')
PAPER = HexColor('#FFF8F1'); SOFT = HexColor('#FFEFDD'); ORANGE = HexColor('#FF8A1F')
DEEP = HexColor('#C2410C'); WOOD = HexColor('#FFF3E6'); FRET = HexColor('#B9A08C')
STRINGC = HexColor('#8C7666'); BLUE = HexColor('#1D4E89')

W, H = landscape(A4)
LOGO = sys.argv[2] if len(sys.argv) > 2 else 'logo.png'

OPEN = [40, 45, 50, 55, 59, 64]           # strings low E .. high e (MIDI)
SNAME = ['6th (low E)', '5th (A)', '4th (D)', '3rd (G)', '2nd (B)', '1st (high e)']
SHORT = ['E', 'A', 'D', 'G', 'B', 'e']
ROOT = 9                                   # A

SCALES = [
    dict(id='major', title='A Major Scale', ints=[0, 2, 4, 5, 7, 9, 11],
         names=['A', 'B', 'C♯', 'D', 'E', 'F♯', 'G♯'], degs=['1', '2', '3', '4', '5', '6', '7'],
         boxes=[2, 4, 7, 9, 12], six='3nps',
         about='The happy, bright sound of “Do Re Mi”. Used in most worship songs and melodies.',
         use='Play over an A major chord, or songs in the key of A.'),
    dict(id='minor', title='A Natural Minor Scale', ints=[0, 2, 3, 5, 7, 8, 10],
         names=['A', 'B', 'C', 'D', 'E', 'F', 'G'], degs=['1', '2', '♭3', '4', '5', '♭6', '♭7'],
         boxes=[3, 5, 7, 10, 12], six='3nps',
         about='The sad, serious sound. Same notes as C major, but A is home.',
         use='Play over an A minor chord, or songs in A minor.'),
    dict(id='pmajor', title='A Major Pentatonic', ints=[0, 2, 4, 7, 9],
         names=['A', 'B', 'C♯', 'E', 'F♯'], degs=['1', '2', '3', '5', '6'],
         boxes=[2, 5, 7, 9, 12], six='diag',
         about='Five notes, no wrong notes. Sweet and open: great for fills between singing.',
         use='Play over A major songs. Good for country, gospel and worship fills.'),
    dict(id='pminor', title='A Minor Pentatonic', ints=[0, 3, 5, 7, 10],
         names=['A', 'C', 'D', 'E', 'G'], degs=['1', '♭3', '4', '5', '♭7'],
         boxes=[3, 5, 8, 10, 12], six='diag',
         about='The most-used scale for guitar solos: rock, blues and pop.',
         use='Play over A minor songs, or an A blues / rock groove.'),
    dict(id='blues', title='A Blues Scale', ints=[0, 3, 5, 6, 7, 10],
         names=['A', 'C', 'D', 'E♭', 'E', 'G'], degs=['1', '♭3', '4', '♭5', '5', '♭7'],
         boxes=[3, 5, 8, 10, 12], six='diag', blue=6,
         about='The minor pentatonic plus one “blue note” (E♭). Gives the crying blues sound.',
         use='Play over a 12-bar blues in A. Slide or bend into the blue note.'),
]

# ---------------------------------------------------------------- theory
def pcs(sc): return [(ROOT + i) % 12 for i in sc['ints']]

def name_of(sc, p):
    return sc['names'][sc['ints'].index((p - ROOT) % 12)]

def deg_of(sc, p):
    return sc['degs'][sc['ints'].index((p - ROOT) % 12)]

def next_in(p, P):
    p += 1
    while p % 12 not in P: p += 1
    return p

def box(P, f):
    """Notes of one position: hand around frets f..f+3 (f-1 allowed as a stretch)."""
    lo, hi = f - 1, f + 3
    notes, s, p = [], 0, OPEN[0] + f
    while p % 12 not in P: p += 1
    while True:
        while s < 6 and p - OPEN[s] > hi: s += 1
        if s == 6: break
        fr = p - OPEN[s]
        if fr < lo: break
        notes.append((s, fr, p)); p = next_in(p, P)
    return notes

def three_nps(P, start_pitch, per=3, strings=6):
    notes, p = [], start_pitch
    for s in range(strings):
        for _ in range(per):
            notes.append((s, p - OPEN[s], p)); p = next_in(p, P)
    return notes

def add_blue(notes, blue_pc):
    """Add the blues b5 to a pentatonic shape, on the string where it sits most naturally."""
    lo_p, hi_p = min(n[2] for n in notes), max(n[2] for n in notes)
    rng = {}
    for s, fr, p in notes: rng.setdefault(s, []).append(fr)
    out = list(notes)
    p = lo_p
    while p <= hi_p:
        if p % 12 == blue_pc:
            best = None
            for s, frs in rng.items():
                fr = p - OPEN[s]
                if fr < 0: continue
                d = 0 if min(frs) <= fr <= max(frs) else min(abs(fr - min(frs)), abs(fr - max(frs)))
                if d <= 1 and (best is None or d < best[0]): best = (d, s, fr)
            if best: out.append((best[1], best[2], p))
        p += 1
    return sorted(out, key=lambda n: n[2])

def finger_box(notes):
    frs = [n[1] for n in notes]
    lo = min(frs)
    def outside(h): return sum(1 for x in frs if x < h or x > h + 3)
    h = lo if outside(lo) < outside(lo + 1) else lo + 1
    fing = {}
    by = {}
    for n in notes: by.setdefault(n[0], []).append(n)
    for s, ns in by.items():
        f = [max(1, min(4, n[1] - h + 1)) for n in ns]
        if len(set(f)) < len(f):
            f = string_fingers([n[1] for n in ns])
        for n, x in zip(ns, f): fing[(n[0], n[1])] = x
    return fing, h

def string_fingers(frs):
    a = frs[0]; span = frs[-1] - a
    out = []
    for x in frs:
        r = x - a
        if span <= 3: out.append(r + 1)
        else: out.append({0: 1, 1: 2, 2: 2, 3: 3}.get(r, 4))
    if len(out) == 3 and out[1] == out[0]: out[1] = 2
    return out

def finger_3nps(notes):
    fing, by = {}, {}
    for n in notes: by.setdefault(n[0], []).append(n)
    for s, ns in by.items():
        for n, x in zip(ns, string_fingers([n[1] for n in ns])): fing[(n[0], n[1])] = x
    return fing

def ways(sc):
    P = pcs(sc)
    res = []
    for i, f in enumerate(sc['boxes']):
        if 'blue' in sc:
            base = box([(ROOT + x) % 12 for x in [0, 3, 5, 7, 10]], f)
            notes = add_blue(base, (ROOT + sc['blue']) % 12)
        else:
            notes = box(P, f)
        fing, h = finger_box(notes)
        res.append(dict(kind='box', n=i + 1, notes=notes, fing=fing, hand=h))
    if sc['six'] == '3nps':
        notes = three_nps(P, OPEN[0] + 5)          # start on low A, 6th string fret 5
        res.append(dict(kind='3nps', n=6, notes=notes, fing=finger_3nps(notes), hand=None))
    else:
        start = OPEN[0]
        while start % 12 not in P: start += 1
        if 'blue' in sc:
            base = three_nps([(ROOT + x) % 12 for x in [0, 3, 5, 7, 10]], OPEN[0] + 0)
            notes = add_blue(base, (ROOT + sc['blue']) % 12)
        else:
            notes = three_nps(P, start)
        res.append(dict(kind='diag', n=6, notes=notes, fing=None, hand=None))
    return res

# ---------------------------------------------------------------- drawing helpers
def txt(c, x, y, s, size=11, font='Sans', color=INK, align='l'):
    c.setFont(font, size); c.setFillColor(color)
    {'l': c.drawString, 'c': c.drawCentredString, 'r': c.drawRightString}[align](x, y, s)

def wrap(c, x, y, s, width, size=10.5, font='Sans', color=INK, lead=None):
    lead = lead or size * 1.4
    words, line = s.split(), ''
    for w in words:
        t = (line + ' ' + w).strip()
        if pdfmetrics.stringWidth(t, font, size) > width and line:
            txt(c, x, y, line, size, font, color); y -= lead; line = w
        else: line = t
    if line: txt(c, x, y, line, size, font, color); y -= lead
    return y

def header(c, title, sub, pg):
    c.setFillColor(PAPER); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(white); c.rect(0, H - 70, W, 70, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.rect(0, H - 74, W, 4, stroke=0, fill=1)
    c.drawImage(LOGO, W - 86, H - 64, 52, 52, mask='auto', preserveAspectRatio=True)
    txt(c, 34, H - 38, title, 22, 'SansB')
    txt(c, 34, H - 58, sub, 11.5, 'Sans', MUTED)
    txt(c, 34, 18, 'Barney Musicals · Shine Worshippers Academy', 8.5, 'Sans', MUTED)
    txt(c, W - 34, 18, str(pg), 8.5, 'Sans', MUTED, 'r')

def dot(c, x, y, r, label, kind):
    if kind == 'root':
        c.setFillColor(ORANGE); c.setStrokeColor(DEEP); c.setLineWidth(1.6)
        c.circle(x, y, r, stroke=1, fill=1); col = INK; font = 'SansB'
    elif kind == 'blue':
        c.setFillColor(BLUE); c.setStrokeColor(BLUE); c.setLineWidth(1)
        c.circle(x, y, r, stroke=1, fill=1); col = white; font = 'SansB'
    else:
        c.setFillColor(INK); c.setStrokeColor(INK); c.setLineWidth(1)
        c.circle(x, y, r, stroke=1, fill=1); col = white; font = 'SansB'
    size = r * (0.95 if len(label) < 2 else 0.78)
    txt(c, x, y - size * 0.36, label, size, font, col, 'c')

def fretboard(c, sc, notes, x0, y0, w, h, f_lo, f_hi, labels='name', octave_lines=True,
              brackets=None, small=False, pairs=None):
    """Draw horizontal neck: high e on top (same as tab). f_lo..f_hi are the frets shown."""
    nf = f_hi - f_lo + 1
    show_nut = f_lo <= 1
    if show_nut: f_lo = 0; nf = f_hi + 1
    cw = w / nf
    sg = h / 5
    def sy(s): return y0 + s * sg          # s: 0 = low E (bottom)
    def fx(fr): return x0 + (fr - f_lo + 0.5) * cw
    # wood
    c.setFillColor(WOOD); c.setStrokeColor(LINE)
    c.rect(x0, y0 - sg * 0.35, w, h + sg * 0.7, stroke=0, fill=1)
    # inlays
    c.setFillColor(HexColor('#EBD8C6'))
    for m in (3, 5, 7, 9, 15, 17, 19, 21):
        if f_lo <= m <= f_lo + nf - 1 and m > 0: c.circle(fx(m), y0 + h / 2, min(cw, sg) * 0.16, stroke=0, fill=1)
    if f_lo <= 12 <= f_lo + nf - 1:
        c.circle(fx(12), y0 + sg * 1.5, min(cw, sg) * 0.16, stroke=0, fill=1)
        c.circle(fx(12), y0 + sg * 3.5, min(cw, sg) * 0.16, stroke=0, fill=1)
    # frets
    for i in range(nf + 1):
        xx = x0 + i * cw
        if show_nut and i == 1:
            c.setStrokeColor(INK); c.setLineWidth(5)
        else:
            c.setStrokeColor(FRET); c.setLineWidth(1.6)
        if show_nut and i == 0: continue
        c.line(xx, y0 - sg * 0.35, xx, y0 + h + sg * 0.35)
    # strings
    for s in range(6):
        c.setStrokeColor(STRINGC); c.setLineWidth(0.6 + (5 - s) * 0.28)
        c.line(x0, sy(s), x0 + w, sy(s))
        txt(c, x0 - 8, sy(s) - 4, SHORT[s], 10 if not small else 8, 'SansB', MUTED, 'r')
    # fret numbers
    for fr in range(f_lo, f_lo + nf):
        lab = 'open' if fr == 0 else str(fr)
        mark = fr in (3, 5, 7, 9, 12, 15, 17)
        txt(c, fx(fr), y0 - sg * 0.35 - (14 if not small else 11), lab, 10 if not small else 7.5,
            'SansB' if mark else 'Sans', INK if mark else MUTED, 'c')
    # brackets (neck map)
    if brackets:
        for i, (a, b, lab) in enumerate(brackets):
            yy = y0 + h + sg * 0.55 + (i % 2) * 18
            xa, xb = fx(a) - cw * 0.45, fx(b) + cw * 0.45
            c.setStrokeColor(DEEP); c.setLineWidth(1.4)
            c.line(xa, yy, xb, yy); c.line(xa, yy, xa, yy - 5); c.line(xb, yy, xb, yy - 5)
            txt(c, (xa + xb) / 2, yy + 3, lab, 8.5, 'SansB', DEEP, 'c')
    # octave lines between roots
    roots = sorted([n for n in notes if (n[2] - ROOT) % 12 == 0], key=lambda n: n[2])
    if pairs is None:
        pairs = [((a[0], a[1]), (b[0], b[1])) for a, b in zip(roots, roots[1:]) if b[2] - a[2] == 12]
    if octave_lines and pairs:
        c.setStrokeColor(ORANGE); c.setLineWidth(2); c.setDash(4, 3)
        for (s1, f1), (s2, f2) in pairs: c.line(fx(f1), sy(s1), fx(f2), sy(s2))
        c.setDash()
    r = min(cw, sg) * (0.36 if not small else 0.4)
    for s, fr, p in notes:
        k = 'root' if (p - ROOT) % 12 == 0 else ('blue' if 'blue' in sc and (p - ROOT) % 12 == sc['blue'] else 'n')
        lab = name_of(sc, p) if labels == 'name' else deg_of(sc, p)
        if fr == 0:
            dot(c, x0 + cw * 0.5, sy(s), r, lab, k)
        else:
            dot(c, fx(fr), sy(s), r, lab, k)
    return fx, sy

def tab(c, sc, seq, fing, x0, y0, w, label):
    """seq: list of (string, fret, pitch). y0 = top line (high e)."""
    lg = 11
    txt(c, x0, y0 + 22, label, 10.5, 'SansB', DEEP)
    for i in range(6):
        c.setStrokeColor(FRET); c.setLineWidth(0.7)
        c.line(x0 + 18, y0 - i * lg, x0 + w, y0 - i * lg)
        txt(c, x0 + 6, y0 - i * lg - 3.2, 'eBGDAE'[i], 8, 'SansB', MUTED, 'c')
    c.setStrokeColor(INK); c.setLineWidth(1.2)
    c.line(x0 + 18, y0, x0 + 18, y0 - 5 * lg); c.line(x0 + w, y0, x0 + w, y0 - 5 * lg)
    step = (w - 36) / max(1, len(seq))
    step = min(step, 34)
    for j, (s, fr, p) in enumerate(seq):
        x = x0 + 34 + j * step
        y = y0 - (5 - s) * lg
        isroot = (p - ROOT) % 12 == 0
        isblue = 'blue' in sc and (p - ROOT) % 12 == sc['blue']
        lab = str(fr)
        tw = pdfmetrics.stringWidth(lab, 'SansB', 9.5) + 4
        c.setFillColor(PAPER); c.rect(x - tw / 2, y - 5, tw, 10, stroke=0, fill=1)
        txt(c, x, y - 3.4, lab, 9.5, 'SansB', DEEP if isroot else (BLUE if isblue else INK), 'c')
        txt(c, x, y0 + 8, name_of(sc, p), 7.5, 'SansB' if isroot else 'Sans',
            DEEP if isroot else MUTED, 'c')
        if fing:
            txt(c, x, y0 - 5 * lg - 13, str(fing[(s, fr)]), 8, 'Sans', MUTED, 'c')
    txt(c, x0 + w + 4, y0 + 8, 'note', 7, 'Sans', MUTED)
    if fing: txt(c, x0 + w + 4, y0 - 5 * lg - 13, 'finger', 7, 'Sans', MUTED)

def ordinal_oct(i):
    return ['low', '1 octave up', '2 octaves up', '3 octaves up'][i]

# ---------------------------------------------------------------- pages
def page_way(c, sc, wy, pg, total_ways):
    notes = wy['notes']
    frs = [n[1] for n in notes]
    lo, hi = min(frs), max(frs)
    if wy['kind'] == 'box':
        name = f"Way {wy['n']} · Position {wy['n']}"
        sub = f"Frets {lo}–{hi} · Put your 1st finger at fret {wy['hand']}"
    elif wy['kind'] == '3nps':
        name = 'Way 6 · Three notes on every string'
        sub = f'Frets {lo}–{hi} · Starts on low A (6th string, fret 5) · Smooth and fast for runs'
    else:
        name = 'Way 6 · Across the neck (diagonal)'
        sub = f'Frets {lo}–{hi} · Climb the whole neck: slide your hand up as you change strings'
    header(c, f"{sc['title']} — {name}", sub, pg)
    # diagram
    f_lo, f_hi = max(1, lo - 1), hi + 1
    if f_hi - f_lo < 6: f_hi = f_lo + 6
    if wy['kind'] == 'diag': f_lo, f_hi = 0, hi + 1
    dx, dy, dw, dh = 60, H - 262, 520, 150
    fretboard(c, sc, notes, dx, dy, dw, dh, f_lo, f_hi)
    # side panel
    px, py, pw = 610, H - 96, 200
    c.setFillColor(white); c.setStrokeColor(LINE); c.setLineWidth(1)
    c.roundRect(px - 12, 296, pw + 24, H - 86 - 296, 8, stroke=1, fill=1)
    txt(c, px, py - 6, 'Octave reference', 11.5, 'SansB', DEEP)
    roots = sorted([n for n in notes if (n[2] - ROOT) % 12 == 0], key=lambda n: n[2])
    y = py - 24
    base_oct = (roots[0][2] - 45) // 12 if roots else 0
    for r in roots:
        o = (r[2] - 45) // 12
        c.setFillColor(ORANGE); c.circle(px + 6, y + 3.5, 6, stroke=0, fill=1)
        txt(c, px + 6, y + 0.6, 'A', 7, 'SansB', INK, 'c')
        txt(c, px + 18, y, f"{SNAME[r[0]].split(' ')[0]} string, fret {r[1]}", 9.5, 'SansB')
        txt(c, px + 18, y - 11.5, ['low A', 'A · 1 octave up', 'A · 2 octaves up', 'A · 3 octaves up'][o],
            8.5, 'Sans', MUTED)
        y -= 27
    c.setStrokeColor(ORANGE); c.setLineWidth(2); c.setDash(4, 3)
    c.line(px, y + 6, px + 22, y + 6); c.setDash()
    txt(c, px + 28, y + 2.5, 'joins each A to the A an octave up', 8.5, 'Sans', MUTED)
    y -= 22
    txt(c, px, y, 'Notes in this scale', 10, 'SansB', DEEP); y -= 16
    n = len(sc['names']); cell = min(28, pw / n)
    for i, (nm, dg) in enumerate(zip(sc['names'], sc['degs'])):
        xx = px + i * cell + cell / 2
        isb = 'blue' in sc and sc['ints'][i] == sc['blue']
        txt(c, xx, y, nm, 10, 'SansB', DEEP if i == 0 else (BLUE if isb else INK), 'c')
        txt(c, xx, y - 12, dg, 8.5, 'Sans', MUTED, 'c')
    # tabs: up then down
    up = sorted(notes, key=lambda n: n[2])
    down = list(reversed(up))[1:]
    tw = W - 120
    tab(c, sc, up, wy['fing'], 40, 240, tw, 'Play up  (low to high)')
    tab(c, sc, down, wy['fing'], 40, 130, tw, 'Play down  (high to low)')
    # tip line
    tips = {
        'box': 'Say the note names as you play. Start and finish on an orange A. Use a metronome at 60, then speed up.',
        '3nps': 'Three notes on each string. Pick down-up-down evenly; this is the shape for fast runs.',
        'diag': 'Shift up with your 1st or 3rd finger when you move to the next string. Great for solos across the neck.',
    }
    txt(c, 40, 36, 'Tip: ' + tips[wy['kind']], 9, 'Sans', MUTED)

def page_scale_intro(c, sc, ws, pg):
    header(c, sc['title'], f"Six ways to play it · {sc['about']}", pg)
    allnotes = []
    P = pcs(sc)
    for s in range(6):
        for fr in range(0, 18):
            p = OPEN[s] + fr
            if p % 12 in P: allnotes.append((s, fr, p))
    br = []
    for w_ in ws[:5]:
        frs = [n[1] for n in w_['notes']]
        br.append((min(frs), max(frs), f"Position {w_['n']}"))
    fretboard(c, sc, allnotes, 60, H - 330, W - 110, 190, 0, 17, octave_lines=False, brackets=br)
    y = 150
    txt(c, 40, y, 'The whole neck', 13, 'SansB', DEEP)
    y = wrap(c, 40, y - 18, 'Every dot above is a note of the scale. Orange dots are A, the home note. '
             'The five positions sit side by side and overlap, so you can move from one to the next. '
             'Way 6 joins them in one long shape.', 360, 10)
    txt(c, 440, 150, 'How to use these pages', 13, 'SansB', DEEP)
    yy = 132
    for line in [f"1.  {sc['use']}",
                 '2.  Learn one position a week. Play it up and down, slowly, saying the note names.',
                 '3.  Find the orange A notes first: they are your map.',
                 '4.  Then join two positions together on the neck.']:
        yy = wrap(c, 440, yy, line, 360, 10) - 2
    notes_line = '   '.join(f"{n} ({d})" for n, d in zip(sc['names'], sc['degs']))
    txt(c, 40, 36, 'Notes: ' + notes_line, 10, 'SansB', INK)

def page_cover(c):
    c.setFillColor(white); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.rect(0, 0, 26, H, stroke=0, fill=1)
    c.setFillColor(SOFT); c.rect(26, 0, 8, H, stroke=0, fill=1)
    c.drawImage(LOGO, W - 250, H - 260, 190, 190, mask='auto', preserveAspectRatio=True)
    txt(c, 80, H - 140, 'Guitar Scales', 46, 'SansB')
    txt(c, 80, H - 190, '6 Ways to Play Every Scale', 26, 'SansB', DEEP)
    y = H - 240
    for l in ['Fretboard pictures, tabs, fingers and octave', 'markers for every way, for class and stage.']:
        txt(c, 80, y, l, 14, 'Sans', MUTED); y -= 20
    # contents
    y = 250
    txt(c, 80, y, 'Inside', 13, 'SansB', DEEP); y -= 22
    items = ['How to read this book', 'Finding the octaves', 'A Major Scale', 'A Natural Minor Scale',
             'A Major Pentatonic', 'A Minor Pentatonic', 'A Blues Scale', 'Play in any key']
    for i, it in enumerate(items):
        col = 80 + (i // 4) * 260; yy = y - (i % 4) * 22
        c.setFillColor(ORANGE); c.circle(col + 5, yy + 4, 4, stroke=0, fill=1)
        txt(c, col + 18, yy, it, 12)
    txt(c, 80, 60, 'Barney Musicals · Shine Worshippers Academy', 11, 'SansB', INK)

def page_howto(c, pg):
    header(c, 'How to read this book', 'Every scale page has a fretboard picture, a tab to play up, and a tab to play down', pg)
    sc = SCALES[3]
    ws = ways(sc)
    fretboard(c, sc, ws[1]['notes'], 60, H - 290, 380, 150, 4, 9)
    x = 490; y = H - 110
    items = [
        ('The picture', 'The neck is drawn as you see it when you look down at your guitar: the thin 1st string (e) is on top, the thick 6th string (E) is at the bottom. This matches the tab.'),
        ('The dots', 'Each dot is a note to play. The letter inside is the note name.'),
        ('Orange dots', 'The home note (A). Start and finish here.'),
        ('Dashed lines', 'Join an A to the next A, one octave higher.'),
        ('Blue dots', 'Only in the blues scale: the “blue note” E♭.'),
    ]
    for t, d in items:
        txt(c, x, y, t, 11.5, 'SansB', DEEP); y = wrap(c, x, y - 15, d, 310, 10) - 6
    # tab explanation
    tab(c, sc, sorted(ws[1]['notes'], key=lambda n: n[2]), ws[1]['fing'], 40, 175, 440, 'Reading the tab')
    y = 196
    for t, d in [('Tab lines', 'Six lines = six strings, high e on top. The number tells you which fret to press.'),
                 ('Note row', 'Above the tab: the name of each note. Sing or say it while you play.'),
                 ('Finger row', 'Below the tab: 1 = index, 2 = middle, 3 = ring, 4 = little finger.')]:
        txt(c, 560, y, t, 11.5, 'SansB', DEEP); y = wrap(c, 560, y - 15, d, 250, 10) - 6
    txt(c, 40, 36, 'Tip for class or stage: open this book full screen and use one page per way. Every page stands on its own.', 9, 'Sans', MUTED)

def page_octaves(c, pg):
    header(c, 'Finding the octaves', 'Know where every A is, and you can never get lost on the neck', pg)
    sc = dict(SCALES[0]); sc = dict(sc, ints=[0], names=['A'], degs=['1'])
    allA = [(s, fr, OPEN[s] + fr) for s in range(6) for fr in range(0, 18) if (OPEN[s] + fr) % 12 == ROOT]
    fx, sy = fretboard(c, sc, allA, 60, H - 300, W - 110, 160, 0, 17, octave_lines=True,
                       pairs=[((0, 5), (2, 7)), ((2, 7), (4, 10)), ((1, 12), (3, 14)), ((3, 2), (5, 5)), ((1, 0), (3, 2)), ((0, 17), (2, 19 - 12 + 12))][:5])
    y = 200
    txt(c, 40, y, 'Octave shapes (each one goes up one octave)', 13, 'SansB', DEEP); y -= 22
    rules = [
        ('6th string → 4th string', 'skip one string, go up 2 frets', 'fret 5 → fret 7'),
        ('5th string → 3rd string', 'skip one string, go up 2 frets', 'fret 12 → fret 14'),
        ('4th string → 2nd string', 'skip one string, go up 3 frets', 'fret 7 → fret 10'),
        ('3rd string → 1st string', 'skip one string, go up 3 frets', 'fret 2 → fret 5'),
        ('6th string → 1st string', 'same fret, two octaves higher', 'fret 5 → fret 5'),
        ('Same string', 'go up 12 frets', 'fret 5 → fret 17'),
    ]
    for i, (a, b, e) in enumerate(rules):
        col = 40 + (i // 3) * 390; yy = y - (i % 3) * 34
        txt(c, col, yy, a, 11, 'SansB')
        txt(c, col, yy - 14, f'{b}   (A: {e})', 10, 'Sans', MUTED)
    txt(c, 40, 36, 'Why +3 frets on the 2nd string? The B string is tuned one fret lower than the others, so shapes that cross it move up one fret.', 9, 'Sans', MUTED)

def page_keys(c, pg):
    header(c, 'Play in any key', 'Every shape in this book moves. Slide the whole shape so the orange dot lands on your new home note.', pg)
    keys = [('E', 0, 12), ('F', 1, 13), ('F♯ / G♭', 2, 14), ('G', 3, 15), ('G♯ / A♭', 4, 16), ('A', 5, 17),
            ('A♯ / B♭', 6, 18), ('B', 7, 19), ('C', 8, 20), ('C♯ / D♭', 9, 21), ('D', 10, 22), ('D♯ / E♭', 11, 23)]
    x0, y0 = 60, H - 120
    txt(c, x0, y0, 'Key', 11, 'SansB', DEEP)
    txt(c, x0 + 140, y0, 'Home note on 6th string', 11, 'SansB', DEEP)
    txt(c, x0 + 340, y0, 'Move every number by', 11, 'SansB', DEEP)
    y = y0 - 24
    for k, f, _ in keys:
        if k == 'A':
            c.setFillColor(SOFT); c.rect(x0 - 8, y - 6, 500, 20, stroke=0, fill=1)
        txt(c, x0, y, k, 11, 'SansB')
        txt(c, x0 + 140, y, f'fret {f}' if f else 'open (or fret 12)', 11)
        d = f - 5
        txt(c, x0 + 340, y, ('same as the book' if d == 0 else f'{d:+d} frets'), 11, 'Sans', MUTED if d == 0 else INK)
        y -= 22
    x = 600; y = H - 120
    txt(c, x, y, 'Example: G major', 12, 'SansB', DEEP)
    y = wrap(c, x, y - 18, 'G is 2 frets lower than A. Take any A major page and play every fret number 2 lower. '
             'Position 2 (frets 4–7) becomes frets 2–5.', 200, 10)
    y -= 10
    txt(c, x, y, 'Minor key? Same rule.', 12, 'SansB', DEEP)
    y = wrap(c, x, y - 18, 'For E minor, E is 5 frets lower than A (or 7 frets higher). Move the A minor shapes.', 200, 10)
    y -= 10
    txt(c, x, y, 'Remember', 12, 'SansB', DEEP)
    wrap(c, x, y - 18, 'If a number goes below 0, add 12. If it goes above 17, take away 12.', 200, 10)

def build(out):
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle('Guitar Scales: 6 Ways to Play Every Scale'); c.setAuthor('Barney Musicals · Shine Worshippers Academy')
    page_cover(c); c.showPage()
    pg = 2
    page_howto(c, pg); c.showPage(); pg += 1
    page_octaves(c, pg); c.showPage(); pg += 1
    for sc in SCALES:
        ws = ways(sc)
        page_scale_intro(c, sc, ws, pg); c.showPage(); pg += 1
        for wy in ws:
            page_way(c, sc, wy, pg, len(ws)); c.showPage(); pg += 1
    page_keys(c, pg); c.showPage()
    c.save()
    return pg

if __name__ == '__main__':
    print('pages', build(sys.argv[1]))
