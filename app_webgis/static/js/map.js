document.addEventListener("DOMContentLoaded", function() {
    // Inicializa o mapa focado em Angra dos Reis
    var map = L.map('map').setView([-23.00, -44.31], 10);

    // 1. Definição dos 3 Mapas de Fundo (Basemaps)
    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    });

    var esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    });

    var googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains:['mt0','mt1','mt2','mt3'],
        attribution: '&copy; Google'
    });

    var cartoPositron = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    });

    // Adiciona o Google Satélite como padrão
    googleSat.addTo(map);

    var baseMaps = {
        "Google Satellite": googleSat,
        "Carto Positron (Claro)": cartoPositron,
        "OpenStreetMap": osm,
        "Satélite (Esri)": esriSatellite
    };

    var overlayMaps = {};
    var layerControl = L.control.layers(baseMaps, overlayMaps, { collapsed: false }).addTo(map);

    // Variável para armazenar cores aleatórias para as camadas
    function getRandomColor() {
        var letters = '0123456789ABCDEF';
        var color = '#';
        for (var i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Função para montar o popup a partir das propriedades (atributos) do GeoJSON
    function onEachFeature(feature, layer) {
        if (feature.properties) {
            let popupContent = '<table class="table table-sm table-striped"><tbody>';
            for (let p in feature.properties) {
                popupContent += `<tr><th>${p}</th><td>${feature.properties[p]}</td></tr>`;
            }
            popupContent += '</tbody></table>';
            layer.bindPopup(popupContent, { maxHeight: 300 });
        }
    }

    // Carregar as camadas da API
    fetch('/api/layers')
        .then(response => response.json())
        .then(layers => {
            const layerListDiv = document.getElementById('layer-list');
            layerListDiv.innerHTML = ''; // Limpa o spinner
            
            if (layers.length === 0) {
                layerListDiv.innerHTML = '<p class="text-muted">Nenhuma camada publicada.</p>';
                return;
            }

            layers.forEach(layerData => {
                // Adiciona um checkbox na sidebar
                const div = document.createElement('div');
                div.className = 'form-check mb-2';
                
                const input = document.createElement('input');
                input.className = 'form-check-input';
                input.type = 'checkbox';
                input.id = 'layer_' + layerData.id;
                
                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = 'layer_' + layerData.id;
                label.innerHTML = `<strong>${layerData.name}</strong> <br><small class="text-muted">${layerData.category}</small>`;
                
                div.appendChild(input);
                div.appendChild(label);
                layerListDiv.appendChild(div);

                let geojsonLayer = null;

                // Evento de ativar/desativar camada
                input.addEventListener('change', function() {
                    if (this.checked) {
                        // Desabilita o checkbox enquanto carrega para evitar cliques duplos
                        this.disabled = true;
                        label.innerHTML += ' <span class="spinner-border spinner-border-sm text-primary" role="status"></span>';

                        fetch('/api/layer/' + layerData.filename)
                            .then(res => res.json())
                            .then(data => {
                                let layerColor = getRandomColor();
                                
                                geojsonLayer = L.geoJSON(data, {
                                    style: function (feature) {
                                        return {
                                            color: layerColor,
                                            weight: 2,
                                            opacity: 1,
                                            fillOpacity: 0.4
                                        };
                                    },
                                    pointToLayer: function (feature, latlng) {
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
                                
                                // Adiciona no controle do Leaflet também
                                layerControl.addOverlay(geojsonLayer, layerData.name);
                                
                                // Se for a primeira camada ativada (Limites de Angra, por exemplo), ajusta o zoom
                                if(layerData.filename.includes('angra.geojson')) {
                                    map.fitBounds(geojsonLayer.getBounds());
                                }
                            })
                            .catch(err => {
                                console.error('Erro ao carregar ' + layerData.name, err);
                                alert('Erro ao carregar a camada ' + layerData.name);
                            })
                            .finally(() => {
                                this.disabled = false;
                                // Remove o spinner do texto
                                label.innerHTML = `<strong>${layerData.name}</strong> <br><small class="text-muted">${layerData.category}</small>`;
                            });
                    } else {
                        if (geojsonLayer) {
                            map.removeLayer(geojsonLayer);
                            layerControl.removeLayer(geojsonLayer);
                            geojsonLayer = null;
                        }
                    }
                });
            });
        })
        .catch(err => {
            console.error("Erro ao buscar camadas da API:", err);
            document.getElementById('layer-list').innerHTML = '<p class="text-danger">Erro ao carregar camadas.</p>';
        });

    // Carregar ocorrências da Curadoria e agrupar com MarkerCluster
    fetch('/api/occurrences')
        .then(response => response.json())
        .then(data => {
            if (data.features && data.features.length > 0) {
                var markers = L.markerClusterGroup({
                    maxClusterRadius: 50 // Agrupa pontos que estão a aproximadamente 100m no nível de zoom
                });

                var geoJsonLayer = L.geoJSON(data, {
                    onEachFeature: function(feature, layer) {
                        let p = feature.properties;
                        let popupContent = `
                            <div style="max-width: 350px; font-size: 11px; max-height: 400px; overflow-y: auto;">
                                <h6 class="fw-bold mb-1 text-primary">${p.title || 'Ocorrência'}</h6>
                                <span class="badge bg-danger mb-2">${p.tipologia || 'Evento registrado'}</span>
                                <span class="badge bg-secondary mb-2">${p.municipio || 'Angra dos Reis'} - ${p.uf || 'RJ'}</span>
                                
                                <div class="accordion accordion-flush" id="popupAccordion_${p.id}">
                                  <!-- Geral -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button p-2 text-primary" type="button" data-bs-toggle="collapse" data-bs-target="#c1_${p.id}">
                                        📌 Evento & Localização
                                      </button>
                                    </h2>
                                    <div id="c1_${p.id}" class="accordion-collapse collapse show">
                                      <div class="accordion-body p-1">
                                        <table class="table table-sm table-striped mb-0" style="font-size:10px;">
                                            <tr><th>Data</th><td>${p.data_evento || '-'}</td></tr>
                                            <tr><th>Bairro</th><td>${p.bairro || '-'}</td></tr>
                                            <tr><th>Zona</th><td>${p.zona || '-'}</td></tr>
                                            <tr><th>Coord (Y, X)</th><td>${p.lat}, ${p.lng}</td></tr>
                                            <tr><th>% Área Atingida</th><td>Urbana: ${p.perc_area_atu || '-'} | Agrícola: ${p.perc_area_atr || '-'}</td></tr>
                                        </table>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  <!-- Clima & Pedologia -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button collapsed p-2" type="button" data-bs-toggle="collapse" data-bs-target="#c2_${p.id}">
                                        ⛅ Clima & Pedologia
                                      </button>
                                    </h2>
                                    <div id="c2_${p.id}" class="accordion-collapse collapse">
                                      <div class="accordion-body p-1">
                                        <table class="table table-sm table-striped mb-0" style="font-size:10px;">
                                            <tr><th>Precipitação</th><td>Evento: ${p.clima_precipitacao_evento || '-'} mm | Mensal: ${p.clima_precipitacao_mensal || '-'} mm</td></tr>
                                            <tr><th>Acumulado 5d / 10d</th><td>${p.clima_precipitacao_5d || '-'} mm / ${p.clima_precipitacao_10d || '-'} mm</td></tr>
                                            <tr><th>Vento / Temp / Pressão</th><td>${p.clima_vento || '-'} m/s | ${p.clima_temperatura || '-'} ºC | ${p.clima_pressao || '-'} atm</td></tr>
                                            <tr><th>Classe de Solo / Textura</th><td>${p.ped_classe_solo || '-'} | ${p.ped_textura || '-'}</td></tr>
                                            <tr><th>Porosidade / Umidade</th><td>${p.ped_porosidade || '-'} % | ${p.ped_umidade_evento || '-'}</td></tr>
                                        </table>
                                      </div>
                                    </div>
                                  </div>

                                  <!-- Geomorfologia & Geologia -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button collapsed p-2" type="button" data-bs-toggle="collapse" data-bs-target="#c3_${p.id}">
                                        ⛰️ Geologia & Relevo
                                      </button>
                                    </h2>
                                    <div id="c3_${p.id}" class="accordion-collapse collapse">
                                      <div class="accordion-body p-1">
                                        <table class="table table-sm table-striped mb-0" style="font-size:10px;">
                                            <tr><th>Declividade / Altitude</th><td>${p.geo_declividade || '-'} % | ${p.geo_altitude || '-'} m</td></tr>
                                            <tr><th>Forma Terreno / Curvatura</th><td>${p.geo_forma_terreno || '-'} | ${p.geo_curvatura || '-'}</td></tr>
                                            <tr><th>Tipo de Rocha / Idade</th><td>${p.geol_tipo_rocha || '-'} | ${p.geol_idade || '-'}</td></tr>
                                            <tr><th>Estrutura / Tectonismo</th><td>${p.geol_estrutura || '-'} | Tectonismo: ${p.geol_tectonismo || '-'}</td></tr>
                                            <tr><th>Fatores Antrópicos</th><td>Escavação: ${p.antrop_escavacao || '-'} | Mineração: ${p.antrop_mineracao || '-'}</td></tr>
                                        </table>
                                      </div>
                                    </div>
                                  </div>

                                  <!-- Impactos Sociais, Econômicos e Ambientais -->
                                  <div class="accordion-item">
                                    <h2 class="accordion-header">
                                      <button class="accordion-button collapsed p-2 text-danger" type="button" data-bs-toggle="collapse" data-bs-target="#c4_${p.id}">
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

                                <div class="mt-2 mb-1"><strong>Descrição:</strong> ${p.description || '-'}</div>
                        `;
                        if (p.media_url) {
                            let filename = (p.media_filename || p.media_url).toLowerCase();
                            if (filename.endsWith('.mp4') || filename.endsWith('.mov') || filename.endsWith('.webm')) {
                                popupContent += `<video width="100%" controls src="${p.media_url}"></video>`;
                            } else {
                                popupContent += `<img src="${p.media_url}" width="100%" class="rounded mt-1">`;
                            }
                        }
                        popupContent += `</div>`;
                        layer.bindPopup(popupContent, { maxWidth: 360 });
                    }
                });

                markers.addLayer(geoJsonLayer);
                map.addLayer(markers);
                layerControl.addOverlay(markers, "Ocorrências de Usuários");
            }
        })
        .catch(err => console.error("Erro ao carregar ocorrências: ", err));

});
