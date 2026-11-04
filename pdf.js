/* ============================================================
   EXPORT PDF (jsPDF, 100 % navigateur)
   ============================================================ */
(function (root) {
    'use strict';

    const NAVY = [30, 60, 114];
    const PAGE_W = 210, PAGE_H = 297, MARGIN = 15;

    function rgb(hex) { return root.StaticMap.hexToRgb(hex || '#1e3c72'); }

    function makeQr(text) {
        return new Promise(resolve => {
            if (!root.QRCode) return resolve(null);
            try {
                const box = document.createElement('div');
                box.style.cssText = 'position:fixed;left:-9999px;top:0';
                document.body.appendChild(box);
                new root.QRCode(box, { text, width: 256, height: 256, colorDark: '#1e3c72', colorLight: '#ffffff', correctLevel: root.QRCode.CorrectLevel.H });
                setTimeout(() => {
                    const c = box.querySelector('canvas');
                    const img = box.querySelector('img');
                    const url = c ? c.toDataURL('image/png') : (img && img.src && img.src.startsWith('data:') ? img.src : null);
                    document.body.removeChild(box);
                    resolve(url);
                }, 120);
            } catch (e) { console.warn('QR code', e); resolve(null); }
        });
    }

    /**
     * @param {object} route  résultat de TramRouter.findRoute
     * @param {object} opts   { start, end, map:{dataUrl,width,height} }
     */
    async function build(route, opts) {
        if (!root.jspdf || !root.jspdf.jsPDF) throw new Error('La bibliothèque PDF (jsPDF) n\'est pas chargée. Vérifiez votre connexion Internet.');
        const pdf = new root.jspdf.jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        const start = opts.start, end = opts.end;

        // ---------- en-tête ----------
        pdf.setFillColor(...NAVY); pdf.rect(0, 0, PAGE_W, 30, 'F');
        pdf.setTextColor(255, 255, 255);
        pdf.setFont('helvetica', 'bold'); pdf.setFontSize(18);
        pdf.text('Itinéraire Tramway Casablanca', MARGIN, 13);
        pdf.setFont('helvetica', 'normal'); pdf.setFontSize(11);
        pdf.text(`${start}  ->  ${end}`, MARGIN, 21);
        const now = new Date();
        pdf.setFontSize(9);
        pdf.text(now.toLocaleDateString('fr-FR') + ' ' + now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }), PAGE_W - MARGIN, 21, { align: 'right' });
        pdf.setFontSize(7); pdf.setTextColor(220, 220, 220);
        pdf.text('Mohamed AIT ABDELMALIK - MSc Geoinformatics', PAGE_W - MARGIN, 24, { align: 'right' });
        pdf.text('Geospatial Data Science | GeoAI & ML', PAGE_W - MARGIN, 27, { align: 'right' });

        // ---------- résumé ----------
        let y = 40;
        const rides = route.steps.filter(s => s.type === 'ride');
        pdf.setTextColor(0, 0, 0); pdf.setFont('helvetica', 'bold'); pdf.setFontSize(12);
        if (route.type === 'direct') pdf.text(`Trajet direct - Ligne ${rides[0].line}`, MARGIN, y);
        else pdf.text(`Itinéraire avec ${route.num_transfers} correspondance(s)`, MARGIN, y);
        y += 7;
        pdf.setFont('helvetica', 'normal'); pdf.setFontSize(10);
        pdf.text(`Temps: ${Math.round(route.total_time)} min  |  Distance: ${route.total_distance_km.toFixed(2)} km  |  Stations: ${route.total_stations}`, MARGIN, y);
        y += 8;

        // ---------- carte ----------
        const imgW = PAGE_W - 2 * MARGIN;
        if (opts.map) {
            const imgH = opts.map.height / opts.map.width * imgW;
            pdf.addImage(opts.map.dataUrl, 'JPEG', MARGIN, y, imgW, imgH);
            pdf.setDrawColor(200, 205, 215); pdf.rect(MARGIN, y, imgW, imgH);
            y += imgH + 8;
        }

        // ---------- aperçu des étapes (page 1) ----------
        pdf.setFont('helvetica', 'bold'); pdf.setFontSize(11); pdf.setTextColor(...NAVY);
        pdf.text('Aperçu', MARGIN, y); y += 6;
        route.steps.forEach(step => {
            if (y > PAGE_H - 22) return;
            if (step.type === 'ride') {
                pdf.setFillColor(...rgb(step.line_color)); pdf.roundedRect(MARGIN, y - 4.5, 14, 6.5, 1, 1, 'F');
                pdf.setTextColor(255, 255, 255); pdf.setFontSize(8.5); pdf.setFont('helvetica', 'bold');
                pdf.text(step.line, MARGIN + 7, y, { align: 'center' });
                pdf.setTextColor(30, 30, 30); pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9.5);
                pdf.text(`${step.from}  ->  ${step.to}   (${step.num_stations} stations, ${Math.round(step.travel_time_min)} min)`, MARGIN + 18, y);
            } else {
                pdf.setTextColor(214, 120, 0); pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9);
                pdf.text(`Correspondance à pied : ${step.from_station} -> ${step.to_station} (${step.walk_time} min)`, MARGIN + 18, y);
            }
            y += 7;
        });

        // ---------- détails ----------
        pdf.addPage(); y = 20;
        pdf.setFontSize(14); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(...NAVY);
        pdf.text('Détails de l\'itinéraire', MARGIN, y); y += 13;

        let n = 1;
        for (const step of route.steps) {
            if (step.type === 'ride') {
                if (y > PAGE_H - 50) { pdf.addPage(); y = 20; }
                pdf.setFillColor(...rgb(step.line_color)); pdf.rect(MARGIN, y - 5, 15, 7, 'F');
                pdf.setTextColor(255, 255, 255); pdf.setFontSize(9); pdf.setFont('helvetica', 'bold');
                pdf.text(step.line, MARGIN + 7.5, y, { align: 'center' });
                pdf.setTextColor(0, 0, 0); pdf.setFontSize(10);
                pdf.text(`Etape ${n} : ${step.from} -> ${step.to}`, MARGIN + 20, y); y += 6;
                pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9); pdf.setTextColor(80, 80, 80);
                pdf.text(`${Math.round(step.travel_time_min)} min  |  ${step.num_stations} stations  |  ${step.distance_km.toFixed(2)} km`, MARGIN + 20, y); y += 8;
                pdf.setTextColor(50, 50, 50);
                step.stations.forEach((s, j) => {
                    if (y > PAGE_H - 15) { pdf.addPage(); y = 20; }
                    if (j === 0) pdf.setFillColor(76, 175, 80);
                    else if (j === step.stations.length - 1) pdf.setFillColor(244, 67, 54);
                    else pdf.setFillColor(150, 150, 150);
                    pdf.circle(MARGIN + 22, y - 1, 1.2, 'F');
                    pdf.text(`${j + 1}. ${s.name}`, MARGIN + 26, y); y += 5;
                });
                y += 6; n++;
            } else {
                if (y > PAGE_H - 20) { pdf.addPage(); y = 20; }
                pdf.setFillColor(255, 243, 224); pdf.rect(MARGIN, y - 4, PAGE_W - 2 * MARGIN, 12, 'F');
                pdf.setTextColor(230, 126, 34); pdf.setFont('helvetica', 'bold'); pdf.setFontSize(10);
                pdf.text(`Correspondance : ${step.from_station} -> ${step.to_station}`, MARGIN + 3, y + 2);
                pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9); pdf.setTextColor(120, 120, 120);
                pdf.text(`Marche : ${step.walk_time} min`, MARGIN + 3, y + 8);
                y += 16;
            }
        }

        // ---------- page auteur ----------
        pdf.addPage();
        pdf.setFillColor(...NAVY); pdf.rect(0, 0, PAGE_W, 40, 'F');
        pdf.setTextColor(255, 255, 255); pdf.setFontSize(20); pdf.setFont('helvetica', 'bold');
        pdf.text('À propos de l\'auteur', MARGIN, 20);
        pdf.setFontSize(10); pdf.setFont('helvetica', 'normal');
        pdf.text('Informations de contact et liens professionnels', MARGIN, 30);

        pdf.setFillColor(56, 239, 125); pdf.circle(MARGIN + 15, 60, 12, 'F');
        pdf.setTextColor(255, 255, 255); pdf.setFontSize(14); pdf.setFont('helvetica', 'bold');
        pdf.text('MA', MARGIN + 15, 62, { align: 'center' });

        pdf.setTextColor(...NAVY); pdf.setFontSize(16);
        pdf.text('Mohamed AIT ABDELMALIK', MARGIN + 32, 55);
        pdf.setTextColor(80, 80, 80); pdf.setFontSize(10); pdf.setFont('helvetica', 'normal');
        ['MSc Geoinformatics @UH2C', 'Geospatial Data Science | GeoAI & ML', 'GIS & Remote Sensing | Geospatial Computing', 'Spatial Intelligence']
            .forEach((t, i) => pdf.text(t, MARGIN + 32, 62 + i * 6));
        pdf.setTextColor(100, 100, 100); pdf.text('Casablanca Metropolitan Area', MARGIN + 32, 87);

        let cy = 105;
        pdf.setFontSize(14); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(...NAVY);
        pdf.text('Contact', MARGIN, cy); cy += 8;
        pdf.setFontSize(11); pdf.setFont('helvetica', 'normal'); pdf.setTextColor(0, 0, 0);
        pdf.text('Email      :  mohamed.aitabdelmalik@gmail.com', MARGIN, cy); cy += 7;
        pdf.text('Téléphone  :  +212 6 51853618', MARGIN, cy); cy += 7;
        pdf.text('Localisation: Casablanca Metropolitan Area', MARGIN, cy); cy += 15;

        pdf.setFontSize(14); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(...NAVY);
        pdf.text('Réseaux sociaux & Portfolio', MARGIN, cy); cy += 10;
        pdf.setFontSize(10); pdf.setFont('helvetica', 'normal');
        [
            ['LinkedIn', [0, 119, 181], [255, 255, 255], 'linkedin.com/in/mohamed-ait-abdelmalik-a7b468195'],
            ['GitHub', [51, 51, 51], [255, 255, 255], 'github.com/mohamed-aitabdelmalik'],
            ['Twitter/X', [0, 0, 0], [255, 255, 255], 'x.com/MoAitAbdelmalik'],
            ['Portfolio', [56, 239, 125], NAVY, 'mohamed-ait-abdelmalik.site'],
        ].forEach(([label, bg, fg, url]) => {
            pdf.setFillColor(...bg); pdf.rect(MARGIN, cy - 5, 30, 7, 'F');
            pdf.setTextColor(...fg); pdf.text(label, MARGIN + 2, cy);
            pdf.setTextColor(0, 0, 0); pdf.text(url, MARGIN + 35, cy);
            cy += 12;
        });
        cy += 8;

        const qr = await makeQr('https://mohamed-ait-abdelmalik.site/');
        if (qr) {
            pdf.setFontSize(14); pdf.setFont('helvetica', 'bold'); pdf.setTextColor(...NAVY);
            pdf.text('Scanner pour visiter le portfolio', MARGIN, cy); cy += 5;
            pdf.addImage(qr, 'PNG', MARGIN, cy, 40, 40);
            pdf.setFontSize(9); pdf.setFont('helvetica', 'normal'); pdf.setTextColor(80, 80, 80);
            ['Scannez ce QR code avec', 'votre téléphone pour', 'découvrir mon portfolio.'].forEach((t, i) => pdf.text(t, MARGIN + 45, cy + 12 + i * 6));
        }

        // ---------- pieds de page ----------
        const pages = pdf.internal.getNumberOfPages();
        for (let i = 1; i <= pages; i++) {
            pdf.setPage(i);
            pdf.setFillColor(...NAVY); pdf.rect(0, PAGE_H - 10, PAGE_W, 10, 'F');
            pdf.setTextColor(255, 255, 255); pdf.setFontSize(8); pdf.setFont('helvetica', 'normal');
            pdf.text(`Tramway Casablanca © ${now.getFullYear()}  -  Mohamed AIT ABDELMALIK  -  Page ${i}/${pages}`, PAGE_W / 2, PAGE_H - 4, { align: 'center' });
        }
        return pdf;
    }

    root.TramPdf = { build };
})(typeof self !== 'undefined' ? self : this);
