function startElapsedCounter(elementId, prefix) {
  var el = document.getElementById(elementId);
  var loaded = Date.now();
  function update() {
    var secs = Math.round((Date.now() - loaded) / 1000);
    if (secs < 10) {
      el.textContent = 'Just now';
    } else if (secs < 60) {
      el.textContent = prefix + ': ' + secs + 's ago';
    } else {
      var mins = Math.floor(secs / 60);
      el.textContent = prefix + ': ' + mins + ' min' + (mins !== 1 ? 's' : '') + ' ago';
    }
  }
  update();
  setInterval(update, 5000);
}

(function () {
  var el = document.getElementById('last-checked-label');
  if (el) {
    startElapsedCounter('last-checked-label', el.dataset.prefix || '');
  }
})();
