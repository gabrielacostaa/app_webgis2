document.addEventListener("DOMContentLoaded", function() {
    // Inicializa o mapa focado em Angra dos Reis
    var map = L.map('map').setView([-23.00, -44.31], 11);

    // 1. Definição dos Mapas de Fundo (Basemaps)
    var googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains:['mt0','mt1','mt2','mt3'],
        attribution: '&copy; Google Satellite'
    });

    var darkMatter = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
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

    var baseMapLayers = {
        'googleSat': googleSat,
        'darkMatter': darkMatter,
        'cartoPositron': cartoPositron,
        'osm': osm,
        'esri': esriSatellite
    };

    var currentBasemap = googleSat;

    // Conectar botões de vidro dos Mapas de Fundo (Basemaps)
    var basemapBtns = document.querySelectorAll('.basemap-glass-btn');
    basemapBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var selectedKey = this.getAttribute('data-basemap');
            var newLayer = baseMapLayers[selectedKey];
            if (newLayer && newLayer !== currentBasemap) {
                map.removeLayer(currentBasemap);
                newLayer.addTo(map);
                currentBasemap = newLayer;

                basemapBtns.forEach(function(b) { b.classList.remove('active'); });
                this.classList.add('active');
            }
        });
    });

    // Botão de Recolher/Expandir Barra Lateral Flutuante (Glassmorphism)
    var btnToggleSidebar = document.getElementById('btnToggleGisSidebar');
    var gisSidebar = document.getElementById('gisSidebar');
    var iconToggleSidebar = document.getElementById('iconToggleSidebar');

    if (btnToggleSidebar && gisSidebar) {
        btnToggleSidebar.addEventListener('click', function() {
            gisSidebar.classList.toggle('collapsed');
            btnToggleSidebar.classList.toggle('sidebar-collapsed');
            if (gisSidebar.classList.contains('collapsed')) {
                if (iconToggleSidebar) iconToggleSidebar.className = 'bi bi-chevron-right fs-5';
            } else {
                if (iconToggleSidebar) iconToggleSidebar.className = 'bi bi-chevron-left fs-5';
            }
            setTimeout(function() { map.invalidateSize(); }, 350);
        });
    }

    var baseMaps = {
        "Google Satellite (HD)": googleSat,
        "Carto Dark Matter (Escuro)": darkMatter,
        "Carto Positron (Claro)": cartoPositron,
        "OpenStreetMap (Ruas)": osm,
        "Esri Satellite": esriSatellite
    };

    var overlayMaps = {};
    var layerControl = L.control.layers(baseMaps, overlayMaps, { collapsed: true, position: 'topright' }).addTo(map);

    function getRandomColor() {
        var colors = ['#2563EB', '#0D9488', '#D97706', '#7C3AED', '#DB2777', '#059669', '#4F46E5'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    // Gerenciador de Legenda Dinâmica
    var activeLegendItems = {};

    function updateDynamicLegend() {
        var container = document.getElementById('map-legend-content');
        if (!container) return;

        var keys = Object.keys(activeLegendItems);
        if (keys.length === 0) {
            container.innerHTML = '<div class="text-muted fst-italic py-1" style="font-size: 10px;">Nenhuma camada ativa</div>';
            return;
        }

        var html = '';
        keys.forEach(function(key) {
            html += '<div class="d-flex align-items-center gap-2 mb-1.5">' + activeLegendItems[key] + '</div>';
        });
        container.innerHTML = html;
    }

    map.on('overlayadd', function(e) {
        if (e.layer && e.layer._layerIdKey && e.layer.legendHtml) {
            activeLegendItems[e.layer._layerIdKey] = e.layer.legendHtml;
            updateDynamicLegend();
        }
    });

    map.on('overlayremove', function(e) {
        if (e.layer && e.layer._layerIdKey) {
            delete activeLegendItems[e.layer._layerIdKey];
            updateDynamicLegend();
        }
    });

    // 1. Símbolo de GPS em BRANCO para Pontos de Deslizamento Registrados (pontos_angra.geojson)
    function createWhiteGPSMarker(latlng) {
        var icon = L.divIcon({
            className: 'gps-marker-container',
            html: '<div class="gps-pin-white shadow-sm"><i class="bi bi-geo-alt-fill"></i></div>',
            iconSize: [26, 26],
            iconAnchor: [13, 26],
            popupAnchor: [0, -26]
        });
        return L.marker(latlng, { icon: icon });
    }

    // 2. Símbolo em AZUL para Pontos de Deslizamento da CURADORIA (/api/occurrences)
    function createBlueGPSMarker(latlng) {
        var icon = L.divIcon({
            className: 'gps-marker-container',
            html: '<div class="gps-pin-blue shadow-sm"><i class="bi bi-geo-alt-fill"></i></div>',
            iconSize: [26, 26],
            iconAnchor: [13, 26],
            popupAnchor: [0, -26]
        });
        return L.marker(latlng, { icon: icon });
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

            // Item especial: Camada de Pontos da Curadoria (Opcional por demanda)
            const curadoriaDiv = document.createElement('div');
            curadoriaDiv.className = 'gis-layer-item curadoria-item';
            
            const curadoriaLabel = document.createElement('label');
            curadoriaLabel.className = 'form-check-label mb-0 cursor-pointer d-flex align-items-center gap-2';
            curadoriaLabel.htmlFor = 'layer_curadoria_demand';
            curadoriaLabel.innerHTML = `<div><strong class="text-white" style="font-size:12px;">Deslizamentos (Curadoria)</strong><br><small class="text-info fw-semibold" style="font-size:10px;">Ocorrências Oficiais (Pinos Azuis)</small></div>`;
            
            const curadoriaInput = document.createElement('input');
            curadoriaInput.className = 'form-check-input ms-2';
            curadoriaInput.type = 'checkbox';
            curadoriaInput.id = 'layer_curadoria_demand';
            
            curadoriaDiv.appendChild(curadoriaLabel);
            curadoriaDiv.appendChild(curadoriaInput);
            layerListDiv.appendChild(curadoriaDiv);

            let curadoriaClusterGroup = null;

            curadoriaInput.addEventListener('change', function() {
                if (this.checked) {
                    this.disabled = true;
                    curadoriaLabel.innerHTML += ' <span class="spinner-border spinner-border-sm text-primary" role="status"></span>';

                    fetch('/api/occurrences')
                        .then(response => response.json())
                        .then(data => {
                            if (data.features && data.features.length > 0) {
                                curadoriaClusterGroup = L.markerClusterGroup({ maxClusterRadius: 40 });

                                var geoJsonLayer = L.geoJSON(data, {
                                    pointToLayer: function (feature, latlng) {
                                        return createBlueGPSMarker(latlng);
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

                                         function fmtRow(label, val) {
                                             if (val === null || val === undefined || String(val).trim() === '' || val === 0 || val === '0') return '';
                                             return `<div class="d-flex justify-content-between py-1 border-bottom" style="font-size:10px;">
                                                 <span class="text-secondary fw-semibold">${label}:</span>
                                                 <span class="fw-bold text-dark text-end ms-2">${val}</span>
                                             </div>`;
                                         }

                                         function fmtSection(accId, title, icon, contentHtml) {
                                             if (!contentHtml || contentHtml.trim() === '') return '';
                                             return `
                                                 <div class="accordion-item border-0 mb-1 rounded-2 overflow-hidden shadow-sm">
                                                     <h2 class="accordion-header" id="heading_${accId}_${p.id}">
                                                         <button class="accordion-button collapsed py-1.5 px-2 bg-light text-dark fw-bold" style="font-size: 10px;" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_${accId}_${p.id}">
                                                             ${icon} ${title}
                                                         </button>
                                                     </h2>
                                                     <div id="collapse_${accId}_${p.id}" class="accordion-collapse collapse" data-bs-parent="#dictAccordion_${p.id}">
                                                         <div class="accordion-body p-2 bg-white">
                                                             ${contentHtml}
                                                         </div>
                                                     </div>
                                                 </div>
                                             `;
                                         }

                                         function withUnit(val, unit, prefix = false) {
                                             if (val === null || val === undefined) return '';
                                             let strVal = String(val).trim();
                                             if (strVal === '' || strVal === '0') return '';
                                             if (strVal.toLowerCase().includes(unit.toLowerCase())) return strVal;
                                             return prefix ? `${unit} ${strVal}` : `${strVal} ${unit}`;
                                         }

                                         let climaHtml = fmtRow('Precipitação Evento', withUnit(p.clima_precipitacao_evento, 'mm')) +
                                                         fmtRow('Precipitação Mensal', withUnit(p.clima_precipitacao_mensal, 'mm')) +
                                                         fmtRow('Acumulado 5d', withUnit(p.clima_precipitacao_5d, 'mm')) +
                                                         fmtRow('Acumulado 10d', withUnit(p.clima_precipitacao_10d, 'mm')) +
                                                         fmtRow('Vento', withUnit(p.clima_vento, 'm/s')) +
                                                         fmtRow('Temperatura', withUnit(p.clima_temperatura, 'ºC')) +
                                                         fmtRow('Pressão', withUnit(p.clima_pressao, 'atm')) +
                                                         fmtRow('Evapotranspiração', p.clima_evapotranspiracao);

                                         let soloHtml = fmtRow('Classe do Solo', p.ped_classe_solo) +
                                                        fmtRow('Profundidade Regolito', withUnit(p.ped_profundidade, 'm')) +
                                                        fmtRow('Textura', p.ped_textura) +
                                                        fmtRow('Porosidade', withUnit(p.ped_porosidade, '%')) +
                                                        fmtRow('UCC', p.ped_ucc) +
                                                        fmtRow('CAD', p.ped_cad) +
                                                        fmtRow('Permeabilidade K', p.ped_k) +
                                                        fmtRow('Umidade no Evento', withUnit(p.ped_umidade_evento, '%'));

                                         let relevoHtml = fmtRow('Declividade', withUnit(p.geo_declividade, '%')) +
                                                          fmtRow('Altitude', withUnit(p.geo_altitude, 'm')) +
                                                          fmtRow('Forma do Terreno', p.geo_forma_terreno) +
                                                          fmtRow('Orientação Encosta', p.geo_orientacao) +
                                                          fmtRow('Curvatura', p.geo_curvatura) +
                                                          fmtRow('Tipo de Rocha', p.geol_tipo_rocha) +
                                                          fmtRow('Composição Rocha', p.geol_composicao) +
                                                          fmtRow('Estrutura', p.geol_estrutura) +
                                                          fmtRow('Tectonismo', p.geol_tectonismo);

                                         let antropHtml = fmtRow('Escavação / Cortes', p.antrop_escavacao) +
                                                          fmtRow('Sobrecarga no Topo', p.antrop_sobrecarga) +
                                                          fmtRow('Uso do Solo', p.antrop_tipo_uso) +
                                                          fmtRow('Mineração', p.antrop_mineracao);

                                         let econHtml = fmtRow('Custo Total Est.', withUnit(p.econ_custo_total, 'R$', true)) +
                                                        fmtRow('Infraestrutura Afetada', p.econ_infraestrutura) +
                                                        fmtRow('Patrimônio Privado', p.econ_patrimonio_privado) +
                                                        fmtRow('Patrimônio Público', p.econ_patrimonio_publico) +
                                                        fmtRow('Danos Agrícolas', p.econ_agri_cultura) +
                                                        fmtRow('Custo Recuperação', withUnit(p.econ_custo_recuperacao, 'R$', true)) +
                                                        fmtRow('Interrupção Serviços', p.econ_interrupcao_setores);

                                         let socHtml = fmtRow('Mortos', p.n_mortos) +
                                                       fmtRow('Feridos', p.n_feridos) +
                                                       fmtRow('Desalojados', withUnit(p.soc_n_desalojados, 'desalojados')) +
                                                       fmtRow('Desabrigados', withUnit(p.soc_n_desabrigados, 'desabrigados')) +
                                                       fmtRow('Desaparecidos', withUnit(p.soc_n_desaparecidos, 'desaparecidos')) +
                                                       fmtRow('Famílias Atingidas', p.soc_n_familias) +
                                                       fmtRow('Impacto Ambiental', p.amb_tipo_impacto) +
                                                       fmtRow('Área Atingida Amb.', withUnit(p.amb_area_atingida, 'ha')) +
                                                       fmtRow('Status Recuperação', p.amb_status_recuperacao);

                                         let dictAccordionHtml = fmtSection('clima', 'Clima & Meteorologia', '⛅', climaHtml) +
                                                                 fmtSection('solo', 'Pedologia & Solo', '🏜️', soloHtml) +
                                                                 fmtSection('relevo', 'Geomorfologia & Geologia', '⛰️', relevoHtml) +
                                                                 fmtSection('antrop', 'Fatores Antrópicos', '🚜', antropHtml) +
                                                                 fmtSection('econ', 'Impacto Econômico', '💰', econHtml) +
                                                                 fmtSection('soc', 'Impacto Social & Ambiental', '👥', socHtml);

                                         let popupContent = `
                                             <div style="max-width: 380px; font-size: 11px; max-height: 480px; overflow-y: auto;" class="p-1">
                                                 <div class="d-flex justify-content-between align-items-center mb-1">
                                                     <span class="badge bg-primary text-white"><i class="bi bi-patch-check-fill"></i> Origem: ${p.origem || 'Curadoria'}</span>
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

                                                 <!-- Botão Gerar / Pré-visualizar Relatório PDF -->
                                                 <button type="button" onclick="previewPdfReport(${p.id})" class="btn btn-sm btn-primary w-100 mb-2 fw-bold text-white shadow-sm">
                                                     📄 Pré-visualizar / Gerar Relatório PDF
                                                 </button>

                                                 <div class="mt-2 mb-2 small"><strong>Descrição:</strong> ${p.description || 'Sem descrição complementar.'}</div>
                                         `;

                                         if (dictAccordionHtml.trim() !== '') {
                                             popupContent += `
                                                 <div class="fw-bold text-dark mb-1 small"><i class="bi bi-journal-text text-primary"></i> Dicionário de Dados Cadastrado:</div>
                                                 <div class="accordion accordion-flush mb-2 border rounded-3 overflow-hidden shadow-sm" id="dictAccordion_${p.id}">
                                                     ${dictAccordionHtml}
                                                 </div>
                                             `;
                                         }

                                         let urls = p.media_urls || [];
                                         if (urls.length === 0 && p.media_url) urls = [p.media_url];

                                         if (urls.length > 0) {
                                             popupContent += `<div class="fw-bold text-dark mb-1 small"><i class="bi bi-images text-success"></i> Mídias do Evento (${urls.length}):</div><div class="d-flex flex-column gap-2 mb-2">`;
                                             urls.forEach(mUrl => {
                                                 let fn = mUrl.toLowerCase();
                                                 if (fn.endsWith('.mp4') || fn.endsWith('.mov') || fn.endsWith('.webm')) {
                                                     popupContent += `<video width="100%" controls src="${mUrl}" class="rounded shadow-sm"></video>`;
                                                 } else {
                                                     popupContent += `<a href="${mUrl}" target="_blank"><img src="${mUrl}" width="100%" class="rounded shadow-sm" style="max-height:180px; object-fit:cover;"></a>`;
                                                 }
                                             });
                                             popupContent += `</div>`;
                                         }

                                         if (p.can_delete) {
                                             popupContent += `
                                                 <form action="/delete_occurrence/${p.id}" method="POST" onsubmit="return confirm('Deseja realmente excluir esta ocorrência do sistema? Esta ação é irreversível.');">
                                                     <button type="submit" class="btn btn-sm btn-outline-danger w-100 mt-1">
                                                         🗑️ Excluir Ocorrência do Sistema
                                                     </button>
                                                 </form>
                                             `;
                                         }

                                         popupContent += `</div>`;
                                         layer.bindPopup(popupContent, { maxWidth: 390 });
                                     }
                                });

                                curadoriaClusterGroup._layerIdKey = 'curadoria';
                                curadoriaClusterGroup.legendHtml = '<span class="legend-gps-blue me-1"><i class="bi bi-geo-alt-fill"></i></span><span>Pontos Curadoria (GPS Azul)</span>';
                                activeLegendItems['curadoria'] = curadoriaClusterGroup.legendHtml;

                                curadoriaClusterGroup.addLayer(geoJsonLayer);
                                map.addLayer(curadoriaClusterGroup);
                                updateDynamicLegend();
                                layerControl.addOverlay(curadoriaClusterGroup, "Pontos de Deslizamento (Curadoria)");
                            }
                        })
                        .catch(err => console.error("Erro ao carregar ocorrências:", err))
                        .finally(() => {
                            this.disabled = false;
                            curadoriaLabel.innerHTML = `<strong>Pontos de Deslizamento (Curadoria)</strong><br><small class="text-primary fw-semibold">Ocorrências Validadas (Pinos Azuis)</small>`;
                        });
                } else {
                    if (curadoriaClusterGroup) {
                        delete activeLegendItems['curadoria'];
                        updateDynamicLegend();
                        map.removeLayer(curadoriaClusterGroup);
                        layerControl.removeLayer(curadoriaClusterGroup);
                        curadoriaClusterGroup = null;
                    }
                }
            });

            layers.forEach(layerData => {
                const filename = (layerData.filename || '').toLowerCase();
                const name = (layerData.name || '').toLowerCase();

                // Identifica se é a camada de pontos de ocorrência históricos registrados
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
                    div.className = 'gis-layer-item';
                    
                    const label = document.createElement('label');
                    label.className = 'form-check-label mb-0 cursor-pointer';
                    label.htmlFor = 'layer_' + layerData.id;
                    label.innerHTML = `<div><strong class="text-white" style="font-size:11.5px;">${layerData.name}</strong><br><small class="text-white-50" style="font-size:10px;">${layerData.category}</small></div>`;
                    
                    const input = document.createElement('input');
                    input.className = 'form-check-input ms-2';
                    input.type = 'checkbox';
                    input.id = 'layer_' + layerData.id;
                    
                    div.appendChild(label);
                    div.appendChild(input);
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
                                                // SIMBOLOGIA BRANCA (Símbolo GPS Branco) para Pontos de Deslizamento Registrados
                                                return createWhiteGPSMarker(latlng);
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
                                    
                                    geojsonLayer._layerIdKey = 'layer_' + layerData.id;
                                    if (isRegisteredPoints) {
                                        geojsonLayer.legendHtml = '<span class="legend-gps-white me-1"><i class="bi bi-geo-alt-fill"></i></span><span>' + layerData.name + ' (GPS Branco)</span>';
                                    } else if (isBoundaryOrBuffer) {
                                        geojsonLayer.legendHtml = '<span class="legend-line-dashed-red me-1"></span><span>' + layerData.name + ' (Tracejado Vermelho)</span>';
                                    } else {
                                        geojsonLayer.legendHtml = '<span class="d-inline-block rounded-circle me-1 border shadow-sm" style="width:14px; height:14px; background-color:' + layerColor + ';"></span><span>' + layerData.name + '</span>';
                                    }

                                    activeLegendItems[geojsonLayer._layerIdKey] = geojsonLayer.legendHtml;
                                    updateDynamicLegend();

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
                                if (geojsonLayer._layerIdKey) {
                                    delete activeLegendItems[geojsonLayer._layerIdKey];
                                    updateDynamicLegend();
                                }
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

});

window.previewPdfReport = function(pointId) {
    const pdfUrl = `/api/occurrence/${pointId}/pdf`;
    const frame = document.getElementById('pdfPreviewFrame');
    const dlBtn = document.getElementById('btnDownloadPdfModal');
    if (frame) {
        frame.src = pdfUrl;
    }
    if (dlBtn) {
        dlBtn.href = pdfUrl;
    }
    const modalEl = document.getElementById('modalPdfPreview');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    } else {
        window.open(pdfUrl, '_blank');
    }
};

