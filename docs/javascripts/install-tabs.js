document$.subscribe(function() {
  /* Tab switching */
  var tabs = document.querySelectorAll('.tab');
  if (tabs.length > 0) {
    tabs.forEach(function(tab) {
      var clone = tab.cloneNode(true);
      tab.parentNode.replaceChild(clone, tab);
      clone.addEventListener('click', function() {
        var target = clone.getAttribute('data-tab');
        document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
        document.querySelectorAll('.install-panel').forEach(function(p) { p.classList.remove('active'); });
        clone.classList.add('active');
        document.querySelector('[data-panel="' + target + '"]').classList.add('active');
      });
    });
  }

  /* Copy toast */
  function showToast() {
    var existing = document.querySelector('.copy-toast');
    if (existing) existing.remove();

    var toast = document.createElement('div');
    toast.className = 'copy-toast';
    toast.textContent = 'Copied!';
    document.body.appendChild(toast);

    requestAnimationFrame(function() {
      toast.classList.add('show');
    });

    setTimeout(function() {
      toast.classList.remove('show');
      setTimeout(function() { toast.remove(); }, 200);
    }, 1500);
  }

  /* Copy buttons */
  var copyBtns = document.querySelectorAll('.term-copy, .copy-btn');
  if (copyBtns.length > 0) {
    copyBtns.forEach(function(btn) {
      var clone = btn.cloneNode(true);
      btn.parentNode.replaceChild(clone, btn);
      clone.addEventListener('click', function(e) {
        e.stopPropagation();
        navigator.clipboard.writeText(clone.getAttribute('data-copy'));
        showToast();
      });
    });
  }

  /* Copy all button */
  var copyAllBtns = document.querySelectorAll('.term-copy-all-btn');
  if (copyAllBtns.length > 0) {
    copyAllBtns.forEach(function(btn) {
      var clone = btn.cloneNode(true);
      btn.parentNode.replaceChild(clone, btn);
      clone.addEventListener('click', function(e) {
        e.stopPropagation();
        navigator.clipboard.writeText(clone.getAttribute('data-copy'));
        showToast();
      });
    });
  }
});
