(() => {
  const main = document.querySelector('main');
  if (!main) return;
  
  main.id = main.id || 'main-content';
  
  const skipLink = document.createElement('a');
  skipLink.href = '#' + main.id;
  skipLink.className = 'skip-link';
  skipLink.textContent = 'Skip to main content';
  
  skipLink.addEventListener('click', (e) => {
    e.preventDefault();
    main.setAttribute('tabindex', '-1');
    main.focus();
    main.scrollIntoView({ behavior: 'smooth', block: 'start' });
    main.addEventListener('blur', () => main.removeAttribute('tabindex'), { once: true });
  });
  
  document.body.insertBefore(skipLink, document.body.firstChild);
})();
