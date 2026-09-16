/* Vicks ΚΥΣΑΤΣ 2026 — Χειρουργική sub-app service worker */
const CACHE = 'vicks-v6-surg-9c0d1e2f';
const CORE = ['./', './index.html', './manifest.json', '../icons/icon-192.png', '../icons/icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => null)))).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (req.mode === 'navigate') { e.respondWith(caches.match('./index.html').then(r => r || fetch(req).then(res => { const cp = res.clone(); caches.open(CACHE).then(c => c.put('./index.html', cp)); return res; }))); return; }
  if (url.origin === location.origin) { e.respondWith(caches.match(req).then(r => r || fetch(req).then(res => { if (res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); } return res; }).catch(() => caches.match('./index.html')))); return; }
  if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) { e.respondWith(caches.open(CACHE).then(async c => { const cached = await c.match(req); const net = fetch(req).then(res => { if (res.ok) c.put(req, res.clone()); return res; }).catch(() => null); return cached || (await net) || new Response('', { status: 503 }); })); return; }
});
self.addEventListener('message', e => { if (e.data === 'skipWaiting') self.skipWaiting(); });
