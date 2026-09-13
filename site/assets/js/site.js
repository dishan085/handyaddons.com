/* handyaddons.com — screenshot gallery and scroll reveal.
   No tracking, no third-party code. */

/* ---------- gallery with navigation and zoom ---------- */
(function () {
  var lb = document.getElementById('lb');
  if (!lb) return;

  var stage = document.getElementById('lb-stage');
  var img = document.getElementById('lbi');
  var cap = document.getElementById('lb-cap');
  var count = document.getElementById('lb-count');
  var prevBtn = document.getElementById('lb-prev');
  var nextBtn = document.getElementById('lb-next');
  var zoomBtn = document.getElementById('lb-zoom');
  var closeBtn = document.getElementById('lbx');

  /* Two screenshots appear twice on the page — in their own section and again
     in the gallery. The viewer lists each picture once, so the counter reads
     1 / 5 rather than 1 / 7, and both copies open the same slide. */
  var nodes = [].slice.call(document.querySelectorAll('[data-full]'));
  var items = [], indexOf = {};
  nodes.forEach(function (n) {
    var src = n.getAttribute('data-full');
    if (!(src in indexOf)) { indexOf[src] = items.length; items.push(n); }
  });
  var i = 0, opener = null;

  function show(n) {
    i = (n + items.length) % items.length;
    var fig = items[i];
    var thumb = fig.querySelector('img');
    img.src = fig.getAttribute('data-full');
    img.alt = thumb ? thumb.alt : '';
    var fc = fig.querySelector('figcaption');
    cap.textContent = fc ? fc.textContent.trim() : '';
    count.textContent = (i + 1) + ' / ' + items.length;
    unzoom();
  }

  function unzoom() {
    stage.classList.remove('zoom');
    zoomBtn.textContent = 'Zoom in';
    stage.scrollTop = 0;
  }
  function toggleZoom() {
    stage.classList.toggle('zoom');
    zoomBtn.textContent = stage.classList.contains('zoom') ? 'Fit to screen' : 'Zoom in';
    stage.scrollTop = 0;
  }

  function open(n, from) {
    opener = from;
    show(n);
    lb.classList.add('on');
    document.body.classList.add('lb-open');
    closeBtn.focus();
  }
  function close() {
    lb.classList.remove('on');
    document.body.classList.remove('lb-open');
    unzoom();
    if (opener) opener.focus();
  }

  nodes.forEach(function (fig) {
    var n = indexOf[fig.getAttribute('data-full')];
    fig.setAttribute('tabindex', '0');
    fig.setAttribute('role', 'button');
    fig.setAttribute('aria-label', 'Enlarge screenshot');
    fig.addEventListener('click', function () { open(n, fig); });
    fig.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(n, fig); }
    });
  });

  prevBtn.addEventListener('click', function () { show(i - 1); });
  nextBtn.addEventListener('click', function () { show(i + 1); });
  zoomBtn.addEventListener('click', toggleZoom);
  img.addEventListener('click', toggleZoom);
  closeBtn.addEventListener('click', close);
  lb.addEventListener('click', function (e) {
    if (e.target === lb || e.target === stage) close();
  });
  document.addEventListener('keydown', function (e) {
    if (!lb.classList.contains('on')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(i - 1);
    else if (e.key === 'ArrowRight') show(i + 1);
  });

  /* swipe between screenshots on touch screens */
  var x0 = null;
  stage.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
  stage.addEventListener('touchend', function (e) {
    if (x0 === null || stage.classList.contains('zoom')) return;
    var dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 45) show(dx < 0 ? i + 1 : i - 1);
    x0 = null;
  }, { passive: true });
})();

/* ---------- scroll reveal ---------- */
(function () {
  document.documentElement.classList.add('js');
  var blocks = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window) ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    blocks.forEach(function (b) { b.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  blocks.forEach(function (b) { io.observe(b); });
})();

/* ---------- back to top ---------- */
(function () {
  var btn = document.getElementById('totop');
  if (!btn) return;
  var shown = false;
  function check() {
    var want = window.scrollY > 700;
    if (want !== shown) { shown = want; btn.classList.toggle('on', want); }
  }
  btn.addEventListener('click', function () {
    var smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
  });
  window.addEventListener('scroll', check, { passive: true });
  check();
})();

/* ---------- active section in the header ---------- */
(function () {
  var links = [].slice.call(document.querySelectorAll('.sitemenu a[href*="#"]'));
  if (!links.length || !('IntersectionObserver' in window)) return;

  var map = {};
  links.forEach(function (a) {
    var id = a.getAttribute('href').split('#')[1];
    var sec = id && document.getElementById(id);
    if (sec) map[id] = { link: a, section: sec };
  });
  var ids = Object.keys(map);
  if (!ids.length) return;

  var visible = {};
  function paint() {
    /* the topmost section currently on screen wins */
    var best = null;
    ids.forEach(function (id) {
      if (!visible[id]) return;
      var top = map[id].section.getBoundingClientRect().top;
      if (best === null || top < map[best].section.getBoundingClientRect().top) best = id;
    });
    ids.forEach(function (id) { map[id].link.classList.toggle('here', id === best); });
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var id = e.target.id;
      visible[id] = e.isIntersecting;
    });
    paint();
  }, { rootMargin: '-96px 0px -55% 0px', threshold: 0 });

  ids.forEach(function (id) { io.observe(map[id].section); });
})();

/* ---------- the hero formula unfolds once, on first view ---------- */
(function () {
  var app = document.getElementById('hero-app');
  if (!app) return;
  if (!('IntersectionObserver' in window) ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    app.classList.add('go');
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    if (entries[0].isIntersecting) { app.classList.add('go'); io.disconnect(); }
  }, { threshold: 0.25 });
  io.observe(app);
})();

/* ---------- the figures count up, once, when the strip comes into view ---------- */
(function () {
  var nums = [].slice.call(document.querySelectorAll('[data-count]'));
  if (!nums.length) return;

  /* The markup already holds the final figure, so with no JavaScript, no
     IntersectionObserver, or reduced motion switched on, nothing needs doing. */
  if (!('IntersectionObserver' in window) ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  function run(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    var dur = 1100 + Math.min(target, 600);   /* larger figures take a little longer */
    var t0 = null;
    el.style.fontVariantNumeric = 'tabular-nums';   /* stops the width jittering */
    function frame(t) {
      if (t0 === null) t0 = t;
      var k = Math.min((t - t0) / dur, 1);
      k = 1 - Math.pow(1 - k, 3);                   /* fast start, gentle landing */
      el.textContent = Math.round(target * k);
      if (k < 1) requestAnimationFrame(frame);
      else el.textContent = target;
    }
    el.textContent = '0';
    requestAnimationFrame(frame);
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { run(e.target); io.unobserve(e.target); }
    });
  }, { threshold: 0.5 });
  nums.forEach(function (n) { io.observe(n); });
})();


/* ---------- the slide-out menu ---------- */
(function () {
  var btn = document.getElementById('menu-btn');
  var panel = document.getElementById('sitemenu');
  var veil = document.getElementById('menu-veil');
  if (!btn || !panel || !veil) return;

  function open() {
    panel.classList.add('open');
    veil.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    btn.setAttribute('aria-label', 'Close menu');
    document.body.classList.add('menu-open');
    var first = panel.querySelector('a');
    if (first) first.focus();
  }
  function close(returnFocus) {
    panel.classList.remove('open');
    veil.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', 'Open menu');
    document.body.classList.remove('menu-open');
    if (returnFocus) btn.focus();
  }
  btn.addEventListener('click', function () {
    panel.classList.contains('open') ? close(true) : open();
  });
  veil.addEventListener('click', function () { close(false); });
  var x = document.getElementById('menu-close');
  if (x) x.addEventListener('click', function () { close(true); });
  /* following a link should close the panel, since the target is on this page */
  panel.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') close(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel.classList.contains('open')) close(true);
  });
  /* if the window grows to desktop width the panel must not stay latched open */
  var wide = window.matchMedia('(min-width: 1060px)');
  (wide.addEventListener ? wide.addEventListener.bind(wide, 'change')
                         : wide.addListener.bind(wide))(function () {
    if (wide.matches) close(false);
  });
})();
