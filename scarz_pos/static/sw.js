/* Hire POS service worker: cache only public shell assets, never private page responses. */
const CACHE_NAME = 'hire-pos-shell-v7';
const SHELL_ASSETS = [
  '/static/css/app.css',
  '/static/js/app.js',
  '/static/js/phone_scanner.js',
  '/static/css/mobile-nav.css',
  '/static/manifest.webmanifest',
  '/static/icon.svg',
  '/static/offline.html'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key.startsWith('hire-pos-') && key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    // Do not cache authenticated pages or business data. Offline navigation gets
    // a neutral fallback that does not expose stale private content.
    event.respondWith(fetch(request).catch(async () => {
      const cache = await caches.open(CACHE_NAME);
      return (await cache.match('/static/offline.html')) || Response.error();
    }));
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(async cached => {
        try {
          const response = await fetch(request);
          if (response.ok && response.type === 'basic') {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
          }
          return response;
        } catch (error) {
          if (cached) return cached;
          throw error;
        }
      })
    );
  }
});
