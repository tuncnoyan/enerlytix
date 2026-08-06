(function () {
  async function copyText(text) {
    if (!text) return false;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }

    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(textArea);
    return ok;
  }

  document.addEventListener('click', async function (event) {
    const button = event.target.closest('.js-copy-invite-link');
    if (!button) return;

    const absoluteUrl = button.getAttribute('data-invite-url') || '';
    try {
      await copyText(absoluteUrl);
      button.textContent = 'Copied';
      setTimeout(function () {
        button.textContent = 'Copy link';
      }, 1500);
    } catch (err) {
      button.textContent = 'Copy failed';
      setTimeout(function () {
        button.textContent = 'Copy link';
      }, 1500);
    }
  });
})();
