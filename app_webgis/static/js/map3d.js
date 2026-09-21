/**
 * MOVMASSA WebGIS - Visualizador 3D de Ocorrências e Terreno (CesiumJS)
 */
document.addEventListener("DOMContentLoaded", function () {
    let cesiumViewer = null;
    let occurrencesDataSource = null;
    const modal3D = document.getElementById("modal3DView");

    if (!modal3D) return;

    modal3D.addEventListener("shown.bs.modal", function () {
        if (!cesiumViewer) {
            initCesium3DViewer();
        } else {
            try {
                cesiumViewer.resize();
            } catch(e) {
                console.log("Resize error:", e);
            }
        }
    });

    function createPinDataUrl(colorHex) {
        const canvas = document.createElement("canvas");
        canvas.width = 48;
        canvas.height = 64;
        const ctx = canvas.getContext("2d");

        // Desenhar pino estilo gota GPS 3D
        ctx.beginPath();
        ctx.arc(24, 22, 18, Math.PI * 0.8, Math.PI * 0.2, false);
        ctx.lineTo(24, 60);
        ctx.closePath();

        ctx.fillStyle = colorHex;
        ctx.shadowColor = "rgba(0,0,0,0.5)";
        ctx.shadowBlur = 8;
        ctx.shadowOffsetY = 4;
        ctx.fill();

        ctx.lineWidth = 3;
        ctx.strokeStyle = "#FFFFFF";
        ctx.stroke();

        // Círculo interno branco
        ctx.shadowBlur = 0;
        ctx.beginPath();
        ctx.arc(24, 22, 9, 0, Math.PI * 2);
        ctx.fillStyle = "#FFFFFF";
        ctx.fill();

        // Ícone interno
        ctx.beginPath();
        ctx.arc(24, 22, 4, 0, Math.PI * 2);
        ctx.fillStyle = colorHex;
        ctx.fill();

        return canvas.toDataURL();
    }

    function initCesium3DViewer() {
        const container = document.getElementById("cesiumContainer");
        if (!container) return;

        try {
            Cesium.Ion.defaultAccessToken = '';

            const esriImageryProvider = new Cesium.UrlTemplateImageryProvider({
                url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                credit: 'Esri World Imagery'
            });

            cesiumViewer = new Cesium.Viewer("cesiumContainer", {
                imageryProvider: esriImageryProvider,
                baseLayerPicker: false,
                geocoder: false,
                homeButton: false,
                sceneModePicker: true,
                navigationHelpButton: false,
                animation: false,
                timeline: false,
                fullscreenButton: false,
                infoBox: true,
                selectionIndicator: true,
                terrainProvider: new Cesium.EllipsoidTerrainProvider()
            });

            // Tentar ativar terreno global com relevo 3D caso disponível
            if (Cesium.createWorldTerrainAsync) {
                Cesium.createWorldTerrainAsync({
                    requestWaterMask: false,
                    requestVertexNormals: true
                }).then(terrain => {
                    if (cesiumViewer && !cesiumViewer.isDestroyed()) {
                        cesiumViewer.terrainProvider = terrain;
                    }
                }).catch(err => {
                    console.log("Usando terreno esférico padrão:", err);
                });
            }

            // Posicionar câmera inicialmente sobre Angra dos Reis (Ângulo de Visão Oblíqua 3D)
            flyToAngra();

            // Carregar pontos de ocorrência
            load3DOccurrences();

            // Configurar botões de ação do Modal 3D
            const btnFlyTo = document.getElementById("btn3DFlyToAngra");
            if (btnFlyTo) btnFlyTo.onclick = flyToAngra;

            const btnTilt = document.getElementById("btn3DTiltOrbit");
            if (btnTilt) btnTilt.onclick = tiltOrbitCamera;

            const btnRefresh = document.getElementById("btn3DRefresh");
            if (btnRefresh) btnRefresh.onclick = load3DOccurrences;

        } catch (err) {
            console.error("Erro ao inicializar Cesium 3D:", err);
            container.innerHTML = `
                <div class="d-flex flex-column align-items-center justify-content-center h-100 text-white p-4 text-center" style="background:#0f172a;">
                    <i class="bi bi-exclamation-triangle-fill text-warning fs-1 mb-3"></i>
                    <h5 class="fw-bold">Não foi possível carregar o motor 3D neste navegador</h5>
                    <p class="text-muted small mb-0">Verifique se a aceleração de hardware (WebGL) está ativada nas configurações do seu navegador.</p>
                    <p class="text-danger small mt-2">Erro detalhado: ${err.message || err}</p>
                </div>
            `;
        }
    }

    function flyToAngra() {
        if (!cesiumViewer) return;
        cesiumViewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(-44.3181, -23.0067, 4500.0),
            orientation: {
                heading: Cesium.Math.toRadians(15.0),
                pitch: Cesium.Math.toRadians(-35.0),
                roll: 0.0
            },
            duration: 2.5
        });
    }

    function tiltOrbitCamera() {
        if (!cesiumViewer) return;
        const currentPitch = cesiumViewer.camera.pitch;
        const targetPitch = currentPitch > -0.5 ? -0.8 : -0.3;
        cesiumViewer.camera.flyTo({
            destination: cesiumViewer.camera.position,
            orientation: {
                heading: cesiumViewer.camera.heading + Cesium.Math.toRadians(45.0),
                pitch: targetPitch,
                roll: 0.0
            },
            duration: 1.5
        });
    }

    function load3DOccurrences() {
        if (!cesiumViewer) return;

        // Remover fonte de dados anterior se existir
        if (occurrencesDataSource) {
            cesiumViewer.dataSources.remove(occurrencesDataSource, true);
        }

        const statusSpan = document.getElementById("status3DLoading");
        if (statusSpan) statusSpan.style.display = "inline-block";

        const pinBlueUrl = createPinDataUrl("#0284c7");

        fetch("/api/occurrences")
            .then(res => res.json())
            .then(geoJsonData => {
                if (!geoJsonData || !geoJsonData.features) return;

                occurrencesDataSource = new Cesium.CustomDataSource("Ocorrencias3D");

                geoJsonData.features.forEach(feat => {
                    const coords = feat.geometry ? feat.geometry.coordinates : null;
                    if (!coords || coords.length < 2) return;

                    const lng = parseFloat(coords[0]);
                    const lat = parseFloat(coords[1]);
                    const props = feat.properties || {};

                    if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

                    const altStemTop = 80.0; // Elevação do pino acima do terreno (metros)

                    // Posição no solo e no topo da haste 3D
                    const groundPos = Cesium.Cartesian3.fromDegrees(lng, lat, 0);
                    const topPos = Cesium.Cartesian3.fromDegrees(lng, lat, altStemTop);

                    // Descrição em HTML formatada para a InfoBox do Cesium
                    let mediaHtml = "";
                    if (props.media_urls && props.media_urls.length > 0) {
                        mediaHtml += `<div style="margin-top:10px;"><strong>📸 Mídias Registradas (${props.media_urls.length}):</strong><br>`;
                        props.media_urls.forEach(url => {
                            if (url.toLowerCase().endsWith(".mp4") || url.toLowerCase().endsWith(".mov")) {
                                mediaHtml += `<video src="${url}" controls style="width:100%; max-height:160px; margin-top:4px; border-radius:6px;"></video>`;
                            } else {
                                mediaHtml += `<a href="${url}" target="_blank"><img src="${url}" style="width:100%; max-height:160px; object-fit:cover; margin-top:4px; border-radius:6px;" /></a>`;
                            }
                        });
                        mediaHtml += `</div>`;
                    }

                    const descriptionHtml = `
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size:12px; color:#1e293b; padding:4px;">
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

                    // Haste Vertical 3D conectando o terreno ao pino
                    occurrencesDataSource.entities.add({
                        name: `Haste 3D #${props.id}`,
                        polyline: {
                            positions: [groundPos, topPos],
                            width: 3,
                            material: new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString('#38bdf8').withAlpha(0.85))
                        }
                    });

                    // Pino 3D
                    occurrencesDataSource.entities.add({
                        id: `occ_3d_${props.id}`,
                        name: props.title || `Ocorrência #${props.id}`,
                        position: topPos,
                        billboard: {
                            image: pinBlueUrl,
                            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                            heightReference: Cesium.HeightReference.NONE,
                            scale: 0.85,
                            disableDepthTestDistance: Number.POSITIVE_INFINITY
                        },
                        description: descriptionHtml
                    });
                });

                cesiumViewer.dataSources.add(occurrencesDataSource);
            })
            .catch(err => console.error("Erro ao carregar 3D:", err))
            .finally(() => {
                if (statusSpan) statusSpan.style.display = "none";
            });
    }
});
