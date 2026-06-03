(function () {
  var input = document.getElementById('signal-filter');
  if (!input) return;
  var rows = document.querySelectorAll('#signal-history-body tr');
  input.addEventListener('input', function () {
    var q = input.value.toLowerCase();
    rows.forEach(function (row) {
      var name = (row.querySelector('.ht-name') || {}).textContent || '';
      row.style.display = name.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
    });
  });
})();
