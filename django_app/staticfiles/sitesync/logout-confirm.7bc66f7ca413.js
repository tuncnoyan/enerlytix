(function () {
  function openModal(modal) {
    modal.hidden = false;
    document.body.classList.add('logout-modal-open');
  }

  function closeModal(modal) {
    modal.hidden = true;
    document.body.classList.remove('logout-modal-open');
  }

  document.addEventListener('click', function (event) {
    const openTrigger = event.target.closest('.js-open-logout-modal');
    const modal = document.getElementById('logoutConfirmModal');

    if (!modal) {
      return;
    }

    if (openTrigger) {
      event.preventDefault();
      openModal(modal);
      return;
    }

    const closeTrigger = event.target.closest('.js-close-logout-modal');
    if (closeTrigger || event.target === modal) {
      event.preventDefault();
      closeModal(modal);
    }
  });

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') {
      return;
    }

    const modal = document.getElementById('logoutConfirmModal');
    if (modal && !modal.hidden) {
      closeModal(modal);
    }
  });
})();
