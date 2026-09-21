/**
 * MOVMASSA WebGIS - Visualizador 3D de Terreno e Ocorrências
 * Engine: MapLibre GL JS v4.7.1 com Terreno DEM 3D
 */
(function () {
    "use strict";

    var map3d = null;
    var markers3D = [];
    var mapInitialized = false;

    function init() {
        var modal3D = document.getElementById("modal3DView");
        if (!modal3D) return;

        // Ao abrir o modal, inicializar ou redimensionar o mapa 3D
        modal3D.addEventListener("shown.bs.modal", function () {
            if (!mapInitialized) {
                init3DMap();
            } else if (map3d) {
                map3d.resize();
            }
        });

        // Botões de ação
        var btnFlyTo = document.getElementById("btn3DFlyToAngra");
        if (btnFlyTo) {
            btnFlyTo.addEventListener("click", function () {
                if (!map3d) return;
                map3d.flyTo({
                    center: [-44.3181, -23.0067],
                    zoom: 13.5,
                    pitch: 60,
                    bearing: 25,
                    duration: 2500
                });
            });
        }

        var btnTilt = document.getElementById("btn3DTiltOrbit");
        if (btnTilt) {
            btnTilt.addEventListener("click", function () {
                if (!map3d) return;
                map3d.easeTo({
                    bearing: map3d.getBearing() + 45,
                    pitch: 65,
                    duration: 1500
                });
            });
        }

        var btnRefresh = document.getElementById("btn3DRefresh");
        if (btnRefresh) {
            btnRefresh.addEventListener("click", function () {
                load3DOccurrences();
            });
        }
    }

    function init3DMap() {
        var container = document.getElementById("map3dContainer");
        var overlay = document.getElementById("map3dOverlayLoading");
        if (!container) return;

        if (typeof maplibregl === "undefined") {
            if (overlay) {
                overlay.innerHTML = '<div class="text-center p-4"><i class="bi bi-exclamation-triangle-fill text-warning fs-1 mb-3"></i><h5 class="fw-bold">Falha ao carregar biblioteca MapLibre GL</h5><p class="text-muted small">Verifique sua conexão e tente novamente.</p></div>';
            }
            return;
        }

        try {
            mapInitialized = true;

            map3d = new maplibregl.Map({
                container: "map3dContainer",
                style: {
                    version: 8,
                    sources: {
                        "esri-satellite": {
                            type: "raster",
                            tiles: [
                                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                            ],
                            tileSize: 256,
                            maxzoom: 19,
                            attribution: "Esri Satellite Imagery"
                        }
                    },
                    layers: [
                        {
                            id: "esri-satellite-layer",
                            type: "raster",
                            source: "esri-satellite",
                            minzoom: 0,
                            maxzoom: 19
                        }
                    ]
                },
                center: [-44.3181, -23.0067], // Angra dos Reis
                zoom: 13,
                pitch: 60, // Inclinação 3D
                bearing: 25,
                maxPitch: 85,
                antialias: true
            });

            // Controles de Navegação 3D
            map3d.addControl(new maplibregl.NavigationControl({
                visualizePitch: true,
                showZoom: true,
                showCompass: true
            }), "top-left");

            map3d.addControl(new maplibregl.ScaleControl({ maxWidth: 200 }), "bottom-right");

            map3d.on("load", function () {
                console.log("[MOVMASSA 3D] Mapa inicializado com sucesso.");

                // Adicionar relevo 3D (DEM)
                try {
                    map3d.addSource("terrain-dem", {
                        type: "raster-dem",
                        url: "https://demotiles.maplibre.org/terrain-tiles/tiles.json",
                        tileSize: 256
                    });

                    map3d.setTerrain({
                        source: "terrain-dem",
                        exaggeration: 1.5
                    });
                    console.log("[MOVMASSA 3D] Terreno 3D ativado.");
                } catch (tErr) {
                    console.warn("[MOVMASSA 3D] Terreno DEM não ativado:", tErr);
                }

                // Ocultar overlay de carregamento
                if (overlay) {
                    overlay.style.opacity = "0";
                    setTimeout(function () {
                        overlay.style.display = "none";
                    }, 400);
                }

                // Carregar ocorrências
                load3DOccurrences();
            });

            map3d.on("error", function (e) {
                console.warn("[MOVMASSA 3D] Erro no mapa:", e);
            });

        } catch (err) {
            console.error("[MOVMASSA 3D] Erro ao instanciar mapa:", err);
            if (overlay) {
                overlay.innerHTML = '<div class="text-center p-4"><i class="bi bi-exclamation-triangle-fill text-warning fs-1 mb-3"></i><h5 class="fw-bold">Erro ao abrir visualizador 3D</h5><p class="text-danger small">' + (err.message || err) + '</p></div>';
            }
            mapInitialized = false;
        }
    }

    function createMarkerPin() {
        var el = document.createElement("div");
        el.className = "marker-3d-pin";
        el.style.width = "34px";
        el.style.height = "34px";
        el.style.borderRadius = "50%";
        el.style.backgroundColor = "#ef4444";
        el.style.border = "3px solid #ffffff";
        el.style.boxShadow = "0 6px 16px rgba(0, 0, 0, 0.6)";
        el.style.display = "flex";
        el.style.alignItems = "center";
        el.style.justifyContent = "center";
        el.style.color = "#ffffff";
        el.style.cursor = "pointer";
        el.style.fontSize = "17px";
        el.style.transition = "transform 0.2s ease";

        el.innerHTML = '<i class="bi bi-geo-alt-fill"></i>';

        el.addEventListener("mouseenter", function () {
            el.style.transform = "scale(1.25)";
        });
        el.addEventListener("mouseleave", function () {
            el.style.transform = "scale(1.0)";
        });

        return el;
    }

    function load3DOccurrences() {
        if (!map3d) return;

        // Limpar marcadores anteriores
        for (var i = 0; i < markers3D.length; i++) {
            markers3D[i].remove();
        }
        markers3D = [];

        var statusSpan = document.getElementById("status3DLoading");
        if (statusSpan) statusSpan.style.display = "inline-block";

        fetch("/api/occurrences")
            .then(function (res) {
                if (!res.ok) throw new Error("Status HTTP " + res.status);
                return res.json();
            })
            .then(function (geoJsonData) {
                if (!geoJsonData || !geoJsonData.features) return;

                console.log("[MOVMASSA 3D] " + geoJsonData.features.length + " pontos carregados.");

                geoJsonData.features.forEach(function (feat) {
                    var coords = feat.geometry ? feat.geometry.coordinates : null;
                    if (!coords || coords.length < 2) return;

                    var lng = parseFloat(coords[0]);
                    var lat = parseFloat(coords[1]);
                    var props = feat.properties || {};

                    if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

                    var mediaHtml = "";
                    if (props.media_urls && props.media_urls.length > 0) {
                        mediaHtml += '<div style="margin-top:10px;"><strong>📸 Mídias Registradas (' + props.media_urls.length + '):</strong><br><div style="display:flex; flex-direction:column; gap:6px; margin-top:4px;">';
                        props.media_urls.forEach(function (url) {
                            if (url.toLowerCase().indexOf(".mp4") !== -1 || url.toLowerCase().indexOf(".mov") !== -1) {
                                mediaHtml += '<video src="' + url + '" controls style="width:100%; max-height:150px; border-radius:6px;"></video>';
                            } else {
                                mediaHtml += '<a href="' + url + '" target="_blank"><img src="' + url + '" style="width:100%; max-height:150px; object-fit:cover; border-radius:6px;" /></a>';
                            }
                        });
                        mediaHtml += '</div></div>';
                    }

                    var popupHtml = '' +
                        '<div style="font-family: \'Plus Jakarta Sans\', sans-serif; font-size:12px; color:#1e293b; max-width:320px; padding:2px;">' +
                        '  <div style="background:#0284c7; color:#ffffff; padding:6px 10px; border-radius:6px; margin-bottom:8px; font-weight:bold;">' +
                        '    📍 ' + (props.title || 'Ocorrência Aprovada') +
                        '  </div>' +
                        '  <div style="margin-bottom:6px;">' +
                        '    <span style="background:#ef4444; color:#fff; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">' +
                        '      ' + (props.tipologia || 'Deslizamento de Encosta') +
                        '    </span>' +
                        '    <span style="background:#f1f5f9; color:#334155; padding:2px 6px; border-radius:4px; font-size:10px; border:1px solid #cbd5e1; margin-left:4px;">' +
                        '      ' + (props.municipio || 'Angra dos Reis') + ' - ' + (props.uf || 'RJ') +
                        '    </span>' +
                        '  </div>' +
                        '  <p style="margin:6px 0; font-size:11px; color:#475569;">' +
                        '    ' + (props.description || 'Sem descrição complementar.') +
                        '  </p>' +
                        '  <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px; margin-top:6px; font-size:10px;">' +
                        '    <div><strong>📋 Responsável:</strong> ' + (props.responsavel_nome || 'Defesa Civil') + '</div>' +
                        '    <div><strong>Esfera:</strong> ' + (props.responsavel_nivel || 'Geral') + '</div>' +
                        '    <div><strong>CPF:</strong> ' + (props.responsavel_cpf || 'N/A') + ' | <strong>Matrícula:</strong> ' + (props.responsavel_matricula || 'N/A') + '</div>' +
                        (props.data_evento ? '<div><strong>Data Evento:</strong> ' + props.data_evento + '</div>' : '') +
                        '  </div>' +
                        mediaHtml +
                        '  <div style="margin-top:10px;">' +
                        '    <a href="/api/occurrence/' + props.id + '/pdf" target="_blank" style="display:block; text-align:center; background:#2563eb; color:#fff; text-decoration:none; padding:6px; border-radius:6px; font-weight:bold; font-size:11px;">' +
                        '      📄 Abrir Relatório PDF' +
                        '    </a>' +
                        '  </div>' +
                        '</div>';

                    var popup = new maplibregl.Popup({ offset: 25, maxWidth: "340px" }).setHTML(popupHtml);
                    var el = createMarkerPin();

                    var marker = new maplibregl.Marker({ element: el })
                        .setLngLat([lng, lat])
                        .setPopup(popup)
                        .addTo(map3d);

                    markers3D.push(marker);
                });
            })
            .catch(function (err) {
                console.error("[MOVMASSA 3D] Erro ao buscar ocorrências:", err);
            })
            .finally(function () {
                if (statusSpan) statusSpan.style.display = "none";
            });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
