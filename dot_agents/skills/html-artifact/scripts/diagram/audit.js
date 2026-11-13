(function audit() {
  // Evaluated by audit-run.ts in a rendered page; never pasted into a delivered page.
  var FIGS = '.vega, .viz-chart, .widget-chart, pre.mermaid, .lanes, figure';
  var errors = [], empty = [], clipped = [], seen = new Set();

  // An element under display:none, at any depth, has no boxes; such figures are not on the page.
  function hidden(el) { return !!el.closest('[hidden]') || !el.getClientRects().length; }
  function name(el) {
    var fig = el.closest('figure') || el, b = fig.querySelector('figcaption b, figcaption strong');
    var id = el.closest('[id]');
    if (fig.id) return fig.id;
    if (b) return b.textContent.trim().slice(0, 80);
    return id ? '#' + id.id : el.tagName.toLowerCase() + '.' + (el.className || '').toString().split(/\s+/)[0];
  }
  function boxed(el) { var r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; }
  function hasError(el) {
    var e = el.querySelector('.viz-error, .widget-error');
    return e && !hidden(e) ? e : null;
  }

  document.querySelectorAll('.viz-error, .widget-error').forEach(function (e) {
    if (hidden(e)) return;
    errors.push({ figure: name(e), text: e.textContent.trim().slice(0, 300) });
  });

  // Empty: SVG-based figures with no drawn SVG, lanes with no marks. A figure showing an error is reported only there.
  document.querySelectorAll(FIGS).forEach(function (el) {
    if (hidden(el)) return;
    var fig = el.closest('figure') || el, host = el;
    // A plain figure is audited only for a generated diagram; hand-drawn SVG and tables are left alone.
    if (el.matches('figure')) {
      host = el.querySelector('.diagram');
      if (!host) return;
    }
    if (hasError(fig) || hasError(host)) return;
    var drew;
    if (el.matches('.lanes')) drew = !!el.querySelector('.track i');
    else {
      var svg = host.querySelector('svg');
      drew = !!svg && boxed(svg);
    }
    var key = name(host);
    if (!drew && !seen.has(host)) { seen.add(host); empty.push(key); }
  });

  // Clipped: SVG text outside its own SVG, or HTML text cut by an ancestor that hides overflow.
  function scrolls(el) { var o = getComputedStyle(el).overflowX; return o === 'auto' || o === 'scroll'; }
  function cuts(el) { var s = getComputedStyle(el); return /hidden|clip/.test(s.overflowX + ' ' + s.overflow); }
  document.querySelectorAll('figure svg text, .viz svg text, .widget svg text').forEach(function (t) {
    if (hidden(t) || !t.textContent.trim()) return;
    var svg = t.ownerSVGElement, r = t.getBoundingClientRect(), s = svg && svg.getBoundingClientRect();
    if (!s || !r.width) return;
    if (r.left < s.left - 1 || r.right > s.right + 1 || r.top < s.top - 1 || r.bottom > s.bottom + 1) {
      clipped.push({ figure: name(svg), text: t.textContent.trim().slice(0, 80) });
    }
  });
  // HTML text is clipped when its box leaves the box of the element itself or of any ancestor that hides
  // overflow, on either axis, unless a scroll container lies on the way (it can be scrolled into view).
  document.querySelectorAll('main *').forEach(function (el) {
    if (el.closest('svg') || hidden(el)) return;
    var own = Array.prototype.some.call(el.childNodes, function (n) { return n.nodeType === 3 && n.textContent.trim(); });
    if (!own) return;
    var tip = el.getAttribute('data-tooltip') || '';
    if (tip && tip.indexOf(el.textContent.trim()) >= 0) return;
    var range = document.createRange(); range.selectNodeContents(el);
    var b = range.getBoundingClientRect();
    if (!b.width && !b.height) return;
    for (var a = el; a && a !== document.body; a = a.parentElement) {
      if (a !== el && scrolls(a)) return;
      if (!cuts(a)) continue;
      var c = a.getBoundingClientRect();
      if (c.width <= 1 || c.height <= 1) return;  // a screen-reader-only box
      if (b.left < c.left - 1 || b.right > c.right + 1 || b.top < c.top - 1 || b.bottom > c.bottom + 1) {
        clipped.push({ figure: name(el), text: el.textContent.trim().slice(0, 80) });
        return;
      }
    }
  });

  var overflow = document.documentElement.scrollWidth > innerWidth + 1;
  return { errors: errors, empty: empty, clipped: clipped, overflow: overflow,
    ok: !errors.length && !empty.length && !clipped.length && !overflow };
})
