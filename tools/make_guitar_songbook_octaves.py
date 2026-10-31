"""Guitar Songbook, Grade 1: every song in every octave and position.

Each of the 15 songs (melodies from tools/guitar_songs_grade1.json, the same notes the website's song player
uses) is moved up the neck one octave at a time, as far as a 22-fret guitar allows, and each octave is
shown in up to 4 hand positions, with tab, note names, fingers, chords and words.

Usage: python3 tools/make_guitar_songbook_octaves.py books/guitar-songbook-octaves-positions.pdf logo.png
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_guitar_scales_book as mb
from make_guitar_scales_book import W, H, OPEN, INK, MUTED, DEEP, ORANGE, SOFT, LINE, FRET, PAPER, white, txt, wrap, header
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics

SONGS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'guitar_songs_grade1.json')))
NAMES = {'C': ['C', 'C♯', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'A♭', 'A', 'B♭', 'B'],
         'G': ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']}
KEYPC = {'C': 0, 'G': 7}
TOP = OPEN[5] + 22                     # highest note on a 22-fret guitar
OCT_WORDS = ['1st octave (lowest)', '2nd octave', '3rd octave', '4th octave (highest)']

def melody(song): return [m for p in song['parts'] for L in p['lines'] for g in L for m in g['notes'] if m]

def octave_shifts(song):
    ms = melody(song)
    return [12 * k for k in range(-4, 4) if min(ms) + 12 * k >= OPEN[0] and max(ms) + 12 * k <= TOP]

def place(ms, f):
    """Put every note in the hand position whose 1st finger is at fret f (f = 0: open position, frets 0-4).
    Each note goes on the string where its fret is nearest the middle of the hand; None if a note does not fit."""
    lo, hi = (0, 4) if f == 0 else (f, f + 4)
    mid = 1.5 if f == 0 else f + 1.5
    out = {}
    for m in set(ms):
        c = [(abs((m - OPEN[s]) - mid), s, m - OPEN[s]) for s in range(6)
             if lo <= m - OPEN[s] <= hi or (f <= 1 and m - OPEN[s] == 0)]
        if not c: return None
        out[m] = min(c)[1:]
    return out

def positions(ms, most=4):
    picks, last, prev = [], -9, None
    for f in range(0, 19):
        p = place(ms, f)
        if p and f >= last + 4 and p != prev:
            picks.append((f, p)); last, prev = f, p
    return picks[:most]

def finger(fr, f):
    if fr == 0: return 0
    return max(1, min(4, fr - (f if f else 1) + 1))

# ---------------------------------------------------------------- drawing
def systems(song):
    """Pack the song's lines into tab systems of at most 22 notes, keeping each line whole."""
    out, cur, n = [], [], 0
    for p in song['parts']:
        for i, L in enumerate(p['lines']):
            cnt = sum(len(g['notes']) for g in L)
            label = p['label'] if i == 0 and p['label'] else ''
            if cur and (n + cnt > 22 or label):
                out.append(cur); cur, n = [], 0
            cur.append((label, L)); n += cnt
    if cur: out.append(cur)
    return out

def draw_system(c, song, sysl, shift, pos, f, y0, x0=40, w=W - 80):
    lg = 11
    keypc = KEYPC[song['k']]
    names = NAMES[song['k']]
    total = sum(len(g['notes']) for _, L in sysl for g in L)
    step = min(34, (w - 30) / max(total, 1))
    for i in range(6):
        c.setStrokeColor(FRET); c.setLineWidth(0.7)
        c.line(x0 + 14, y0 - i * lg, x0 + w, y0 - i * lg)
        txt(c, x0 + 5, y0 - i * lg - 3, 'eBGDAE'[i], 8, 'SansB', MUTED, 'c')
    c.setStrokeColor(INK); c.setLineWidth(1.1)
    c.line(x0 + 14, y0, x0 + 14, y0 - 5 * lg); c.line(x0 + w, y0, x0 + w, y0 - 5 * lg)
    x = x0 + 14 + step * 0.7
    for li, (label, L) in enumerate(sysl):
        if label: txt(c, x - step * 0.4, y0 + 30, label, 8.5, 'SansB', DEEP)
        if li:
            c.setStrokeColor(INK); c.setLineWidth(1.1); xb = x - step * 0.5
            c.line(xb, y0, xb, y0 - 5 * lg)
        for g in L:
            gx0 = x
            txt(c, x - 3, y0 + 21, g['chord'].replace('>', ' → '), 9.5, 'SansB', DEEP)
            for m in g['notes']:
                if m is None:
                    txt(c, x, y0 - 2.5 * lg - 3, '–', 9, 'Sans', MUTED, 'c'); x += step; continue
                m += shift; s, fr = pos[m]
                y = y0 - (5 - s) * lg
                root = (m - keypc) % 12 == 0
                lab = str(fr); tw = pdfmetrics.stringWidth(lab, 'SansB', 10.5) + 3
                c.setFillColor(PAPER); c.rect(x - tw / 2, y - 5, tw, 10, stroke=0, fill=1)
                txt(c, x, y - 3.7, lab, 10.5, 'SansB', DEEP if root else INK, 'c')
                txt(c, x, y0 + 7, names[m % 12], 8.5, 'SansB' if root else 'Sans', DEEP if root else MUTED, 'c')
                txt(c, x, y0 - 5 * lg - 12, str(finger(fr, f)), 8, 'Sans', MUTED, 'c')
                x += step
            if g['words']:
                txt(c, gx0 - 3, y0 - 5 * lg - 26, g['words'], 9.5, 'Sans', INK)
        x += step * 0.4
    return y0 - 5 * lg - 26

def page_cover(c):
    c.setFillColor(white); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(ORANGE); c.rect(0, 0, 26, H, stroke=0, fill=1)
    c.setFillColor(SOFT); c.rect(26, 0, 8, H, stroke=0, fill=1)
    c.drawImage(mb.LOGO, W - 250, H - 260, 190, 190, mask='auto', preserveAspectRatio=True)
    txt(c, 80, H - 140, 'Guitar Songbook, Grade 1', 40, 'SansB')
    txt(c, 80, H - 185, 'Every Octave and Position', 28, 'SansB', DEEP)
    y = H - 235
    for l in ['The 15 Grade 1 songs, moved up the neck one octave at a time,',
              'each octave in several hand positions, with tab, fingers, chords and words.']:
        txt(c, 80, y, l, 14, 'Sans', MUTED); y -= 20
    txt(c, 80, 60, 'Barney Musicals · Shine Worshippers Academy', 11, 'SansB', INK)

def page_intro(c, pg):
    header(c, 'How to use this book', 'Same song, same notes: higher or lower on the neck, and in different hand positions', pg)
    y = H - 110
    for t, d in [('Octaves', 'Each song is played in every octave that fits on a guitar, from the lowest to the highest. '
                  'A guitar with 22 frets covers just under 4 octaves, so a song can be played in 4 octaves only when its tune is small '
                  '(Mary Had a Little Lamb and God is so Good). Most songs fit 3 octaves; Bits of Paper, with the widest tune, fits 2.'),
                 ('Positions', 'In each octave the song is shown in up to 4 hand positions. Put your 1st finger on the fret named at the top of the page; '
                  'the other fingers cover the next frets (finger 1 on that fret, 2 on the next, and so on). The same notes then sound the same, '
                  'but feel different under your hand. Open position uses open strings near the nut.'),
                 ('The tab', 'Six lines are the six strings, high e on top. The number is the fret, 0 = open string. Above the tab: the chord to strum '
                  'and the note names. Below: the finger (0 = open, 1 = index, 2 = middle, 3 = ring, 4 = little) and the words.'),
                 ('Orange notes', 'The home note of the song’s key (C or G) is orange, so you can always see where the tune comes home.'),
                 ('Practise', 'Learn the song in the lowest octave first. Then play the same song an octave higher, then in another position. '
                  'Say or sing the note names as you play.')]:
        txt(c, 40, y, t, 12, 'SansB', DEEP); y = wrap(c, 40, y - 16, d, W - 90, 10.5) - 8

def page_contents(c, pg, index):
    header(c, 'Contents', 'Every song starts on the page shown. On screen, use the bookmarks to jump to a song and octave.', pg)
    y = H - 110
    for i, s in enumerate(SONGS):
        txt(c, 60, y, f"{i + 1}.  {s['t']}", 11.5, 'Sans')
        txt(c, 420, y, f"{len(octave_shifts(s))} octaves", 10.5, 'Sans', MUTED)
        txt(c, 560, y, str(index[i]), 11.5, 'SansB', INK, 'r'); y -= 22

def plan():
    """[(song index, octave number, shift, position number, f, placement, page count)] in book order."""
    out = []
    for si, s in enumerate(SONGS):
        ms = melody(s); n = len(systems(s))
        for oi, sh in enumerate(octave_shifts(s)):
            for pi, (f, pos) in enumerate(positions([m + sh for m in ms])):
                out.append((si, oi, sh, pi, f, pos, -(-n // 3)))
    return out

def build(out):
    P = plan()
    index, pg = {}, 4
    for si, oi, sh, pi, f, pos, npg in P:
        index.setdefault(si, pg); pg += npg
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle('Guitar Songbook, Grade 1: Every Octave and Position'); c.setAuthor('Barney Musicals · Shine Worshippers Academy')
    page_cover(c); c.showPage()
    page_intro(c, 2); c.showPage()
    page_contents(c, 3, index); c.showPage()
    pg = 4
    for si, oi, sh, pi, f, pos, npg in P:
        s = SONGS[si]; ms = [m + sh for m in melody(s)]
        if pi == 0 and oi == 0:
            c.bookmarkPage(f's{si}'); c.addOutlineEntry(s['t'], f's{si}', 0)
        if pi == 0:
            c.bookmarkPage(f's{si}o{oi}'); c.addOutlineEntry(OCT_WORDS[oi] if len(octave_shifts(s)) == 4 else f'Octave {oi + 1}', f's{si}o{oi}', 1)
        frs = [fr for _, fr in pos.values()]
        hand = 'Open position (near the nut)' if f == 0 else f'1st finger at fret {f}'
        sy = systems(s)
        for part in range(npg):
            more = f'  (page {part + 1} of {npg})' if npg > 1 else ''
            header(c, f"{s['t']} — Octave {oi + 1} · Position {pi + 1}{more}",
                   f"Key of {s['k']} · Frets {min(frs)}–{max(frs)} · {hand} · Octave {oi + 1} of {len(octave_shifts(s))}", pg)
            y = H - 130
            for sysl in sy[part * 3:(part + 1) * 3]:
                y = draw_system(c, s, sysl, sh, pos, f, y) - 72
            c.showPage(); pg += 1
    c.save()
    return pg - 1

if __name__ == '__main__':
    print('pages', build(sys.argv[1]))
