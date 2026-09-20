document.addEventListener("DOMContentLoaded", function() {
    // Inicializa o mapa focado em Angra dos Reis
    var map = L.map('map').setView([-23.00, -44.31], 11);

    // 1. Definição dos Mapas de Fundo (Basemaps)
    var googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains:['mt0','mt1','mt2','mt3'],
        attribution: '&copy; Google Satellite'
    });

    var cartoPositron = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    });

    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    });

    var esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    });

    // Adiciona o Google Satélite como padrão
    googleSat.addTo(map);

    var baseMaps = {
        "Google Satellite (Satelite HD)": googleSat,
        "Carto Positron (Claro)": cartoPositron,
        "OpenStreetMap (Ruas)": osm,
        "Esri Satellite": esriSatellite
    };

    var overlayMaps = {};
    var layerControl = L.control.layers(baseMaps, overlayMaps, { collapsed: false }).addTo(map);

    function getRandomColor() {
        var colors = ['#2563EB', '#0D9488', '#D97706', '#7C3AED', '#DB2777', '#059669', '#4F46E5'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    // Função para criar o ícone moderno de ponto de deslizamento (Simbologia Moderna)
    function createModernPointMarker(latlng) {
        return L.circleMarker(latlng, {
            radius: 6.5,
            fillColor: "#FFFFFF",  // Branco puro
            color: "#0F172A",      // Contorno escuro elegante
            weight: 2,
            opacity: 1.0,
            fillOpacity: 1.0
        });
    }

    // Função de montagem de popup genérico para atributos de GeoJSON
    function onEachFeature(feature, layer) {
        if (feature.properties) {
            let popupContent = '<div style="max-height: 260px; overflow-y: auto;"><table class="table table-sm table-striped" style="font-size:11px;"><tbody>';
            for (let p in feature.properties) {
                popupContent += `<tr><th class="text-secondary">${p}</th><td>${feature.properties[p]}</td></tr>`;
            }
            popupContent += '</tbody></table></div>';
            layer.bindPopup(popupContent, { maxHeight: 300 });
        }
    }

    // Carregar as camadas vetoriais da API
    fetch('/api/layers')
        .then(response => response.json())
        .then(layers => {
            const layerListDiv = document.getElementById('layer-list');
            if (layerListDiv) layerListDiv.innerHTML = '';
            
            if (layers.length === 0 && layerListDiv) {
                layerListDiv.innerHTML = '<p class="text-muted small">Nenhuma camada cadastrada.</p>';
                return;
            }

            layers.forEach(layerData => {
                const filename = (layerData.filename || '').toLowerCase();
                const name = (layerData.name || '').toLowerCase();

                // Identifica se é a camada de pontos de ocorrência
                const isRegisteredPoints = filename.includes('pontos') || name.includes('pontos') || name.includes('deslizamento');

                // Identifica se é camada de Limite Municipal ou Buffer (LINHA TRACEJADA VERMELHA E SEM PREENCHIMENTO)
                const isBoundaryOrBuffer = !isRegisteredPoints && (
                    filename === 'angra.geojson' ||
                    filename === 'au_angra_geojson.geojson' ||
                    filename.includes('buffer') ||
                    name.includes('buffer') ||
                    name.includes('limite municipal') ||
                    name === 'angra dos reis'
                );

                if (layerListDiv) {
                    const div = document.createElement('div');
                    div.className = 'form-check mb-2 p-2 rounded bg-light border border-light shadow-sm';
                    
                    const input = document.createElement('input');
                    input.className = 'form-check-input ms-1';
                    input.type = 'checkbox';
                    input.id = 'layer_' + layerData.id;
                    
                    const label = document.createElement('label');
                    label.className = 'form-check-label ms-2';
                    label.htmlFor = 'layer_' + layerData.id;
                    
                    // Exibe APENAS o nome da camada e sua categoria embaixo (sem rótulos de simbologia)
                    label.innerHTML = `<strong>${layerData.name}</strong><br><small class="text-muted">${layerData.category}</small>`;
                    
                    div.appendChild(input);
                    div.appendChild(label);
                    layerListDiv.appendChild(div);

                    let geojsonLayer = null;

                    input.addEventListener('change', function() {
                        if (this.checked) {
                            this.disabled = true;
                            label.innerHTML += ' <span class="spinner-border spinner-border-sm text-primary" role="status"></span>';

                            fetch('/api/layer/' + layerData.filename)
                                .then(res => res.json())
                                .then(data => {
                                    let layerColor = getRandomColor();
                                    
                                    geojsonLayer = L.geoJSON(data, {
                                        style: function (feature) {
                                            if (isBoundaryOrBuffer) {
                                                return {
                                                    color: '#DC2626',      // Vermelho forte
                                                    dashArray: '6, 6',     // Linha tracejada
                                                    weight: 2.5,
                                                    opacity: 1,
                                                    fill: false,           // Sem preenchimento
                                                    fillOpacity: 0
                                                };
                                            }
                                            return {
                                                color: layerColor,
                                                weight: 2,
                                                opacity: 0.9,
                                                fillOpacity: 0.35
                                            };
                                        },
                                        pointToLayer: function (feature, latlng) {
                                            if (isRegisteredPoints) {
                                                return createModernPointMarker(latlng);
                                            }
                                            return L.circleMarker(latlng, {
                                                radius: 5,
                                                fillColor: layerColor,
                                                color: "#000",
                                                weight: 1,
                                                opacity: 1,
                                                fillOpacity: 0.8
                                            });
                                        },
                                        onEachFeature: onEachFeature
                                    }).addTo(map);
                                    
                                    layerControl.addOverlay(geojsonLayer, layerData.name);
                                    
                                    if(filename === 'angra.geojson' || filename.includes('angra')) {
                                        try { map.fitBounds(geojsonLayer.getBounds()); } catch(e){}
                                    }
                                })
                                .catch(err => {
                                    console.error('Erro ao carregar ' + layerData.name, err);
                                })
                                .finally(() => {
                                    this.disabled = false;
                                    label.innerHTML = `<strong>${layerData.name}</strong><br><small class="text-muted">${layerData.category}</small>`;
                                });
                        } else {
                            if (geojsonLayer) {
                                map.removeLayer(geojsonLayer);
                                layerControl.removeLayer(geojsonLayer);
                                geojsonLayer = null;
                            }
                        }
                    });
                }
            });
        })
        .catch(err => console.error("Erro ao buscar camadas:", err));

    // Carregar ocorrências da Curadoria (Aprovadas) e agrupar com MarkerCluster
    fetch('/api/occurrences')
        .then(response => response.json())
        .then(data => {
            if (data.features && data.features.length > 0) {
                var markers = L.markerClusterGroup({
                    maxClusterRadius: 40
                });

                var geoJsonLayer = L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        return createModernPointMarker(latlng);
                    },
                    onEachFeature: function(feature, layer) {
                        let p = feature.properties;
                        
                        let levelName = {
                            'admin_geral': 'Administrador Geral',
                            'admin_nacional': 'Defesa Civil Nacional',
                            'admin_estadual': 'Defesa Civil Estadual',
                            'admin_municipal': 'Defesa Civil Municipal',
                            'org': 'Organização Parceira',
                            'user': 'Usuário Registrador'
                        }[p.responsavel_nivel] || p.responsavel_nivel || 'Curador Responsável';

                        let popupContent = `
                            <div style="max-width: 360px; font-size: 11px; max-height: 420px; overflow-y: auto;" class="p-1">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <span class="badge bg-success text-white"><i class="bi bi-check-circle-fill"></i> Origem: ${p.origem || 'Curadoria'}</span>
                                    <span class="badge bg-secondary">${p.municipio || 'Angra dos Reis'} - ${p.uf || 'RJ'}</span>
                                </div>

                                <h6 class="fw-bold mb-1 text-primary">${p.title || 'Ocorrência Aprovada'}</h6>
                                <span class="badge bg-danger mb-2">${p.tipologia || 'Deslizamento de Encosta'}</span>
                                
                                <div class="p-2 mb-2 rounded bg-light border shadow-sm" style="font-size: 10px;">
                                    <div class="fw-bold text-dark mb-1">📋 Responsável Técnico:</div>
                                    <div><strong>Nome:</strong> ${p.responsavel_nome || 'Defesa Civil'}</div>
                                    <div><strong>Atuação:</strong> <span class="badge bg-dark">${levelName}</span></div>
                                    <div><strong>CPF:</strong> ${p.responsavel_cpf || '***.***.***-**'} | <strong>Matrícula:</strong> ${p.responsavel_matricula || 'N/A'}</div>
                                </div>

                                <!-- Botão Gerar Relatório PDF -->
                                <a href="/api/occurrence/${p.id}/pdf" target="_blank" class="btn btn-sm btn-primary w-100 mb-2 fw-bold text-white">
                                    📄 Gerar Relatório PDF Profissional
                                </a>

                                <div class="accordion accordion-flush mb-2 border rounded" id="popupAccordion_${p.id}">
                                  <!-- Evento & Localização -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button p-2 text-primary fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#c1_${p.id}">
                                        📌 Evento & Coordenadas
                                      </button>
                                    </h2>
                                    <div id="c1_${p.id}" class="accordion-collapse collapse show">
                                      <div class="accordion-body p-1">
                                        <table class="table table-sm table-striped mb-0" style="font-size:10px;">
                                            <tr><th>Data do Evento</th><td>${p.data_evento || '-'}</td></tr>
                                            <tr><th>Bairro / Local</th><td>${p.bairro || '-'}</td></tr>
                                            <tr><th>Zona de Risco</th><td>${p.zona || '-'}</td></tr>
                                            <tr><th>Coordenadas (Y, X)</th><td>${p.lat}, ${p.lng}</td></tr>
                                            <tr><th>% Área Atingida</th><td>Urbana: ${p.perc_area_atu || '-'} | Agrícola: ${p.perc_area_atr || '-'}</td></tr>
                                        </table>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  <!-- Clima & Pedologia -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button collapsed p-2 fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#c2_${p.id}">
                                        ⛅ Clima & Pedologia (Solo)
                                      </button>
                                    </h2>
                                    <div id="c2_${p.id}" class="accordion-collapse collapse">
                                      <div class="accordion-body p-1">
                                        <table class="table table-sm table-striped mb-0" style="font-size:10px;">
                                            <tr><th>Precipitação Evento</th><td>${p.clima_precipitacao_evento || '-'} mm</td></tr>
                                            <tr><th>Precipitação Mensal</th><td>${p.clima_precipitacao_mensal || '-'} mm</td></tr>
                                            <tr><th>Acumulado 5d / 10d</th><td>${p.clima_precipitacao_5d || '-'} mm / ${p.clima_precipitacao_10d || '-'} mm</td></tr>
                                            <tr><th>Vento / Temp / Pressão</th><td>${p.clima_vento || '-'} m/s | ${p.clima_temperatura || '-'} ºC | ${p.clima_pressao || '-'} atm</td></tr>
                                            <tr><th>Classe de Solo (Embrapa)</th><td>${p.ped_classe_solo || '-'}</td></tr>
                                            <tr><th>Profundidade / Textura</th><td>${p.ped_profundidade || '-'} | ${p.ped_textura || '-'}</td></tr>
                                            <tr><th>Porosidade / Umidade</th><td>${p.ped_porosidade || '-'} % | ${p.ped_umidade_evento || '-'}</td></tr>
                                        </table>
                                      </div>
                                    </div>
                                  </div>

                                  <!-- Geologia & Geomorfologia -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button collapsed p-2 fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#c3_${p.id}">
                                        ⛰️ Geologia & Relevo
                                      </button>
                                    </h2>
                                    <div id="c3_${p.id}" class="accordion-collapse collapse">
                                      <div class="accordion-body p-1">
                                        <table class="table table-sm table-striped mb-0" style="font-size:10px;">
                                            <tr><th>Declividade / Altitude</th><td>${p.geo_declividade || '-'} | ${p.geo_altitude || '-'} m</td></tr>
                                            <tr><th>Forma Terreno / Curvatura</th><td>${p.geo_forma_terreno || '-'} | ${p.geo_curvatura || '-'}</td></tr>
                                            <tr><th>Tipo de Rocha / Idade</th><td>${p.geol_tipo_rocha || '-'} | ${p.geol_idade || '-'}</td></tr>
                                            <tr><th>Estrutura / Tectonismo</th><td>${p.geol_estrutura || '-'} | Tectonismo: ${p.geol_tectonismo || '-'}</td></tr>
                                            <tr><th>Fatores Antrópicos</th><td>Escavação: ${p.antrop_escavacao || '-'} | Mineração: ${p.antrop_mineracao || '-'}</td></tr>
                                        </table>
                                      </div>
                                    </div>
                                  </div>

                                  <!-- Impactos -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button collapsed p-2 text-danger fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#c4_${p.id}">
                                        💰 Impactos (Soc/Econ/Amb)
                                      </button>
                                    </h2>
                                    <div id="c4_${p.id}" class="accordion-collapse collapse">
                                      <div class="accordion-body p-1">
                                        <table class="table table-sm table-striped mb-0" style="font-size:10px;">
                                            <tr><th>Mortos / Feridos</th><td>${p.n_mortos || 0} mortos | ${p.n_feridos || 0} feridos</td></tr>
                                            <tr><th>Desalojados / Desabrigados</th><td>${p.soc_n_desalojados || '-'} desalojados | ${p.soc_n_desabrigados || '-'} desabrigados</td></tr>
                                            <tr><th>Custo Danos Econômicos</th><td>${p.econ_custo_total || '-'} (Recuperação: ${p.econ_custo_recuperacao || '-'})</td></tr>
                                            <tr><th>Infraestrutura Atingida</th><td>${p.econ_infraestrutura || '-'}</td></tr>
                                            <tr><th>Impacto Ambiental</th><td>${p.amb_tipo_impacto || '-'} | Área: ${p.amb_area_atingida || '-'} ha</td></tr>
                                        </table>
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                <div class="mt-2 mb-2 small"><strong>Descrição:</strong> ${p.description || 'Sem descrição complementar.'}</div>
                        `;

                        if (p.media_url) {
                            let filename = (p.media_filename || p.media_url).toLowerCase();
                            if (filename.endsWith('.mp4') || filename.endsWith('.mov') || filename.endsWith('.webm')) {
                                popupContent += `<video width="100%" controls src="${p.media_url}" class="rounded mb-2"></video>`;
                            } else {
                                popupContent += `<img src="${p.media_url}" width="100%" class="rounded mb-2 shadow-sm">`;
                            }
                        }

                        if (p.can_delete) {
                            popupContent += `
                                <form action="/delete_occurrence/${p.id}" method="POST" onsubmit="return confirm('Deseja realmente excluir esta ocorrência do sistema? Esta ação é irreversível.');">
                                    <button type="submit" class="btn btn-sm btn-outline-danger w-100">
                                        🗑️ Excluir Ocorrência do Sistema
                                    </button>
                                </form>
                            `;
                        }

                        popupContent += `</div>`;
                        layer.bindPopup(popupContent, { maxWidth: 380 });
                    }
                });

                markers.addLayer(geoJsonLayer);
                map.addLayer(markers);
                layerControl.addOverlay(markers, "Pontos de Deslizamento Registrados (Curadoria)");
            }
        })
        .catch(err => console.error("Erro ao carregar ocorrências:", err));
});
