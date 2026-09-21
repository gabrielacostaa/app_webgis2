/**
 * MOVMASSA WebGIS - Visualizador 3D de Terreno e Ocorrências
 * Engine: MapLibre GL JS (latest) + DEM Terrain
 */
(function () {
    "use strict";

    let map3d = null;
    let markers3D = [];
    let mapInitialized = false;

    // Wait for DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }

    function setup() {
        const modal3D = document.getElementById("modal3DView");
        if (!modal3D) return;

        modal3D.addEventListener("shown.bs.modal", function () {
            const container = document.getElementById("cesiumContainer");
            if (!container) return;

            if (!mapInitialized) {
                // Small delay to ensure the modal is fully visible and container has dimensions
                setTimeout(function () {
                    initMap(container);
                }, 400);
            } else if (map3d) {
                map3d.resize();
            }
        });

        // Setup action buttons (even before map init)
        var btnFlyTo = document.getElementById("btn3DFlyToAngra");
        if (btnFlyTo) btnFlyTo.addEventListener("click", flyToAngra);

        var btnTilt = document.getElementById("btn3DTiltOrbit");
        if (btnTilt) btnTilt.addEventListener("click", orbit3D);

        var btnRefresh = document.getElementById("btn3DRefresh");
        if (btnRefresh) btnRefresh.addEventListener("click", loadOccurrences);
    }

    function initMap(container) {
        // Prevent double init
        if (mapInitialized) return;
        mapInitialized = true;

        // Check MapLibre availability
        if (typeof maplibregl === "undefined") {
            showError(container, "MapLibre GL JS não foi carregado. Verifique sua conexão com a internet.");
            mapInitialized = false;
            return;
        }

        // Check WebGL support
        var canvas = document.createElement("canvas");
        var gl = canvas.getContext("webgl2") || canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
        if (!gl) {
            showError(container, "Seu navegador não suporta WebGL. Ative a aceleração de hardware nas configurações.");
            mapInitialized = false;
            return;
        }

        // Show loading
        container.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;background:#0f172a;color:#fff;">' +
            '<div class="spinner-border text-info mb-3" role="status"></div>' +
            '<p class="fw-semibold mb-1">Inicializando Mapa 3D...</p>' +
            '<p class="small text-muted">Carregando imagens de satélite e elevação</p>' +
            '</div>';

        try {
            // Create map with ONLY satellite tiles (no terrain in style)
            map3d = new maplibregl.Map({
                container: container,
                style: {
                    version: 8,
                    sources: {
                        "satellite": {
                            type: "raster",
                            tiles: [
                                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                            ],
                            tileSize: 256,
                            maxzoom: 18,
                            attribution: "Esri Satellite"
                        }
                    },
                    layers: [
                        {
                            id: "satellite",
                            type: "raster",
                            source: "satellite"
                        }
                    ]
                },
                center: [-44.3181, -23.0067],
                zoom: 13,
                pitch: 60,
                bearing: 25,
                maxPitch: 85
            });

            // Add controls
            map3d.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-left");
            map3d.addControl(new maplibregl.ScaleControl({ maxWidth: 200 }), "bottom-right");

            // On map load - add terrain and occurrences
            map3d.on("load", function () {
                console.log("[MOVMASSA 3D] Mapa carregado com sucesso");

                // Try to add 3D terrain
                addTerrain();

                // Load occurrences
                loadOccurrences();
            });

            map3d.on("error", function (e) {
                console.warn("[MOVMASSA 3D] Map error:", e.error ? e.error.message : e);
            });

        } catch (err) {
            console.error("[MOVMASSA 3D] Init error:", err);
            showError(container, "Erro ao criar o mapa: " + (err.message || String(err)));
            mapInitialized = false;
        }
    }

    function addTerrain() {
        if (!map3d) return;

        try {
            // Use MapLibre's official demo terrain tiles (reliable, free, no auth)
            map3d.addSource("demTerrain", {
                type: "raster-dem",
                tiles: [
                    "https://demotiles.maplibre.org/terrain-tiles/{z}/{x}/{y}.png"
                ],
                tileSize: 256
            });

            map3d.setTerrain({
                source: "demTerrain",
                exaggeration: 1.5
            });

            console.log("[MOVMASSA 3D] Terreno 3D ativado com sucesso");
        } catch (e) {
            console.warn("[MOVMASSA 3D] Terreno 3D indisponível (mapa continua plano):", e.message || e);

            // Fallback: try AWS Terrarium tiles
            try {
                map3d.addSource("demTerrain2", {
                    type: "raster-dem",
                    tiles: [
                        "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
                    ],
                    tileSize: 256,
                    encoding: "terrarium"
                });

                map3d.setTerrain({
                    source: "demTerrain2",
                    exaggeration: 1.5
                });
                console.log("[MOVMASSA 3D] Terreno 3D (fallback AWS) ativado");
            } catch (e2) {
                console.warn("[MOVMASSA 3D] Terreno fallback também falhou:", e2.message || e2);
            }
        }
    }

    function showError(container, msg) {
        container.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;background:#0f172a;color:#fff;padding:2rem;text-align:center;">' +
            '<i class="bi bi-exclamation-triangle-fill text-warning" style="font-size:3rem;margin-bottom:1rem;"></i>' +
            '<h5 class="fw-bold">Erro no Mapa 3D</h5>' +
            '<p class="text-muted small">' + msg + '</p>' +
            '<button class="btn btn-outline-info btn-sm mt-2" onclick="location.reload()">Recarregar Página</button>' +
            '</div>';
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
        map3d.easeTo({
            bearing: map3d.getBearing() + 45,
            pitch: 65,
            duration: 1500
        });
    }

    function createMarkerEl() {
        var el = document.createElement("div");
        el.style.cssText = "width:32px;height:32px;border-radius:50%;background:#0284c7;border:3px solid #fff;box-shadow:0 4px 12px rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;color:#fff;cursor:pointer;font-size:16px;transition:transform .2s;";
        el.innerHTML = '<i class="bi bi-geo-alt-fill"></i>';
        el.onmouseenter = function () { el.style.transform = "scale(1.3)"; };
        el.onmouseleave = function () { el.style.transform = "scale(1)"; };
        return el;
    }

    function loadOccurrences() {
        if (!map3d) return;

        // Clear previous
        for (var i = 0; i < markers3D.length; i++) {
            markers3D[i].remove();
        }
        markers3D = [];

        var spinner = document.getElementById("status3DLoading");
        if (spinner) spinner.style.display = "inline-block";

        fetch("/api/occurrences")
            .then(function (res) {
                if (!res.ok) throw new Error("HTTP " + res.status);
                return res.json();
            })
            .then(function (data) {
                if (!data || !data.features) return;

                console.log("[MOVMASSA 3D]", data.features.length, "ocorrências carregadas");

                for (var i = 0; i < data.features.length; i++) {
                    var feat = data.features[i];
                    if (!feat.geometry || !feat.geometry.coordinates) continue;

                    var lng = parseFloat(feat.geometry.coordinates[0]);
                    var lat = parseFloat(feat.geometry.coordinates[1]);
                    if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) continue;

                    var p = feat.properties || {};

                    var html = '<div style="font-family:sans-serif;font-size:12px;max-width:300px;">' +
                        '<div style="background:#0284c7;color:#fff;padding:6px 10px;border-radius:6px;margin-bottom:8px;font-weight:bold;">📍 ' + (p.title || "Ocorrência") + '</div>' +
                        '<div style="margin-bottom:6px;"><span style="background:#ef4444;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;">' + (p.tipologia || "Deslizamento") + '</span></div>' +
                        '<p style="margin:4px 0;font-size:11px;color:#555;">' + (p.description || "Sem descrição.") + '</p>' +
                        '<div style="background:#f8f9fa;border:1px solid #ddd;border-radius:6px;padding:6px;font-size:10px;">' +
                        '<div><b>Responsável:</b> ' + (p.responsavel_nome || "N/A") + '</div>' +
                        '<div><b>Município:</b> ' + (p.municipio || "N/A") + ' - ' + (p.uf || "RJ") + '</div>' +
                        (p.data_evento ? '<div><b>Data:</b> ' + p.data_evento + '</div>' : '') +
                        '</div>';

                    if (p.media_urls && p.media_urls.length > 0) {
                        html += '<div style="margin-top:8px;"><b>📸 Mídias (' + p.media_urls.length + '):</b><br>';
                        for (var j = 0; j < Math.min(p.media_urls.length, 3); j++) {
                            var url = p.media_urls[j];
                            if (url.match(/\.(mp4|mov)$/i)) {
                                html += '<video src="' + url + '" controls style="width:100%;max-height:120px;border-radius:4px;margin-top:4px;"></video>';
                            } else {
                                html += '<img src="' + url + '" style="width:100%;max-height:120px;object-fit:cover;border-radius:4px;margin-top:4px;" />';
                            }
                        }
                        html += '</div>';
                    }

                    html += '<div style="margin-top:8px;"><a href="/api/occurrence/' + (p.id || 0) + '/pdf" target="_blank" style="display:block;text-align:center;background:#2563eb;color:#fff;text-decoration:none;padding:6px;border-radius:6px;font-weight:bold;font-size:11px;">📄 Relatório PDF</a></div>';
                    html += '</div>';

                    var popup = new maplibregl.Popup({ offset: 20, maxWidth: "320px" }).setHTML(html);
                    var marker = new maplibregl.Marker({ element: createMarkerEl() })
                        .setLngLat([lng, lat])
                        .setPopup(popup)
                        .addTo(map3d);

                    markers3D.push(marker);
                }
            })
            .catch(function (err) {
                console.error("[MOVMASSA 3D] Erro ao carregar ocorrências:", err);
            })
            .finally(function () {
                if (spinner) spinner.style.display = "none";
            });
    }

})();
