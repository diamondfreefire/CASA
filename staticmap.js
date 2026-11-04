/* ============================================================
   CARTE STATIQUE (pour le PDF) - dessinée dans un <canvas>
   Remplace l'ancien endpoint Flask /api/static-map (PIL + requests).
   ============================================================ */
(function (root) {
    'use strict';

    const BASEMAPS = {
        osm:            { url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '© OpenStreetMap contributors', maxZoom: 19 },
        carto_light:    { url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', attribution: '© OpenStreetMap contributors © CARTO', maxZoom: 19 },
        carto_dark:     { url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', attribution: '© OpenStreetMap contributors © CARTO', maxZoom: 19 },
        esri_satellite: { url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attribution: 'Tiles © Esri', maxZoom: 19 },
        esri_street:    { url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', attribution: 'Tiles © Esri', maxZoom: 19 },
        esri_topo:      { url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attribution: 'Tiles © Esri', maxZoom: 19 },
        opentopo:       { url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attribution: '© OpenTopoMap (CC-BY-SA)', maxZoom: 17 },
    };

    const TILE = 256;

    function lonlatToPixel(lon, lat, z) {
        const n = Math.pow(2, z), rad = lat * Math.PI / 180;
        return {
            x: (lon + 180) / 360 * n * TILE,
            y: (1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2 * n * TILE,
        };
    }

    function tileUrl(key, z, x, y) {
        const cfg = BASEMAPS[key] || BASEMAPS.osm;
        const n = Math.pow(2, z);
        return cfg.url.replace('{s}', 'abc'[(x + y) % 3]).replace('{r}', '')
            .replace('{z}', z).replace('{x}', ((x % n) + n) % n).replace('{y}', y);
    }

    function loadTile(url, timeout) {
        return new Promise(resolve => {
            const img = new Image();
            img.crossOrigin = 'anonymous';           // canvas non "taché" => export possible
            const timer = setTimeout(() => { img.src = ''; resolve(null); }, timeout);
            img.onload = () => { clearTimeout(timer); resolve(img); };
            img.onerror = () => { clearTimeout(timer); resolve(null); };
            img.src = url;
        });
    }

    function hexToRgb(hex) {
        const h = String(hex).replace('#', '');
        return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    }

    /**
     * @param {object} spec
     *   rides:     [{ color:'#E30613', path:[[lat,lon],...] }]
     *   transfers: [{ path:[[lat,lon],[lat,lon]] }]
     *   stations:  [{ name, lat, lon, kind:'start'|'end'|'transfer'|'stop', color }]
     *   basemap:   clé de BASEMAPS
     * @returns {Promise<{dataUrl:string, width:number, height:number, tilesLoaded:number, tilesTotal:number}>}
     */
    async function render(spec) {
        const W = spec.width || 1400, H = spec.height || 900;
        const all = [];
        (spec.rides || []).forEach(r => r.path.forEach(p => all.push(p)));
        (spec.transfers || []).forEach(r => r.path.forEach(p => all.push(p)));
        (spec.stations || []).forEach(s => all.push([s.lat, s.lon]));
        if (!all.length) throw new Error('Aucune coordonnée à dessiner');

        let minLat = Math.min(...all.map(p => p[0])), maxLat = Math.max(...all.map(p => p[0]));
        let minLon = Math.min(...all.map(p => p[1])), maxLon = Math.max(...all.map(p => p[1]));
        const mLat = Math.max((maxLat - minLat) * 0.08, 0.003), mLon = Math.max((maxLon - minLon) * 0.08, 0.003);
        minLat -= mLat; maxLat += mLat; minLon -= mLon; maxLon += mLon;

        const cfg = BASEMAPS[spec.basemap] || BASEMAPS.osm;
        let zoom = 10;
        for (let z = 10; z <= cfg.maxZoom; z++) {
            const a = lonlatToPixel(minLon, maxLat, z), b = lonlatToPixel(maxLon, minLat, z);
            if (b.x - a.x <= W - 60 && b.y - a.y <= H - 60) zoom = z; else break;
        }
        const a = lonlatToPixel(minLon, maxLat, zoom), b = lonlatToPixel(maxLon, minLat, zoom);
        const left = (a.x + b.x) / 2 - W / 2, top = (a.y + b.y) / 2 - H / 2;
        const toPx = (lat, lon) => { const p = lonlatToPixel(lon, lat, zoom); return [p.x - left, p.y - top]; };

        const canvas = document.createElement('canvas');
        canvas.width = W; canvas.height = H;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#eef1f6'; ctx.fillRect(0, 0, W, H);

        // ---- tuiles ----
        const jobs = [];
        const tx0 = Math.floor(left / TILE), ty0 = Math.floor(top / TILE);
        const tx1 = Math.floor((left + W) / TILE), ty1 = Math.floor((top + H) / TILE);
        for (let x = tx0; x <= tx1; x++) {
            for (let y = ty0; y <= ty1; y++) {
                if (y < 0 || y >= Math.pow(2, zoom)) continue;
                jobs.push(loadTile(tileUrl(spec.basemap, zoom, x, y), 9000)
                    .then(img => { if (img) ctx.drawImage(img, Math.round(x * TILE - left), Math.round(y * TILE - top), TILE, TILE); return !!img; }));
            }
        }
        const results = await Promise.all(jobs);
        const tilesLoaded = results.filter(Boolean).length;

        // ---- tracés ----
        function stroke(path, color, width, dash) {
            ctx.beginPath();
            path.forEach((p, i) => { const [x, y] = toPx(p[0], p[1]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
            ctx.setLineDash(dash || []);
            ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
            ctx.stroke(); ctx.setLineDash([]);
        }
        (spec.transfers || []).forEach(t => { stroke(t.path, '#ffffff', 9); stroke(t.path, '#ff9800', 5, [2, 9]); });
        (spec.rides || []).forEach(r => { stroke(r.path, 'rgba(255,255,255,.95)', 16); });
        (spec.rides || []).forEach(r => { stroke(r.path, r.color, 10); });

        // ---- stations + étiquettes ----
        ctx.font = '600 13px "Segoe UI", Roboto, Arial, sans-serif';
        ctx.textBaseline = 'middle';
        const placed = [];
        const collide = (r) => placed.some(q => r.x < q.x + q.w && r.x + r.w > q.x && r.y < q.y + q.h && r.y + r.h > q.y);

        const order = { start: 0, end: 0, transfer: 1, stop: 2 };
        const sts = (spec.stations || []).slice().sort((p, q) => order[p.kind] - order[q.kind]);

        sts.forEach(s => {
            const [x, y] = toPx(s.lat, s.lon);
            const big = s.kind !== 'stop';
            const r = big ? 8 : 6;
            ctx.beginPath(); ctx.arc(x, y, r + 2, 0, 7); ctx.fillStyle = '#fff'; ctx.fill();
            ctx.lineWidth = 3; ctx.strokeStyle = s.kind === 'transfer' ? '#ff9800' : (s.color || '#333'); ctx.stroke();
        });
        sts.forEach(s => {
            const [x, y] = toPx(s.lat, s.lon);
            const tw = ctx.measureText(s.name).width, w = tw + 12, h = 20;
            const must = s.kind !== 'stop';
            const spots = [[14, -h / 2], [-w - 14, -h / 2], [-w / 2, -h - 14], [-w / 2, 14]];
            let spot = null;
            for (const [dx, dy] of spots) {
                const rect = { x: x + dx, y: y + dy, w, h };
                if (rect.x < 4 || rect.y < 4 || rect.x + w > W - 4 || rect.y + h > H - 4) continue;
                if (!collide(rect)) { spot = rect; break; }
            }
            if (!spot && must) spot = { x: Math.min(Math.max(x + 14, 4), W - w - 4), y: Math.min(Math.max(y - h / 2, 4), H - h - 4), w, h };
            if (!spot) return;
            placed.push(spot);
            ctx.fillStyle = 'rgba(255,255,255,.96)';
            ctx.strokeStyle = s.kind === 'transfer' ? '#ff9800' : (s.color || '#666'); ctx.lineWidth = 1.5;
            ctx.beginPath();
            if (ctx.roundRect) ctx.roundRect(spot.x, spot.y, w, h, 4); else ctx.rect(spot.x, spot.y, w, h);
            ctx.fill(); ctx.stroke();
            ctx.fillStyle = '#1b2433';
            ctx.fillText(s.name, spot.x + 6, spot.y + h / 2 + 1);
        });

        // ---- départ / arrivée ----
        function pin(st, color, txt) {
            if (!st) return;
            const [x, y] = toPx(st.lat, st.lon);
            ctx.beginPath(); ctx.arc(x, y, 19, 0, 7); ctx.fillStyle = '#fff'; ctx.fill();
            ctx.beginPath(); ctx.arc(x, y, 15, 0, 7); ctx.fillStyle = color; ctx.fill();
            ctx.fillStyle = '#fff'; ctx.font = '800 14px "Segoe UI", Arial, sans-serif';
            ctx.textAlign = 'center'; ctx.fillText(txt, x, y + 1); ctx.textAlign = 'left';
        }
        pin(sts.find(s => s.kind === 'start'), '#4caf50', 'A');
        pin(sts.find(s => s.kind === 'end'), '#f44336', 'B');

        // ---- attribution ----
        ctx.font = '11px Arial, sans-serif'; ctx.textBaseline = 'alphabetic';
        const tw = ctx.measureText(cfg.attribution).width;
        ctx.fillStyle = 'rgba(255,255,255,.85)'; ctx.fillRect(W - tw - 14, H - 20, tw + 14, 20);
        ctx.fillStyle = '#333'; ctx.fillText(cfg.attribution, W - tw - 7, H - 6);

        let dataUrl;
        try { dataUrl = canvas.toDataURL('image/jpeg', 0.92); }
        catch (e) { throw new Error('Export de la carte impossible (fond de carte non autorisé) – essayez « OpenStreetMap ».'); }
        return { dataUrl, width: W, height: H, tilesLoaded, tilesTotal: results.length, zoom };
    }

    root.StaticMap = { render, BASEMAPS, lonlatToPixel, hexToRgb };
})(typeof self !== 'undefined' ? self : this);
