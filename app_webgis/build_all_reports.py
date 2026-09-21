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

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def generate_thesis_docx(filepath="app_webgis/relatorio_tese_webgis_att.docx"):
    doc = docx.Document()
    
    # Margens padrão da página (2,54 cm = 1.0 polegada)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Estilo Normal (Corpo do texto)
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x2B, 0x2B, 0x2B)

    # Título Principal
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("DESENVOLVIMENTO E ARQUITETURA DO GEOPORTAL WEBGIS (MOVMASSA) PARA GESTÃO E CURADORIA DE OCORRÊNCIAS DE MOVIMENTO DE MASSA")
    r_title.bold = True
    r_title.font.size = Pt(15)
    r_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Azul Marinho
    p_title.paragraph_format.space_after = Pt(4)

    # Subtítulo
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Capítulo Metodológico Atualizado para Tese de Doutorado em Agronomia / Ciência do Solo\n(Redação Didática Voltada para Pesquisadores das Ciências Agrárias e Ambientais)")
    r_sub.italic = True
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    p_sub.paragraph_format.space_after = Pt(18)

    # --- Seção 1 ---
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("1. Introdução e Contexto Agronômico-Pedológico")
    r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    
    p1 = doc.add_paragraph(
        "A análise e a mitigação dos riscos associados a movimentos de massa — tais como deslizamentos de encostas, escorregamentos rotacionais e processos erosivos acelerados — "
        "representam temas prioritários para a Ciência do Solo, a Engenharia Agronômica e a Gestão Ambiental de Bacias Hidrográficas. "
        "No município de Angra dos Reis - RJ, marcado por um relevo acidentado na Serra do Mar e elevados índices pluviométricos acumulados, "
        "a degradação das encostas compromete a fertilidade dos solos, provoca o assoreamento dos corpos d'água e ameaça a infraestrutura rural e urbana."
    )
    p1.paragraph_format.line_spacing = 1.15
    p1.paragraph_format.space_after = Pt(6)

    p2 = doc.add_paragraph(
        "Para responder a esse desafio sem a necessidade de softwares complexos de geoprocessamento em cada computador de campo, foi desenvolvido o Geoportal WebGIS denominado MOVMASSA. "
        "O MOVMASSA é uma plataforma cartográfica interativa acessível via navegador de internet (em celulares ou computadores). "
        "Ele possibilita a coleta contínua de dados de campo, a visualização de feições erosivas sobre imagens de satélite e a integração participativa entre técnicos da Defesa Civil e a comunidade científica."
    )
    p2.paragraph_format.line_spacing = 1.15
    p2.paragraph_format.space_after = Pt(12)

    # --- Seção 2 ---
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("2. Arquitetura da Aplicação Explicada para Cientistas do Solo")
    r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p3 = doc.add_paragraph(
        "Para garantir autonomia tecnológica e custo zero em licenças de software, o sistema foi totalmente concebido com ferramentas de código aberto (Open-Source). "
        "Para os pesquisadores da Ciência do Solo, a estrutura do WebGIS pode ser compreendida pela analogia com uma estação experimental organizada em três setores funcionais:"
    )
    p3.paragraph_format.line_spacing = 1.15
    p3.paragraph_format.space_after = Pt(8)

    # Marcadores Explicativos
    bullets = [
        ("Interface Visual de Campo (Frontend): ", "Corresponde ao 'mapa na tela'. É a camada construída com HTML5, CSS e a biblioteca JavaScript Leaflet.js, responsável por desenhar o mapa interativo, carregar imagens de satélite (Google Satellite) e agrupar ocorrências próximas em um raio de 100 metros (clusters) para evitar poluição visual."),
        ("Motor Computacional (Backend): ", "Atua como o 'centro de processamento' da estação. Desenvolvido na linguagem Python com o framework Flask e GeoPandas, o motor recebe os formulários de campo, calcula coordenadas de GPS, executa validações técnicas e gerencia a exportação de dados."),
        ("Arquivo Digital de Dados (Banco de Dados): ", "É o 'repositório estruturado' (banco SQL em SQLite3/PostgreSQL). Armazena com segurança os dados cadastrais e as informações técnicas dos 10 domínios ambientais (pedologia, clima, relevo, geologia e impactos).")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        r_bt = bp.add_run(b_title)
        r_bt.bold = True
        r_bt.font.color.rgb = RGBColor(0x2E, 0x6B, 0x9E)
        bp.add_run(b_desc)
        bp.paragraph_format.line_spacing = 1.15
        bp.paragraph_format.space_after = Pt(4)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Tabela de Tecnologias
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    hdr_titles = ['Componente', 'Ferramenta Tecnológica', 'Conceito Simples', 'Aplicação Prática em Ciência do Solo']
    for i, title in enumerate(hdr_titles):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "1B365D")
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    tech_data = [
        ("Motor de Processamento", "Python (Flask)", "Linguagem de programação que processa dados no servidor.", "Calcula coordenadas GPS, organiza imagens de campo e valida regras de acesso."),
        ("Tratamento Espacial", "GeoPandas e Shapely", "Bibliotecas para geometria e mapas vetoriais.", "Lê e converte automaticamente arquivos Shapefile (.zip), GeoPackage (.gpkg) e GeoJSON."),
        ("Mapa Interativo", "JavaScript (Leaflet.js)", "Biblioteca visual de mapas dinâmicos.", "Renderiza o mapa com fundo de satélite e agrupa pontos próximos em ícones dinâmicos."),
        ("Formulários e Visual", "HTML5, CSS3, Bootstrap", "Linguagens de estruturação de páginas.", "Cria abas intuitivas para o Dicionário de Dados e botões de upload massivo de arquivos."),
        ("Banco de Dados", "SQL (SQLite3 / Postgres)", "Arquivo digital relacional seguro.", "Guarda o histórico de ocorrências e os dados ambientais (Textura, Cambissolo, Pluviosidade)."),
        ("Camadas Cartográficas", "IBGE e ANA (WGS 84)", "Arquivos de limites e redes hidrográficas.", "Projeta no mapa os limites municipais de Angra dos Reis, bacias e redes de drenagem.")
    ]

    for row_idx, row_data in enumerate(tech_data):
        row_cells = table.add_row().cells
        fill_hex = "F0F4F8" if row_idx % 2 == 0 else "FFFFFF"
        for i, text in enumerate(row_data):
            row_cells[i].text = text
            set_cell_background(row_cells[i], fill_hex)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- Seção 3 ---
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("3. Governança Territorial e Controle de Acesso (RBAC) por Esferas")
    r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_gov = doc.add_paragraph(
        "Um dos grandes avanços incorporados à plataforma foi a estruturação de um sistema de controle de acesso rigoroso, "
        "baseado em níveis institucionais e responsabilidade científica. Para assegurar a integridade dos dados e impedir duplicidades ou alterações indevidas, "
        "o sistema define papéis claros para cada usuário do WebGIS:"
    )
    p_gov.paragraph_format.line_spacing = 1.15
    p_gov.paragraph_format.space_after = Pt(8)

    gov_roles = [
        ("Administrador Geral: ", "Possui visibilidade e poder de edição/exclusão irrestrito sobre todas as esferas (Nacional, Estadual e Municipal). É responsável por nomear os Gestores institucionais."),
        ("Gestores da Defesa Civil (Nacional, Estadual e Municipal): ", "Nomeados para gerenciar sua respectiva esfera administrativa. Podem cadastrar novos Agentes de Campo para sua jurisdição, aprovar/rejeitar submissões pendentes e editar/excluir qualquer ocorrência cadastrada por agentes da sua esfera."),
        ("Agentes de Campo (Defesa Civil): ", "Possuem autonomia total para realizar levantamentos de campo (cadastro de 1 ponto com GPS, upload massivo de Shapefiles em .zip e tabelas em CSV). No painel de Curadoria Técnica, possuem visibilidade transparente de todos os registros da rede, contudo podem editar e excluir exclusivamente os registros inseridos por eles mesmos (verificado via parâmetro de propriedade user_id == current_user.id). Não possuem acesso à área de gestão de usuários nem permissão para aprovar/rejeitar submissões institucionais.")
    ]

    for r_title, r_desc in gov_roles:
        bp = doc.add_paragraph(style='List Bullet')
        r_bt = bp.add_run(r_title)
        r_bt.bold = True
        r_bt.font.color.rgb = RGBColor(0x2E, 0x6B, 0x9E)
        bp.add_run(r_desc)
        bp.paragraph_format.line_spacing = 1.15
        bp.paragraph_format.space_after = Pt(6)

    p_sec = doc.add_paragraph(
        "Além disso, o sistema conta com dois mecanismos essenciais de validação cadastral: "
        "(1) Validação Única por CPF, que impede que um mesmo agente seja cadastrado duplicadamente em esferas distintas da Defesa Civil; "
        "e (2) Login Automático via E-mail Institucional, evitando redundâncias de nomes de usuários entre diferentes municípios ou estados."
    )
    p_sec.paragraph_format.line_spacing = 1.15
    p_sec.paragraph_format.space_after = Pt(12)

    # --- Seção 4 ---
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("4. Etapas Metodológicas do Desenvolvimento do WebGIS MOVMASSA")
    r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    steps = [
        ("Passo 1: Padronização das Camadas Cartográficas e Pedológicas", 
         "Reunificação e conversão de dados geoespaciais de órgãos oficiais (IBGE, ANA, CPRM) para o datum WGS 84 (EPSG:4326). Camadas como 'Áreas Urbanizadas', 'Limites Municipais', 'Bacias Hidrográficas' e 'Rede de Drenagem' foram padronizadas para superposição no mapa."),
        
        ("Passo 2: Configuração do Servidor e Segurança Cadastral", 
         "Estruturação do motor Flask em Python e banco relacional. Implementação de criptografia de senhas (Scrypt) e integração de campos obrigatórios (CPF e Matrícula Funcional), garantindo rastreabilidade oficial de todos os registros."),
        
        ("Passo 3: Modelagem do Dicionário de Dados Ambiental (10 Domínios)", 
         "Criação de formulários técnicos abrangendo: (1) Geral/Evento, (2) Clima/Precipitação, (3) Pedologia (Classe de solo, profundidade do regolito, textura, porosidade), (4) Geomorfologia (declividade, altitude, forma do terreno), (5) Geologia, (6) Fatores Antrópicos, (7) Impactos Econômicos, (8) Impactos Sociais, (9) Impactos Ambientais e (10) Mídias (Fotos e Vídeos)."),
        
        ("Passo 4: Desenvolvimento do Mapa Interativo com Imagem de Satélite", 
         "Integração do mapa visual com fundo de alta resolução Google Satellite e mecanismo automático de agrupamento espacial (Clusters a ~100m), permitindo navegar fluidamente pelas encostas de Angra dos Reis."),
        
        ("Passo 5: Coleta Participativa em Campo com GPS Mobile", 
         "Implementação da API de Geolocalização (HTML5) no navegador do celular, permitindo captura instantânea de Latitude e Longitude durante vistorias técnicas de campo, acompanhada de upload direto de fotos e vídeos."),
        
        ("Passo 6: Painel de Curadoria Técnica e Validação Científica", 
         "Fila de controle de qualidade onde ocorrências passam por avaliação. Gestores podem aprovar registros e torná-los camadas ativas, enquanto Agentes possuem a prerrogativa de gerenciar e atualizar os seus próprios pontos."),
        
        ("Passo 7: Emissão de Relatórios Técnicos PDF e Exportação GIS", 
         "Módulo de geração dinâmica de fichas completas de ocorrência em PDF e ferramenta de exportação em Shapefile (.zip), GeoPackage e GeoJSON para análises avançadas no QGIS ou ArcGIS."),
        
        ("Passo 8: Deploy Continuo e Disponibilização na Nuvem", 
         "Configuração e versionamento em repositório GitHub (gabrielacostaa/app_webgis2) com deploy automatizado no Render, assegurando estabilidade e acessibilidade pública.")
    ]

    for title, desc in steps:
        h2 = doc.add_heading(level=2)
        r_h2 = h2.add_run(title)
        r_h2.font.color.rgb = RGBColor(0x2E, 0x6B, 0x9E)
        p = doc.add_paragraph(desc)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(8)

    # --- Seção 5 ---
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("5. Aplicação Prática na Ciência do Solo e Conservação do Meio Ambiente")
    r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_conc = doc.add_paragraph(
        "A integração entre a Ciência do Solo, a Pedologia e as Geotecnologias Web no MOVMASSA proporciona uma ferramenta robusta para o planejamento ambiental. "
        "Permite correlacionar classes de solos (como Cambissolos e Latossolos em declives acentuados) com acumulados pluviométricos críticos, "
        "fornecendo subsídios científicos para planos de contingência, zoneamento de uso do solo e prevenção contra a perda de horizontes férteis em bacias hidrográficas."
    )
    p_conc.paragraph_format.line_spacing = 1.15
    p_conc.paragraph_format.space_after = Pt(12)

    # --- Seção 6 ---
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("6. Referências Bibliográficas (Formatação ABNT)")
    r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    refs = [
        "AGAFONKIN, V. Leaflet: An Open-Source JavaScript Library for Mobile-Friendly Interactive Maps. Versão 1.9.4. 2023. Disponível em: <https://leafletjs.com/>. Acesso em: 15 set. 2026.",
        "CEBALLOS, F.; GARCIA, M. Web GIS application development using open source JavaScript libraries. Journal of Geographic Information System, v. 11, n. 2, p. 145-158, 2019.",
        "EMBRAPA - EMPRESA BRASILEIRA DE PESQUISA AGROPECUÁRIA. Sistema Brasileiro de Classificação de Solos. 5. ed. Brasília, DF: Embrapa, 2018. 356 p.",
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

    doc.save(filepath)
    print(f"Documento DOCX atualizado salvo com sucesso em: {filepath}")

def generate_pptx_presentation(filepath="app_webgis/apresentacao_tese_webgis.pptx"):
    prs = pptx.Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_shape_color(shape, fill_rgb, line_rgb=None):
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_rgb
        if line_rgb:
            shape.line.color.rgb = line_rgb
        else:
            shape.line.fill.background()

    # SLIDE 1: Título
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_color(bg1, PptRGBColor(0x1B, 0x36, 0x5D))

    tb1 = s1.shapes.add_textbox(PptInches(1.0), PptInches(1.5), PptInches(11.333), PptInches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p1 = tf1.paragraphs[0]
    p1.text = "DESENVOLVIMENTO DO GEOPORTAL WEBGIS MOVMASSA"
    p1.font.bold = True
    p1.font.size = PptPt(30)
    p1.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    p2 = tf1.add_paragraph()
    p2.text = "Geotecnologias Aplicadas à Ciência do Solo, Gestão de Riscos e Curadoria Técnica de Encostas"
    p2.font.size = PptPt(20)
    p2.font.color.rgb = PptRGBColor(0xCB, 0xD5, 0xE1)
    p2.space_before = PptPt(14)

    p3 = tf1.add_paragraph()
    p3.text = "Apresentação para Banca Examinadora de Doutorado (Agronomia / Ciência do Solo)"
    p3.font.size = PptPt(15)
    p3.font.italic = True
    p3.font.color.rgb = PptRGBColor(0x94, 0xA3, 0xB8)
    p3.space_before = PptPt(30)

    # SLIDE 2: Tecnologias
    s2 = prs.slides.add_slide(blank_layout)
    bg2 = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_color(bg2, PptRGBColor(0xF8, 0xFA, 0xFC))

    hbar2 = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.2))
    set_shape_color(hbar2, PptRGBColor(0x1B, 0x36, 0x5D))
    tb_h2 = s2.shapes.add_textbox(PptInches(0.8), PptInches(0.2), PptInches(11.5), PptInches(0.8))
    p_h2 = tb_h2.text_frame.paragraphs[0]
    p_h2.text = "Arquitetura Didática do WebGIS MOVMASSA"
    p_h2.font.bold = True
    p_h2.font.size = PptPt(24)
    p_h2.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    cards_data = [
        ("Visual & Mapa (Frontend)", "JavaScript (Leaflet.js)", [
            "• Renderização de mapa dinâmico com satélite.",
            "• Agrupamento espacial (~100m) em clusters.",
            "• Geolocalização automática por GPS móvel.",
            "• Upload direto de fotos e vídeos da encosta."
        ]),
        ("Motor no Servidor (Backend)", "Python 3.9 (Flask) + GeoPandas", [
            "• Processamento de coordenadas e geometrias.",
            "• Validação de regras de acesso (RBAC).",
            "• Geração de relatórios técnicos em PDF.",
            "• Exportação GIS (Shapefile .zip, GeoJSON)."
        ]),
        ("Dados Ambientais (SQL)", "SQLite3 / PostgreSQL", [
            "• Dicionário de Dados com 10 domínios.",
            "• Dados de Pedologia, Clima, Relevo e Mídia.",
            "• Bloqueio de duplicidade por CPF do agente.",
            "• Histórico oficial com rastreabilidade."
        ])
    ]

    card_width = PptInches(3.6)
    card_height = PptInches(5.2)
    card_top = PptInches(1.6)

    for idx, (ctitle, csub, citems) in enumerate(cards_data):
        left_pos = PptInches(0.8 + idx * 4.0)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, card_top, card_width, card_height)
        set_shape_color(card, PptRGBColor(0xFF, 0xFF, 0xFF), PptRGBColor(0xCB, 0xD5, 0xE1))

        tb_card = s2.shapes.add_textbox(left_pos + PptInches(0.2), card_top + PptInches(0.2), card_width - PptInches(0.4), card_height - PptInches(0.4))
        tf_c = tb_card.text_frame
        tf_c.word_wrap = True

        p_ct = tf_c.paragraphs[0]
        p_ct.text = ctitle
        p_ct.font.bold = True
        p_ct.font.size = PptPt(16)
        p_ct.font.color.rgb = PptRGBColor(0x1B, 0x36, 0x5D)

        p_cs = tf_c.add_paragraph()
        p_cs.text = csub
        p_cs.font.italic = True
        p_cs.font.size = PptPt(12)
        p_cs.font.color.rgb = PptRGBColor(0x2E, 0x6B, 0x9E)
        p_cs.space_after = PptPt(12)

        for item in citems:
            p_ci = tf_c.add_paragraph()
            p_ci.text = item
            p_ci.font.size = PptPt(12)
            p_ci.font.color.rgb = PptRGBColor(0x33, 0x41, 0x55)
            p_ci.space_after = PptPt(6)

    # SLIDE 3: Governança
    s3 = prs.slides.add_slide(blank_layout)
    bg3 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_color(bg3, PptRGBColor(0xF8, 0xFA, 0xFC))

    hbar3 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.2))
    set_shape_color(hbar3, PptRGBColor(0x1B, 0x36, 0x5D))
    tb_h3 = s3.shapes.add_textbox(PptInches(0.8), PptInches(0.2), PptInches(11.5), PptInches(0.8))
    p_h3 = tb_h3.text_frame.paragraphs[0]
    p_h3.text = "Governança Territorial e Níveis de Permissão"
    p_h3.font.bold = True
    p_h3.font.size = PptPt(24)
    p_h3.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    gov_cards = [
        ("Agentes de Campo", "Autonomia de Levantamento", [
            "✔ Cadastram pontos individuais e massivos (Shapefile/CSV).",
            "✔ Visualizam a Curadoria Técnica completa para transparência.",
            "✔ Editam e excluem EXCLUSIVAMENTE os seus próprios pontos.",
            "✖ Não aprovam/rejeitam submissões nem gerenciam usuários."
        ]),
        ("Gestores por Esfera", "Nacional, Estadual e Municipal", [
            "✔ Cadastram agentes exclusivamente da sua esfera administrativa.",
            "✔ Editam, aprovam, rejeitam e excluem QUALQUER ponto de sua esfera.",
            "✔ Garantem o controle de qualidade institucional dos dados.",
            "✖ Não alteram cadastros de esferas paralelas."
        ]),
        ("Admin Geral", "Gestão Científica e Global", [
            "✔ Acesso total e irrestrito sobre todas as esferas e dados.",
            "✔ Nomeia os Gestores da Defesa Civil e Organizações.",
            "✔ Gerencia o banco de dados e as camadas globais do geoportal.",
            "✔ Exporta bases completas para análises de doutorado."
        ])
    ]

    for idx, (gtitle, gsub, gitems) in enumerate(gov_cards):
        left_pos = PptInches(0.8 + idx * 4.0)
        card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, card_top, card_width, card_height)
        set_shape_color(card, PptRGBColor(0xFF, 0xFF, 0xFF), PptRGBColor(0xCB, 0xD5, 0xE1))

        tb_card = s3.shapes.add_textbox(left_pos + PptInches(0.2), card_top + PptInches(0.2), card_width - PptInches(0.4), card_height - PptInches(0.4))
        tf_c = tb_card.text_frame
        tf_c.word_wrap = True

        p_gt = tf_c.paragraphs[0]
        p_gt.text = gtitle
        p_gt.font.bold = True
        p_gt.font.size = PptPt(16)
        p_gt.font.color.rgb = PptRGBColor(0x1B, 0x36, 0x5D)

        p_gs = tf_c.add_paragraph()
        p_gs.text = gsub
        p_gs.font.italic = True
        p_gs.font.size = PptPt(12)
        p_gs.font.color.rgb = PptRGBColor(0x2E, 0x6B, 0x9E)
        p_gs.space_after = PptPt(12)

        for item in gitems:
            p_gi = tf_c.add_paragraph()
            p_gi.text = item
            p_gi.font.size = PptPt(12)
            p_gi.font.color.rgb = PptRGBColor(0x33, 0x41, 0x55)
            p_gi.space_after = PptPt(6)

    # SLIDE 4: Passo a Passo
    s4 = prs.slides.add_slide(blank_layout)
    bg4 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_color(bg4, PptRGBColor(0xF8, 0xFA, 0xFC))

    hbar4 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.2))
    set_shape_color(hbar4, PptRGBColor(0x1B, 0x36, 0x5D))
    tb_h4 = s4.shapes.add_textbox(PptInches(0.8), PptInches(0.2), PptInches(11.5), PptInches(0.8))
    p_h4 = tb_h4.text_frame.paragraphs[0]
    p_h4.text = "Fluxo Metodológico do Desenvolvimento"
    p_h4.font.bold = True
    p_h4.font.size = PptPt(24)
    p_h4.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    msteps = [
        ("1. Padronização Cartográfica WGS 84", "Reunificação de limites cartográficos (IBGE), drenagem (ANA) e imagens de satélite."),
        ("2. Segurança e Controle por CPF/E-mail", "Autenticação oficial com CPF obrigatório, matrícula e e-mail automático como login."),
        ("3. Dicionário Ambiental (10 Domínios)", "Formulário de pedologia, pluviosidade, declividade, geologia e relatórios PDF."),
        ("4. Coleta Mobile & Curadoria Técnica", "Captura por GPS no celular e gerenciamento com privilégios por autoria do registro."),
        ("5. Exportação Multiformato (GIS)", "Download automático dos pontos aprovados em Shapefile (.zip), GeoPackage e GeoJSON.")
    ]

    for idx, (st_t, st_d) in enumerate(msteps):
        top_pos = PptInches(1.6 + idx * 1.1)
        
        pill = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.8), top_pos, PptInches(0.6), PptInches(0.9))
        set_shape_color(pill, PptRGBColor(0x2E, 0x6B, 0x9E))
        tf_p = pill.text_frame
        p_p = tf_p.paragraphs[0]
        p_p.text = str(idx + 1)
        p_p.font.bold = True
        p_p.font.size = PptPt(20)
        p_p.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)
        p_p.alignment = PP_ALIGN.CENTER

        sbox = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(1.5), top_pos, PptInches(11.0), PptInches(0.9))
        set_shape_color(sbox, PptRGBColor(0xFF, 0xFF, 0xFF), PptRGBColor(0xE2, 0xE8, 0xF0))

        tf_sb = sbox.text_frame
        tf_sb.word_wrap = True
        p_st = tf_sb.paragraphs[0]
        p_st.text = st_t
        p_st.font.bold = True
        p_st.font.size = PptPt(15)
        p_st.font.color.rgb = PptRGBColor(0x1B, 0x36, 0x5D)

        p_sd = tf_sb.add_paragraph()
        p_sd.text = st_d
        p_sd.font.size = PptPt(12)
        p_sd.font.color.rgb = PptRGBColor(0x47, 0x55, 0x69)

    # SLIDE 5: Conclusões Agronômicas
    s5 = prs.slides.add_slide(blank_layout)
    bg5 = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    set_shape_color(bg5, PptRGBColor(0xF8, 0xFA, 0xFC))

    hbar5 = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.2))
    set_shape_color(hbar5, PptRGBColor(0x1B, 0x36, 0x5D))
    tb_h5 = s5.shapes.add_textbox(PptInches(0.8), PptInches(0.2), PptInches(11.5), PptInches(0.8))
    p_h5 = tb_h5.text_frame.paragraphs[0]
    p_h5.text = "Contribuição Científica para a Ciência do Solo"
    p_h5.font.bold = True
    p_h5.font.size = PptPt(24)
    p_h5.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)

    box_l = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.8), PptInches(1.6), PptInches(5.7), PptInches(5.2))
    set_shape_color(box_l, PptRGBColor(0xFF, 0xFF, 0xFF), PptRGBColor(0xCB, 0xD5, 0xE1))

    tf_bl = box_l.text_frame
    tf_bl.word_wrap = True
    p_blt = tf_bl.paragraphs[0]
    p_blt.text = "Relevância Agronômica & Ambiental"
    p_blt.font.bold = True
    p_blt.font.size = PptPt(18)
    p_blt.font.color.rgb = PptRGBColor(0x1B, 0x36, 0x5D)
    p_blt.space_after = PptPt(12)

    agri_pts = [
        "✔ Conservação de Solos em Encostas: Diagnóstico rápido de movimentos de massa em bacias hidrográficas.",
        "✔ Correlação Pedológica: Integração de classes de solos (Cambissolos/Latossolos) com precipitações pluviométricas.",
        "✔ Suporte a Políticas Públicas: Base padronizada para zoneamento ambiental e gestão de riscos.",
        "✔ Coleta Descentralizada: Autonomia para agentes de campo com validação institucional."
    ]
    for pt in agri_pts:
        p_pt = tf_bl.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = PptPt(13)
        p_pt.font.color.rgb = PptRGBColor(0x33, 0x41, 0x55)
        p_pt.space_after = PptPt(10)

    box_r = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(6.8), PptInches(1.6), PptInches(5.7), PptInches(5.2))
    set_shape_color(box_r, PptRGBColor(0x1B, 0x36, 0x5D))

    tf_br = box_r.text_frame
    tf_br.word_wrap = True
    p_brt = tf_br.paragraphs[0]
    p_brt.text = "Fundamentação Bibliográfica (ABNT)"
    p_brt.font.bold = True
    p_brt.font.size = PptPt(18)
    p_brt.font.color.rgb = PptRGBColor(0xFF, 0xFF, 0xFF)
    p_brt.space_after = PptPt(12)

    cites = [
        "• EMBRAPA (2018): Sistema Brasileiro de Classificação de Solos.",
        "• Graser & Olaya (2015): Processamento de dados espaciais em software livre.",
        "• Pebesma & Bivand (2023): Ciência de Dados Espaciais aplicada.",
        "• Goodchild (2007): Sensoriamento participativo e informação geográfica voluntária."
    ]
    for cite in cites:
        p_ct = tf_br.add_paragraph()
        p_ct.text = cite
        p_ct.font.size = PptPt(13)
        p_ct.font.color.rgb = PptRGBColor(0xE2, 0xE8, 0xF0)
        p_ct.space_after = PptPt(10)

    prs.save(filepath)
    print(f"Apresentação PPTX atualizada salva com sucesso em: {filepath}")

def generate_changes_docx(filepath="app_webgis/relatorio_mudancas_hoje.docx"):
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x2B, 0x2B, 0x2B)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("RELATÓRIO DE ATUALIZAÇÕES E MELHORIAS NO GEOPORTAL MOVMASSA")
    r_title.bold = True
    r_title.font.size = Pt(16)
    r_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run(f"Síntese Executiva de Implementações Concluídas em 21 de Setembro de 2026")
    r_sub.italic = True
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    p_sub.paragraph_format.space_after = Pt(18)

    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("1. Resumo das Alterações Efetuadas")
    r_h1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    changes = [
        ("Reestruturação do Controle de Acesso e Autonomia de Agentes: ", "Agentes de campo receberam plenas permissões funcionais de levantamento de dados (cadastro de 1 ponto, upload massivo em Shapefile .zip e CSV). Na Curadoria Técnica, visualizam a lista completa para transparência, podendo editar e excluir EXCLUSIVAMENTE os registros cadastrados por eles mesmos."),
        ("Gestão Institucional por Esferas da Defesa Civil: ", "Gestores (Nacional, Estadual e Municipal) foram habilitados para cadastrar novos agentes dentro de sua jurisdição, além de editar, aprovar, rejeitar e excluir qualquer ocorrência da sua respectiva esfera."),
        ("Validação em Tempo Real e Bloqueio de Duplicidades por CPF: ", "Implementado filtro de verificação que impede o cadastro de uma mesma pessoa física em diferentes esferas da Defesa Civil."),
        ("Login Automático via E-mail Institucional: ", "O e-mail do funcionário torna-se automaticamente o seu login no sistema, eliminando inconsistências de usuários duplicados."),
        ("Obrigatoriedade de CPF e Matrícula Funcional: ", "Inclusão dos campos obrigatórios com asterisco vermelho e coluna 'Função no Sistema' na área de administração."),
        ("Emissão de Relatório Técnico em PDF: ", "Módulo dinâmico de geração de PDF individual para cada ponto de ocorrência cadastrado com os 10 domínios ambientais."),
        ("Manutenção da Compatibilidade de Banco de Dados: ", "Resolução de restrição no PostgreSQL referente ao campo de senha legada e gravação simultânea de hash de senha.")
    ]

    for title, desc in changes:
        p = doc.add_paragraph(style='List Bullet')
        r_t = p.add_run(title)
        r_t.bold = True
        r_t.font.color.rgb = RGBColor(0x2E, 0x6B, 0x9E)
        p.add_run(desc)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- Seção 2: Credenciais ---
    h1_2 = doc.add_heading(level=1)
    r_h1_2 = h1_2.add_run("2. Credenciais de Acesso Padrão (Usuários e Senhas)")
    r_h1_2.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    p_cred = doc.add_paragraph(
        "Para a realização de testes, validações por bancas examinadoras e demonstrações operacionais, "
        "o sistema possui as seguintes contas institucionais pré-configuradas:"
    )
    p_cred.paragraph_format.line_spacing = 1.15
    p_cred.paragraph_format.space_after = Pt(8)

    # Tabela de Credenciais
    tbl_cred = doc.add_table(rows=1, cols=5)
    tbl_cred.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_hdr = tbl_cred.rows[0].cells
    c_titles = ['Perfil / Esfera', 'Nome de Usuário', 'E-mail de Login', 'Senha Inicial', 'Função / Escopo']
    for i, title in enumerate(c_titles):
        c_hdr[i].text = title
        set_cell_background(c_hdr[i], "1B365D")
        for paragraph in c_hdr[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    cred_data = [
        ("Administrador Geral", "admin", "admin.geral@geoportal.gov.br", "Admin@123", "Gestão global de todas as esferas e dados."),
        ("Gestor Nacional", "defesa_nacional", "nacional@defesacivil.gov.br", "Defesa@123", "Gestão e cadastro de agentes na esfera Nacional."),
        ("Gestor Estadual", "defesa_estadual", "estadual@defesacivil.rj.gov.br", "Defesa@123", "Gestão e cadastro de agentes na esfera Estadual RJ."),
        ("Gestor Municipal", "defesa_municipal", "defesacivil@angra.rj.gov.br", "Defesa@123", "Gestão e cadastro de agentes na esfera Municipal."),
        ("Organização Parceira", "org", "contato@orgamb.org.br", "Org@123", "Gestão técnica de relatórios e dados da ONG."),
        ("Agente de Campo", "user", "usuario@email.com", "User@123", "Coleta de campo (1-ponto/Shape/CSV) e edição de pontos próprios.")
    ]

    for r_idx, r_data in enumerate(cred_data):
        row_cells = tbl_cred.add_row().cells
        fill_hex = "F0F4F8" if r_idx % 2 == 0 else "FFFFFF"
        for i, text in enumerate(r_data):
            row_cells[i].text = text
            set_cell_background(row_cells[i], fill_hex)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    doc.save(filepath)
    print(f"Relatório de Mudanças DOCX salvo em: {filepath}")

if __name__ == "__main__":
    generate_thesis_docx()
    generate_pptx_presentation()
    generate_changes_docx()
