/* Datos y dibujo de acordes, compartidos por todas las páginas. */
window.Acordes = (function(){
// --- datos: nombre, notas en inglés, notas en español, semitonos desde Do ---
var MAJ = [
  ["C",  "Do mayor",       ["C","E","G"],     ["Do","Mi","Sol"],       0, ""],
  ["C#", "Do sostenido m.",["C#","E#","G#"],  ["Do#","Mi#","Sol#"],    1, "Casi siempre se escribe Db: Db – F – Ab (Reb – Fa – Lab)."],
  ["D",  "Re mayor",       ["D","F#","A"],    ["Re","Fa#","La"],       2, ""],
  ["Eb", "Mi bemol mayor", ["Eb","G","Bb"],   ["Mib","Sol","Sib"],     3, "También aparece como D#."],
  ["E",  "Mi mayor",       ["E","G#","B"],    ["Mi","Sol#","Si"],      4, ""],
  ["F",  "Fa mayor",       ["F","A","C"],     ["Fa","La","Do"],        5, ""],
  ["F#", "Fa sostenido m.",["F#","A#","C#"],  ["Fa#","La#","Do#"],     6, "Igual que Gb: Gb – Bb – Db."],
  ["G",  "Sol mayor",      ["G","B","D"],     ["Sol","Si","Re"],       7, ""],
  ["Ab", "La bemol mayor", ["Ab","C","Eb"],   ["Lab","Do","Mib"],      8, "También G#."],
  ["A",  "La mayor",       ["A","C#","E"],    ["La","Do#","Mi"],       9, ""],
  ["Bb", "Si bemol mayor", ["Bb","D","F"],    ["Sib","Re","Fa"],      10, "También A#."],
  ["B",  "Si mayor",       ["B","D#","F#"],   ["Si","Re#","Fa#"],     11, "También Cb."]
];
var MIN = [
  ["Cm",  "Do menor",            ["C","Eb","G"],   ["Do","Mib","Sol"],     0, ""],
  ["C#m", "Do sostenido menor",  ["C#","E","G#"],  ["Do#","Mi","Sol#"],    1, "Muy usado; su enarmónico Dbm es raro."],
  ["Dm",  "Re menor",            ["D","F","A"],    ["Re","Fa","La"],       2, ""],
  ["Ebm", "Mi bemol menor",      ["Eb","Gb","Bb"], ["Mib","Solb","Sib"],   3, "También D#m."],
  ["Em",  "Mi menor",            ["E","G","B"],    ["Mi","Sol","Si"],      4, ""],
  ["Fm",  "Fa menor",            ["F","Ab","C"],   ["Fa","Lab","Do"],      5, ""],
  ["F#m", "Fa sostenido menor",  ["F#","A","C#"],  ["Fa#","La","Do#"],     6, "También Gbm."],
  ["Gm",  "Sol menor",           ["G","Bb","D"],   ["Sol","Sib","Re"],     7, ""],
  ["G#m", "Sol sostenido menor", ["G#","B","D#"],  ["Sol#","Si","Re#"],    8, "También Abm."],
  ["Am",  "La menor",            ["A","C","E"],    ["La","Do","Mi"],       9, "Solo teclas blancas."],
  ["Bbm", "Si bemol menor",      ["Bb","Db","F"],  ["Sib","Reb","Fa"],    10, "También A#m."],
  ["Bm",  "Si menor",            ["B","D","F#"],   ["Si","Re","Fa#"],     11, ""]
];

// --- teclado: 2 octavas, resalta las teclas pulsadas ---
var WHITE = [0,2,4,5,7,9,11], BLACK = [1,3,6,8,10];
var W = 24, H = 76, BW = 13, BH = 48;

function keyboard(on, octaves){
  var svg = '', i, oct, st, x, wi = 0, marks = {};
  var OCT = octaves || 2;
  on.forEach(function(s, idx){ marks[s] = idx === 0 ? 'root' : 'on'; });
  // blancas
  for(oct = 0; oct < OCT; oct++){
    for(i = 0; i < 7; i++){
      st = oct * 12 + WHITE[i];
      x = wi * W;
      var m = marks[st];
      svg += '<rect x="' + x + '" y="0" width="' + W + '" height="' + H + '" rx="2.5" ' +
             'fill="var(--key-white)" stroke="var(--key-edge)" stroke-width="1"/>';
      if(m){
        var fill = m === 'root' ? 'var(--brass)' : 'var(--key-on)';
        svg += '<rect x="' + (x + 2.5) + '" y="' + (BH + 4) + '" width="' + (W - 5) +
               '" height="' + (H - BH - 8) + '" rx="2" fill="' + fill + '"/>';
      }
      wi++;
    }
  }
  // negras (encima)
  wi = 0;
  for(oct = 0; oct < OCT; oct++){
    for(i = 0; i < 7; i++){
      st = oct * 12 + WHITE[i];
      x = wi * W;
      if(BLACK.indexOf((WHITE[i] + 1) % 12) !== -1 && i !== 6){
        var bs = st + 1, bm = marks[bs];
        var bfill = bm === 'root' ? 'var(--brass)' : (bm === 'on' ? 'var(--key-on-black)' : 'var(--key-black)');
        svg += '<rect x="' + (x + W - BW / 2) + '" y="0" width="' + BW + '" height="' + BH +
               '" rx="2" fill="' + bfill + '"/>';
      }
      wi++;
    }
  }
  var w = 7 * OCT * W;
  return '<svg class="kb" viewBox="-1 -1 ' + (w + 2) + ' ' + (H + 2) + '" role="img" aria-hidden="true" ' +
         'shape-rendering="geometricPrecision" preserveAspectRatio="xMidYMid meet">' + svg + '</svg>';
}

function card(c, quality){
  var steps = quality === 'maj' ? [0,4,7] : [0,3,7];
  var on = steps.map(function(s){ return c[4] + s; });
  var en = c[2], es = c[3];
  var sym = c[0];
  var rel = quality === 'maj'
    ? '3ª mayor + 3ª menor'
    : '3ª menor + 3ª mayor';
  return '<article class="chord">' +
    '<div class="chord-top"><div class="sym">' + sym + '</div>' +
    '<div class="es"><strong>' + c[1] + '</strong>' + rel + '</div></div>' +
    keyboard(on) +
    '<dl class="rows">' +
      '<div class="row"><dt>Inglés</dt><dd><span class="r1">' + en[0] + '</span> – ' + en[1] + ' – ' + en[2] + '</dd></div>' +
      '<div class="row"><dt>Español</dt><dd><span class="r1">' + es[0] + '</span> – ' + es[1] + ' – ' + es[2] + '</dd></div>' +
      '<div class="row"><dt>Semitonos</dt><dd>0 – ' + steps[1] + ' – 7</dd></div>' +
      '<div class="row"><dt>Dedos</dt><dd>1 – 3 – 5 (MD) · 5 – 3 – 1 (MI)</dd></div>' +
    '</dl>' +
    (c[5] ? '<p class="alt">' + c[5] + '</p>' : '') +
    '</article>';
}

  function byRoot(quality, pc){
    var data = quality === 'maj' ? MAJ : MIN;
    for(var i = 0; i < data.length; i++){ if(data[i][4] === ((pc % 12) + 12) % 12) return data[i]; }
    return data[0];
  }

  var NOTE_EN = ["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"];
  var NOTE_ES = ["Do","Do#","Re","Mib","Mi","Fa","Fa#","Sol","Lab","La","Sib","Si"];
  function nameEn(st){ return NOTE_EN[((st % 12) + 12) % 12]; }
  function nameEs(st){ return NOTE_ES[((st % 12) + 12) % 12]; }

  return { MAJ: MAJ, MIN: MIN, keyboard: keyboard, card: card, byRoot: byRoot,
           nameEn: nameEn, nameEs: nameEs };
})();
