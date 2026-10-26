// Service worker: makes the tracker installable and lets it open offline.
// Bump VERSION whenever index.html, icons or this file change, so old caches get cleaned up.
// Cache names carry a tracker id, so two trackers on one website never delete each other's caches.
var TRACKER = 'main';
var VERSION = 'v1';
var PREFIX = 'jt-' + TRACKER + '-';
var SHELL_CACHE = PREFIX + 'shell-' + VERSION;
var DATA_CACHE = PREFIX + 'data-' + VERSION;
var FONT_CACHE = PREFIX + 'fonts-' + VERSION;
var SHELL = [
  './',
  'index.html',
  'config.js',
  'manifest.webmanifest',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/icon-maskable-512.png',
  'icons/apple-touch-icon.png',
  'icons/favicon-32.png'
];

self.addEventListener('install', function(e){
  e.waitUntil(caches.open(SHELL_CACHE).then(function(c){ return c.addAll(SHELL); }).then(function(){ return self.skipWaiting(); }));
});

self.addEventListener('activate', function(e){
  var keep = [SHELL_CACHE, DATA_CACHE, FONT_CACHE];
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k.indexOf(PREFIX) === 0 && keep.indexOf(k) === -1; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});

// Network first, falling back to the cache (used for jobs.json and the page itself).
function networkFirst(req, cacheName, cacheKey){
  return fetch(req).then(function(res){
    if(res && res.ok){
      var copy = res.clone();
      caches.open(cacheName).then(function(c){ c.put(cacheKey || req, copy); });
    }
    return res;
  }).catch(function(){
    return caches.match(cacheKey || req, {ignoreSearch: true}).then(function(hit){
      return hit || caches.match('index.html');
    });
  });
}

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;
  var url = new URL(req.url);

  // Google Fonts: serve from cache, refresh in the background.
  if(url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com'){
    e.respondWith(caches.open(FONT_CACHE).then(function(c){
      return c.match(req).then(function(hit){
        var net = fetch(req).then(function(res){ if(res && (res.ok || res.type === 'opaque')) c.put(req, res.clone()); return res; }).catch(function(){ return hit; });
        return hit || net;
      });
    }));
    return;
  }
  if(url.origin !== self.location.origin) return;

  // CV files (PDF/.tex): never cached by the service worker, always straight from the network,
  // so a re-generated tailored CV is never stale. Checked before navigations so opening a PDF
  // in a tab can't overwrite the cached page.
  if(/\.(pdf|tex|docx)$/i.test(url.pathname)) return;

  // Job list and settings: always try the network so new jobs and config edits show up;
  // the cache ignores the ?t= cache-buster and is only used offline.
  if(/\/(jobs\.json|config\.js)$/.test(url.pathname)){
    e.respondWith(networkFirst(req, DATA_CACHE, new Request(url.origin + url.pathname)));
    return;
  }
  // Page navigations: network first so design updates arrive, cached copy when offline.
  if(req.mode === 'navigate'){
    e.respondWith(networkFirst(req, SHELL_CACHE, new Request(new URL('index.html', self.registration.scope).href)));
    return;
  }
  // Other app files (icons, manifest): cache first.
  e.respondWith(caches.match(req).then(function(hit){ return hit || fetch(req); }));
});
