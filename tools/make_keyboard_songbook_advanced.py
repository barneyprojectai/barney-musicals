"""Keyboard Songbook, Grade 1: Advanced Chords.

The 15 Grade 1 songs (melodies and fingers from tools/keyboard_songs_grade1.json, the same notes the
website's song player uses) in the usual playing octave, with the simple chords made richer:
maj7, add9, 6, 7sus4, slash chords, relative-minor and ii substitutions, the gospel "I7 to IV" and minor iv.
A chord is only changed when it does not clash with the tune (no chord note a half step from a melody note).

Usage: python3 tools/make_keyboard_songbook_advanced.py books/keyboard-songbook-advanced.pdf logo.png
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_guitar_scales_book as mb
from make_guitar_scales_book import W, H, INK, MUTED, DEEP, ORANGE, SOFT, LINE, PAPER, BLUE, white, txt, wrap, header
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor

LHC = HexColor('#CFE0F5'); LHB = HexColor('#7FA7D9')
SONGS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keyboard_songs_grade1.json')))
NAMES = {'C': ['C', 'C♯', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'A♭', 'A', 'B♭', 'B'],
         'G': ['C', 'C♯', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'B♭', 'B']}
KEYPC = {'C': 0, 'G': 7}
WHITE = {0, 2, 4, 5, 7, 9, 11}
BASIC = {'C': 0, 'D': 2, 'F': 5, 'G': 7}
# chord qualities: intervals from the root
Q = {'': [0, 4, 7], 'maj7': [0, 4, 7, 11], 'add9': [0, 2, 4, 7], '6': [0, 4, 7, 9], '7': [0, 4, 7, 10],
     'm7': [0, 3, 7, 10], '7sus4': [0, 5, 7, 10]}
ABOUT = [('maj7', 'Major 7th', 'Add the note a half step below the root. Soft and warm: used for the home chord and chord IV.'),
         ('add9', 'Add 9', 'Add the 2nd (the 9th) to the chord. Bright and open: very common in worship songs.'),
         ('6', 'Sixth', 'Add the 6th. A sweet, finished sound: good for the last chord of a song.'),
         ('m7', 'Minor 7th (substitute)', 'The chord on the 6th note (Am7 in C) can take the place of the home chord. The chord on the 2nd note (Dm7 in C) can take the place of chord IV, best just before chord V.'),
         ('7', 'Dominant 7th', 'Chord V with a 7th pulls home. The home chord with a 7th (C7 in C) pulls to chord IV: the gospel move.'),
         ('7sus4', '7 sus 4', 'Chord V with the 4th in place of the 3rd, then back to V7: a stronger ending.'),
         ('slash', 'Slash chord', 'G/B means a G chord with B as the lowest note. The bass walks C – B – C instead of jumping.')]

def pcname(pc, k): return NAMES[k][pc % 12]

def chord_name(root, q, k, bass=None):
    return pcname(root, k) + q + ('/' + pcname(bass, k) if bass is not None else '')

def clashes(root, q, mel):
    tones = {(root + i) % 12 for i in Q[q]}
    if q == 'maj7' and any(m % 12 == root % 12 for m in mel): return True   # root in the tune rubs against the 7th
    return any(m % 12 not in tones and any((m - t) % 12 in (1, 11) for t in tones) for m in mel)

# ---------------------------------------------------------------- reharmonising
def events(song):
    """Every chord of the song in order, with the tune notes it sits under."""
    ev = []
    for pi, p in enumerate(song['parts']):
        for li, L in enumerate(p['lines']):
            for gi, g in enumerate(L):
                chs = g['chord'].split('>')
                mel = [m for m in g['notes'] if m]
                for ci, ch in enumerate(chs):
                    ev.append(dict(key=(pi, li, gi, ci), basic=ch, mel=mel, n=len(mel), two=len(chs) > 1,
                                   end=gi == len(L) - 1 and ci == len(chs) - 1))
    ev[-1]['last'] = True
    return ev

def advance(song):
    """{chord key: [(root, quality, bass)]}: usually one chord, two for a 7sus4 → 7 ending."""
    t = KEYPC[song['k']]; ev = events(song); out = {}
    deg = lambda e: (BASIC[e['basic'][0]] - t) % 12
    for i, e in enumerate(ev):
        d = deg(e); root = BASIC[e['basic'][0]]
        prev = ev[i - 1] if i else None; nxt = ev[i + 1] if i + 1 < len(ev) else None
        pd = deg(prev) if prev else None; nd = deg(nxt) if nxt else None
        same_prev = prev is not None and prev['basic'] == e['basic'] and not prev.get('subbed')
        c = []
        if d == 0:
            if e.get('last'): c = [(root, '6', None), (root, 'add9', None)]
            elif same_prev and nd not in (None, 0): c = [((t + 9) % 12, 'm7', None)]
            elif nd == 5 and not e['end']: c = [(root, '7', None)]
            c += [(root, 'maj7', None), (root, 'add9', None), (root, '6', None)]
        elif d == 5:
            if nd == 7 or (same_prev and nd != 5): c = [((t + 2) % 12, 'm7', None)]   # ii7 before V, or for a repeated IV
            c += [(root, 'maj7', None), (root, 'add9', None), (root, '6', None)]
        elif d == 7:
            if pd == 0 and nd == 0 and not e['end'] and not e['two']: c = [(root, '7' if e['basic'].endswith('7') else '', (root + 4) % 12)]
            if nd == 0 and e['end'] and e['n'] >= 2 and not e['two'] \
                    and not clashes(root, '7sus4', e['mel'][:-1]) and not clashes(root, '7', e['mel'][-1:]):
                out[e['key']] = [(root, '7sus4', None), (root, '7', None)]; continue
            c += [(root, '7', None)]
        elif d == 2:
            c = [(root, '7', None)]
        c.append((root, '7' if e['basic'].endswith('7') else '', None))
        pick = next((x for x in c if not clashes(x[0], x[1], e['mel'])), c[-1])   # the Grade 1 chord if all clash
        if pick[0] != root: e['subbed'] = True
        out[e['key']] = [pick]
    return out

# ---------------------------------------------------------------- left-hand voicings
def voicings(root, q, bass, lo, hi):
    pcs = [(root + i) % 12 for i in Q[q]]
    out = []
    for r in range(len(pcs)):
        rot = pcs[r:] + pcs[:r]
        if bass is not None and rot[0] != bass % 12: continue
        for o in range(2, 6):
            ns = [12 * o + rot[0]]
            for pc in rot[1:]:
                n = ns[-1] + 1
                while n % 12 != pc: n += 1
                ns.append(n)
            if lo <= ns[0] and ns[-1] <= hi: out.append(ns)
    return out

def lh_fingers(ns):
    a = ns[1] - ns[0]
    if len(ns) == 3: return '5 4 1' if a <= 2 else ('5 3 1' if a <= 4 else '5 2 1')
    return '5 4 2 1' if a <= 2 else '5 3 2 1'

def lh_plan(song, adv):
    """Left-hand keys for every chord: the inversion nearest the chord before, below the tune of that line."""
    prev, out = None, {}
    for pi, p in enumerate(song['parts']):
        for li, L in enumerate(p['lines']):
            top = min(min(m for g in L for m in g['notes'] if m) - 1, 59)
            for gi, g in enumerate(L):
                for ci in range(len(g['chord'].split('>'))):
                    vs = []
                    for root, q, bass in adv[(pi, li, gi, ci)]:
                        ref = prev or [top - 10, top - 7, top - 4, top - 1]
                        ns = min(voicings(root, q, bass, 40, top),
                                 key=lambda v: (sum(abs(a - b) for a, b in zip(v, ref)) + 3 * abs(len(v) - len(ref)), -v[0]))
                        vs.append(ns); prev = ns
                    out[(pi, li, gi, ci)] = vs
    return out

# ---------------------------------------------------------------- drawing
def keyboard(c, x0, y0, w, h, lo, hi, marks):
    whites = [m for m in range(lo, hi + 1) if m % 12 in WHITE]
    kw = w / len(whites); xs = {}
    for i, m in enumerate(whites):
        xs[m] = x0 + i * kw
        c.setFillColor(marks.get(m, white)); c.setStrokeColor(MUTED); c.setLineWidth(0.6)
        c.rect(x0 + i * kw, y0 - h, kw, h, stroke=1, fill=1)
    for m in range(lo, hi + 1):
        if m % 12 in WHITE or m - 1 not in xs: continue
        bx = xs[m - 1] + kw * .68; bw = kw * .64
        col = marks.get(m, INK)
        col = LHB if col is LHC else col
        c.setFillColor(col); c.setStrokeColor(INK); c.setLineWidth(0.6)
        c.rect(bx, y0 - h * .62, bw, h * .62, stroke=1, fill=1)

def mini(c, x, y, name, ns, w=92):
    """A chord picture: the name, a small keyboard (lowest key orange), the keys and fingers."""
    lo = ns[0] - (ns[0] % 12) if ns[0] % 12 < 5 else ns[0] - ((ns[0] - 5) % 12)
    hi = lo + 16
    while hi < ns[-1] + 1: hi += 1
    while hi % 12 not in (4, 11): hi += 1
    marks = {n: (ORANGE if i == 0 else LHC) for i, n in enumerate(ns)}
    txt(c, x, y + 4, name, 10, 'SansB', DEEP)
    keyboard(c, x, y - 2, w, 30, lo, hi, marks)
    txt(c, x, y - 44, ' '.join(NAMES['C'][n % 12] for n in ns) + '   (' + lh_fingers(ns) + ')', 7.5, 'Sans', MUTED)

STEP = 30
def items_of(song, adv, lh):
    lines = []
    for pi, p in enumerate(song['parts']):
        for li, L in enumerate(p['lines']):
            items = []
            for gi, g in enumerate(L):
                chs = g['chord'].split('>')
                names, keys, fgs = [], [], []
                for ci in range(len(chs)):
                    for (root, q, bass), ns in zip(adv[(pi, li, gi, ci)], lh[(pi, li, gi, ci)]):
                        names.append(chord_name(root, q, song['k'], bass))
                        keys.append(' '.join(NAMES['C'][n % 12] for n in ns)); fgs.append(lh_fingers(ns))
                basic = ' → '.join(chs); adv_s = ' → '.join(names)
                key_s = '  |  '.join(keys); fg_s = '  |  '.join(fgs)
                wneed = max(len(g['notes']) * STEP, pdfmetrics.stringWidth(adv_s, 'SansB', 10.5) + 10,
                            pdfmetrics.stringWidth(key_s, 'Sans', 8) + 10, pdfmetrics.stringWidth(g['words'], 'Sans', 9.5) + 8)
                items.append(dict(g=g, basic=basic, adv=adv_s, keys=key_s, fg=fg_s, w=wneed, changed=adv_s != basic))
            lines.append((p['label'] if li == 0 else '', items))
    return lines

def rows(lines, width):
    """Pack the song's lines into rows that fit the page width (a bar line between song lines)."""
    out, cur, wsum, lab = [], [], 0, ''
    for label, items in lines:
        lw = sum(it['w'] for it in items) + 16
        if cur and (label or wsum + lw > width):
            out.append((lab, cur)); cur, wsum = [], 0
        if not cur: lab = label
        else: cur.append(dict(bar=True, w=16)); wsum += 16
        for it in items:
            if cur and not cur[-1].get('bar') and wsum + it['w'] > width:
                out.append((lab, cur)); lab, cur, wsum = '', [], 0
            cur.append(it); wsum += it['w']
    if cur: out.append((lab, cur))
    return out

ROW_H = 104
def draw_row(c, song, row, y):
    label, items = row
    keypc = KEYPC[song['k']]
    x = 44
    if label: txt(c, 40, y + 16, label, 9.5, 'SansB', DEEP)
    for it in items:
        if it.get('bar'):
            c.setStrokeColor(MUTED); c.setLineWidth(1); c.line(x + 4, y + 10, x + 4, y - 88); x += it['w']; continue
        g = it['g']
        txt(c, x, y, it['adv'], 10.5, 'SansB', DEEP)
        txt(c, x, y - 11, ('was ' + it['basic']) if it['changed'] else 'same', 7.5, 'Sans', MUTED)
        txt(c, x, y - 24, it['keys'], 8, 'Sans', BLUE)
        txt(c, x, y - 34, it['fg'], 7.5, 'Sans', MUTED)
        nx = x + STEP / 2 - 4
        for m, f in zip(g['notes'], g['fingers']):
            if m is None:
                txt(c, nx, y - 56, '–', 11, 'Sans', MUTED, 'c'); nx += STEP; continue
            root = (m - keypc) % 12 == 0
            if root:
                c.setFillColor(SOFT); c.roundRect(nx - 12, y - 61, 24, 17, 4, stroke=0, fill=1)
            txt(c, nx, y - 56, NAMES[song['k']][m % 12], 10.5, 'SansB', DEEP if root else INK, 'c')
            txt(c, nx, y - 71, str(f) if f else '·', 8.5, 'Sans', MUTED, 'c')
            nx += STEP
        txt(c, x, y - 86, g['words'], 9.5, 'Sans', INK)
        x += it['w']
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(40, y - 93, W - 40, y - 93)

def song_chords(song, adv, lh):
    seen = {}
    for k in sorted(adv):
        for (root, q, bass), ns in zip(adv[k], lh[k]):
            seen.setdefault(chord_name(root, q, song['k'], bass), ns)
    return seen

PER_ROW = 7
def chord_strip(c, seen, y):
    txt(c, 40, y, 'Chords in this song (left hand; orange = lowest key)', 10, 'SansB', INK)
    x, yy = 40, y - 20
    for i, (name, ns) in enumerate(seen.items()):
        if i and i % PER_ROW == 0: x, yy = 40, yy - 68
        mini(c, x, yy, name, ns); x += 108
    return yy - 62

def page_cover(c):
    c.setFillColor(white); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.rect(0, 0, 26, H, stroke=0, fill=1)
    c.setFillColor(SOFT); c.rect(26, 0, 8, H, stroke=0, fill=1)
    c.drawImage(mb.LOGO, W - 200, H - 170, 140, 140, mask='auto', preserveAspectRatio=True)
    txt(c, 80, H - 230, 'Keyboard Songbook, Grade 1', 40, 'SansB')
    txt(c, 80, H - 275, 'Advanced Chords', 28, 'SansB', DEEP)
    y = H - 320
    for l in ['The same 15 songs and the same tune, with richer chords:',
              'major 7ths, add 9, sixths, 7 sus 4, slash chords and chord substitutions.']:
        txt(c, 80, y, l, 14, 'Sans', MUTED); y -= 20
    x = 80
    for name, ns in [('Cmaj7', [48, 52, 55, 59]), ('Am7', [45, 48, 52, 55]), ('Fadd9', [53, 55, 57, 60]),
                     ('G7sus4', [43, 48, 50, 53]), ('G/B', [47, 50, 55])]:
        mini(c, x, 170, name, ns, 110); x += 135
    txt(c, 80, 60, 'Barney Musicals · Shine Worshippers Academy', 11, 'SansB', INK)

def page_intro(c, pg):
    header(c, 'How to use this book', 'Same songs, same tune, same right hand: only the chords are new', pg)
    y = H - 106
    for t, d in [('The tune', 'The right hand plays the tune in the usual place on the keyboard, with the same notes and fingers as the '
                  'Grade 1 songbook. Learn the song from that book first.'),
                 ('The chords', 'Above every group of notes is the new, richer chord in orange, and under it the simple chord it replaces '
                  '(“was C”). The left hand plays the keys written in blue, from the lowest key up, with the fingers shown under them '
                  '(5 = little finger, 1 = thumb). Hold the chord until the next one. A chord is only changed where it sounds good with the tune.'),
                 ('Smooth chords', 'The left hand uses inversions: the chord keys are moved so the hand stays in one place and only a '
                  'finger or two moves to the next chord. The keyboard pictures at the top of each song show every chord shape it uses; '
                  'the orange key is the lowest note.'),
                 ('The new chords', 'Page 3 explains each kind of chord: major 7th, add 9, sixth, minor 7th substitutes, 7th chords, '
                  '7 sus 4 and slash chords.'),
                 ('Practise', 'Play the left hand alone first, saying the chord names. Then play hands together slowly. '
                  'When it is easy, go back to the Grade 1 chords and hear the difference.')]:
        txt(c, 40, y, t, 12, 'SansB', DEEP); y = wrap(c, 40, y - 16, d, W - 90, 10.5) - 8

def page_kinds(c, pg):
    header(c, 'The new chords', 'Every kind of chord used in this book, shown in the key of C', pg)
    ex = {'maj7': ('Cmaj7', [48, 52, 55, 59]), 'add9': ('Cadd9', [48, 50, 52, 55]), '6': ('C6', [48, 52, 55, 57]),
          'm7': ('Am7', [45, 48, 52, 55]), '7': ('C7', [48, 52, 55, 58]), '7sus4': ('G7sus4', [43, 48, 50, 53]),
          'slash': ('G/B', [47, 50, 55])}
    for i, (k, t, d) in enumerate(ABOUT):
        x = 40 + (i % 2) * 390; y = H - 118 - (i // 2) * 112
        name, ns = ex[k]
        mini(c, x, y, name, ns, 110)
        txt(c, x + 130, y + 4, t, 11.5, 'SansB', DEEP)
        wrap(c, x + 130, y - 12, d, 235, 9.5)

def page_contents(c, pg, index):
    header(c, 'Contents', 'On screen, use the bookmarks to jump to a song.', pg)
    y = H - 108
    for i, s in enumerate(SONGS):
        txt(c, 60, y, f"{i + 1}.  {s['t']}", 11.5, 'Sans')
        txt(c, 400, y, f"Key of {s['k']}", 10, 'Sans', MUTED)
        txt(c, 560, y, str(index[i]), 11.5, 'SansB', INK, 'r'); y -= 22

def layout(song):
    adv = advance(song); lh = lh_plan(song, adv); seen = song_chords(song, adv, lh)
    rs = rows(items_of(song, adv, lh), W - 90)
    pages, cur, y = [], [], H - 100 - (82 + 68 * ((len(seen) - 1) // PER_ROW)) - 4
    for r in rs:
        need = ROW_H + (16 if r[0] else 0)
        if cur and y - need < 20:
            pages.append(cur); cur, y = [], H - 100
        cur.append(r); y -= need
    pages.append(cur)
    return adv, lh, seen, pages

def build(out):
    plan = [layout(s) for s in SONGS]
    index, pg = {}, 5
    for i, p in enumerate(plan):
        index[i] = pg; pg += len(p[3])
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle('Keyboard Songbook, Grade 1: Advanced Chords'); c.setAuthor('Barney Musicals · Shine Worshippers Academy')
    page_cover(c); c.showPage()
    page_intro(c, 2); c.showPage()
    page_kinds(c, 3); c.showPage()
    page_contents(c, 4, index); c.showPage()
    pg = 5
    for si, (adv, lh, seen, pages) in enumerate(plan):
        s = SONGS[si]
        c.bookmarkPage(f's{si}'); c.addOutlineEntry(s['t'], f's{si}', 0)
        for part, rws in enumerate(pages):
            more = f'  (page {part + 1} of {len(pages)})' if len(pages) > 1 else ''
            header(c, f"{s['t']}{more}", f"Key of {s['k']} · Advanced chords · Right hand as in the Grade 1 songbook", pg)
            y = H - 100
            if part == 0: y = chord_strip(c, seen, y) - 4
            for r in rws:
                if r[0]: y -= 16
                draw_row(c, s, r, y); y -= ROW_H
            c.showPage(); pg += 1
    c.save()
    return pg - 1

if __name__ == '__main__':
    print('pages', build(sys.argv[1]))
