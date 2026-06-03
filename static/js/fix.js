(function () {
  document.querySelectorAll('.fix-btn').forEach(function (btn) {
    var label = btn.dataset.label;
    var confirming = false;
    var cancelBtn = null;

    function reset() {
      confirming = false;
      btn.textContent = label;
      btn.disabled = false;
      if (cancelBtn && cancelBtn.parentNode) {
        cancelBtn.parentNode.removeChild(cancelBtn);
      }
      cancelBtn = null;
    }

    function submit() {
      btn.disabled = true;
      btn.textContent = 'Applying…';
      if (cancelBtn && cancelBtn.parentNode) {
        cancelBtn.parentNode.removeChild(cancelBtn);
      }
      cancelBtn = null;
      fetch('/fix/' + encodeURIComponent(btn.dataset.signal), { method: 'POST' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) {
            btn.textContent = 'Applied — reloading…';
            setTimeout(function () { location.reload(); }, 1000);
          } else {
            alert('Could not apply fix: ' + (data.error || 'Unknown error'));
            reset();
          }
        })
        .catch(function (err) {
          alert('Request failed: ' + err);
          reset();
        });
    }

    btn.addEventListener('click', function () {
      if (confirming) {
        submit();
      } else {
        confirming = true;
        btn.textContent = 'Confirm?';
        cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Cancel';
        cancelBtn.className = 'fix-cancel';
        cancelBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          reset();
        });
        btn.insertAdjacentElement('afterend', cancelBtn);
      }
    });
  });
})();
