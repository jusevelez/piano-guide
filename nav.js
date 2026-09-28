/* Menú principal: abre y cierra el desplegable de Canciones. */
(function(){
  var drops = document.querySelectorAll('.site-nav .drop');
  if(!drops.length) return;

  function close(d){
    d.querySelector('button').setAttribute('aria-expanded', 'false');
    d.querySelector('.menu').hidden = true;
  }
  function closeAll(){ Array.prototype.forEach.call(drops, close); }

  Array.prototype.forEach.call(drops, function(d){
    var btn = d.querySelector('button'), menu = d.querySelector('.menu');
    var timer, openedByHover = false;

    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');

    function open(byHover){
      clearTimeout(timer);
      closeAll();
      menu.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
      openedByHover = !!byHover;
    }

    btn.addEventListener('click', function(ev){
      ev.stopPropagation();
      if(menu.hidden){ open(false); return; }
      // si lo abrió el ratón al pasar por encima, el clic no debe cerrarlo
      if(openedByHover){ openedByHover = false; return; }
      close(d);
    });

    // se abre al pasar el ratón; en táctil no, porque ahí solo vale el toque
    d.addEventListener('pointerenter', function(ev){
      if(ev.pointerType === 'mouse') open(true);
    });
    d.addEventListener('pointerleave', function(ev){
      if(ev.pointerType !== 'mouse') return;
      timer = setTimeout(function(){ close(d); }, 180);
    });
    d.addEventListener('focusin', function(){ if(menu.hidden) open(true); });
  });

  document.addEventListener('click', function(ev){
    if(!ev.target.closest('.site-nav .drop')) closeAll();
  });
  document.addEventListener('keydown', function(ev){
    if(ev.key === 'Escape') closeAll();
  });
})();
