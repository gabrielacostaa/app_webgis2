/**
 * MOVMASSA WebGIS - Visualizador 3D de Terreno e Ocorrências (MapLibre GL 3D)
 */
document.addEventListener("DOMContentLoaded", function () {
    let map3d = null;
    let markers3D = [];
    const modal3D = document.getElementById("modal3DView");

    if (!modal3D) return;

    modal3D.addEventListener("shown.bs.modal", function () {
        if (!map3d) {
            initMapLibre3DViewer();
        } else {
            setTimeout(() => {
                map3d.resize();
            }, 200);
        }
    });

    function initMapLibre3DViewer() {
        const container = document.getElementById("cesiumContainer");
        if (!container) return;

        try {
            // Estilo do Mapa 3D: Satélite Esri + Terreno 3D Terrarium (Elevação de Relevo)
            const mapStyle = {
                version: 8,
                sources: {
                    "esri-satellite": {
                        type: "raster",
                        tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
                        tileSize: 256,
                        attribution: "Esri World Imagery"
                    },
                    "terrain-dem": {
                        type: "raster-dem",
                        tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
                        tileSize: 256,
                        encoding: "terrarium"
                    }
                },
                layers: [
                    {
                        id: "satellite-layer",
                        type: "raster",
                        source: "esri-satellite",
                        minzoom: 0,
                        maxzoom: 19
                    }
                ],
                terrain: {
                    source: "terrain-dem",
                    exaggeration: 1.5
                }
            };

            map3d = new maplibregl.Map({
                container: "cesiumContainer",
                style: mapStyle,
                center: [-44.3181, -23.0067], // Angra dos Reis
                zoom: 13,
                pitch: 60, // Inclinação 3D de 60 graus
                bearing: 25, // Rotação inicial 3D
                maxPitch: 85,
                antialias: true
            });

            // Adicionar controles de navegação 3D (Bússola e Zoom)
            map3d.addControl(new maplibregl.NavigationControl({
                visualizePitch: true,
                showZoom: true,
                showCompass: true
            }), 'top-left');

            map3d.on('load', function () {
                load3DOccurrences();
            });

            // Configurar botões de ação do Modal 3D
            const btnFlyTo = document.getElementById("btn3DFlyToAngra");
            if (btnFlyTo) btnFlyTo.onclick = flyToAngra;

            const btnTilt = document.getElementById("btn3DTiltOrbit");
            if (btnTilt) btnTilt.onclick = orbit3D;

            const btnRefresh = document.getElementById("btn3DRefresh");
            if (btnRefresh) btnRefresh.onclick = load3DOccurrences;

        } catch (err) {
            console.error("Erro ao inicializar MapLibre 3D:", err);
            container.innerHTML = `
                <div class="d-flex flex-column align-items-center justify-content-center h-100 text-white p-4 text-center" style="background:#0f172a;">
                    <i class="bi bi-exclamation-triangle-fill text-warning fs-1 mb-3"></i>
                    <h5 class="fw-bold">Não foi possível carregar o mapa 3D neste navegador</h5>
                    <p class="text-muted small mb-0">Verifique se a aceleração de hardware (WebGL) está ativada nas configurações do seu navegador.</p>
                    <p class="text-danger small mt-2">Erro: ${err.message || err}</p>
                </div>
            `;
        }
    }

    function flyToAngra() {
        if (!map3d) return;
        map3d.flyTo({
            center: [-44.3181, -23.0067],
            zoom: 13.5,
            pitch: 60,
            bearing: 25,
            duration: 2500
        });
    }

    function orbit3D() {
        if (!map3d) return;
        const currentBearing = map3d.getBearing();
        map3d.easeTo({
            bearing: currentBearing + 45,
            pitch: 65,
            duration: 1500
        });
    }

    function create3DMarkerElement() {
        const el = document.createElement('div');
        el.className = 'marker-3d-pin';
        el.style.width = '36px';
        el.style.height = '36px';
        el.style.borderRadius = '50%';
        el.style.backgroundColor = '#0284c7';
        el.style.border = '3px solid #ffffff';
        el.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.6)';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.color = '#ffffff';
        el.style.cursor = 'pointer';
        el.style.fontSize = '18px';
        el.style.transition = 'transform 0.2s ease-in-out';

        el.innerHTML = '<i class="bi bi-geo-alt-fill"></i>';

        el.addEventListener('mouseenter', () => {
            el.style.transform = 'scale(1.25)';
        });
        el.addEventListener('mouseleave', () => {
            el.style.transform = 'scale(1.0)';
        });

        return el;
    }

    function load3DOccurrences() {
        if (!map3d) return;

        // Limpar marcadores anteriores
        markers3D.forEach(m => m.remove());
        markers3D = [];

        const statusSpan = document.getElementById("status3DLoading");
        if (statusSpan) statusSpan.style.display = "inline-block";

        fetch("/api/occurrences")
            .then(res => res.json())
            .then(geoJsonData => {
                if (!geoJsonData || !geoJsonData.features) return;

                geoJsonData.features.forEach(feat => {
                    const coords = feat.geometry ? feat.geometry.coordinates : null;
                    if (!coords || coords.length < 2) return;

                    const lng = parseFloat(coords[0]);
                    const lat = parseFloat(coords[1]);
                    const props = feat.properties || {};

                    if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

                    let mediaHtml = "";
                    if (props.media_urls && props.media_urls.length > 0) {
                        mediaHtml += `<div style="margin-top:10px;"><strong>📸 Mídias Registradas (${props.media_urls.length}):</strong><br><div style="display:flex; flex-direction:column; gap:6px; margin-top:4px;">`;
                        props.media_urls.forEach(url => {
                            if (url.toLowerCase().endsWith(".mp4") || url.toLowerCase().endsWith(".mov")) {
                                mediaHtml += `<video src="${url}" controls style="width:100%; max-height:160px; border-radius:6px;"></video>`;
                            } else {
                                mediaHtml += `<a href="${url}" target="_blank"><img src="${url}" style="width:100%; max-height:160px; object-fit:cover; border-radius:6px;" /></a>`;
                            }
                        });
                        mediaHtml += `</div></div>`;
                    }

                    const popupHtml = `
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size:12px; color:#1e293b; max-width:320px; padding:2px;">
                            <div style="background:#0284c7; color:#ffffff; padding:6px 10px; border-radius:6px; margin-bottom:8px; font-weight:bold;">
                                📍 ${props.title || 'Ocorrência Aprovada'}
                            </div>
                            <div style="margin-bottom:6px;">
                                <span style="background:#ef4444; color:#fff; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">
                                    ${props.tipologia || 'Deslizamento de Encosta'}
                                </span>
                                <span style="background:#f1f5f9; color:#334155; padding:2px 6px; border-radius:4px; font-size:10px; border:1px solid #cbd5e1; margin-left:4px;">
                                    ${props.municipio || 'Angra dos Reis'} - ${props.uf || 'RJ'}
                                </span>
                            </div>
                            <p style="margin:6px 0; font-size:11px; color:#475569;">
                                ${props.description || 'Sem descrição complementar.'}
                            </p>
                            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px; margin-top:6px; font-size:10px;">
                                <div><strong>📋 Responsável Técnico:</strong> ${props.responsavel_nome || 'Defesa Civil'}</div>
                                <div><strong>Esfera:</strong> ${props.responsavel_nivel || 'Geral'}</div>
                                <div><strong>CPF:</strong> ${props.responsavel_cpf || 'N/A'} | <strong>Matrícula:</strong> ${props.responsavel_matricula || 'N/A'}</div>
                                ${props.data_evento ? `<div><strong>Data Evento:</strong> ${props.data_evento}</div>` : ''}
                            </div>
                            ${mediaHtml}
                            <div style="margin-top:10px;">
                                <a href="/api/occurrence/${props.id}/pdf" target="_blank" style="display:block; text-align:center; background:#2563eb; color:#fff; text-decoration:none; padding:6px; border-radius:6px; font-weight:bold; font-size:11px;">
                                    📄 Abrir Relatório PDF
                                </a>
                            </div>
                        </div>
                    `;

                    const popup = new maplibregl.Popup({ offset: 25, maxWidth: '340px' }).setHTML(popupHtml);
                    const el = create3DMarkerElement();

                    const marker = new maplibregl.Marker({ element: el })
                        .setLngLat([lng, lat])
                        .setPopup(popup)
                        .addTo(map3d);

                    markers3D.push(marker);
                });
            })
            .catch(err => console.error("Erro ao carregar pontos 3D:", err))
            .finally(() => {
                if (statusSpan) statusSpan.style.display = "none";
            });
    }
});
