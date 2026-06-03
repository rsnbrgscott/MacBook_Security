(function () {
  var el = document.getElementById('countdown');
  if (!el) return;
  var remaining = parseInt(el.textContent, 10);
  if (!remaining || remaining <= 0) return;
  function tick() {
    if (remaining <= 0) { location.reload(); return; }
    el.textContent = remaining;
    remaining -= 1;
    setTimeout(tick, 1000);
  }
  setTimeout(tick, 1000);
})();
