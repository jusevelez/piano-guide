"""Lee una captura de Synthesia y devuelve las notas resaltadas.

Uso: python3 read_synthesia.py imagen.png [--hand-color morado]
"""
import sys
import numpy as np
from PIL import Image

WHITE_CYCLE = "CDEFGAB"
HAS_SHARP   = {"C":1,"D":1,"E":0,"F":1,"G":1,"A":1,"B":0}

def load(path):
    return np.array(Image.open(path).convert('RGB')).astype(int)

def keyboard_rows(a):
    """Devuelve (y en zona solo-blancas, y en zona con negras)."""
    lum = a.mean(axis=2)
    bright = (lum > 200).mean(axis=1)
    ys = [y for y in range(a.shape[0]) if bright[y] > 0.22]
    top, bottom = min(ys), max(ys)
    # dentro del teclado, las negras acaban donde la fila pasa a ser casi toda blanca
    split = bottom
    for y in range(top, bottom + 1):
        if bright[y] > 0.60:
            split = y
            break
    y_black = int(top + (split - top) * 0.6)
    y_white = int(split + (bottom - split) * 0.6)
    return y_white, y_black

def white_grid(a, y):
    lum = a[y].mean(axis=1)
    cuts, s = [], None
    for i, v in enumerate(lum < 180):
        if v and s is None: s = i
        elif not v and s is not None: cuts.append((s + i - 1) / 2); s = None
    cuts = np.array(cuts)
    step = float(np.median(np.diff(cuts)))
    idx = np.round((cuts - cuts[0]) / step)
    A = np.vstack([idx, np.ones_like(idx)]).T
    slope, intercept = np.linalg.lstsq(A, cuts, rcond=None)[0]
    n = int(round((cuts[-1] - intercept) / slope))
    return [(intercept + slope * k, intercept + slope * (k + 1)) for k in range(n)], slope

def classify(px):
    r, g, b = px
    if r > 150 and r - g > 55 and b - g > 40: return 'hl'      # morado
    if r > 150 and r - g > 55 and r - b > 55: return 'red'     # otra mano
    if min(px) > 190: return 'white'
    if max(px) < 95: return 'black'
    return '?'

def read(path):
    a = load(path)
    yw, yb = keyboard_rows(a)
    grid, step = white_grid(a, yw)

    whites = []
    for x0, x1 in grid:
        c = int((x0 + x1) / 2)
        band = a[yw, max(0, c - 5):c + 6]
        kinds = [classify(p) for p in band]
        whites.append(('hl' if kinds.count('hl') > 3 else
                       'red' if kinds.count('red') > 3 else 'white', c))

    # negras: entre cada par de blancas, mirar arriba
    blacks = []
    for i in range(len(grid) - 1):
        c = int(grid[i][1])
        band = a[yb, max(0, c - 4):c + 5]
        kinds = [classify(p) for p in band]
        present = kinds.count('black') + kinds.count('hl') + kinds.count('red') > 4
        state = ('hl' if kinds.count('hl') > 3 else
                 'red' if kinds.count('red') > 3 else 'black')
        blacks.append((present, state, c))

    # alinear el patrón de negras (2-3) con el ciclo C D E F G A B
    pattern = [1 if p else 0 for p, _, _ in blacks] + [0]
    best, score = 0, -1
    for off in range(7):
        s = sum(1 for i, v in enumerate(pattern[:-1])
                if HAS_SHARP[WHITE_CYCLE[(i + off) % 7]] == v)
        if s > score: best, score = off, s
    names = [WHITE_CYCLE[(i + best) % 7] for i in range(len(grid))]
    return names, whites, blacks, score, len(grid)

if __name__ == '__main__':
    names, whites, blacks, score, n = read(sys.argv[1])
    print(f'teclas blancas: {n} · patrón de negras acertado en {score}/{n-1}')
    out = []
    for i, (state, c) in enumerate(whites):
        if state == 'hl': out.append((c, names[i]))
        elif state == 'red': out.append((c, names[i] + ' (roja)'))
    for present, state, c in blacks:
        if not present: continue
        i = next(j for j in range(len(names)) if abs((whites[j][1]) - c) < 40 and whites[j][1] < c)
        if state == 'hl': out.append((c, names[i] + '#'))
        elif state == 'red': out.append((c, names[i] + '# (roja)'))
    out.sort()
    print('notas resaltadas, de grave a agudo:')
    for c, n_ in out: print(f'  x={c:5d}  {n_}')
