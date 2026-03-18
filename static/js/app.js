document.addEventListener('DOMContentLoaded', () => {
  const copyButtons = document.querySelectorAll('[data-copy-target]');

  copyButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const targetId = button.getAttribute('data-copy-target');
      const target = document.getElementById(targetId);
      if (!target) return;

      try {
        await navigator.clipboard.writeText(target.textContent.trim());
        button.textContent = 'Código copiado';
        setTimeout(() => {
          button.textContent = 'Copiar código';
        }, 1600);
      } catch (error) {
        console.error('Não foi possível copiar o código.', error);
      }
    });
  });
});
