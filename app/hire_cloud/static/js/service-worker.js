const CACHE_NAME = "hire-cloud-shell-v2";
const SHELL_URLS = [
  "/",
  "/static/manifest.webmanifest",
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/icons/hire-icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key.startsWith("hire-cloud-shell-") && key !== CACHE_NAME)
        .map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  // Never cache authenticated pages or API/health responses: another user of
  // the same device must not receive a previous user's workspace offline.
  if (
    url.pathname === "/dashboard" ||
    url.pathname.startsWith("/dashboard/") ||
    url.pathname === "/auth" ||
    url.pathname.startsWith("/auth/") ||
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/health/")
  ) return;

  if (request.mode === "navigate") {
    // Only the public landing page is eligible for offline navigation fallback.
    if (url.pathname !== "/") return;
    event.respondWith(
      fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put("/", copy));
        }
        return response;
      }).catch(() => caches.match("/"))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request))
  );
});
