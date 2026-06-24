// Rohith Builds — Service Worker v1.0
// Strategy: Cache-first for static assets, Network-first for pages

const CACHE_NAME = 'rohithbuilds-v1';
const STATIC_CACHE = 'rohithbuilds-static-v1';

// Assets to pre-cache on install
const PRECACHE_ASSETS = [
  '/',
  '/learn',
  '/jobs',
  '/prompts',
  '/static/images/logo_compressed.png',
  '/static/images/logo.webp',
];

// Pages that should ALWAYS be fresh (network-first)
const NETWORK_FIRST_PATTERNS = [
  /^\/$/,                  // Homepage
  /^\/learn/,              // Learning portal
  /^\/jobs/,               // Jobs board
  /^\/prompts/,            // Prompts lists
  /^\/prompt\//,           // Prompt detail pages
  /^\/collections/,        // Prompt collections
  /^\/improve/,            // Prompt helper tool
  /^\/dashboard/,          // User dashboard
  /^\/admin/,              // Admin panel
  /^\/login/,              // Auth page
  /^\/logout/,             // Auth page
  /^\/register/,           // Auth page
  /^\/api\//,              // All API endpoints
];

// ── Install: pre-cache critical assets ──────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Pre-cache failed (some assets may not exist yet):', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// ── Activate: clean old caches ───────────────────────────────────
self.addEventListener('activate', (event) => {
  const VALID_CACHES = [CACHE_NAME, STATIC_CACHE];
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames
          .filter((name) => !VALID_CACHES.includes(name))
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: smart routing strategy ───────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin requests
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  // Skip browser extension requests
  if (url.protocol === 'chrome-extension:') return;

  const isNetworkFirst = NETWORK_FIRST_PATTERNS.some((pattern) =>
    pattern.test(url.pathname)
  );

  if (isNetworkFirst) {
    // Network-first: try fresh from server, fall back to cache
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => caches.match(request))
    );
  } else {
    // Cache-first: serve from cache, update in background
    event.respondWith(
      caches.match(request).then((cached) => {
        const fetchPromise = fetch(request).then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        });
        return cached || fetchPromise;
      })
    );
  }
});

// ── Push notifications (future use) ─────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json();
  self.registration.showNotification(data.title || 'Rohith Builds', {
    body: data.body || 'You have a new update!',
    icon: '/static/images/logo_compressed.png',
    badge: '/static/images/logo_compressed.png',
    tag: 'rohithbuilds-notification',
    renotify: true,
    data: { url: data.url || '/' },
  });
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});
