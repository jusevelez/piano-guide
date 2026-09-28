"""Lee capturas o vídeos de Synthesia y devuelve las teclas encendidas.

  python3 tools-read-synthesia.py imagen.png
  python3 tools-read-synthesia.py video.mp4 [--fps 15] [--desde 0] [--hasta 60]

Cómo funciona: mide el teclado en la imagen, reconstruye la rejilla de teclas
blancas y alinea el patrón de teclas negras (grupos de 2 y 3) para saber qué
letra es cada tecla. Los píxeles se clasifican por tono (HSV), así que sirve
con los distintos temas de Synthesia.
"""
import sys
import numpy as np
from PIL import Image

WHITE_CYCLE = "CDEFGAB"
HAS_SHARP = {"C": 1, "D": 1, "E": 0, "F": 1, "G": 1, "A": 1, "B": 0}


# --------------------------------------------------------------- color

def classify(px):
    r, g, b = [c / 255.0 for c in px]
    mx, mn = max(r, g, b), min(r, g, b)
    v, d = mx, mx - mn
    s = 0 if mx == 0 else d / mx
    if d == 0:      h = 0
    elif mx == r:   h = (60 * ((g - b) / d)) % 360
    elif mx == g:   h = 60 * ((b - r) / d) + 120
    else:           h = 60 * ((r - g) / d) + 240
    if s < 0.18:                  return 'white' if v > 0.65 else 'black'
    if v < 0.40:                  return 'black'
    if 250 <= h <= 340:           return 'hl'      # morado: la mano que seguimos
    if h <= 25 or h >= 345:       return 'red'     # rojo: la otra mano
    return '?'


def kind_at(a, y, x, half=4):
    band = a[y, max(0, x - half):x + half + 1]
    kinds = [classify(p) for p in band]
    for k in ('hl', 'red'):
        if kinds.count(k) > half: return k
    return max(set(kinds), key=kinds.count)


# ------------------------------------------------------------ geometría

def keyboard_rows(a):
    """(y en la zona de solo blancas, y en la zona con negras)."""
    lum = a.mean(axis=2)
    bright = (lum > 180).mean(axis=1)
    ys = [y for y in range(a.shape[0]) if bright[y] > 0.22]
    top, bottom = min(ys), max(ys)
    split = bottom
    for y in range(top, bottom + 1):
        if bright[y] > 0.60:
            split = y
            break
    return int(split + (bottom - split) * 0.6), int(top + (split - top) * 0.6)


def white_grid(a, y):
    """Bordes de cada tecla blanca, ajustando una rejilla regular."""
    lum = a[y].mean(axis=1)
    cuts, s = [], None
    for i, v in enumerate(lum < 180):
        if v and s is None: s = i
        elif not v and s is not None:
            cuts.append((s + i - 1) / 2); s = None
    cuts = np.array(cuts)
    step = float(np.median(np.diff(cuts)))
    idx = np.round((cuts - cuts[0]) / step)
    A = np.vstack([idx, np.ones_like(idx)]).T
    slope, intercept = np.linalg.lstsq(A, cuts, rcond=None)[0]
    n = int(round((cuts[-1] - intercept) / slope))
    return [(intercept + slope * k, intercept + slope * (k + 1)) for k in range(n)]


def layout(a):
    """Geometría fija del vídeo/captura: rejilla, filas y nombre de cada tecla."""
    y_white, y_black = keyboard_rows(a)
    grid = white_grid(a, y_white)

    # el patrón de negras solo se usa para alinear, y solo con huecos fiables
    seen = []
    for i in range(len(grid) - 1):
        seen.append(kind_at(a, y_black, int(grid[i][1])))
    best, score, total = 0, -1, 0
    for off in range(7):
        ok = n = 0
        for i, k in enumerate(seen):
            if k in ('hl', 'red', '?'): continue   # tapado por una nota encendida
            n += 1
            if HAS_SHARP[WHITE_CYCLE[(i + off) % 7]] == (1 if k == 'black' else 0):
                ok += 1
        if ok > score: best, score, total = off, ok, n
    names = [WHITE_CYCLE[(i + best) % 7] for i in range(len(grid))]
    return dict(grid=grid, names=names, semis=semitones(names),
                y_white=y_white, y_black=y_black, score=score, total=total)


# --------------------------------------------------------------- lectura

SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def semitones(names):
    """Altura de cada tecla blanca en semitonos, contando desde la primera."""
    out, oct_ = [], 0
    for i, n in enumerate(names):
        if i and n == "C": oct_ += 1
        out.append(SEMI[n] + 12 * oct_)
    return out


def lit_keys(a, lay):
    """Teclas encendidas en este fotograma: [(altura, nombre, color)]."""
    grid, names, semis = lay['grid'], lay['names'], lay['semis']
    out = []
    for i, (x0, x1) in enumerate(grid):
        k = kind_at(a, lay['y_white'], int((x0 + x1) / 2), 6)
        if k in ('hl', 'red'):
            out.append((semis[i], names[i], k))
        # la negra a la derecha, solo donde el teclado realmente tiene una
        if i < len(grid) - 1 and HAS_SHARP[names[i]]:
            kb = kind_at(a, lay['y_black'], int(x1))
            if kb in ('hl', 'red'):
                out.append((semis[i] + 1, names[i] + '#', kb))
    out.sort()
    return out


# ----------------------------------------------------------------- vídeo

def frames(path, fps, start, end):
    import subprocess, imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, '-hide_banner', '-loglevel', 'error']
    if start: cmd += ['-ss', str(start)]
    if end:   cmd += ['-to', str(end)]
    cmd += ['-i', path, '-vf', f'fps={fps}', '-f', 'rawvideo',
            '-pix_fmt', 'rgb24', '-']
    meta = subprocess.run([exe, '-hide_banner', '-i', path],
                          capture_output=True, text=True).stderr
    dim = next(t for t in meta.split(',') if 'x' in t and t.strip()[0].isdigit())
    w, h = [int(v) for v in dim.strip().split(' ')[0].split('x')]
    size = w * h * 3
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=size * 2)
    i = 0
    while True:
        buf = p.stdout.read(size)
        if len(buf) < size: break
        yield (start or 0) + i / fps, np.frombuffer(buf, np.uint8).reshape(h, w, 3).astype(int)
        i += 1
    p.stdout.close(); p.wait()


def read_video(path, fps, start, end):
    """Devuelve [(t, conjunto de teclas encendidas)] fotograma a fotograma."""
    lay, out = None, []
    for t, frame in frames(path, fps, start, end):
        if lay is None:
            lay = layout(frame)
            print(f"teclado: {len(lay['grid'])} blancas · patrón alineado "
                  f"{lay['score']}/{lay['total']}", file=sys.stderr)
        out.append((round(t, 3), frozenset(lit_keys(frame, lay))))
    return out


def onsets(timeline):
    ev, prev = [], frozenset()
    for t, now in timeline:
        for semi, name, color in sorted(now - prev):
            ev.append((t, semi, name, color))
        prev = now
    return ev


# ---------------------------------------------------------- acordes

TRIADS = [(0, 4, 7, ''), (0, 3, 7, 'm'), (0, 3, 6, 'dim'), (0, 4, 8, 'aug')]


def name_chord(semis, names):
    """Nombre del acorde a partir de las alturas (con bajo invertido si toca)."""
    pcs = sorted({s % 12 for s in semis})
    bass = names[0].rstrip('#') + ('#' if names[0].endswith('#') else '')
    for root in pcs:
        rel = tuple(sorted((p - root) % 12 for p in pcs))
        for a, b, c, suf in TRIADS:
            if rel == (a, b, c):
                rname = next(n for s, n in zip(semis, names) if s % 12 == root)
                return rname + suf + ('' if root == semis[0] % 12 else '/' + bass)
    if len(pcs) == 2: return '+'.join(dict.fromkeys(names))
    return ' '.join(dict.fromkeys(names))


def chords(timeline, minimo=0.25, hand='hl'):
    """Tramos en los que suena un mismo grupo de teclas, ya estabilizado.

    Se queda con lo que de verdad se sostiene: los estados de paso de un
    acorde arpegiado duran poco y se descartan."""
    segs = []
    for t, now in timeline:
        keys = frozenset((s, n) for s, n, c in now if c == hand)
        if segs and segs[-1][1] == keys: segs[-1][2] = t
        else: segs.append([t, keys, t])

    dur = lambda s: s[2] - s[0]
    keep = [s for s in segs if s[1] and dur(s) >= minimo]

    out = []
    for t0, keys, t1 in keep:
        if out and out[-1][3] == keys:           # mismo acorde que sigue sonando
            out[-1] = (out[-1][0], round(t1 - out[-1][0], 2), out[-1][2], keys)
            continue
        notes = sorted(keys)
        out.append((t0, round(t1 - t0, 2),
                    name_chord([x for x, _ in notes], [n for _, n in notes]), keys))
    return [(t, d, n, sorted(k)) for t, d, n, k in out]


# ------------------------------------------------------------------ cli

if __name__ == '__main__':
    path = sys.argv[1]
    arg = lambda f, d: float(sys.argv[sys.argv.index(f) + 1]) if f in sys.argv else d

    if path.lower().endswith(('.mp4', '.mov', '.mkv', '.webm')):
        ev = read_video(path, arg('--fps', 15), arg('--desde', 0), arg('--hasta', 0) or None)
        if '--acordes' in sys.argv:
            for t, d, name, notes in chords(ev, arg('--minimo', 0.25)):
                bajo = notes[0][1]
                arriba = ' '.join(n for _, n in notes[1:])
                print(f'{t:8.2f}s ({d:4.1f}s)  {name:8s}  bajo {bajo:3s}  arriba {arriba}')
        else:
            for t, semi, name, color in onsets(ev):
                print(f'{t:8.2f}s  {name:3s}  {"" if color == "hl" else "(otra mano)"}')
    else:
        a = np.array(Image.open(path).convert('RGB')).astype(int)
        lay = layout(a)
        print(f"teclas blancas: {len(lay['grid'])} · patrón alineado "
              f"{lay['score']}/{lay['total']}")
        for name, color in lit_keys(a, lay):
            print(f'  {name:3s}  {"" if color == "hl" else "(otra mano)"}')
