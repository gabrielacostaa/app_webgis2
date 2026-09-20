import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

import pptx
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_word_document(filename="relatorio_tese_webgis.docx"):
    doc = docx.Document()
    
    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x2B, 0x2B, 0x2B)

    # Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("DESENVOLVIMENTO E ARQUITETURA DO GEOPORTAL WEBGIS (MOVMASSA) PARA GESTÃO E CURADORIA DE OCORRÊNCIAS DE MOVIMENTO DE MASSA")
    title_run.bold = True
    title_run.font.size = Pt(15)
    title_run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Navy Blue
    
    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle_p.add_run("Capítulo Metodológico para Tese de Doutorado em Agronomia / Ciências Agrárias\n(Redação Acessível para Banca Examinadora)")
    sub_run.italic = True
    sub_run.font.size = Pt(11)
    sub_run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Section 1
    h1 = doc.add_heading(level=1)
    h1_run = h1.add_run("1. Introdução e Contexto Agronômico-Ambiental")
    h1_run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    
    p1 = doc.add_paragraph(
        "A análise e mitigação de riscos associados a movimentos de massa (como deslizamentos de terra, corridas de lama e processos erosivos em encostas) "
        "são temas centrais para a Agronomia, a Ciência do Solo e o Planejamento Agronômico-Ambiental. "
        "A ocorrência desses eventos afeta diretamente a conservação do solo, a estabilidade das bacias hidrográficas e a segurança das populações rurais e periórbana."
    )
    p1.paragraph_format.line_spacing = 1.15
    p1.paragraph_format.space_after = Pt(6)

    p2 = doc.add_paragraph(
        "Para monitorar e gerenciar esses eventos no município de Angra dos Reis - RJ, foi desenvolvido o geoportal interativo denominado MOVMASSA. "
        "O MOVMASSA funciona como um Sistema de Informação Geográfica na Web (WebGIS), ou seja, uma plataforma mapeada que permite visualizar, cadastrar e analisar dados no mapa "
        "diretamente pelo navegador da internet (no celular ou computador), sem a necessidade de instalar programas pesados como o QGIS ou ArcGIS."
    )
    p2.paragraph_format.line_spacing = 1.15
    p2.paragraph_format.space_after = Pt(12)

    # Section 2
    h1 = doc.add_heading(level=1)
    h1_run = h1.add_run("2. Tecnologias Utilizadas Explicadas de Forma Didática")
    h1_run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p3 = doc.add_paragraph(
        "Para possibilitar a criação deste geoportal sem custos com licenças de software e garantindo total transparência científica, "
        "foram utilizadas ferramentas de código aberto (Open-Source). A estrutura da aplicação é comparável ao funcionamento de uma propriedade agrícola "
        "organizada em três setores principais: a 'Interface visual' (o balcão de atendimento), o 'Servidor' (o motor de processamento) e o 'Banco de Dados' (o arquivo central)."
    )
    p3.paragraph_format.line_spacing = 1.15
    p3.paragraph_format.space_after = Pt(8)

    # Table of Technologies
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    hdr_titles = ['Componente', 'Ferramenta Utilizada', 'O que é em termos simples?', 'Função Prática na Agronomia/WebGIS']
    for i, title in enumerate(hdr_titles):
        hdr_cells[i].text = title
        shading_elm = parse_xml(r'<w:shd {} w:fill="1B365D"/>'.format(nsdecls('w')))
        hdr_cells[i]._tc.get_or_add_tcPr().append(shading_elm)
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    tech_data = [
        ("Motor Computacional (Backend)", "Python (Flask)", "Linguagem de programação que atua como o 'cérebro' do sistema no servidor.", "Recebe os dados enviados do campo, processa coordenadas geográficas e controla o fluxo de informações do aplicativo."),
        ("Geoprocessamento Server-Side", "GeoPandas e Shapely", "Ferramentas matemáticas para tratamento de dados geográficos no servidor.", "Lê e converte automaticamente os arquivos de mapa em formatos como Shapefile (.zip), GeoPackage (.gpkg) e GeoJSON."),
        ("Mapa Interativo (Frontend)", "JavaScript com Leaflet.js", "Linguagem visual que constrói o mapa interativo na tela do usuário.", "Desenha o mapa interativo na tela, carrega imagens de satélite (Google Satellite) e agrupa pontos próximos (~100m) para evitar sobreposição."),
        ("Interface e Formulários", "HTML5, CSS3 e Bootstrap", "Linguagens estruturais para criar páginas, botões e formulários elegantes.", "Cria os formulários de cadastro de campo, botões de envio de fotos/vídeos e as abas organizadas do Dicionário de Dados."),
        ("Banco de Dados Relacional", "SQL (SQLite3)", "Um 'arquivo digital organizado' que guarda registros em tabelas interligadas.", "Armazena com segurança as senhas dos usuários e as informações científicas dos 10 domínios ambientais cadastrados."),
        ("Formatos Vetoriais", "GeoJSON, Shapefile e GeoPackage", "Formatos digitais de arquivos geográficos (pontos, linhas e polígonos).", "Representam no mapa os limites municipais, as bacias hidrográficas, as redes de drenagem, as rodovias e os pontos de deslizamento.")
    ]

    for row_idx, row_data in enumerate(tech_data):
        row_cells = table.add_row().cells
        fill_hex = "F0F4F8" if row_idx % 2 == 0 else "FFFFFF"
        for i, text in enumerate(row_data):
            row_cells[i].text = text
            shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), fill_hex))
            row_cells[i]._tc.get_or_add_tcPr().append(shading_elm)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Section 3
    h1 = doc.add_heading(level=1)
    h1_run = h1.add_run("3. Passo a Passo do Desenvolvimento do Sistema MOVMASSA")
    h1_run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    steps = [
        ("Passo 1: Organização e Padronização das Camadas Geográficas", 
         "O primeiro passo consistiu em reunificar e padronizar os dados geográficos do município de Angra dos Reis. Camadas oficiais de órgãos como IBGE e ANA foram convertidas para o sistema geodésico WGS 84 (EPSG:4326), definindo uma nomenclatura padronizada e inteligível para o usuário (ex: 'Área Urbanizada', 'Bacia Hidrográfica', 'Pontos de Deslizamento Registrados' e 'Trechos de Drenagem')."),
        
        ("Passo 2: Construção da Infraestrutura de Servidor e Autenticação", 
         "Com a linguagem Python e o framework Flask, foi estruturado o servidor web. Foi implementado um sistema de acesso seguro com login e senhas criptografadas, permitindo diferenciar três níveis de usuários (RBAC - Controle de Acesso Baseado em Papéis): Usuários Comuns (comunidade/campo), Organizações Parceiras e Administradores (equipe técnica/professores)."),
        
        ("Passo 3: Modelagem do Dicionário de Dados de Riscos e Desastres (10 Domínios)", 
         "Para garantir o rigor técnico exigido na Agronomia e na Gestão de Riscos, o banco de dados foi estruturado em 10 domínios temáticos interligados: (1) Geral/Evento, (2) Fatores Climáticos (chuva/pluviosidade), (3) Pedologia (características do solo), (4) Geomorfologia (relevo e declividade), (5) Geologia (rocha e intemperismo), (6) Fatores Antrópicos (cortes, aterros e desmatamento), (7) Impactos Econômicos, (8) Impactos Sociais, (9) Impactos Ambientais e (10) Registros Multimídia (fotos e vídeos)."),
        
        ("Passo 4: Criação do Mapa Interativo com Imagem de Satélite", 
         "Utilizando a biblioteca JavaScript Leaflet.js, o mapa interativo foi integrado nativamente com imagens de satélite de alta resolução (Google Satellite). Foi adicionado um algoritmo de agrupamento espacial (Leaflet.markercluster) que reúne automaticamente pontos de deslizamento ocorridos a menos de 100 metros de distância, evitando a poluição visual do mapa."),
        
        ("Passo 5: Coleta Participativa em Campo com GPS e Envio de Mídia", 
         "Para simplificar o trabalho dos pesquisadores e técnicos em campo, foi incorporada a tecnologia de geolocalização do navegador (HTML5 Geolocation). Com um simples clique no celular, a coordenada exata (Latitude e Longitude) é preenchida automaticamente no formulário, permitindo também o upload imediato de fotos e vídeos da encosta afetada."),
        
        ("Passo 6: Sistema de Curadoria Científica das Ocorrências Cadastradas", 
         "As ocorrências cadastradas em campo não entram imediatamente como 'públicas' no mapa. Elas passam por uma fila de avaliação no Painel de Administração. Os pesquisadores e professores (administradores) analisam as fotos e o formulário preenchido, podendo aprovar, editar ajustes técnicos ou recusar a submissão, assegurando a confiabilidade científica dos dados exibidos."),
        
        ("Passo 7: Módulo de Exportação de Dados para Softwares de GIS (QGIS/ArcGIS)", 
         "O sistema permite que agrônomos e analistas exportem os dados cadastrados no geoportal em formatos espaciais consagrados (Shapefile em arquivo .zip, GeoPackage e GeoJSON), viabilizando análises espaciais complementares em softwares de geoprocessamento tradicionais."),
        
        ("Passo 8: Segurança e Disponibilização da Aplicação", 
         "As senhas administrativas padrão e chaves de segurança foram devidamente protegidas em variáveis de ambiente. A aplicação foi configurada para execução local e disponibilização via links de tunelamento/nuvem para validação por parceiros e bancas examinadoras.")
    ]

    for title, desc in steps:
        h2 = doc.add_heading(level=2)
        h2_run = h2.add_run(title)
        h2_run.font.color.rgb = RGBColor(0x2E, 0x6B, 0x9E)
        p = doc.add_paragraph(desc)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(8)

    # Section 4
    h1 = doc.add_heading(level=1)
    h1_run = h1.add_run("4. Considerações para a Ciência Agronômica")
    h1_run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_conc = doc.add_paragraph(
        "A construção do geoportal MOVMASSA demonstra como a unão entre a Ciência do Solo, a Geomorfologia e as Geotecnologias Web "
        "pode resultar em ferramentas práticas de tomada de decisão. O aplicativo democratiza o acesso a informações geoespaciais, "
        "permite o diagnóstico rápido de áreas de instabilidade de encostas e oferece um banco de dados padronizado para suporte a políticas públicas "
        "de conservação do solo e planejamento do uso da terra."
    )
    p_conc.paragraph_format.line_spacing = 1.15
    p_conc.paragraph_format.space_after = Pt(12)

    # Section 5: References
    h1 = doc.add_heading(level=1)
    h1_run = h1.add_run("5. Referências Bibliográficas (Formatação ABNT)")
    h1_run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    refs = [
        "AGAFONKIN, V. Leaflet: An Open-Source JavaScript Library for Mobile-Friendly Interactive Maps. Versão 1.9.4. 2023. Disponível em: <https://leafletjs.com/>. Acesso em: 15 set. 2026.",
        "CEBALLOS, F.; GARCIA, M. Web GIS application development using open source JavaScript libraries. Journal of Geographic Information System, v. 11, n. 2, p. 145-158, 2019.",
        "GOODCHILD, M. F. Citizens as sensors: the world of volunteered geography. GeoJournal, v. 69, n. 4, p. 211-221, 2007.",
        "GRASER, A.; OLAYA, V. Processing: a Python framework for the development of spatial data processing algorithms. Transactions in GIS, v. 19, n. 6, p. 869-887, 2015.",
        "GRINBERG, M. Flask Web Development: Developing Web Applications with Python. 2. ed. Sebastopol: O'Reilly Media, 2018.",
        "OPEN GEOSPATIAL CONSORTIUM (OGC). OGC GeoJSON Encoding Standard. OGC Document 17-003r1. Wayland: Open Geospatial Consortium, 2018.",
        "PEBESMA, E.; BIVAND, R. Spatial Data Science: With Applications in R and Python. 1. ed. Boca Raton: CRC Press, 2023."
    ]

    for ref in refs:
        p_ref = doc.add_paragraph(ref)
        p_ref.paragraph_format.space_after = Pt(6)
        p_ref.paragraph_format.line_spacing = 1.0

    doc.save(filename)
    print(f"Documento Word salvo com sucesso: {filename}")

def create_powerpoint_presentation(filename="apresentacao_tese_webgis.pptx"):
    prs = pptx.Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_shape_flat_color(shape, rgb):
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb
        shape.line.fill.background()

    # SLIDE 1: Title Slide
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_flat_color(bg1, PptRGBColor(0x1B, 0x36, 0x5D))

    tb1 = slide1.shapes.add_textbox(PptInches(1.0), PptInches(1.5), PptInches(11.333), PptInches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p1 = tf1.paragraphs[0]
    p1.text = "DESENVOLVIMENTO DO GEOPORTAL WEBGIS MOVMASSA"
    p1.font.bold = True
    p1.font.size = PptPt(32)
    p1.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)
    p1.alignment = PP_ALIGN.LEFT

    p2 = tf1.add_paragraph()
    p2.text = "Geotecnologias Aplicadas à Gestão e Curadoria de Riscos de Movimento de Massa em Angra dos Reis - RJ"
    p2.font.size = PptPt(20)
    p2.font.color.rgb = PptRGBColor(0xCB, 0xD5, 0xE1)
    p2.space_before = PptPt(14)

    p3 = tf1.add_paragraph()
    p3.text = "Apresentação para Banca Examinadora de Doutorado (Agronomia / Ciências Agrárias)"
    p3.font.size = PptPt(16)
    p3.font.italic = True
    p3.font.color.rgb = PptRGBColor(0x94, 0xA3, 0xB8)
    p3.space_before = PptPt(30)

    # SLIDE 2: What is WebGIS & Stack
    slide2 = prs.slides.add_slide(blank_layout)
    bg2 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_flat_color(bg2, PptRGBColor(0xF8, 0xFA, 0xFC))

    # Header Bar
    hbar2 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.2))
    set_shape_flat_color(hbar2, PptRGBColor(0x1B, 0x36, 0x5D))
    tb_h2 = slide2.shapes.add_textbox(PptInches(0.8), PptInches(0.2), PptInches(11.5), PptInches(0.8))
    p_h2 = tb_h2.text_frame.paragraphs[0]
    p_h2.text = "O que é o WebGIS MOVMASSA e Tecnologias Utilizadas?"
    p_h2.font.bold = True
    p_h2.font.size = PptPt(24)
    p_h2.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    # 3 Cards Layout
    card_width = PptInches(3.6)
    card_height = PptInches(5.2)
    card_top = PptInches(1.6)

    col_data = [
        ("Navegador & Mapa (Frontend)", "JavaScript (Leaflet.js) + HTML5", [
            "• O que faz: Desenha o mapa interativo na tela do celular ou PC.",
            "• Imagem de Satélite: Carrega visão Google Satellite de alta resolução.",
            "• Agrupamento (~100m): Reúne pontos próximos em clusters digitais.",
            "• GPS de Campo: Captura coordenadas automáticas via celular."
        ]),
        ("Motor no Servidor (Backend)", "Python 3.9 (Flask) + GeoPandas", [
            "• O que faz: Atua como o 'cérebro' central do sistema.",
            "• Processamento Espacial: Converte e manipula arquivos geográficos.",
            "• Segurança & Login: Protege senhas e controla acessos por perfil.",
            "• Exportação GIS: Gera arquivos Shapefile (.zip), GeoPackage e GeoJSON."
        ]),
        ("Banco de Dados & Dados", "SQL (SQLite3) + Camadas OGC", [
            "• O que faz: Arquivo digital organizado que guarda as informações.",
            "• Dicionário de Dados: Salva 10 domínios (Solo, Relevo, Chuva, Mídia).",
            "• Controle de Acesso: Níveis para Comunidade, Org. e Administradores.",
            "• Camadas Territoriais: IBGE (Limites/Urbano) e ANA (Drenagem/Bacias)."
        ])
    ]

    for idx, (title, sub, items) in enumerate(col_data):
        left_pos = PptInches(0.8 + idx * 4.0)
        card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, card_top, card_width, card_height)
        set_shape_flat_color(card, PptRGBColor(0xFF, 0xFF, 0xFF))
        card.line.color.rgb = PptRGBColor(0xCB, 0xD5, 0xE1)

        tb_card = slide2.shapes.add_textbox(left_pos + PptInches(0.2), card_top + PptInches(0.2), card_width - PptInches(0.4), card_height - PptInches(0.4))
        tf_c = tb_card.text_frame
        tf_c.word_wrap = True

        p_ct = tf_c.paragraphs[0]
        p_ct.text = title
        p_ct.font.bold = True
        p_ct.font.size = PptPt(17)
        p_ct.font.color.rgb = PptRGBColor(0x1B, 0x36, 0x5D)

        p_cs = tf_c.add_paragraph()
        p_cs.text = sub
        p_cs.font.italic = True
        p_cs.font.size = PptPt(13)
        p_cs.font.color.rgb = PptRGBColor(0x2E, 0x6B, 0x9E)
        p_cs.space_after = PptPt(12)

        for item in items:
            p_ci = tf_c.add_paragraph()
            p_ci.text = item
            p_ci.font.size = PptPt(12)
            p_ci.font.color.rgb = PptRGBColor(0x33, 0x41, 0x55)
            p_ci.space_after = PptPt(6)

    # SLIDE 3: Methodology (Steps)
    slide3 = prs.slides.add_slide(blank_layout)
    bg3 = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_flat_color(bg3, PptRGBColor(0xF8, 0xFA, 0xFC))

    hbar3 = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.2))
    set_shape_flat_color(hbar3, PptRGBColor(0x1B, 0x36, 0x5D))
    tb_h3 = slide3.shapes.add_textbox(PptInches(0.8), PptInches(0.2), PptInches(11.5), PptInches(0.8))
    p_h3 = tb_h3.text_frame.paragraphs[0]
    p_h3.text = "Passo a Passo do Desenvolvimento Metodológico"
    p_h3.font.bold = True
    p_h3.font.size = PptPt(24)
    p_h3.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    method_steps = [
        ("1. Padronização de Camadas Espaciais", "Organização das camadas de limites (IBGE), drenagem/bacias (ANA) e áreas urbanizadas no padrão WGS 84."),
        ("2. Estruturação do Servidor & Segurança", "Desenvolvimento do motor em Python (Flask) e banco de dados SQLite com controle de senhas e perfis de acesso."),
        ("3. Dicionário de Dados em 10 Domínios", "Modelagem de formulário técnico abrangendo Clima, Solo (Pedologia), Relevo (Geomorfologia), Antrópico e Mídias."),
        ("4. Mapa Interativo e Curadoria Técnica", "Integração de mapa de satélite, captura GPS em campo pelo celular e painel de validação científica por pesquisadores."),
        ("5. Exportação Multi-Formato (QGIS/ArcGIS)", "Módulo de conversão e download automático dos registros aprovados em Shapefile (.zip), GeoPackage e GeoJSON.")
    ]

    for idx, (st_title, st_desc) in enumerate(method_steps):
        top_pos = PptInches(1.6 + idx * 1.1)
        
        # Step Number Pill
        pill = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.8), top_pos, PptInches(0.6), PptInches(0.9))
        set_shape_flat_color(pill, PptRGBColor(0x2E, 0x6B, 0x9E))
        tf_pill = pill.text_frame
        p_pill = tf_pill.paragraphs[0]
        p_pill.text = str(idx + 1)
        p_pill.font.bold = True
        p_pill.font.size = PptPt(20)
        p_pill.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)
        p_pill.alignment = PP_ALIGN.CENTER

        # Step Text Box
        sbox = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(1.5), top_pos, PptInches(11.0), PptInches(0.9))
        set_shape_flat_color(sbox, PptRGBColor(0xFF, 0xFF, 0xFF))
        sbox.line.color.rgb = PptRGBColor(0xE2, 0xE8, 0xF0)

        tf_sb = sbox.text_frame
        tf_sb.word_wrap = True
        p_st = tf_sb.paragraphs[0]
        p_st.text = st_title
        p_st.font.bold = True
        p_st.font.size = PptPt(15)
        p_st.font.color.rgb = PptRGBColor(0x1B, 0x36, 0x5D)

        p_sd = tf_sb.add_paragraph()
        p_sd.text = st_desc
        p_sd.font.size = PptPt(12)
        p_sd.font.color.rgb = PptRGBColor(0x47, 0x55, 0x69)

    # SLIDE 4: Conclusions for Agronomy & Defense
    slide4 = prs.slides.add_slide(blank_layout)
    bg4 = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_flat_color(bg4, PptRGBColor(0xF8, 0xFA, 0xFC))

    hbar4 = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.2))
    set_shape_flat_color(hbar4, PptRGBColor(0x1B, 0x36, 0x5D))
    tb_h4 = slide4.shapes.add_textbox(PptInches(0.8), PptInches(0.2), PptInches(11.5), PptInches(0.8))
    p_h4 = tb_h4.text_frame.paragraphs[0]
    p_h4.text = "Aplicações Agronômicas e Contribuição Científica"
    p_h4.font.bold = True
    p_h4.font.size = PptPt(24)
    p_h4.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    # Left Box - Benefits
    box_l = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.8), PptInches(1.6), PptInches(5.7), PptInches(5.2))
    set_shape_flat_color(box_l, PptRGBColor(0xFF, 0xFF, 0xFF))
    box_l.line.color.rgb = PptRGBColor(0xCB, 0xD5, 0xE1)

    tf_bl = box_l.text_frame
    tf_bl.word_wrap = True
    p_blt = tf_bl.paragraphs[0]
    p_blt.text = "Relevância para a Ciência Agronômica"
    p_blt.font.bold = True
    p_blt.font.size = PptPt(18)
    p_blt.font.color.rgb = PptRGBColor(0x1B, 0x36, 0x5D)
    p_blt.space_after = PptPt(12)

    agri_points = [
        "✔ Conservação do Solo e Água: Mapeamento detalhado de feições erosivas e instabilidades de encosta.",
        "✔ Planejamento do Uso da Terra: Integração de declividade, pedologia e fatores antrópicos na bacia hidrográfica.",
        "✔ Monitoramento Participativo: Coleta simplificada em campo por técnicos e produtores via celular.",
        "✔ Suporte à Tomada de Decisão: Base confiável e validada para políticas públicas de gestão de riscos ambientais."
    ]
    for pt in agri_points:
        p_pt = tf_bl.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = PptPt(13)
        p_pt.font.color.rgb = PptRGBColor(0x33, 0x41, 0x55)
        p_pt.space_after = PptPt(10)

    # Right Box - Key Citations
    box_r = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(6.8), PptInches(1.6), PptInches(5.7), PptInches(5.2))
    set_shape_flat_color(box_r, PptRGBColor(0x1B, 0x36, 0x5D))

    tf_br = box_r.text_frame
    tf_br.word_wrap = True
    p_brt = tf_br.paragraphs[0]
    p_brt.text = "Fundamentação Teórico-Científica"
    p_brt.font.bold = True
    p_brt.font.size = PptPt(18)
    p_brt.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)
    p_brt.space_after = PptPt(12)

    cites = [
        "• Graser & Olaya (2015): Relevância de algoritmos em ambiente open-source para geoprocessamento.",
        "• Pebesma & Bivand (2023): Ciência de Dados Espaciais aplicada com linguagens de programação.",
        "• Goodchild (2007): Geografia Voluntária (VGI) como ferramenta de sensoriamento participativo.",
        "• Open Geospatial Consortium (2018): Interoperabilidade e padronização de dados espaciais (GeoJSON)."
    ]
    for cite in cites:
        p_ct = tf_br.add_paragraph()
        p_ct.text = cite
        p_ct.font.size = PptPt(13)
        p_ct.font.color.rgb = PptRGBColor(0xE2, 0xE8, 0xF0)
        p_ct.space_after = PptPt(10)

    prs.save(filename)
    print(f"Apresentação PowerPoint salva com sucesso: {filename}")

if __name__ == "__main__":
    create_word_document()
    create_powerpoint_presentation()
