/* ============================================================
   TRAMWAY CASABLANCA - application (carte + interface)
   100 % statique : plus besoin de serveur Flask.
   ============================================================ */
(function () {
    'use strict';

    const $ = id => document.getElementById(id);
    const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const isMobile = () => window.matchMedia('(max-width: 820px)').matches;

    // stockage local (peut être indisponible : navigation privée, etc.)
    const store = {
        get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
        set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
    };

    let toastTimer = null;
    function toast(msg, ms) {
        const t = $('toast');
        t.textContent = msg; t.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => t.classList.remove('show'), ms || 3200);
    }

    // ------------------------------------------------------------
    // Fonds de carte
    // ------------------------------------------------------------
    const BASEMAPS = window.StaticMap.BASEMAPS;
    let tileLayer = null;

    function setBasemap(key) {
        if (!BASEMAPS[key]) key = 'osm';
        const cfg = BASEMAPS[key];
        if (tileLayer) map.removeLayer(tileLayer);
        tileLayer = L.tileLayer(cfg.url, { attribution: cfg.attribution, maxZoom: cfg.maxZoom, subdomains: 'abc' }).addTo(map);
        tileLayer.bringToBack();
        $('basemap-select').value = key;
        store.set('tram.basemap', key);
        currentBasemap = key;
    }

    // ------------------------------------------------------------
    // État
    // ------------------------------------------------------------
    let currentBasemap = 'osm';
    let net = null, router = null;
    const lineLayers = {};          // id -> polyline
    const lineStations = {};        // id -> layerGroup de stations
    const lineVisible = {};
    const stationMarkers = {};      // station id -> marker
    let routeGroup = null;
    let stepLayers = [];            // un featureGroup par étape
    let lastRoute = null;
    let userMarker = null;

    const map = L.map('map', { zoomControl: true }).setView([33.5731, -7.5898], 12);
    L.control.scale({ imperial: false }).addTo(map);

    function updateZoomClass() {
        map.getContainer().classList.toggle('zoom-lo', map.getZoom() < 14);
    }
    map.on('zoomend', updateZoomClass);
    updateZoomClass();

    const badge = lid => `<span class="badge" style="background:${esc(net.lines[lid].color)}">${esc(lid)}</span>`;
    const lineColor = lid => net.lines[lid].color;

    // ------------------------------------------------------------
    // Réseau : lignes + stations
    // ------------------------------------------------------------
    function drawNetwork() {
        const legend = $('legend-content');
        legend.innerHTML = '';

        router.lineIds.forEach(lid => {
            const l = net.lines[lid];
            const latlngs = router.hasGeometry(lid)
                ? l.geometry
                : l.stations.map(s => [net.stations[s].lat, net.stations[s].lon]);
            lineLayers[lid] = L.polyline(latlngs, { color: l.color, weight: 5, opacity: 0.85, lineJoin: 'round' })
                .bindTooltip(`<b>${esc(lid)}</b> – ${esc(l.description)}`, { sticky: true })
                .addTo(map);
            lineVisible[lid] = true;
            lineStations[lid] = L.layerGroup().addTo(map);

            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `<div class="legend-color" style="background:${esc(l.color)}"></div><span>${esc(lid)} – ${esc(l.description)}</span>`;
            item.addEventListener('click', () => { setLineVisible(lid, !lineVisible[lid]); item.classList.toggle('off', !lineVisible[lid]); });
            legend.appendChild(item);
        });

        Object.keys(net.stations).forEach(sid => {
            const st = net.stations[sid];
            const lid = (router.stationLines[sid] || [])[0];
            const corr = (router.corrOf[sid] || []).length > 0;
            const icon = L.divIcon({
                className: 'st-icon',
                html: `<div class="st${corr ? ' corr' : ''}" data-sid="${esc(sid)}"><span class="dot"></span><span class="lbl">${esc(st.n)}</span></div>`,
                iconSize: [0, 0],
            });
            const marker = L.marker([st.lat, st.lon], { icon, zIndexOffset: corr ? 500 : 0, keyboard: false, title: st.n });
            marker.bindPopup(() => buildPopup(sid), { maxWidth: 300 });
            stationMarkers[sid] = marker;
            if (lid) marker.addTo(lineStations[lid]);
        });
    }

    function setLineVisible(lid, on) {
        lineVisible[lid] = on;
        if (on) { lineLayers[lid].addTo(map); lineStations[lid].addTo(map); }
        else { map.removeLayer(lineLayers[lid]); map.removeLayer(lineStations[lid]); }
    }
    function showAllLines() {
        router.lineIds.forEach(lid => { if (!lineVisible[lid]) setLineVisible(lid, true); });
        document.querySelectorAll('.legend-item.off').forEach(e => e.classList.remove('off'));
    }

    function stationEl(sid) {
        const m = stationMarkers[sid], root = m && m.getElement();
        return root ? root.querySelector('.st') : null;
    }

    function buildPopup(sid) {
        const st = net.stations[sid];
        const corrs = router.corrOf[sid] || [];
        const lines = router.stationLines[sid] || [];
        const el = document.createElement('div');
        el.className = 'pop';
        el.innerHTML = `
            <div class="pop-head${corrs.length ? ' corr' : ''}">${corrs.length ? '🔀 ' : '🚏 '}${esc(st.n)}</div>
            <div class="pop-lines">${lines.map(badge).join('')}</div>
            ${corrs.length ? `<div class="pop-corr"><b class="t">🔀 Correspondances :</b>${corrs.map(c =>
                `➜ ${badge(c.to_line)} ${esc(net.stations[c.to_station].n)} <span style="color:#999">(${c.walk_time} min à pied)</span>`).join('<br>')}</div>` : ''}
            <div class="pop-actions">
                <button type="button" class="a-start">📍 Départ</button>
                <button type="button" class="a-end">🎯 Arrivée</button>
            </div>
            <div class="pop-gps">${st.lat.toFixed(6)}, ${st.lon.toFixed(6)}</div>`;
        el.querySelector('.a-start').addEventListener('click', () => { pickStation('start', st.n); map.closePopup(); });
        el.querySelector('.a-end').addEventListener('click', () => { pickStation('end', st.n); map.closePopup(); });
        return el;
    }

    function pickStation(which, name) {
        $(which === 'start' ? 'start-input' : 'end-input').value = name;
        toast((which === 'start' ? 'Départ : ' : 'Arrivée : ') + name);
        if ($('start-input').value && $('end-input').value) calculateRoute();
    }

    // ------------------------------------------------------------
    // Auto-complétion (locale, sans accents)
    // ------------------------------------------------------------
    function setupAutocomplete(inputId, listId) {
        const input = $(inputId), list = $(listId);
        let active = -1, items = [];

        function close() { list.classList.remove('show'); input.setAttribute('aria-expanded', 'false'); active = -1; }
        function choose(name) { input.value = name; close(); }
        function highlight() { [...list.children].forEach((c, i) => c.classList.toggle('active', i === active)); }

        function render() {
            const q = input.value.trim();
            if (!q) return close();
            items = router.searchStations(q).slice(0, 8);
            if (!items.length) return close();
            list.innerHTML = '';
            items.forEach(s => {
                const div = document.createElement('div');
                div.className = 'autocomplete-item'; div.setAttribute('role', 'option');
                div.innerHTML = `<span class="station-name">${esc(s.name)}</span>${s.lines.map(badge).join('')}`;
                div.addEventListener('mousedown', e => { e.preventDefault(); choose(s.name); });
                list.appendChild(div);
            });
            active = -1;
            list.classList.add('show'); input.setAttribute('aria-expanded', 'true');
        }

        input.addEventListener('input', render);
        input.addEventListener('focus', render);
        input.addEventListener('blur', () => setTimeout(close, 120));
        input.addEventListener('keydown', e => {
            if (!list.classList.contains('show')) return;
            if (e.key === 'ArrowDown') { e.preventDefault(); active = (active + 1) % items.length; highlight(); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); active = (active - 1 + items.length) % items.length; highlight(); }
            else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); choose(items[active].name); }
            else if (e.key === 'Escape') close();
        });
    }

    // ------------------------------------------------------------
    // Calcul + affichage
    // ------------------------------------------------------------
    function calculateRoute() {
        const start = $('start-input').value.trim(), end = $('end-input').value.trim();
        if (!start || !end) { toast('Veuillez entrer les deux stations'); return; }

        clearRoute();
        const route = router.findRoute(start, end, 3);
        if (route.error) { lastRoute = null; showError(route.error); return; }

        lastRoute = route;
        displayRoute(route);
        drawRoute(route);
        updateUrl(route);
        if (isMobile()) $('result').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function showError(message) {
        const r = $('result');
        r.innerHTML = `<div class="result-header error"><h3>❌ Erreur</h3><p style="font-size:13px;color:#555;margin-top:6px">${esc(message)}</p></div>`;
        r.classList.add('show');
    }

    function displayRoute(route) {
        const rides = route.steps.filter(s => s.type === 'ride');
        let title;
        if (!rides.length) title = '🚶 Correspondance à pied';
        else if (route.type === 'direct') title = '✅ Itinéraire direct';
        else title = `🔀 Itinéraire avec ${route.num_transfers} correspondance(s)`;

        let html = `<div class="result-header"><h3>${title}</h3>
            <div class="result-stats"><span>⏱️ ${Math.round(route.total_time)} min</span><span>📏 ${route.total_distance_km.toFixed(2)} km</span><span>📊 ${route.total_stations} stations</span></div>
            <div class="route-pills">${esc(route.start.name)} &nbsp;${rides.map(r => badge(r.line)).join(' › ')}&nbsp; ${esc(route.end.name)}</div></div>`;

        let n = 1;
        route.steps.forEach((step, i) => {
            if (step.type === 'ride') {
                html += `<div class="step ride" style="--c:${esc(step.line_color)}" data-step="${i}">
                    <div class="step-title">${badge(step.line)}<span>Étape ${n++}</span>
                        <button type="button" class="zoom" data-zoom="${i}" title="Zoomer sur ce tronçon">🔍 Voir</button></div>
                    <div class="step-detail">De <b>${esc(step.from)}</b> → À <b>${esc(step.to)}</b><br>
                        ⏱️ ${Math.round(step.travel_time_min)} min &nbsp;|&nbsp; 📊 ${step.num_stations} stations &nbsp;|&nbsp; 📏 ${step.distance_km.toFixed(2)} km</div>
                    <div class="stations-list">${step.stations.map((s, k) =>
                        `<div class="station-item${k === 0 ? ' start' : k === step.stations.length - 1 ? ' end' : ''}" data-sid="${esc(s.id)}"><span class="station-dot"></span><span>${esc(s.name)}</span></div>`).join('')}</div>
                </div>`;
            } else {
                html += `<div class="step transfer" data-step="${i}"><div class="step-title">🚶 Correspondance
                    <button type="button" class="zoom" data-zoom="${i}">🔍 Voir</button></div>
                    <div class="step-detail">Descendre à <b>${esc(step.from_station)}</b><br>Marcher <b>${step.walk_time} min</b> jusqu'à <b>${esc(step.to_station)}</b></div></div>`;
            }
        });

        const r = $('result');
        r.innerHTML = html;
        r.classList.add('show');

        r.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => focusStep(+b.dataset.zoom)));
        r.querySelectorAll('.station-item').forEach(el => el.addEventListener('click', () => {
            const m = stationMarkers[el.dataset.sid];
            if (!m) return;
            map.flyTo(m.getLatLng(), Math.max(map.getZoom(), 16), { duration: 0.6 });
            m.openPopup();
        }));
    }

    // ------------------------------------------------------------
    // Dessin de l'itinéraire : SEUL le tronçon A -> B est coloré
    // ------------------------------------------------------------
    function clearRoute() {
        if (routeGroup) { map.removeLayer(routeGroup); routeGroup = null; }
        stepLayers = [];
        map.getContainer().classList.remove('route-on');
        document.querySelectorAll('.st.on-route').forEach(e => { e.classList.remove('on-route', 'key'); e.style.removeProperty('--c'); });
        Object.values(lineLayers).forEach(p => p.setStyle({ opacity: 0.85, weight: 5 }));
    }

    function pinIcon(kind) {
        const start = kind === 'start';
        return L.divIcon({
            className: 'pin-icon', iconSize: [0, 0],
            html: `<div class="pin ${kind}" style="position:relative">${start ? 'A' : 'B'}<span class="pin-tag">${start ? 'Départ' : 'Arrivée'}</span></div>`,
        });
    }

    function drawRoute(route) {
        showAllLines();
        $('legend').classList.add('collapsed');
        routeGroup = L.layerGroup().addTo(map);
        map.getContainer().classList.add('route-on');
        Object.values(lineLayers).forEach(p => p.setStyle({ opacity: 0.2, weight: 4 }));

        const all = [];
        route.steps.forEach((step, i) => {
            const path = step.path;
            path.forEach(p => all.push(p));
            if (step.type === 'ride') {
                const casing = L.polyline(path, { color: '#fff', weight: 14, opacity: 0.95, lineCap: 'round', lineJoin: 'round', interactive: false });
                const main = L.polyline(path, { color: step.line_color, weight: 8, opacity: 1, lineCap: 'round', lineJoin: 'round' })
                    .bindTooltip(`<b>${esc(step.line)}</b> : ${esc(step.from)} → ${esc(step.to)}<br>${step.num_stations} stations · ${Math.round(step.travel_time_min)} min`, { sticky: true });
                const flow = L.polyline(path, { color: '#fff', weight: 2.5, opacity: 0.9, dashArray: '1 14', lineCap: 'round', className: 'route-flow', interactive: false });
                const fg = L.featureGroup([casing, main, flow]).addTo(routeGroup);
                fg._main = main;
                stepLayers[i] = fg;

                step.stations.forEach((s, k) => {
                    const el = stationEl(s.id);
                    if (!el) return;
                    el.classList.add('on-route');
                    el.classList.toggle('key', k === 0 || k === step.stations.length - 1);
                    el.style.setProperty('--c', step.line_color);
                });
            } else {
                const dash = L.polyline(step.path, { color: '#ff9800', weight: 5, opacity: 1, dashArray: '2 9', lineCap: 'round' }).addTo(routeGroup);
                const mid = [(step.path[0][0] + step.path[1][0]) / 2, (step.path[0][1] + step.path[1][1]) / 2];
                L.marker(mid, { interactive: false, icon: L.divIcon({ className: 'walk-icon', iconSize: [0, 0], html: '<div class="walk">🚶</div>' }) }).addTo(routeGroup);
                stepLayers[i] = L.featureGroup([dash]);
                [step.from_id, step.to_id].forEach(id => { const el = stationEl(id); if (el) el.classList.add('on-route', 'key'); });
            }
        });

        [route.start.id, route.end.id].forEach(id => { const el = stationEl(id); if (el) el.classList.add('key'); });
        L.marker([route.start.lat, route.start.lon], { icon: pinIcon('start'), zIndexOffset: 1000, interactive: false }).addTo(routeGroup);
        L.marker([route.end.lat, route.end.lon], { icon: pinIcon('end'), zIndexOffset: 1000, interactive: false }).addTo(routeGroup);

        if (all.length) map.fitBounds(L.latLngBounds(all), { padding: [60, 60], maxZoom: 16 });
    }

    function focusStep(i) {
        const fg = stepLayers[i];
        if (!fg) return;
        map.fitBounds(fg.getBounds(), { padding: [80, 80], maxZoom: 17 });
        if (fg._main) {
            fg._main.setStyle({ weight: 13 });
            setTimeout(() => fg._main.setStyle({ weight: 8 }), 700);
        }
    }

    function resetRoute() {
        $('start-input').value = ''; $('end-input').value = '';
        $('result').classList.remove('show'); $('result').innerHTML = '';
        lastRoute = null;
        clearRoute();
        $('legend').classList.remove('collapsed');
        map.closePopup();
        map.setView([33.5731, -7.5898], 12);
        try { history.replaceState(null, '', location.pathname); } catch (e) { /* ignore */ }
    }

    function updateUrl(route) {
        try {
            const q = new URLSearchParams({ from: route.start.name, to: route.end.name });
            history.replaceState(null, '', location.pathname + '?' + q.toString());
        } catch (e) { /* ignore (file://, iframe...) */ }
    }

    // ------------------------------------------------------------
    // GPS
    // ------------------------------------------------------------
    function locateMe() {
        if (!navigator.geolocation) { toast('Géolocalisation non supportée par ce navigateur'); return; }
        navigator.geolocation.getCurrentPosition(pos => {
            const { latitude: lat, longitude: lon } = pos.coords;
            if (userMarker) map.removeLayer(userMarker);
            userMarker = L.circleMarker([lat, lon], { radius: 8, color: '#fff', weight: 3, fillColor: '#2a7de1', fillOpacity: 1 }).addTo(map).bindTooltip('Vous êtes ici');
            const near = router.nearestStation(lat, lon, 2000);
            if (!near) { toast('Aucune station à moins de 2 km'); map.setView([lat, lon], 14); return; }
            $('start-input').value = near.name;
            map.setView([lat, lon], 15);
            toast(`Station la plus proche : ${near.name} (${Math.round(near.distance_m)} m)`, 4500);
        }, err => toast('Erreur GPS : ' + err.message));
    }

    // ------------------------------------------------------------
    // PDF
    // ------------------------------------------------------------
    function buildStaticSpec(route) {
        const rides = [], transfers = [], stations = [], seen = new Set();
        const add = (s, kind, color) => {
            if (seen.has(s.id)) { const e = stations.find(x => x.id === s.id); if (e && kind !== 'stop') e.kind = kind; return; }
            seen.add(s.id); stations.push({ id: s.id, name: s.name, lat: s.lat, lon: s.lon, kind, color });
        };
        route.steps.forEach(step => {
            if (step.type === 'ride') {
                rides.push({ color: step.line_color, path: step.path });
                step.stations.forEach((s, k) => add(s, k === 0 || k === step.stations.length - 1 ? 'transfer' : 'stop', step.line_color));
            } else {
                transfers.push({ path: step.path });
                [step.from_id, step.to_id].forEach(id => add({ id, name: net.stations[id].n, lat: net.stations[id].lat, lon: net.stations[id].lon }, 'transfer', '#ff9800'));
            }
        });
        add(route.start, 'start', '#4caf50'); add(route.end, 'end', '#f44336');
        stations.find(s => s.id === route.start.id).kind = 'start';
        stations.find(s => s.id === route.end.id).kind = 'end';
        return { rides, transfers, stations, basemap: currentBasemap };
    }

    const slug = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\w]+/g, '_').replace(/^_|_$/g, '');

    async function downloadPDF() {
        const btn = $('download-btn'), label = btn.innerHTML;
        if (!lastRoute) { toast('Veuillez d\'abord calculer un itinéraire'); return; }
        btn.disabled = true; btn.innerHTML = '⏳ Génération du PDF...';
        try {
            const mapImg = await window.StaticMap.render(buildStaticSpec(lastRoute));
            const pdf = await window.TramPdf.build(lastRoute, { start: lastRoute.start.name, end: lastRoute.end.name, map: mapImg });
            pdf.save(`Itineraire_${slug(lastRoute.start.name)}_${slug(lastRoute.end.name)}.pdf`);
            btn.innerHTML = '✅ PDF créé !';
            if (!mapImg.tilesLoaded) toast('Fond de carte indisponible : le PDF contient uniquement le tracé.', 5000);
        } catch (err) {
            console.error('Erreur PDF:', err);
            toast('❌ ' + err.message, 6000);
            btn.innerHTML = label;
        }
        setTimeout(() => { btn.innerHTML = label; btn.disabled = false; }, 1800);
    }

    // ------------------------------------------------------------
    // Démarrage
    // ------------------------------------------------------------
    async function init() {
        $('year').textContent = new Date().getFullYear();
        const lg = $('legend'), lgTitle = $('legend-title');
        lgTitle.addEventListener('click', () => lg.classList.toggle('collapsed'));
        lgTitle.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); lg.classList.toggle('collapsed'); } });
        $('author-close').addEventListener('click', () => { $('author-panel').style.display = 'none'; });

        $('sheet-toggle').addEventListener('click', () => {
            const sb = $('sidebar'), collapsed = sb.classList.toggle('collapsed');
            $('sheet-toggle').setAttribute('aria-expanded', String(!collapsed));
            $('sheet-toggle').textContent = collapsed ? '▴' : '▾';
            setTimeout(() => map.invalidateSize(), 300);
        });

        try {
            const res = await fetch('data/network.json');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            net = await res.json();
        } catch (e) {
            console.error(e);
            showError('Impossible de charger les données du réseau (data/network.json). Si vous ouvrez le fichier directement (file://), lancez un petit serveur local : « python3 -m http.server ».');
            return;
        }
        router = window.TramRouter.create(net);

        const saved = store.get('tram.basemap');
        setBasemap(saved && BASEMAPS[saved] ? saved : 'osm');
        $('basemap-select').addEventListener('change', e => setBasemap(e.target.value));

        drawNetwork();
        setupAutocomplete('start-input', 'start-list');
        setupAutocomplete('end-input', 'end-list');

        $('route-form').addEventListener('submit', e => { e.preventDefault(); calculateRoute(); });
        $('reset-btn').addEventListener('click', resetRoute);
        $('gps-btn').addEventListener('click', locateMe);
        $('download-btn').addEventListener('click', downloadPDF);
        $('swap-btn').addEventListener('click', () => {
            const a = $('start-input'), b = $('end-input');
            [a.value, b.value] = [b.value, a.value];
            if (a.value && b.value) calculateRoute();
        });

        // lien partageable : ?from=...&to=...
        const q = new URLSearchParams(location.search);
        if (q.get('from') && q.get('to')) {
            $('start-input').value = q.get('from'); $('end-input').value = q.get('to');
            calculateRoute();
        }

        // pour les tests / la console
        window.TramApp = { map, router, net, calculateRoute, getRoute: () => lastRoute, stepLayers: () => stepLayers };
    }

    init();
})();
