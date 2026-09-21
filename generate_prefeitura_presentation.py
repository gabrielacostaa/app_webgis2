"""
Gerador de Apresentação Executiva (PPTX) e Dossiê Técnico Institucional (DOCX)
Projeto MOVMASSA - Geoportal WebGIS & Blockchain para a Prefeitura de Angra dos Reis
"""
import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

import pptx
from pptx.util import Inches as PInches, Pt as PPt
from pptx.dml.color import RGBColor as PRGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

def set_cell_background(cell, fill_color):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_color}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def generate_dossie_docx():
    doc = docx.Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)
        
    NAVY = RGBColor(15, 23, 42)       # #0F172A
    EMERALD = RGBColor(5, 150, 105)   # #059669
    CYAN = RGBColor(6, 182, 212)      # #06B6D4
    SLATE = RGBColor(71, 85, 105)     # #475569
    DARK_BLUE = RGBColor(30, 58, 138) # #1E3A8A
    
    # -------------------------------------------------------------
    # CABEÇALHO FORMAL
    # -------------------------------------------------------------
    p_inst = doc.add_paragraph()
    p_inst.paragraph_format.space_after = Pt(2)
    r_inst = p_inst.add_run("ESTADO DO RIO DE JANEIRO • MUNICÍPIO DE ANGRA DOS REIS\nDOSSIÊ TÉCNICO-EXECUTIVO PARA A ADMINISTRAÇÃO MUNICIPAL E DEFESA CIVIL")
    r_inst.font.size = Pt(9)
    r_inst.font.bold = True
    r_inst.font.color.rgb = SLATE
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(14)
    r_line = p_div.add_run("—" * 50)
    r_line.font.color.rgb = CYAN
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # TÍTULO PRINCIPAL
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("GEOPORTAL MOVMASSA PRO")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = NAVY
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(18)
    r_sub = p_sub.add_run("Sistema Integrado de Inteligência Geoespacial, Gestão de Risco de Desastres e Notarização em Blockchain para Angra dos Reis")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = EMERALD
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # BOX RESUMO EXECUTIVO
    t_box = doc.add_table(rows=1, cols=1)
    t_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_box = t_box.cell(0, 0)
    set_cell_background(c_box, "F0FDF4") # Emerald tint
    set_cell_margins(c_box, top=140, bottom=140, left=200, right=200)
    
    p_box = c_box.paragraphs[0]
    p_box.paragraph_format.space_after = Pt(0)
    r_bt = p_box.add_run("SÍNTESE PARA O GABINETE DO PREFEITO E SECRETARIAS MUNICIPAIS\n")
    r_bt.font.bold = True
    r_bt.font.size = Pt(10.5)
    r_bt.font.color.rgb = EMERALD
    
    r_bb = p_box.add_run(
        "O presente dossiê apresenta à Prefeitura Municipal de Angra dos Reis a trajetória completa de desenvolvimento da plataforma "
        "MOVMASSA. O sistema foi construído a partir de pesquisas de Doutorado em Ciência do Solo e Geotecnologias, evoluindo de uma análise "
        "estática em QGIS para um Geoportal WebGIS corporativo em tempo real, equipado com ferramentas de campo, curadoria técnica multiesferas, "
        "geração automática de laudos técnicos em PDF e, pioneiramente, certificação de fé pública por Blockchain (SHA-256 Merkle Ledger). "
        "A plataforma confere ao município soberania de dados, transparência e segurança jurídica na gestão de áreas de risco de encostas."
    )
    r_bb.font.size = Pt(9.5)
    r_bb.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # SEÇÃO 1: CONTEXTO E HISTÓRICO
    # -------------------------------------------------------------
    h1 = doc.add_paragraph()
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    r_h1 = h1.add_run("1. Origem, Motivação e o Desafio de Angra dos Reis")
    r_h1.font.name = "Arial"
    r_h1.font.size = Pt(14)
    r_h1.font.bold = True
    r_h1.font.color.rgb = DARK_BLUE

    p1 = doc.add_paragraph()
    p1.paragraph_format.space_after = Pt(8)
    p1.paragraph_format.line_spacing = 1.15
    p1.add_run(
        "O município de Angra dos Reis apresenta uma das configurações geoambientais mais complexas do Brasil: a confluência entre o "
        "escarpamento íngreme da Serra do Mar, solos rasos altamente saturáveis (Cambissolos e Neossolos) e índices pluviométricos extremos "
        "que frequentemente superam 2.000 mm anuais. Historicamente, os movimentos de massa (deslizamentos, corridas de detritos e "
        "quedas de blocos) impõem severos desafios humanitários, habitacionais e econômicos à gestão municipal."
    )

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(8)
    p2.paragraph_format.line_spacing = 1.15
    p2.add_run(
        "O projeto MOVMASSA nasceu no âmbito do Doutorado com a missão de transformar o conhecimento pedológico e geotécnico em uma "
        "ferramenta operacional e acessível, integrando dados de campo, cartografia territorial e tecnologia de ponta para salvar vidas e "
        "otimizar o planejamento urbano da Prefeitura de Angra dos Reis."
    )

    # -------------------------------------------------------------
    # SEÇÃO 2: CRONOLOGIA DE DESENVOLVIMENTO
    # -------------------------------------------------------------
    h2 = doc.add_paragraph()
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    r_h2 = h2.add_run("2. Linha do Tempo e Evolução Tecnológica do MOVMASSA")
    r_h2.font.name = "Arial"
    r_h2.font.size = Pt(14)
    r_h2.font.bold = True
    r_h2.font.color.rgb = DARK_BLUE

    # Tabela Cronológica
    t_cron = doc.add_table(rows=6, cols=3)
    t_cron.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_w = [Inches(1.2), Inches(2.2), Inches(3.6)]
    
    h_cron = ["Fase / Época", "Marco Tecnológico", "Entregas & Resultados para o Município"]
    for i, h_text in enumerate(h_cron):
        cell = t_cron.cell(0, i)
        cell.width = c_w[i]
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(255, 255, 255)

    fases = [
        ("Fase 1\n(Início)", "Modelagem Geoespacial Desktop (QGIS)", "Mapeamento das bacias hidrográficas, zonas de declividade crítica, classes de solo e delimitação das manchas urbanizadas de Angra."),
        ("Fase 2", "Construção do WebGIS Interativo", "Migração da cartografia estática para uma infraestrutura web baseada em Python Flask, Leaflet, GeoPandas e banco de dados relacional/espacial em nuvem."),
        ("Fase 3", "Coleta em Campo & Upload Massivo", "Criação de módulos de registro com captura instantânea de coordenadas GPS, fotos e vídeos de vistorias, além de importador massivo de Shapefiles (.zip) e CSV."),
        ("Fase 4", "Curadoria Técnica & Laudos em PDF", "Implementação da hierarquia de usuários (Nacional, Estadual, Municipal), controle de aprovação de ocorrências e motor de emissão de laudos oficiais em PDF com 8 domínios de dados."),
        ("Fase 5\n(Atual)", "Design Glassmorphism & Blockchain", "Interface moderna com painel flutuante translúcido (estilo Ambiental Pro) e motor criptográfico Blockchain SHA-256 para assegurar fé pública e imutabilidade dos laudos.")
    ]

    for idx, (f_epoca, f_marco, f_entregas) in enumerate(fases):
        row_i = idx + 1
        c0 = t_cron.cell(row_i, 0)
        c1 = t_cron.cell(row_i, 1)
        c2 = t_cron.cell(row_i, 2)
        
        c0.width, c1.width, c2.width = c_w[0], c_w[1], c_w[2]
        bg_row = "F8FAFC" if idx % 2 == 0 else "FFFFFF"
        for c in (c0, c1, c2):
            set_cell_background(c, bg_row)
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)
            
        r0 = c0.paragraphs[0].add_run(f_epoca)
        r0.font.bold = True
        r0.font.size = Pt(8.5)
        r0.font.color.rgb = DARK_BLUE
        
        r1 = c1.paragraphs[0].add_run(f_marco)
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = EMERALD
        
        r2 = c2.paragraphs[0].add_run(f_entregas)
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # SEÇÃO 3: MÓDULOS E FUNCIONALIDADES DO GEOPORTAL
    # -------------------------------------------------------------
    h3 = doc.add_paragraph()
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(6)
    r_h3 = h3.add_run("3. Principais Módulos do Sistema MOVMASSA")
    r_h3.font.name = "Arial"
    r_h3.font.size = Pt(14)
    r_h3.font.bold = True
    r_h3.font.color.rgb = DARK_BLUE

    modulos = [
        ("Módulo 1: Visualizador WebGIS com Interface Glassmorphism", "Painel flutuante em vidro fosco (Frosted Glass) sobreposto ao mapa de alta resolução, permitindo alternância entre Satélite HD, Dark Canvas, Light Canvas e OpenStreetMap, com controle dinâmico de camadas e recolhimento lateral com 1 clique."),
        ("Módulo 2: Acervo Territorial de Camadas Vetoriais", "Visualização em tempo real de limites municipais, buffers de segurança, áreas urbanizadas de Angra, zonas de declividade e camadas de infraestrutura."),
        ("Módulo 3: Coleta em Campo & Curadoria Técnica", "Formulário responsivo com geolocalização automática por GPS do dispositivo, anexação de até 5 fotografias e 2 vídeos de vistoria, encaminhados para mesa de triagem e curadoria técnica da Defesa Civil."),
        ("Módulo 4: Dicionário de Dados Multidomínio (8 Domínios)", "Cadastro exaustivo de 8 eixos: (1) Identificação Geral, (2) Clima e Pluviosidade, (3) Pedologia e Solos, (4) Geomorfologia e Relevo, (5) Geologia e Litologia, (6) Ações Antrópicas e Ocupação, (7) Danos Socioeconômicos e Vítimas, (8) Impactos Ambientais."),
        ("Módulo 5: Gerador de Laudos Técnicos em PDF Oficial", "Emissão instantânea de laudos padronizados e periciais, organizados em tabelas técnicas de alto padrão com fotos de vistoria e carimbo institucional de Angra dos Reis."),
        ("Módulo 6: Interoperabilidade Espacial (Exportação GIS)", "Download direto dos dados e ocorrências em formatos Shapefile (.zip), GeoPackage (.gpkg) e GeoJSON (.geojson), garantindo integração imediata com softwares como QGIS e ArcGIS.")
    ]

    for m_tit, m_desc in modulos:
        p_m = doc.add_paragraph()
        p_m.paragraph_format.space_after = Pt(4)
        p_m.paragraph_format.left_indent = Inches(0.2)
        r_mt = p_m.add_run(f"• {m_tit}: ")
        r_mt.font.bold = True
        r_mt.font.size = Pt(9.5)
        r_mt.font.color.rgb = EMERALD
        r_md = p_m.add_run(m_desc)
        r_md.font.size = Pt(9.5)
        r_md.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # SEÇÃO 4: A INOVAÇÃO DO BLOCKCHAIN
    # -------------------------------------------------------------
    h4 = doc.add_paragraph()
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(6)
    r_h4 = h4.add_run("4. A Inovação do Blockchain e Rastreabilidade Criptográfica")
    r_h4.font.name = "Arial"
    r_h4.font.size = Pt(14)
    r_h4.font.bold = True
    r_h4.font.color.rgb = DARK_BLUE

    p_b1 = doc.add_paragraph()
    p_b1.paragraph_format.space_after = Pt(8)
    p_b1.paragraph_format.line_spacing = 1.15
    p_b1.add_run(
        "A mais recente inovação implementada no Geoportal MOVMASSA é o motor de Notarização em Blockchain e Cadeia de Custódia Espacial "
        "(Spatial Data Provenance). Em situações de desastre, laudos técnicos frequentemente fundamentam ações civis públicas, decretações "
        "de estado de emergência e liberação de verbas federais."
    )

    p_b2 = doc.add_paragraph()
    p_b2.paragraph_format.space_after = Pt(8)
    p_b2.paragraph_format.line_spacing = 1.15
    p_b2.add_run(
        "Com a tecnologia implementada, assim que uma ocorrência é homologada pelo curador da Defesa Civil, o sistema gera uma assinatura "
        "matemática SHA-256 única de todos os atributos físicos, geográficos e fotográficos, encadeando-a no Livro-Razão (blockchain_ledger). "
        "Isso assegura que:"
    )

    b_points = [
        "Imutabilidade Estrita: Nenhum registro pode ser adulterado, apagado ou retrodatado sem invalidar a chave criptográfica do bloco.",
        "Fé Pública e Valor Probatório: O relatório PDF emitido possui validade jurídica garantida sob a Lei Federal nº 14.129/2021 (Governo Digital).",
        "Auditoria Multiesferas: A Prefeitura de Angra pode compartilhar a base de dados com CEMADEN, Defesa Civil Estadual e Ministério Público sem qualquer risco de questionamento sobre a autenticidade dos dados.",
        "API de Verificação em Tempo Real: O portal disponibiliza a rota /api/blockchain/verify/<id> para conferência instantânea da integridade dos laudos."
    ]
    for bp in b_points:
        p_bp = doc.add_paragraph()
        p_bp.paragraph_format.space_after = Pt(4)
        p_bp.paragraph_format.left_indent = Inches(0.2)
        r_bp = p_bp.add_run(f"✔ {bp}")
        r_bp.font.size = Pt(9.5)
        r_bp.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # SEÇÃO 5: BENEFÍCIOS DIRETOS PARA A PREFEITURA
    # -------------------------------------------------------------
    h5 = doc.add_paragraph()
    h5.paragraph_format.space_before = Pt(14)
    h5.paragraph_format.space_after = Pt(6)
    r_h5 = h5.add_run("5. Benefícios Diretos para o Município de Angra dos Reis")
    r_h5.font.name = "Arial"
    r_h5.font.size = Pt(14)
    r_h5.font.bold = True
    r_h5.font.color.rgb = DARK_BLUE

    # Tabela Benefícios
    t_ben = doc.add_table(rows=5, cols=2)
    t_ben.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_wb = [Inches(2.4), Inches(4.3)]
    
    h_ben = ["Dimensão de Gestão", "Ganhos Concretos para a Administração Municipal"]
    for i, h_text in enumerate(h_ben):
        cell = t_ben.cell(0, i)
        cell.width = c_wb[i]
        set_cell_background(cell, "059669") # Emerald
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(255, 255, 255)

    ben_data = [
        ("Agilidade na Resposta da Defesa Civil", "Redução drástica do tempo entre a vistoria de campo e a homologação do laudo, eliminando formulários de papel e retrabalho manual."),
        ("Captação de Recursos Federais (MIDR)", "Laudos técnicos robustos com dados de solo, clima e fotos georreferenciadas facilitam a aprovação célere de verbas junto ao Fundo Nacional de Desastres."),
        ("Planejamento Urbano e Habitação", "Mapeamento geoespacial preciso de encostas e áreas vulneráveis para orientar obras de contenção, drenagem e reassentamento seguro."),
        ("Governança e Transparência Pública", "Posicionamento de Angra dos Reis na vanguarda tecnológica nacional como um dos primeiros municípios a aplicar Blockchain e WebGIS na Defesa Civil.")
    ]

    for idx, (b_dim, b_ganho) in enumerate(ben_data):
        row_i = idx + 1
        c0 = t_ben.cell(row_i, 0)
        c1 = t_ben.cell(row_i, 1)
        c0.width, c1.width = c_wb[0], c_wb[1]
        bg_row = "F8FAFC" if idx % 2 == 0 else "FFFFFF"
        for c in (c0, c1):
            set_cell_background(c, bg_row)
            set_cell_margins(c, top=80, bottom=80, left=100, right=100)
            
        r0 = c0.paragraphs[0].add_run(b_dim)
        r0.font.bold = True
        r0.font.size = Pt(8.5)
        r0.font.color.rgb = DARK_BLUE
        
        r1 = c1.paragraphs[0].add_run(b_ganho)
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # -------------------------------------------------------------
    # SEÇÃO 6: CONCLUSÃO E PROPOSTA DE COOPERAÇÃO
    # -------------------------------------------------------------
    h6 = doc.add_paragraph()
    h6.paragraph_format.space_before = Pt(14)
    h6.paragraph_format.space_after = Pt(6)
    r_h6 = h6.add_run("6. Conclusão e Proposta de Acordo de Cooperação Técnica (ACT)")
    r_h6.font.name = "Arial"
    r_h6.font.size = Pt(14)
    r_h6.font.bold = True
    r_h6.font.color.rgb = DARK_BLUE

    p_c1 = doc.add_paragraph()
    p_c1.paragraph_format.space_after = Pt(8)
    p_c1.paragraph_format.line_spacing = 1.15
    p_c1.add_run(
        "O Geoportal MOVMASSA PRO encontra-se em estágio operacional pleno, hospedado em nuvem e pronto para uso institucional imediato "
        "pelos agentes e gestores da Prefeitura Municipal de Angra dos Reis. Propõe-se a formalização de um Acordo de Cooperação Técnica (ACT) "
        "entre a Universidade e o Município para capacitação contínua de agentes da Defesa Civil, alimentação recíproca de bases de dados "
        "espaciais e aprimoramento contínuo dos modelos preditivos de estabilidade de encostas."
    )

    # Referências Normativas
    p_ref_t = doc.add_paragraph()
    p_ref_t.paragraph_format.space_before = Pt(14)
    p_ref_t.paragraph_format.space_after = Pt(4)
    r_rt = p_ref_t.add_run("Referências Normativas e Bibliográficas:")
    r_rt.font.bold = True
    r_rt.font.size = Pt(10)
    r_rt.font.color.rgb = SLATE

    refs_dossie = [
        "1. BRASIL. Lei Federal nº 12.608, de 10 de abril de 2012. Institui a Política Nacional de Proteção e Defesa Civil (PNPDEC).",
        "2. BRASIL. Lei Federal nº 14.129, de 29 de março de 2021. Marco Legal do Governo Digital e Transparência Pública.",
        "3. ZHANG, X. et al. (2020). Blockchain-based traceable and trusted emergency management system for natural disasters. International Journal of Disaster Risk Reduction, v. 51, p. 101861.",
        "4. XU, Y. et al. (2020). A blockchain-based spatial data provenance model for geographic information systems. ISPRS Int. J. Geo-Inf., v. 9, n. 10, p. 575."
    ]
    for rf in refs_dossie:
        p_rf = doc.add_paragraph()
        p_rf.paragraph_format.space_after = Pt(3)
        p_rf.paragraph_format.left_indent = Inches(0.2)
        r_rf = p_rf.add_run(rf)
        r_rf.font.size = Pt(8)
        r_rf.font.color.rgb = SLATE

    out_docx = "/Users/gabrielacosta/Desktop/Documentos/Doutorado/QGis-_WebGis/Geoportal/MOVMASSA_Dossie_Executivo_Prefeitura_Angra.docx"
    doc.save(out_docx)
    print("Dossiê DOCX gerado com sucesso em:", out_docx)

def generate_prefeitura_pptx():
    prs = pptx.Presentation()
    prs.slide_width = PInches(13.333) # 16:9 widescreen
    prs.slide_height = PInches(7.5)
    
    # Palette
    COLOR_NAVY = PRGBColor(15, 23, 42)       # #0F172A
    COLOR_SLATE = PRGBColor(30, 41, 59)      # #1E293B
    COLOR_EMERALD = PRGBColor(5, 150, 105)   # #059669
    COLOR_CYAN = PRGBColor(6, 182, 212)      # #06B6D4
    COLOR_SKY = PRGBColor(56, 189, 248)      # #38BDF8
    COLOR_WHITE = PRGBColor(255, 255, 255)
    COLOR_LIGHT_GRAY = PRGBColor(241, 245, 249)
    COLOR_MUTED = PRGBColor(148, 163, 184)
    COLOR_AMBER = PRGBColor(245, 158, 11)
    
    blank_layout = prs.slide_layouts[6]
    
    def create_header_slide(title, category="MOVMASSA PRO • PREFEITURA DE ANGRA DOS REIS"):
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_NAVY
        bg.line.color.rgb = COLOR_NAVY
        
        # Header Box
        tb = slide.shapes.add_textbox(PInches(0.8), PInches(0.45), PInches(11.7), PInches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p_c = tf.paragraphs[0]
        p_c.text = category.upper()
        p_c.font.size = PPt(10)
        p_c.font.bold = True
        p_c.font.color.rgb = COLOR_CYAN
        p_c.space_after = PPt(4)
        
        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.size = PPt(23)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE
        
        # Bottom Line
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PInches(0.8), PInches(6.85), PInches(11.73), PInches(0.04))
        bar.fill.solid()
        bar.fill.fore_color.rgb = COLOR_SLATE
        bar.line.color.rgb = COLOR_SLATE
        
        # Footer text
        tb_f = slide.shapes.add_textbox(PInches(0.8), PInches(6.92), PInches(11.7), PInches(0.4))
        tf_f = tb_f.text_frame
        p_f = tf_f.paragraphs[0]
        p_f.text = "Geoportal MOVMASSA • Inteligência Geoespacial e Defesa Civil • Angra dos Reis - RJ"
        p_f.font.size = PPt(9)
        p_f.font.color.rgb = COLOR_MUTED
        
        return slide

    # -------------------------------------------------------------
    # SLIDE 1: Capa Executiva Prefeitura
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_NAVY
    bg1.line.color.rgb = COLOR_NAVY
    
    # Barra lateral verde esmeralda
    bar1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, PInches(0.9), PInches(1.2), PInches(0.18), PInches(4.8))
    bar1.fill.solid()
    bar1.fill.fore_color.rgb = COLOR_EMERALD
    bar1.line.color.rgb = COLOR_EMERALD
    
    tb1 = s1.shapes.add_textbox(PInches(1.3), PInches(1.1), PInches(11.2), PInches(5.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p_badge = tf1.paragraphs[0]
    p_badge.text = "APRESENTAÇÃO INSTITUCIONAL • PREFEITURA MUNICIPAL & DEFESA CIVIL DE ANGRA DOS REIS"
    p_badge.font.size = PPt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_CYAN
    p_badge.space_after = PPt(12)
    
    p_main = tf1.add_paragraph()
    p_main.text = "Geoportal MOVMASSA PRO"
    p_main.font.size = PPt(38)
    p_main.font.bold = True
    p_main.font.color.rgb = COLOR_WHITE
    p_main.space_after = PPt(8)
    
    p_subt = tf1.add_paragraph()
    p_subt.text = "Da Modelagem Espacial em Ciência do Solo ao Geoportal com Blockchain:\nSolução Tecnológica para Prevenção e Gestão de Desastres de Encosta"
    p_subt.font.size = PPt(16)
    p_subt.font.color.rgb = COLOR_LIGHT_GRAY
    p_subt.space_after = PPt(28)
    
    p_auth = tf1.add_paragraph()
    p_auth.text = "Autoria: Pesquisa de Doutorado em Ciência do Solo / Geotecnologias • Angra dos Reis - RJ"
    p_auth.font.size = PPt(12)
    p_auth.font.bold = True
    p_auth.font.color.rgb = COLOR_EMERALD

    # -------------------------------------------------------------
    # SLIDE 2: O Desafio de Angra dos Reis
    # -------------------------------------------------------------
    s2 = create_header_slide("O Desafio Crítico: Vulnerabilidade a Deslizamentos em Angra", "1. CONTEXTO E DIAGNÓSTICO")
    
    cards_s2 = [
        ("Geomorfologia Escarpada", "Encostas com declividades acentuadas (> 30°) diretamente sobre áreas urbanizadas e litorâneas.", "🏔️", COLOR_CYAN),
        ("Saturação de Solos Rasos", "Cambissolos e Neossolos de baixa retenção, sujeitos a rápido colapso em eventos pluviométricos extremos.", "🌧️", COLOR_EMERALD),
        ("Impacto Social & Econômico", "Histórico severo de deslizamentos, interdições de moradias, interrupção de vias e demandas por laudos periciais.", "⚠️", COLOR_AMBER)
    ]
    for i, (ctit, cdesc, icon, colr) in enumerate(cards_s2):
        left = PInches(0.8 + i * 3.95)
        top = PInches(1.8)
        width = PInches(3.75)
        height = PInches(4.6)
        
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = colr
        card.line.width = PPt(2)
        
        tb = s2.shapes.add_textbox(left + PInches(0.2), top + PInches(0.3), width - PInches(0.4), height - PInches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{icon}  {ctit}"
        p.font.size = PPt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.space_after = PPt(14)
        
        p2 = tf.add_paragraph()
        p2.text = cdesc
        p2.font.size = PPt(13)
        p2.font.color.rgb = COLOR_LIGHT_GRAY
        p2.line_spacing = 1.25

    # -------------------------------------------------------------
    # SLIDE 3: A Jornada de Desenvolvimento
    # -------------------------------------------------------------
    s3 = create_header_slide("A Jornada de Construção: Do QGIS ao Geoportal WebGIS", "2. EVOLUÇÃO TECNOLÓGICA")
    
    stages = [
        ("Fase 1: QGIS Desktop", "Estruturação das camadas vetoriais e raster (solos, declividade, geologia e malha de Angra).", COLOR_SLATE),
        ("Fase 2: Arquitetura WebGIS", "Desenvolvimento do portal interativo com Python Flask, Leaflet e banco espacial em nuvem.", COLOR_SLATE),
        ("Fase 3: Curadoria & Campo", "Formulários de campo com GPS, fotos/vídeos e mesa de triagem multiesferas da Defesa Civil.", COLOR_SLATE),
        ("Fase 4: Blockchain & Laudos", "Notarização criptográfica SHA-256 e emissão de laudos oficiais em PDF com fé pública.", COLOR_EMERALD)
    ]
    for i, (stit, sdesc, colr) in enumerate(stages):
        left = PInches(0.8 + i * 2.95)
        top = PInches(1.9)
        width = PInches(2.8)
        height = PInches(4.4)
        
        card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = colr if colr != COLOR_SLATE else PRGBColor(51, 65, 85)
        card.line.width = PPt(2 if colr == COLOR_EMERALD else 1)
        
        tb = s3.shapes.add_textbox(left + PInches(0.15), top + PInches(0.25), width - PInches(0.3), height - PInches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p_num = tf.paragraphs[0]
        p_num.text = f"ETAPA 0{i+1}"
        p_num.font.size = PPt(11)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_CYAN if i < 3 else COLOR_EMERALD
        p_num.space_after = PPt(8)
        
        p = tf.add_paragraph()
        p.text = stit
        p.font.size = PPt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.space_after = PPt(10)
        
        p2 = tf.add_paragraph()
        p2.text = sdesc
        p2.font.size = PPt(11.5)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 4: A Interface Glassmorphism
    # -------------------------------------------------------------
    s4 = create_header_slide("Interface Moderna: Painel Flutuante em Vidro Fosco (Glassmorphism)", "3. DESIGN & EXPERIÊNCIA DO USUÁRIO")
    
    feats_s4 = [
        ("Design Estilo Ambiental Pro", "Painel translúcido sobreposto ao mapa de satélite com efeito de desfoque profundo (backdrop-filter: blur(24px)).", "✨"),
        ("Seletor de Mapas de Alta Definição", "Alternância instantânea entre Satélite HD, Dark Canvas, Light Canvas e OpenStreetMap sem recarregar a página.", "🗺️"),
        ("Controle de Visualização com 1 Clique", "Botão retrátil lateral para ocultar o painel e permitir análise em tela inteira do território de Angra.", "👁️"),
        ("Acessibilidade & Modo Noturno", "Suporte completo a tema escuro/claro para operações diurnas e vistorias noturnas de campo.", "🌙")
    ]
    for i, (ftit, fdesc, icon) in enumerate(feats_s4):
        row = i // 2
        col = i % 2
        left = PInches(0.8 + col * 5.9)
        top = PInches(1.8 + row * 2.4)
        width = PInches(5.7)
        height = PInches(2.1)
        
        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = PRGBColor(51, 65, 85)
        
        tb = s4.shapes.add_textbox(left + PInches(0.2), top + PInches(0.2), width - PInches(0.4), height - PInches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{icon}  {ftit}"
        p.font.size = PPt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_CYAN
        p.space_after = PPt(6)
        
        p2 = tf.add_paragraph()
        p2.text = fdesc
        p2.font.size = PPt(12)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 5: Coleta em Campo & Upload Massivo
    # -------------------------------------------------------------
    s5 = create_header_slide("Coleta em Campo & Importação Massiva de Dados Espaciais", "4. AQUISIÇÃO DE DADOS")
    
    cards_s5 = [
        ("Registro Rápido em Campo (GPS)", "O agente aciona 'Capturar GPS', anexa até 5 fotos e 2 vídeos de vistoria e envia imediatamente à Defesa Civil.", "📱", COLOR_CYAN),
        ("Upload Massivo de Shapefiles (.zip)", "Importação direta de nuvens de pontos e camadas de projetos anteriores do QGIS em segundos.", "📦", COLOR_EMERALD),
        ("Importação de Planilhas CSV", "Conversão automática de tabelas de coordenadas X/Y ou Latitude/Longitude para feições GeoJSON.", "📊", COLOR_SKY)
    ]
    for i, (ctit, cdesc, icon, colr) in enumerate(cards_s5):
        left = PInches(0.8 + i * 3.95)
        top = PInches(1.8)
        width = PInches(3.75)
        height = PInches(4.6)
        
        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = colr
        card.line.width = PPt(1.5)
        
        tb = s5.shapes.add_textbox(left + PInches(0.2), top + PInches(0.3), width - PInches(0.4), height - PInches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{icon}  {ctit}"
        p.font.size = PPt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.space_after = PPt(14)
        
        p2 = tf.add_paragraph()
        p2.text = cdesc
        p2.font.size = PPt(13)
        p2.font.color.rgb = COLOR_LIGHT_GRAY
        p2.line_spacing = 1.25

    # -------------------------------------------------------------
    # SLIDE 6: Curadoria Técnica Multiesferas
    # -------------------------------------------------------------
    s6 = create_header_slide("Mesa de Curadoria Técnica & Hierarquia da Defesa Civil", "5. GOVERNANÇA E CONTROLE")
    
    spheres = [
        ("Defesa Civil Municipal (Angra)", "Aprovação, edição e homologação das ocorrências e vistorias da cidade.", "🏢"),
        ("Defesa Civil Estadual (SEDEC-RJ)", "Visão consolidada regional e apoio técnico às ações de resposta.", "🏛️"),
        ("Defesa Civil Nacional (MIDR)", "Acesso aos laudos para liberação de verbas do Fundo Nacional de Calamidades.", "🇧🇷"),
        ("Agentes & Usuários de Campo", "Envio direto de registros e acompanhamento do status de aprovação.", "👷")
    ]
    for i, (stit, sdesc, icon) in enumerate(spheres):
        row = i // 2
        col = i % 2
        left = PInches(0.8 + col * 5.9)
        top = PInches(1.8 + row * 2.4)
        width = PInches(5.7)
        height = PInches(2.1)
        
        card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = COLOR_EMERALD if i == 0 else PRGBColor(51, 65, 85)
        card.line.width = PPt(2 if i == 0 else 1)
        
        tb = s6.shapes.add_textbox(left + PInches(0.2), top + PInches(0.2), width - PInches(0.4), height - PInches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{icon}  {stit}"
        p.font.size = PPt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_EMERALD if i == 0 else COLOR_CYAN
        p.space_after = PPt(6)
        
        p2 = tf.add_paragraph()
        p2.text = sdesc
        p2.font.size = PPt(12)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 7: Dicionário de Dados Científico (8 Domínios)
    # -------------------------------------------------------------
    s7 = create_header_slide("Dicionário de Dados Robusto: 8 Domínios Técnicos de Análise", "6. RIGOR CIENTÍFICO")
    
    domains = [
        "1. Identificação Geral (Coordenadas, Bairro, Tipologia)",
        "2. Condições Climáticas (Precipitação do evento, 5d, 10d, Vento)",
        "3. Parâmetros Pedológicos (Classe de Solo, Profundidade, Textura)",
        "4. Fatores Geomorfológicos (Declividade, Altitude, Curvatura)",
        "5. Geologia & Litologia (Tipo de Rocha, Estrutura, Tectonismo)",
        "6. Ações Antrópicas (Escavações, Sobrecargas, Desmatamento)",
        "7. Danos Socioeconômicos (Famílias, Desalojados, Vítimas, Custos)",
        "8. Impactos Ambientais (Área Atingida em ha, Biodiversidade, Recursos)"
    ]
    for i, dom in enumerate(domains):
        row = i // 2
        col = i % 2
        left = PInches(0.8 + col * 5.9)
        top = PInches(1.8 + row * 1.2)
        width = PInches(5.7)
        height = PInches(1.0)
        
        card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = PRGBColor(51, 65, 85)
        
        tb = s7.shapes.add_textbox(left + PInches(0.2), top + PInches(0.15), width - PInches(0.4), height - PInches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = dom
        p.font.size = PPt(12.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 8: Laudos Técnicos em PDF Oficial
    # -------------------------------------------------------------
    s8 = create_header_slide("Emissão Automatizada de Laudos Técnicos Oficiais em PDF", "7. DOCUMENTAÇÃO PERICIAL")
    
    feats_pdf = [
        ("Padronização Institucional", "Laudos periciais completos gerados com 1 clique, com o brasão/logo de Angra dos Reis e cabeçalho oficial da Defesa Civil.", "📄"),
        ("Integração Fotográfica de Campo", "Inclusão automática das fotos de vistoria em alta resolução anexadas pelo agente no momento do registro.", "📸"),
        ("Exportação Espacial Integrada", "Download simultâneo das camadas em Shapefile, GeoPackage e GeoJSON para alimentação direta do QGIS municipal.", "💾"),
        ("Eliminação de Papel & Burocracia", "Processo 100% digital que agiliza a tomada de decisões emergenciais do Gabinete de Crise da Prefeitura.", "⚡")
    ]
    for i, (ptit, pdesc, icon) in enumerate(feats_pdf):
        row = i // 2
        col = i % 2
        left = PInches(0.8 + col * 5.9)
        top = PInches(1.8 + row * 2.4)
        width = PInches(5.7)
        height = PInches(2.1)
        
        card = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = PRGBColor(51, 65, 85)
        
        tb = s8.shapes.add_textbox(left + PInches(0.2), top + PInches(0.2), width - PInches(0.4), height - PInches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{icon}  {ptit}"
        p.font.size = PPt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_CYAN
        p.space_after = PPt(6)
        
        p2 = tf.add_paragraph()
        p2.text = pdesc
        p2.font.size = PPt(12)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 9: A Inovação do Blockchain
    # -------------------------------------------------------------
    s9 = create_header_slide("A Vanguarda Tecnológica: Notarização em Blockchain", "8. SEGURANÇA E FÉ PÚBLICA")
    
    b_steps = [
        ("1. Hash Canônico SHA-256", "Assinatura criptográfica calculada sobre todos os dados de solo, declividade, coordenadas e fotos.", COLOR_CYAN),
        ("2. Livro-Razão Encadeado", "Cada laudo é ancorado no bloco anterior, formando uma corrente imutável e auditável.", COLOR_EMERALD),
        ("3. Fé Pública & Lei 14.129", "Validade jurídica plena perante o Ministério Público e Tribunais de Contas.", COLOR_AMBER),
        ("4. Detecção de Fraudes", "Verificação em tempo real via API que alerta qualquer tentativa de adulteração de laudos.", PRGBColor(168, 85, 247))
    ]
    for i, (btit, bdesc, colr) in enumerate(b_steps):
        left = PInches(0.8 + i * 2.95)
        top = PInches(1.9)
        width = PInches(2.8)
        height = PInches(4.4)
        
        card = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = colr
        card.line.width = PPt(2)
        
        tb = s9.shapes.add_textbox(left + PInches(0.15), top + PInches(0.25), width - PInches(0.3), height - PInches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = btit
        p.font.size = PPt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.space_after = PPt(10)
        
        p2 = tf.add_paragraph()
        p2.text = bdesc
        p2.font.size = PPt(11.5)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 10: Benefícios para Angra dos Reis
    # -------------------------------------------------------------
    s10 = create_header_slide("Ganhos Concretos para a Prefeitura de Angra dos Reis", "9. IMPACTO MUNICIPAL")
    
    bens_pref = [
        ("Salvar Vidas & Prevenção", "Identificação antecipada de encostas instáveis com base em dados reais de solo e precipitação.", "🛡️"),
        ("Captação de Recursos Federais", "Laudos técnicos periciais sólidos facilitam a liberação ágil de verbas junto ao MIDR/Governo Federal.", "💰"),
        ("Segurança Jurídica do Município", "Comprovação com fé pública de todas as ações preventivas e vistorias executadas pela Prefeitura.", "⚖️"),
        ("Liderança em Cidades Inteligentes", "Angra dos Reis torna-se pioneira nacional na aplicação de Blockchain e WebGIS na Defesa Civil.", "🏆")
    ]
    for i, (btit, bdesc, icon) in enumerate(bens_pref):
        row = i // 2
        col = i % 2
        left = PInches(0.8 + col * 5.9)
        top = PInches(1.8 + row * 2.4)
        width = PInches(5.7)
        height = PInches(2.1)
        
        card = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = COLOR_EMERALD if i == 0 else PRGBColor(51, 65, 85)
        card.line.width = PPt(2 if i == 0 else 1)
        
        tb = s10.shapes.add_textbox(left + PInches(0.2), top + PInches(0.2), width - PInches(0.4), height - PInches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{icon}  {btit}"
        p.font.size = PPt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_EMERALD if i == 0 else COLOR_CYAN
        p.space_after = PPt(6)
        
        p2 = tf.add_paragraph()
        p2.text = bdesc
        p2.font.size = PPt(12)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 11: Proposta de Parceria & Próximos Passos
    # -------------------------------------------------------------
    s11 = create_header_slide("Próximos Passos: Acordo de Cooperação Técnica (ACT)", "10. ENCAMINHAMENTO")
    
    steps_act = [
        ("1. Implantação e Uso Imediato", "O Geoportal está pronto em nuvem para utilização operacional pela Defesa Civil de Angra.", COLOR_CYAN),
        ("2. Capacitação de Agentes", "Treinamento prático da equipe municipal para coleta de campo com GPS e curadoria técnica.", COLOR_EMERALD),
        ("3. Integração de Novas Camadas", "Incorporação de novos dados de obras, drenagem e áreas de risco mapeadas pelo município.", COLOR_SKY),
        ("4. Assinatura do Termo de ACT", "Formalização da parceria científica entre a Universidade e a Prefeitura de Angra dos Reis.", COLOR_AMBER)
    ]
    for i, (atit, adesc, colr) in enumerate(steps_act):
        left = PInches(0.8 + i * 2.95)
        top = PInches(1.9)
        width = PInches(2.8)
        height = PInches(4.4)
        
        card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = colr
        card.line.width = PPt(2)
        
        tb = s11.shapes.add_textbox(left + PInches(0.15), top + PInches(0.25), width - PInches(0.3), height - PInches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = atit
        p.font.size = PPt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.space_after = PPt(10)
        
        p2 = tf.add_paragraph()
        p2.text = adesc
        p2.font.size = PPt(11.5)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 12: Encerramento e Contato
    # -------------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    bg12 = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg12.fill.solid()
    bg12.fill.fore_color.rgb = COLOR_NAVY
    bg12.line.color.rgb = COLOR_NAVY
    
    tb12 = s12.shapes.add_textbox(PInches(1.5), PInches(1.8), PInches(10.3), PInches(4.0))
    tf12 = tb12.text_frame
    tf12.word_wrap = True
    
    p_thx = tf12.paragraphs[0]
    p_thx.text = "MOVMASSA PRO"
    p_thx.font.size = PPt(42)
    p_thx.font.bold = True
    p_thx.font.color.rgb = COLOR_EMERALD
    p_thx.alignment = PP_ALIGN.CENTER
    p_thx.space_after = PPt(8)
    
    p_motto = tf12.add_paragraph()
    p_motto.text = "Ciência do Solo, Geotecnologias e Blockchain a Serviço da Vida e de Angra dos Reis"
    p_motto.font.size = PPt(18)
    p_motto.font.color.rgb = COLOR_WHITE
    p_motto.alignment = PP_ALIGN.CENTER
    p_motto.space_after = PPt(28)
    
    p_cnt = tf12.add_paragraph()
    p_cnt.text = "Aberto para Perguntas, Demonstração ao Vivo e Deliberação do Acordo de Cooperação Técnica"
    p_cnt.font.size = PPt(13)
    p_cnt.font.color.rgb = COLOR_CYAN
    p_cnt.alignment = PP_ALIGN.CENTER

    out_pptx = "/Users/gabrielacosta/Desktop/Documentos/Doutorado/QGis-_WebGis/Geoportal/MOVMASSA_Apresentacao_Prefeitura_Angra.pptx"
    prs.save(out_pptx)
    print("Apresentação PPTX gerada com sucesso em:", out_pptx)

if __name__ == "__main__":
    generate_dossie_docx()
    generate_prefeitura_pptx()
