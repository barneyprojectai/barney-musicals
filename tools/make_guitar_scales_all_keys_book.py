"""Guitar Scales in Every Key: all 12 major and 12 minor scales, each in 1, 2, 3 and 4 octaves
and in 7 positions (three notes per string), with fretboard pictures, tabs and octave markers.

Usage: python3 tools/make_guitar_scales_all_keys_book.py books/guitar-scales-every-key.pdf logo.png
Reuses the drawing helpers from make_guitar_scales_book.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_guitar_scales_book as mb
from make_guitar_scales_book import (W, H, OPEN, SNAME, INK, MUTED, DEEP, ORANGE, SOFT, LINE, white,
                                     txt, wrap, header, fretboard, tab, finger_box, finger_3nps, next_in)
from reportlab.pdfgen import canvas

LET = 'CDEFGAB'; LETPC = [0, 2, 4, 5, 7, 9, 11]
MAJ = [0, 2, 4, 5, 7, 9, 11]; MIN = [0, 2, 3, 5, 7, 8, 10]
KEYS = {'major': ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'],
        'minor': ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']}

def pc_of(k):
    p = LETPC[LET.index(k[0])]
    for ch in k[1:]: p += 1 if ch == '#' else -1
    return p % 12

def pretty(n): return n[0] + n[1:].replace('#', '♯').replace('b', '♭')

def spell(k, ints):
    li, r = LET.index(k[0]), pc_of(k)
    out = []
    for i, iv in enumerate(ints):
        L = LET[(li + i) % 7]; d = ((r + iv) - LETPC[LET.index(L)]) % 12
        if d > 6: d -= 12
        out.append(L + ('#' * d if d > 0 else 'b' * -d))
    return [pretty(n) for n in out]

def make_sc(kind, k):
    ints = MAJ if kind == 'major' else MIN
    degs = ['1', '2', '3', '4', '5', '6', '7'] if kind == 'major' else ['1', '2', '♭3', '4', '5', '♭6', '♭7']
    return dict(kind=kind, key=k, pc=pc_of(k), ints=ints, names=spell(k, ints), degs=degs,
                title=f"{pretty(k)} {'Major' if kind == 'major' else 'Minor'}")

# ---------------------------------------------------------------- the 11 ways (same as the website tool)
def one_octave(pc, ints):
    fE, fA = (pc - 4) % 12, (pc - 9) % 12
    onE = fE <= fA + 1 and fE <= 7
    rs, rf = (0, fE) if onE else (1, fA)
    lo, hi, s = max(0, rf - 1), max(0, rf - 1) + 4, rs
    out = []
    for iv in ints + [12]:
        m = OPEN[rs] + rf + iv
        for x in range(s, 6):
            f = m - OPEN[x]
            if lo <= f <= hi: s = x; break
        out.append((s, m - OPEN[s], m))
    return out

def nps3(P, start, count=18):
    out, p = [], start
    for s in range(6):
        for _ in range(3):
            out.append((s, p - OPEN[s], p)); p = next_in(p, P)
    return out[:count]

def long_run(P, start, top):
    ms, p = [], start
    while p % 12 not in P: p += 1
    while p <= top: ms.append(p); p = next_in(p, P)
    out, i = [], 0
    for s in range(6):
        for _ in range(len(ms) // 6 + (1 if s < len(ms) % 6 else 0)):
            out.append((s, ms[i] - OPEN[s], ms[i])); i += 1
    return out

def fingers(notes):
    """Fingers for 3-per-string shapes; an open string is finger 0 and the fretted notes on that string are fingered on their own."""
    fing, by = {}, {}
    for n in notes: by.setdefault(n[0], []).append(n[1])
    for s, frs in by.items():
        pressed = [f for f in frs if f > 0]
        for f, x in zip(pressed, mb.string_fingers(pressed) if pressed else []): fing[(s, f)] = x
        if 0 in frs: fing[(s, 0)] = 0
    return fing

def ways(sc):
    pc, P = sc['pc'], [(sc['pc'] + i) % 12 for i in sc['ints']]
    r = (pc - 4) % 12
    res = []
    n = one_octave(pc, sc['ints'])
    res.append(dict(name='1 octave', sub='One octave in one hand position, near the nut', notes=n, fing={k: (0 if k[1] == 0 else v) for k, v in finger_box(n)[0].items()}, long=False))
    n = nps3(P, OPEN[0] + r, 15)
    res.append(dict(name='2 octaves', sub='Three notes on each of the five lowest strings, from the home note on the 6th string', notes=n, fing=fingers(n), long=False))
    n = long_run(P, OPEN[0] + r, OPEN[0] + r + 36)
    res.append(dict(name='3 octaves', sub='From the lowest home note up three octaves: slide your hand up the neck as you change strings', notes=n, fing=None, long=True))
    n = long_run(P, OPEN[0], OPEN[5] + 22)
    res.append(dict(name='4 octaves (whole neck)', sub='Every note of the scale from the lowest note up to fret 22: as close to 4 octaves as a guitar allows', notes=n, fing=None, long=True))
    for i, iv in enumerate(sc['ints']):
        f = (r + iv) % 12
        n = nps3(P, OPEN[0] + f)
        res.append(dict(name=f"Position {i + 1}", sub=f"Three notes on every string, starting on {sc['names'][i]} (6th string, fret {f})",
                        notes=n, fing=fingers(n), long=False))
    return res

# ---------------------------------------------------------------- pages
OCT_WORDS = ['lowest {k}', '{k} · 1 octave up', '{k} · 2 octaves up', '{k} · 3 octaves up', '{k} · 4 octaves up']

def roots_of(sc, notes):
    return sorted([n for n in notes if (n[2] - sc['pc']) % 12 == 0], key=lambda n: n[2])

def page_way(c, sc, wy, num, pg):
    mb.ROOT = sc['pc']
    notes = wy['notes']; frs = [n[1] for n in notes]; lo, hi = min(frs), max(frs)
    k = sc['names'][0]; base = OPEN[0] + (sc['pc'] - 4) % 12
    header(c, f"{sc['title']} — Way {num} · {wy['name']}", f"Frets {lo}–{hi} · {wy['sub']}", pg)
    roots = roots_of(sc, notes)
    if wy['long']:
        fretboard(c, sc, notes, 60, H - 262, W - 110, 150, 0, max(hi + 1, 12))
        y = 286
        txt(c, 40, y, 'Octave reference:', 10, 'SansB', DEEP)
        x = 150
        for rt in roots:
            s = f"{SNAME[rt[0]].split(' ')[0]} string fret {rt[1]} ({OCT_WORDS[(rt[2] - base) // 12].format(k=k)})"
            c.setFillColor(ORANGE); c.circle(x + 4, y + 3.5, 4, stroke=0, fill=1)
            txt(c, x + 11, y, s, 8.6, 'Sans', INK); x += 22 + mb.pdfmetrics.stringWidth(s, 'Sans', 8.6)
    else:
        f_lo, f_hi = max(1, lo - 1), hi + 1
        if f_hi - f_lo < 6: f_hi = f_lo + 6
        fretboard(c, sc, notes, 60, H - 262, 520, 150, f_lo, f_hi)
        px, py, pw = 610, H - 96, 200
        c.setFillColor(white); c.setStrokeColor(LINE); c.setLineWidth(1)
        c.roundRect(px - 12, 296, pw + 24, H - 86 - 296, 8, stroke=1, fill=1)
        txt(c, px, py - 6, 'Octave reference', 11.5, 'SansB', DEEP)
        y = py - 24
        for rt in roots:
            c.setFillColor(ORANGE); c.circle(px + 6, y + 3.5, 6, stroke=0, fill=1)
            txt(c, px + 18, y, f"{SNAME[rt[0]].split(' ')[0]} string, fret {rt[1]}", 9.5, 'SansB')
            txt(c, px + 18, y - 11.5, OCT_WORDS[(rt[2] - base) // 12].format(k=k), 8.5, 'Sans', MUTED)
            y -= 27
        c.setStrokeColor(ORANGE); c.setLineWidth(2); c.setDash(4, 3); c.line(px, y + 6, px + 22, y + 6); c.setDash()
        txt(c, px + 28, y + 2.5, f'joins each {k} to the {k} an octave up', 8.5, 'Sans', MUTED)
        y -= 22
        txt(c, px, y, 'Notes in this scale', 10, 'SansB', DEEP); y -= 16
        for i, (nm, dg) in enumerate(zip(sc['names'], sc['degs'])):
            xx = px + i * 28 + 14
            txt(c, xx, y, nm, 10, 'SansB', DEEP if i == 0 else INK, 'c')
            txt(c, xx, y - 12, dg, 8.5, 'Sans', MUTED, 'c')
    up = sorted(notes, key=lambda n: n[2]); down = list(reversed(up))[1:]
    tab(c, sc, up, wy['fing'], 40, 240, W - 120, 'Play up  (low to high)')
    tab(c, sc, down, wy['fing'], 40, 130, W - 120, 'Play down  (high to low)')
    txt(c, 40, 36, f"Tip: start and finish on an orange {k}. Say the note names as you play. Use a metronome at 60, then speed up.", 9, 'Sans', MUTED)

def page_cover(c):
    c.setFillColor(white); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.rect(0, 0, 26, H, stroke=0, fill=1)
    c.setFillColor(SOFT); c.rect(26, 0, 8, H, stroke=0, fill=1)
    c.drawImage(mb.LOGO, W - 250, H - 260, 190, 190, mask='auto', preserveAspectRatio=True)
    txt(c, 80, H - 140, 'Guitar Scales', 46, 'SansB')
    txt(c, 80, H - 190, 'in Every Key', 30, 'SansB', DEEP)
    y = H - 240
    for l in ['All 12 major and 12 minor scales.', 'Each one in 1, 2, 3 and 4 octaves and in 7 positions,',
              'with fretboard pictures, tabs, fingers and octave markers.']:
        txt(c, 80, y, l, 14, 'Sans', MUTED); y -= 20
    txt(c, 80, 60, 'Barney Musicals · Shine Worshippers Academy', 11, 'SansB', INK)

def page_intro(c, pg):
    header(c, 'How to use this book', 'Every key has 11 pages: the same 11 ways for every major and minor scale', pg)
    y = H - 110
    items = [('Ways 1 to 4: octaves', 'Way 1 is one octave in one hand position. Way 2 is two octaves, three notes on each of the five lowest strings. '
              'Way 3 climbs three octaves from the lowest home note. Way 4 uses the whole neck, from the lowest note up to fret 22: '
              'that is as close to 4 octaves as a guitar allows (a full 4 octaves needs a 24-fret guitar).'),
             ('Ways 5 to 11: the 7 positions', 'Three notes on every string. Position 1 starts on the home note on the 6th string, '
              'position 2 on the 2nd note of the scale, and so on up to position 7. Together they cover the whole neck.'),
             ('The picture', 'The neck as you see it looking down at your guitar: thin 1st string (e) on top, thick 6th string (E) at the bottom, the same as the tab. '
              'Each dot is a note to play, with its name inside.'),
             ('Orange dots and dashed lines', 'Orange dots are the home note of the key. The dashed line joins each home note to the one an octave higher.'),
             ('The tab', 'Six lines are the six strings. The number is the fret. Above the tab is the note name; below it, the finger '
              '(0 = open string, 1 = index, 2 = middle, 3 = ring, 4 = little). Long runs have no finger row: slide your hand up as you change strings.')]
    for t, d in items:
        txt(c, 40, y, t, 12, 'SansB', DEEP); y = wrap(c, 40, y - 16, d, W - 90, 10.5) - 8

def page_contents(c, pg, index):
    header(c, 'Contents', 'Every key starts on the page shown. On screen, use the bookmarks to jump to a key.', pg)
    for col, kind in enumerate(['major', 'minor']):
        x = 60 + col * 380; y = H - 110
        txt(c, x, y, 'Major scales' if kind == 'major' else 'Minor scales', 13, 'SansB', DEEP); y -= 24
        for k in KEYS[kind]:
            sc = make_sc(kind, k)
            txt(c, x, y, sc['title'], 11.5, 'Sans')
            txt(c, x + 260, y, str(index[(kind, k)]), 11.5, 'SansB', INK, 'r'); y -= 20.5

def build(out):
    pages_per_key = 11
    first = 4                                      # cover, how to use, contents, then the keys
    index, pg = {}, first
    for kind in ('major', 'minor'):
        for k in KEYS[kind]: index[(kind, k)] = pg; pg += pages_per_key
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle('Guitar Scales in Every Key'); c.setAuthor('Barney Musicals · Shine Worshippers Academy')
    page_cover(c); c.showPage()
    page_intro(c, 2); c.showPage()
    page_contents(c, 3, index); c.showPage()
    pg = first
    for kind in ('major', 'minor'):
        c.bookmarkPage(kind); c.addOutlineEntry('Major scales' if kind == 'major' else 'Minor scales', kind, 0)
        for k in KEYS[kind]:
            sc = make_sc(kind, k)
            for i, wy in enumerate(ways(sc)):
                if i == 0:
                    key = f'{kind}-{k}'; c.bookmarkPage(key); c.addOutlineEntry(sc['title'], key, 1)
                page_way(c, sc, wy, i + 1, pg); c.showPage(); pg += 1
    c.save()
    return pg - 1

if __name__ == '__main__':
    print('pages', build(sys.argv[1]))
