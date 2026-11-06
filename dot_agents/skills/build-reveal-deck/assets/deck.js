Reveal.initialize({
  width: 1600, height: 900, margin: 0, center: false, hash: true,
  transition: 'slide', backgroundTransition: 'fade', transitionSpeed: 'default',
  slideNumber: 'c/t', controls: true, progress: true,
  autoAnimateDuration: 1.1, autoAnimateEasing: 'cubic-bezier(.2,.8,.2,1)',
  plugins: window.RevealNotes ? [RevealNotes] : []
});

// An arrow's head (marker-end) is attached only once its line has finished drawing.
// Put data-marker="<marker id>" on the path instead of marker-end.
// Viewers who ask for less motion get the whole line and its head at once.
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
let DRAW_MS = 0;
function setDrawMs() {
  DRAW_MS = reduceMotion.matches ? 0 : 1100;
  document.documentElement.style.setProperty('--draw-ms', DRAW_MS + 'ms');
}
setDrawMs();
reduceMotion.addEventListener('change', setDrawMs);

function markerTargets(f) {
  return [...(f.matches('[data-marker]') ? [f] : []), ...f.querySelectorAll('[data-marker]')];
}
function setMarker(el, on) {
  clearTimeout(el._t); el._t = null;
  if (on) el.setAttribute('marker-end', 'url(#' + el.dataset.marker + ')');
  else el.removeAttribute('marker-end');
}
function syncMarkers() {
  document.querySelectorAll('.reveal [data-marker]').forEach(el => {
    const frag = el.closest('.fragment');
    setMarker(el, !frag || frag.classList.contains('visible'));
  });
}
function measureDraws() {
  document.querySelectorAll('.reveal .fragment.draw :is(path, line, polyline)').forEach(el => {
    if (el.closest('marker') || el.style.getPropertyValue('--len')) return;
    try {
      const L = el.getTotalLength();
      if (!(L > 0)) return;
      el.style.transition = 'none';  // otherwise the offset animates from the old value and the line flashes
      el.style.setProperty('--len', Math.ceil(L) + 1);
      el.getBoundingClientRect();
      el.style.transition = '';
    } catch (_) {}
  });
}
Reveal.on('fragmentshown', e => e.fragments.forEach(f => {
  const delay = f.classList.contains('draw') ? DRAW_MS : 0;
  markerTargets(f).forEach(el => { clearTimeout(el._t); el._t = setTimeout(() => setMarker(el, true), delay); });
}));
Reveal.on('fragmenthidden', e => e.fragments.forEach(f => markerTargets(f).forEach(el => setMarker(el, false))));
Reveal.on('ready', () => { measureDraws(); syncMarkers(); });
Reveal.on('slidechanged', () => { measureDraws(); syncMarkers(); });
