"""Keyboard Songbook, Grade 1: Advanced — every song in 4 octaves, with left-hand chords in inversions.

Each of the 15 songs (melodies and fingers from tools/keyboard_songs_grade1.json, the same notes the
website's song player uses) is played in 4 octaves on a 61-key keyboard (C2 to C7). The left hand plays
each chord in the inversion nearest the one before (smooth chords), placed below the right hand.

Usage: python3 tools/make_keyboard_songbook_advanced.py books/keyboard-songbook-advanced.pdf logo.png
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_guitar_scales_book as mb
from make_guitar_scales_book import W, H, INK, MUTED, DEEP, ORANGE, SOFT, LINE, PAPER, BLUE, white, txt, wrap, header
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor

LHC = HexColor('#CFE0F5')                 # light blue for left-hand keys
LHB = HexColor('#7FA7D9'); SOFTB = HexColor('#FFC48A')   # the same marks on black keys
SONGS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keyboard_songs_grade1.json')))
NAMES = {'C': ['C', 'C♯', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'A♭', 'A', 'B♭', 'B'],
         'G': ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']}
KEYPC = {'C': 0, 'G': 7}
LO, HI = 36, 96                           # 61-key keyboard: C2 .. C7
# chord tones (7th chords as 3 notes: root, 3rd, 7th, like the Grade 1 book)
CHORDS = {'C': [0, 4, 7], 'F': [5, 9, 0], 'G': [7, 11, 2], 'G7': [7, 11, 5], 'D': [2, 6, 9], 'D7': [2, 6, 0]}
INV = ['Root position', '1st inversion', '2nd inversion']
WHITE = {0, 2, 4, 5, 7, 9, 11}

def nm(m, k='C'): return f"{NAMES[k][m % 12]}{m // 12 - 1}"

def melody(song): return [m for p in song['parts'] for L in p['lines'] for g in L for m in g['notes'] if m]

def octave_shifts(song):
    """4 octaves that fit on the keyboard, as high as possible so the left hand has room below."""
    ms = melody(song)
    ok = [12 * k for k in range(-4, 4) if min(ms) + 12 * k >= LO and max(ms) + 12 * k <= HI]
    return ok[-4:]

def voicings(ch):
    """Every close-position voicing of the chord on the keyboard: (notes, inversion number)."""
    t = CHORDS[ch]; out = []
    for inv in range(3):
        rot = t[inv:] + t[:inv]
        for o in range(1, 9):
            ns = [12 * o + rot[0]]
            for pc in rot[1:]:
                n = ns[-1] + 1
                while n % 12 != pc: n += 1
                ns.append(n)
            if LO <= ns[0] and ns[-1] <= HI: out.append((ns, inv))
    return out

def lh_fingers(ns):
    if len(ns) == 1: return '5'
    a = ns[1] - ns[0]
    return '5 4 1' if a <= 2 else ('5 3 1' if a <= 4 else '5 2 1')

def lh_plan(song, shift):
    """Left-hand keys for each chord change: smooth inversions below the right hand of that line."""
    prev, out = None, {}
    for pi, p in enumerate(song['parts']):
        for li, L in enumerate(p['lines']):
            top = min(min(m for g in L for m in g['notes'] if m) + shift - 1, 59)
            last = None
            for gi, g in enumerate(L):
                for ci, ch in enumerate(g['chord'].split('>')):
                    if ch == last and ci == 0 and gi: continue
                    last = ch
                    cand = [v for v in voicings(ch) if v[0][-1] <= top]
                    if cand:
                        ref = prev or [top - 9, top - 5, top - 1]
                        ns, inv = min(cand, key=lambda v: (sum(abs(a - b) for a, b in zip(v[0], ref)), -v[0][0]))
                    else:                                  # no room for 3 keys: play the bass note only
                        r = CHORDS[ch][0]; n = LO + (r - LO) % 12
                        ns, inv = [n], -1
                    prev = ns if len(ns) == 3 else prev
                    out[(pi, li, gi, ci)] = (ns, inv)
    return out

# ---------------------------------------------------------------- drawing
def keyboard(c, x0, y0, w, h, lo, hi, marks, labels=True):
    """marks: {midi: (fill colour, text)}. Draws white then black keys; y0 is the top edge."""
    whites = [m for m in range(lo, hi + 1) if m % 12 in WHITE]
    kw = w / len(whites); xs = {}
    for i, m in enumerate(whites):
        xs[m] = x0 + i * kw
        col = marks.get(m, (white, ''))[0]
        c.setFillColor(col); c.setStrokeColor(MUTED); c.setLineWidth(0.6)
        c.rect(x0 + i * kw, y0 - h, kw, h, stroke=1, fill=1)
        if m in marks and marks[m][1]:
            txt(c, x0 + (i + .5) * kw, y0 - h + 5, marks[m][1], min(8, kw * .5), 'SansB', INK, 'c')
        if labels and m % 12 == 0:
            txt(c, x0 + (i + .5) * kw, y0 - h - 11, f'C{m // 12 - 1}', 7.5, 'SansB' if m == 60 else 'Sans',
                DEEP if m == 60 else MUTED, 'c')
    for m in range(lo, hi + 1):
        if m % 12 in WHITE: continue
        if m - 1 not in xs: continue
        bx = xs[m - 1] + kw * .68; bw = kw * .64
        col = marks.get(m, (INK, ''))[0]
        col = {id(LHC): LHB, id(SOFT): SOFTB}.get(id(col), col)
        c.setFillColor(col); c.setStrokeColor(INK); c.setLineWidth(0.6)
        c.rect(bx, y0 - h * .62, bw, h * .62, stroke=1, fill=1)
        if m in marks and marks[m][1]:
            txt(c, bx + bw / 2, y0 - h * .62 + 4, marks[m][1], min(6.5, kw * .42), 'SansB', INK, 'c')

def song_keyboard(c, song, shift, lh, y0):
    keypc = KEYPC[song['k']]; marks = {}
    for ns, inv in lh.values():
        for n in ns: marks[n] = (LHC, '')
    for m in set(melody(song)):
        m += shift; marks[m] = (ORANGE if (m - keypc) % 12 == 0 else SOFT, '')
    keyboard(c, 40, y0, W - 80, 52, LO, HI, marks)
    x = 40; y = y0 - 76
    for col, t in [(SOFT, 'Right hand (tune)'), (ORANGE, 'Home note of the key'), (LHC, 'Left hand (chords)')]:
        c.setFillColor(col); c.setStrokeColor(MUTED); c.rect(x, y - 1, 12, 9, stroke=1, fill=1)
        txt(c, x + 17, y, t, 9, 'Sans', INK); x += 160
    txt(c, W - 40, y, 'C4 = middle C', 9, 'SansB', DEEP, 'r')
    return y - 24

STEP = 34
def group_items(song, shift, lh):
    """Flatten the song into lines of drawable groups."""
    lines = []
    for pi, p in enumerate(song['parts']):
        for li, L in enumerate(p['lines']):
            items = []
            for gi, g in enumerate(L):
                chs = g['chord'].split('>')
                lhs = [lh.get((pi, li, gi, ci)) for ci in range(len(chs))]
                lab = '  '.join(' '.join(nm(n, song['k']) for n in v[0]) for v in lhs if v)
                fg = '  '.join(lh_fingers(v[0]) for v in lhs if v)
                wneed = max(len(g['notes']) * STEP, pdfmetrics.stringWidth(lab, 'Sans', 8) + 10,
                            pdfmetrics.stringWidth(g['words'], 'Sans', 9.5) + 8,
                            pdfmetrics.stringWidth(' → '.join(chs), 'SansB', 9.5) + 8)
                items.append(dict(g=g, chs=chs, lab=lab, fg=fg, w=wneed))
            lines.append((p['label'] if li == 0 else '', items))
    return lines

def rows(lines, width):
    """Pack the song's lines into rows that fit the page width; a line starts a new row only when it must."""
    out, cur, wsum, lab = [], [], 0, ''
    for label, items in lines:
        lw = sum(it['w'] for it in items) + 16
        if cur and (label or wsum + lw > width):
            out.append((lab, cur)); cur, wsum = [], 0
        if not cur: lab = label
        elif cur: cur.append(dict(bar=True, w=16)); wsum += 16
        for it in items:
            if cur and not cur[-1].get('bar') and wsum + it['w'] > width:
                out.append((lab, cur)); lab, cur, wsum = '', [], 0
            cur.append(it); wsum += it['w']
    if cur: out.append((lab, cur))
    return out

ROW_H = 92
KB_H = 100                                 # keyboard picture + key at the top of an octave
def draw_row(c, song, shift, row, y):
    label, items = row
    keypc = KEYPC[song['k']]
    x = 54
    if label: txt(c, 40, y + 15, label, 9.5, 'SansB', DEEP)
    for it in items:
        if it.get('bar'):
            c.setStrokeColor(MUTED); c.setLineWidth(1); c.line(x + 4, y + 8, x + 4, y - 78); x += it['w']; continue
        g = it['g']
        txt(c, x, y, ' → '.join(it['chs']), 10, 'SansB', DEEP)
        txt(c, x, y - 13, it['lab'], 8, 'Sans', BLUE)
        txt(c, x, y - 24, it['fg'], 7.5, 'Sans', MUTED)
        nx = x + STEP / 2 - 4
        for m, f in zip(g['notes'], g['fingers']):
            if m is None:
                txt(c, nx, y - 46, '–', 11, 'Sans', MUTED, 'c'); nx += STEP; continue
            m += shift; root = (m - keypc) % 12 == 0
            if root:
                c.setFillColor(SOFT); c.roundRect(nx - 15, y - 51, 30, 17, 4, stroke=0, fill=1)
            txt(c, nx, y - 46, nm(m, song['k']), 10.5, 'SansB', DEEP if root else INK, 'c')
            txt(c, nx, y - 61, str(f) if f else '·', 8.5, 'Sans', MUTED, 'c')
            nx += STEP
        txt(c, x, y - 77, g['words'], 9.5, 'Sans', INK)
        x += it['w']
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(40, y - 84, W - 40, y - 84)

def page_cover(c):
    c.setFillColor(white); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.rect(0, 0, 26, H, stroke=0, fill=1)
    c.setFillColor(SOFT); c.rect(26, 0, 8, H, stroke=0, fill=1)
    c.drawImage(mb.LOGO, W - 200, H - 170, 140, 140, mask='auto', preserveAspectRatio=True)
    txt(c, 80, H - 230, 'Keyboard Songbook, Grade 1', 40, 'SansB')
    txt(c, 80, H - 275, 'Advanced: 4 Octaves and Both Hands', 28, 'SansB', DEEP)
    y = H - 320
    for l in ['The 15 Grade 1 songs in 4 octaves across the keyboard,',
              'with the left hand playing smooth chords in inversions, note names, fingers and words.']:
        txt(c, 80, y, l, 14, 'Sans', MUTED); y -= 20
    keyboard(c, 80, 185, W - 160, 70, LO, HI, {60: (ORANGE, '')})
    txt(c, 80, 60, 'Barney Musicals · Shine Worshippers Academy', 11, 'SansB', INK)

def page_intro(c, pg):
    header(c, 'How to use this book', 'Same song, same fingers: low, middle and high on the keyboard, with both hands', pg)
    y = H - 108
    for t, d in [('4 octaves', 'Every song is written 4 times, from the lowest octave to the highest, on a 61-key keyboard (C2 to C7). '
                  'The fingers stay the same in every octave: only the place on the keyboard changes. A picture of the keyboard at the start '
                  'of each octave shows where both hands play.'),
                 ('Note names', 'Each note has its octave number: C4 is middle C, C5 is the next C up, C3 the next C down. '
                  'So G4 and G5 are the same note, one octave apart.'),
                 ('Left hand', 'The left hand plays the chord written above the notes, and holds it until the chord changes. '
                  'Instead of always playing the chord from its root, it uses the inversion nearest the chord before, so the hand hardly moves '
                  '(see the chord shapes on page 3). In the lowest octave there is no room under the tune, so the left hand plays just the '
                  'bass note (the name of the chord).'),
                 ('Fingers', 'Right hand: 1 = thumb, 2 = index, 3 = middle, 4 = ring, 5 = little finger. A dot means play with the finger '
                  'that feels natural. Left hand fingers are shown under the chord keys, from the lowest key to the highest.'),
                 ('Orange notes', 'The home note of the song’s key (C or G) is orange, so you can always see where the tune comes home.'),
                 ('Practise', 'Learn the song hands apart in the middle octave first. Then hands together, then move to the other octaves. '
                  'Say or sing the note names as you play.')]:
        txt(c, 40, y, t, 12, 'SansB', DEEP); y = wrap(c, 40, y - 16, d, W - 90, 10.5) - 7

def page_shapes(c, pg):
    header(c, 'Left-hand chord shapes', 'Every chord in this book in its 3 positions. Fingers from the lowest key: 5 = little finger, 1 = thumb', pg)
    y = H - 104
    for ch in ['C', 'F', 'G', 'G7', 'D', 'D7']:
        txt(c, 40, y - 24, ch, 18, 'SansB', DEEP)
        for inv in range(3):
            vs = [v for v, i in voicings(ch) if i == inv and 48 <= v[0] < 60]
            ns = vs[0]
            x = 110 + inv * 240
            marks = {n: (ORANGE if n % 12 == CHORDS[ch][0] else LHC, '') for n in ns}
            keyboard(c, x, y - 4, 200, 40, 48, 71, marks, labels=False)
            txt(c, x, y + 2, f"{INV[inv]}: {' '.join(nm(n) for n in ns)}   ({lh_fingers(ns)})", 8.5, 'Sans', INK)
        y -= 74
    txt(c, 40, y + 10, 'G7 and D7 use 3 keys (root, 3rd and 7th), the same as in the Grade 1 book. Orange = the chord’s name note.', 9, 'Sans', MUTED)

def page_contents(c, pg, index):
    header(c, 'Contents', 'Every song starts on the page shown. On screen, use the bookmarks to jump to a song and octave.', pg)
    y = H - 108
    for i, s in enumerate(SONGS):
        txt(c, 60, y, f"{i + 1}.  {s['t']}", 11.5, 'Sans')
        sh = octave_shifts(s); ms = melody(s)
        txt(c, 400, y, 'first note ' + ', '.join(nm(ms[0] + x, s['k']) for x in sh), 10, 'Sans', MUTED)
        txt(c, 640, y, str(index[i][0]), 11.5, 'SansB', INK, 'r'); y -= 22

def layout(song, shift):
    lh = lh_plan(song, shift)
    rs = rows(group_items(song, shift, lh), W - 100)
    pages, cur, y = [], [], H - 96 - KB_H
    for r in rs:
        need = ROW_H + (16 if r[0] else 0)
        if cur and y - need < 22:          # keep the words of the last row above the footer
            pages.append(cur); cur, y = [], H - 96
        cur.append(r); y -= need
    pages.append(cur)
    return lh, pages

def build(out):
    plan = []
    for si, s in enumerate(SONGS):
        for oi, sh in enumerate(octave_shifts(s)):
            lh, pages = layout(s, sh)
            plan.append((si, oi, sh, lh, pages))
    index, pg = {}, 5
    for si, oi, sh, lh, pages in plan:
        index.setdefault(si, []).append(pg); pg += len(pages)
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle('Keyboard Songbook, Grade 1: Advanced'); c.setAuthor('Barney Musicals · Shine Worshippers Academy')
    page_cover(c); c.showPage()
    page_intro(c, 2); c.showPage()
    page_shapes(c, 3); c.showPage()
    page_contents(c, 4, index); c.showPage()
    pg = 5
    for si, oi, sh, lh, pages in plan:
        s = SONGS[si]; ms = [m + sh for m in melody(s)]
        if oi == 0:
            c.bookmarkPage(f's{si}'); c.addOutlineEntry(s['t'], f's{si}', 0)
        c.bookmarkPage(f's{si}o{oi}'); c.addOutlineEntry(f'Octave {oi + 1}', f's{si}o{oi}', 1)
        low = ['lowest', 'low', 'high', 'highest'][oi]
        for part, rws in enumerate(pages):
            more = f'  (page {part + 1} of {len(pages)})' if len(pages) > 1 else ''
            header(c, f"{s['t']} — Octave {oi + 1} of 4{more}",
                   f"Key of {s['k']} · Right hand {nm(min(ms), s['k'])} to {nm(max(ms), s['k'])} ({low}) · First note {nm(ms[0], s['k'])}", pg)
            y = H - 96
            if part == 0: y = song_keyboard(c, s, sh, lh, y)
            for r in rws:
                if r[0]: y -= 16
                draw_row(c, s, sh, r, y); y -= ROW_H
            c.showPage(); pg += 1
    c.save()
    return pg - 1

if __name__ == '__main__':
    print('pages', build(sys.argv[1]))
