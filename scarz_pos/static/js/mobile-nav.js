/* Accessible mobile sidebar navigation. */
document.addEventListener('DOMContentLoaded', () => {
  const nav = document.getElementById('app-navigation');
  const toggle = document.getElementById('mobile-nav-toggle');
  if (!nav || !toggle) return;

  const backdrop = document.createElement('button');
  backdrop.type = 'button';
  backdrop.className = 'mobile-nav-backdrop';
  backdrop.setAttribute('aria-label', 'Close navigation menu');
  backdrop.tabIndex = -1;
  document.body.appendChild(backdrop);

  const closeButton = nav.querySelector('.mobile-nav-close');
  const mobileQuery = window.matchMedia('(max-width: 720px)');
  let previousFocus = null;

  const closeMenu = (restoreFocus = true) => {
    nav.classList.remove('is-open');
    backdrop.classList.remove('is-visible');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('mobile-nav-open');
    if (restoreFocus && mobileQuery.matches) toggle.focus();
  };

  const openMenu = () => {
    previousFocus = document.activeElement;
    nav.classList.add('is-open');
    backdrop.classList.add('is-visible');
    toggle.setAttribute('aria-expanded', 'true');
    document.body.classList.add('mobile-nav-open');
    const firstLink = nav.querySelector('a, button:not(.mobile-nav-close), .link-button');
    (closeButton || firstLink || nav).focus?.();
  };

  toggle.addEventListener('click', () => {
    if (nav.classList.contains('is-open')) closeMenu();
    else openMenu();
  });
  closeButton?.addEventListener('click', () => closeMenu());
  backdrop.addEventListener('click', () => closeMenu());
  nav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    if (mobileQuery.matches) closeMenu(false);
  }));
  nav.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => closeMenu(false)));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && nav.classList.contains('is-open')) closeMenu();
    if (event.key === 'Tab' && nav.classList.contains('is-open') && mobileQuery.matches) {
      const focusable = [...nav.querySelectorAll('a[href], button:not([hidden]), input:not([hidden]), [tabindex]:not([tabindex="-1"])')]
        .filter(element => !element.disabled && element.offsetParent !== null);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
  const syncViewport = () => {
    if (!mobileQuery.matches) closeMenu(false);
  };
  mobileQuery.addEventListener?.('change', syncViewport);
  window.addEventListener('resize', syncViewport);
});
