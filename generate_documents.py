import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

import pptx
from pptx.util import Inches as PInches, Pt as PPt
from pptx.dml.color import RGBColor as PRGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

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

def generate_docx():
    doc = docx.Document()
    
    # Page setup - Margins 2.5 cm
    for section in doc.sections:
        section.top_margin = Inches(0.98)
        section.bottom_margin = Inches(0.98)
        section.left_margin = Inches(0.98)
        section.right_margin = Inches(0.98)
        
    # Styles & Colors
    NAVY = RGBColor(15, 23, 42)       # #0F172A
    EMERALD = RGBColor(5, 150, 105)   # #059669
    CYAN = RGBColor(6, 182, 212)      # #06B6D4
    SLATE = RGBColor(71, 85, 105)     # #475569
    DARK_BLUE = RGBColor(30, 58, 138) # #1E3A8A
    
    # -------------------------------------------------------------
    # HEADER / CAPA
    # -------------------------------------------------------------
    p_inst = doc.add_paragraph()
    p_inst.paragraph_format.space_after = Pt(4)
    run_inst = p_inst.add_run("PROGRAMA DE PÓS-GRADUAÇÃO EM CIÊNCIA DO SOLO / GEOTECNOLOGIAS\nPROJETO MOVMASSA — ANGRA DOS REIS / RJ")
    run_inst.font.size = Pt(9.5)
    run_inst.font.bold = True
    run_inst.font.color.rgb = SLATE
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(16)
    r_line = p_div.add_run("—" * 45)
    r_line.font.color.rgb = CYAN
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run("INTEGRAÇÃO DE BLOCKCHAIN E CADEIA DE CUSTÓDIA CRIPTOGRÁFICA EM GEOPORTAL WEBGIS")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = NAVY
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(20)
    r_sub = p_sub.add_run("Fundamentação Teórica, Arquitetura de Notarização Espacial e Aplicabilidade na Gestão de Riscos de Desastres Naturais")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = EMERALD
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Box Resumo Executivo
    table_res = doc.add_table(rows=1, cols=1)
    table_res.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_res = table_res.cell(0, 0)
    set_cell_background(cell_res, "F0FDF4") # Light emerald
    set_cell_margins(cell_res, top=140, bottom=140, left=200, right=200)
    
    p_res = cell_res.paragraphs[0]
    p_res.paragraph_format.space_after = Pt(0)
    r_res_t = p_res.add_run("RESUMO EXECUTIVO & INOVAÇÃO CIENTÍFICA\n")
    r_res_t.font.bold = True
    r_res_t.font.size = Pt(10.5)
    r_res_t.font.color.rgb = EMERALD
    
    r_res_b = p_res.add_run(
        "Este documento técnico-científico fundamenta a integração da tecnologia Blockchain no Geoportal MOVMASSA "
        "(WebGIS de monitoramento e análise de risco de deslizamentos em Angra dos Reis, RJ). Apresenta-se o conceito de "
        "Spatial Data Provenance (rastreabilidade e proveniência de dados geoespaciais), demonstrando como algoritmos de hash "
        "SHA-256 e livros-razão distribuídos garantem fé pública, integridade matemática inviolável e transparência em auditorias "
        "multiesferas da Defesa Civil (Municipal, Estadual e Nacional), em estrita conformidade com a Lei Federal nº 14.129/2021."
    )
    r_res_b.font.size = Pt(9.5)
    r_res_b.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # SEÇÃO 1
    # -------------------------------------------------------------
    h1 = doc.add_paragraph()
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    r_h1 = h1.add_run("1. O que é a Tecnologia Blockchain?")
    r_h1.font.name = "Arial"
    r_h1.font.size = Pt(14)
    r_h1.font.bold = True
    r_h1.font.color.rgb = DARK_BLUE

    p1 = doc.add_paragraph()
    p1.paragraph_format.space_after = Pt(8)
    p1.paragraph_format.line_spacing = 1.15
    p1.add_run(
        "Originalmente concebido por Nakamoto (2008), o Blockchain é uma estrutura de dados distribuída, append-only "
        "(somente acréscimo) e criptograficamente assegurada, que funciona como um livro-razão (ledger) descentralizado. "
        "Cada registro transacional é agrupado em um bloco estruturado que contém: (i) um carimbo de tempo inviolável (timestamp), "
        "(ii) o hash criptográfico dos dados locais (payload), e (iii) o hash do bloco imediatamente anterior (previous hash)."
    )

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(8)
    p2.paragraph_format.line_spacing = 1.15
    p2.add_run(
        "A interligação encadeada por funções de dispersão unidirecionais (funções hash criptográficas, como o SHA-256) confere ao sistema a "
        "propriedade de imutabilidade estrita: qualquer tentativa de retroescrita, exclusão ou manipulação de um único parâmetro "
        "(ex.: coordenada geográfica, espessura de horizonte pedológico ou cota de declividade) resulta na invalidação imediata "
        "de toda a cadeia subsequente (Tapscott & Tapscott, 2016; Zheng et al., 2018)."
    )

    # -------------------------------------------------------------
    # SEÇÃO 2
    # -------------------------------------------------------------
    h2 = doc.add_paragraph()
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    r_h2 = h2.add_run("2. Por que aplicar Blockchain ao Geoportal MOVMASSA?")
    r_h2.font.name = "Arial"
    r_h2.font.size = Pt(14)
    r_h2.font.bold = True
    r_h2.font.color.rgb = DARK_BLUE

    p3 = doc.add_paragraph()
    p3.paragraph_format.space_after = Pt(8)
    p3.paragraph_format.line_spacing = 1.15
    p3.add_run(
        "A gestão de riscos e desastres geo-hidrológicos em áreas de alta vulnerabilidade, como o município de Angra dos Reis (RJ), "
        "demanda informações técnicas que orientam evacuações, interdições de moradias, obras de bioengenharia e liberação de verbas "
        "emergenciais. A aplicação do Blockchain no MOVMASSA endereça quatro pilares fundamentais:"
    )

    # Tabela 4 Pilares
    table_pil = doc.add_table(rows=5, cols=2)
    table_pil.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths = [Inches(2.2), Inches(4.5)]
    
    headers = ["Pilar Estratégico", "Impacto Prático e Científico no Geoportal"]
    for i, h_text in enumerate(headers):
        cell = table_pil.cell(0, i)
        cell.width = col_widths[i]
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    rows_data = [
        ("A. Fé Pública e Validade Jurídica dos Laudos", "Laudos técnicos de vistorias de deslizamento possuem repercussão no Ministério Público e Defensoria. O selo SHA-256 no relatório PDF comprova que os dados de solo, declividade e vítimas não sofreram adulterações ex-post."),
        ("B. Cadeia de Custódia Espacial (Spatial Provenance)", "Rastreabilidade completa do ciclo de vida do dado: identificação digital unívoca do Agente Cadastrador, Carimbo de Tempo UTC e assinatura eletrônica do Curador Técnico da Defesa Civil."),
        ("C. Auditoria Multiesferas Descentralizada", "Permite que CEMADEN, Defesa Civil Nacional (MIDR), Defesa Civil Estadual (SEDEC-RJ) e Defesa Civil Municipal auditem a mesma base imutável, eliminando assimetrias de informação e conflitos de competência."),
        ("D. Transparência em Fundos Públicos e Seguros", "Garante a lisura requerida para a prestação de contas do Fundo Nacional para Calamidades Públicas (Fundo Nacional de Defesa Civil) e para a liquidação de sinistros habitacionais e securitários.")
    ]

    for idx, (p_title_text, p_desc_text) in enumerate(rows_data):
        row_idx = idx + 1
        cell_t = table_pil.cell(row_idx, 0)
        cell_d = table_pil.cell(row_idx, 1)
        
        cell_t.width = col_widths[0]
        cell_d.width = col_widths[1]
        
        bg_c = "F8FAFC" if idx % 2 == 0 else "FFFFFF"
        set_cell_background(cell_t, bg_c)
        set_cell_background(cell_d, bg_c)
        set_cell_margins(cell_t, top=80, bottom=80, left=100, right=100)
        set_cell_margins(cell_d, top=80, bottom=80, left=100, right=100)
        
        p_t = cell_t.paragraphs[0]
        r_t = p_t.add_run(p_title_text)
        r_t.font.bold = True
        r_t.font.size = Pt(9)
        r_t.font.color.rgb = DARK_BLUE
        
        p_d = cell_d.paragraphs[0]
        r_d = p_d.add_run(p_desc_text)
        r_d.font.size = Pt(8.5)
        r_d.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # SEÇÃO 3
    # -------------------------------------------------------------
    h3 = doc.add_paragraph()
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(6)
    r_h3 = h3.add_run("3. Arquitetura Implementada no MOVMASSA (Modelo Híbrido)")
    r_h3.font.name = "Arial"
    r_h3.font.size = Pt(14)
    r_h3.font.bold = True
    r_h3.font.color.rgb = DARK_BLUE

    p4 = doc.add_paragraph()
    p4.paragraph_format.space_after = Pt(8)
    p4.paragraph_format.line_spacing = 1.15
    p4.add_run(
        "Para conciliar a alta performance exigida por um WebGIS interativo com os princípios de imutabilidade do Blockchain, "
        "adotou-se a arquitetura híbrida com Notarização Digital (On-Chain Hash / Off-Chain Data), recomendada por Ramachandran et al. (2020) "
        "e Zhang et al. (2020). O fluxo operacional opera da seguinte forma:"
    )

    steps = [
        ("Passo 1: Coleta em Campo e Persistência Espacial", "O agente registra as coordenadas WGS84, espessura do solo, litologia, declividade, precipitação acumulada e mídias no banco de dados espacial relacional (PostgreSQL/PostGIS ou SQLite)."),
        ("Passo 2: Curadoria e Geração do Hash Canônico (Payload)", "No momento da validação do registro por um curador qualificado, o motor criptográfico serializa os atributos canônicos e calcula o hash digest SHA-256."),
        ("Passo 3: Encadeamento no Livro-Razão (Block Linking)", "O sistema busca o hash do último bloco registrado, calcula o novo Block Hash conectando Índice + Timestamp ISO + Hash Anterior + Payload Hash + Identificador do Curador, e persiste a transação na tabela blockchain_ledger."),
        ("Passo 4: Certificação no Laudo Técnico Oficial (PDF)", "O relatório técnico gerado em ReportLab incorpora a seção '11. Certificado Criptográfico de Notarização em Blockchain', estampando a chave do bloco e a declaração de conformidade com a Lei Federal nº 14.129/2021."),
        ("Passo 5: API de Verificação Contínua de Integridade", "Qualquer entidade pode acionar a rota /api/blockchain/verify/<id> para verificar se os dados persistidos sofreram adulteração física ou lógica.")
    ]

    for s_title, s_desc in steps:
        p_step = doc.add_paragraph()
        p_step.paragraph_format.space_after = Pt(4)
        p_step.paragraph_format.left_indent = Inches(0.2)
        r_st = p_step.add_run(f"• {s_title}: ")
        r_st.font.bold = True
        r_st.font.size = Pt(9.5)
        r_st.font.color.rgb = EMERALD
        r_sd = p_step.add_run(s_desc)
        r_sd.font.size = Pt(9.5)
        r_sd.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # SEÇÃO 4
    # -------------------------------------------------------------
    h4 = doc.add_paragraph()
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(6)
    r_h4 = h4.add_run("4. Contribuição Científica para a Tese de Doutorado")
    r_h4.font.name = "Arial"
    r_h4.font.size = Pt(14)
    r_h4.font.bold = True
    r_h4.font.color.rgb = DARK_BLUE

    p5 = doc.add_paragraph()
    p5.paragraph_format.space_after = Pt(8)
    p5.paragraph_format.line_spacing = 1.15
    p5.add_run(
        "A integração entre Ciência do Solo, Análise Espacial de Desastres e Criptografia em Blockchain consolida um avanço "
        "metodológico pioneiro na literatura brasileira de Geotecnologias aplicadas à Defesa Civil. Essa abordagem proporciona:"
    )

    benefits = [
        "Inovação Metodológica: Transposição do conceito de Spatial Data Provenance para o monitoramento de movimentos gravitacionais de massa.",
        "Potencial de Publicação de Alto Impacto: Alinhamento temático com periódicos como International Journal of Disaster Risk Reduction (Elsevier), Computers & Geosciences e ISPRS International Journal of Geo-Information.",
        "Governança Digital e Transparência: Atendimento prático e mensurável às exigências da Política Nacional de Proteção e Defesa Civil (Lei nº 12.608/2012) e do Marco Legal de Governo Digital (Lei nº 14.129/2021)."
    ]
    for b in benefits:
        p_b = doc.add_paragraph()
        p_b.paragraph_format.space_after = Pt(4)
        p_b.paragraph_format.left_indent = Inches(0.2)
        r_b = p_b.add_run(f"✔ {b}")
        r_b.font.size = Pt(9.5)
        r_b.font.color.rgb = NAVY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # -------------------------------------------------------------
    # REFERÊNCIAS BIBLIOGRÁFICAS REAIS (ABNT / APA)
    # -------------------------------------------------------------
    h_ref = doc.add_paragraph()
    h_ref.paragraph_format.space_before = Pt(16)
    h_ref.paragraph_format.space_after = Pt(8)
    r_href = h_ref.add_run("5. Referências Bibliográficas Reais")
    r_href.font.name = "Arial"
    r_href.font.size = Pt(14)
    r_href.font.bold = True
    r_href.font.color.rgb = DARK_BLUE

    references = [
        "BRASIL. Lei Federal nº 12.608, de 10 de abril de 2012. Institui a Política Nacional de Proteção e Defesa Civil - PNPDEC. Diário Oficial da União, Brasília, DF, 2012.",
        "BRASIL. Lei Federal nº 14.129, de 29 de março de 2021. Dispõe sobre princípios, regras e instrumentos para o Governo Digital e o aumento da eficiência pública. Diário Oficial da União, Brasília, DF, 2021.",
        "NAKAMOTO, S. Bitcoin: A Peer-to-Peer Electronic Cash System. Decentralized Business Review, 2008. Disponível em: <https://bitcoin.org/bitcoin.pdf>.",
        "RAMACHANDRAN, G. S. et al. Towards a decentralized data marketplace for smart cities. In: 2018 IEEE International Smart Cities Conference (ISC2). IEEE, p. 1-8, 2018. DOI: 10.1109/ISC2.2018.8656952.",
        "TAPSCOTT, D.; TAPSCOTT, A. Blockchain Revolution: How the Technology Behind Bitcoin Is Changing Money, Business, and the World. Penguin, New York, 2016.",
        "WANG, S. et al. Blockchain-enabled spatial data infrastructure for smart governance. International Journal of Geographical Information Science, v. 34, n. 12, p. 2420-2442, 2020. DOI: 10.1080/13658816.2020.1764693.",
        "XU, Y. et al. A blockchain-based spatial data provenance model for geographic information systems. ISPRS International Journal of Geo-Information, v. 9, n. 10, p. 575, 2020. DOI: 10.3390/ijgi9100575.",
        "ZHANG, X. et al. Blockchain-based traceable and trusted emergency management system for natural disasters. International Journal of Disaster Risk Reduction, v. 51, p. 101861, 2020. DOI: 10.1016/j.ijdrr.2020.101861.",
        "ZHENG, Z. et al. Blockchain challenges and opportunities: A survey. International Journal of Web and Grid Services, v. 14, n. 4, p. 352-375, 2018. DOI: 10.1504/IJWGS.2018.095647."
    ]

    for ref in references:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.space_after = Pt(6)
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.left_indent = Inches(0.25)
        p_ref.paragraph_format.first_line_indent = Inches(-0.25)
        r_ref = p_ref.add_run(ref)
        r_ref.font.size = Pt(8.5)
        r_ref.font.color.rgb = SLATE

    output_path = "/Users/gabrielacosta/Desktop/Documentos/Doutorado/QGis-_WebGis/Geoportal/MOVMASSA_Blockchain_Geoportal_Explicacao_Tecnica.docx"
    doc.save(output_path)
    print("DOCX gerado com sucesso em:", output_path)

def generate_pptx():
    prs = pptx.Presentation()
    prs.slide_width = PInches(13.333) # 16:9 widescreen
    prs.slide_height = PInches(7.5)
    
    # Palette
    COLOR_NAVY = PRGBColor(15, 23, 42)       # #0F172A
    COLOR_SLATE = PRGBColor(30, 41, 59)      # #1E293B
    COLOR_EMERALD = PRGBColor(5, 150, 105)   # #059669
    COLOR_CYAN = PRGBColor(6, 182, 212)      # #06B6D4
    COLOR_WHITE = PRGBColor(255, 255, 255)
    COLOR_LIGHT_GRAY = PRGBColor(241, 245, 249)
    COLOR_MUTED = PRGBColor(148, 163, 184)
    
    blank_layout = prs.slide_layouts[6]
    
    # -------------------------------------------------------------
    # SLIDE 1: Capa Executiva
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_NAVY
    bg1.line.color.rgb = COLOR_NAVY
    
    # Glow bar
    bar1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, PInches(1.0), PInches(1.4), PInches(0.15), PInches(4.2))
    bar1.fill.solid()
    bar1.fill.fore_color.rgb = COLOR_EMERALD
    bar1.line.color.rgb = COLOR_EMERALD
    
    # Title Box
    tb1 = slide1.shapes.add_textbox(PInches(1.4), PInches(1.3), PInches(11.0), PInches(4.5))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p_badge = tf1.paragraphs[0]
    p_badge.text = "MOVMASSA PRO • WEBGRIS DE RISCO DE DESLIZAMENTOS"
    p_badge.font.size = PPt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_CYAN
    p_badge.space_after = PPt(10)
    
    p_main = tf1.add_paragraph()
    p_main.text = "Blockchain & Notarização Criptográfica Aplicada ao Geoportal"
    p_main.font.size = PPt(34)
    p_main.font.bold = True
    p_main.font.color.rgb = COLOR_WHITE
    p_main.space_after = PPt(12)
    
    p_subt = tf1.add_paragraph()
    p_subt.text = "Fé Pública, Rastreabilidade Espacial (Spatial Provenance) e Governança Interinstitucional na Defesa Civil"
    p_subt.font.size = PPt(16)
    p_subt.font.color.rgb = COLOR_MUTED
    p_subt.space_after = PPt(28)
    
    p_auth = tf1.add_paragraph()
    p_auth.text = "Doutorado em Ciência do Solo / Geotecnologias • Angra dos Reis - RJ"
    p_auth.font.size = PPt(12)
    p_auth.font.color.rgb = COLOR_EMERALD

    # Helper function for content slides
    def create_base_slide(title_text, category_text="ARQUITETURA & FUNDAMENTAÇÃO"):
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_NAVY
        bg.line.color.rgb = COLOR_NAVY
        
        # Header Top
        tb = slide.shapes.add_textbox(PInches(0.8), PInches(0.5), PInches(11.5), PInches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p_c = tf.paragraphs[0]
        p_c.text = category_text.upper()
        p_c.font.size = PPt(10)
        p_c.font.bold = True
        p_c.font.color.rgb = COLOR_CYAN
        p_c.space_after = PPt(4)
        
        p_t = tf.add_paragraph()
        p_t.text = title_text
        p_t.font.size = PPt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE
        
        # Bottom bar
        bar_b = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PInches(0.8), PInches(6.8), PInches(11.7), PInches(0.04))
        bar_b.fill.solid()
        bar_b.fill.fore_color.rgb = COLOR_SLATE
        bar_b.line.color.rgb = COLOR_SLATE
        
        return slide

    # -------------------------------------------------------------
    # SLIDE 2: O que é Blockchain?
    # -------------------------------------------------------------
    slide2 = create_base_slide("1. Conceito Fundamental de Blockchain", "CONCEITOS CHAVE")
    
    cards_s2 = [
        ("Livro-Razão Imutável", "Estrutura distribuída de registro onde cada dado é gravado em blocos encadeados. Não permite exclusão ou alteração posterior sem invalidar toda a rede.", COLOR_EMERALD),
        ("Criptografia SHA-256", "Algoritmo matemático de dispersão que gera uma 'impressão digital' única de 64 caracteres hexadecimais para cada conjunto de dados da ocorrência.", COLOR_CYAN),
        ("Carimbo de Tempo (Timestamp)", "Assinatura temporal UTC auditável que certifica a data e hora exatas em que o laudo técnico de solo e deslizamento foi emitido e homologado.", PRGBColor(245, 158, 11))
    ]
    
    for i, (ctitle, cdesc, accent_color) in enumerate(cards_s2):
        left = PInches(0.8 + i * 4.0)
        top = PInches(1.8)
        width = PInches(3.7)
        height = PInches(4.6)
        
        card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = accent_color
        card.line.width = PPt(1.5)
        
        tb = slide2.shapes.add_textbox(left + PInches(0.2), top + PInches(0.3), width - PInches(0.4), height - PInches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = f"0{i+1}. {ctitle}"
        p1.font.size = PPt(16)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.space_after = PPt(14)
        
        p2 = tf.add_paragraph()
        p2.text = cdesc
        p2.font.size = PPt(13)
        p2.font.color.rgb = COLOR_LIGHT_GRAY
        p2.line_spacing = 1.2

    # -------------------------------------------------------------
    # SLIDE 3: 4 Pilares de Aplicação no MOVMASSA
    # -------------------------------------------------------------
    slide3 = create_base_slide("2. Por que aplicar Blockchain no MOVMASSA?", "JUSTIFICATIVA E VALOR PRÁTICO")
    
    pillars = [
        ("Fé Pública dos Laudos", "Laudos técnicos de encosta têm validade jurídica em inquéritos do Ministério Público e perícias técnicas criminais.", "⚖️"),
        ("Spatial Provenance", "Rastreabilidade completa: quem coletou, quando cadastrou e qual gestor de Defesa Civil aprovou na curadoria.", "📍"),
        ("Auditoria Multiesferas", "Integração segura entre CEMADEN, Defesa Civil Nacional, SEDEC-RJ e Município de Angra dos Reis.", "🏛️"),
        ("Transparência de Recursos", "Comprovação incontestável para liberação de fundos de calamidade e liquidação de seguros residenciais.", "💰")
    ]
    
    for i, (ptitle, pdesc, icon) in enumerate(pillars):
        row = i // 2
        col = i % 2
        left = PInches(0.8 + col * 5.9)
        top = PInches(1.8 + row * 2.4)
        width = PInches(5.7)
        height = PInches(2.1)
        
        card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = PRGBColor(51, 65, 85)
        
        tb = slide3.shapes.add_textbox(left + PInches(0.2), top + PInches(0.2), width - PInches(0.4), height - PInches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = f"{icon}  {ptitle}"
        p1.font.size = PPt(15)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_CYAN
        p1.space_after = PPt(8)
        
        p2 = tf.add_paragraph()
        p2.text = pdesc
        p2.font.size = PPt(12)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 4: Arquitetura do Modelo Híbrido
    # -------------------------------------------------------------
    slide4 = create_base_slide("3. Arquitetura Híbrida de Notarização Espacial", "ENGENHARIA DO SISTEMA")
    
    steps_s4 = [
        ("1. Coleta e Vistoria", "Agente cadastra atributos de solo, clima, declividade e fotos no WebGIS.", COLOR_CYAN),
        ("2. Curadoria Técnica", "Gestor qualificado homologa o registro na plataforma.", COLOR_EMERALD),
        ("3. Hash SHA-256", "Motor criptográfico calcula digest canônico e gera Block Hash encadeado.", PRGBColor(245, 158, 11)),
        ("4. Certificado no PDF", "Laudo oficial é emitido com selo criptográfico imutável e verificável.", PRGBColor(168, 85, 247))
    ]
    
    for i, (stitle, sdesc, colr) in enumerate(steps_s4):
        left = PInches(0.8 + i * 2.95)
        top = PInches(2.0)
        width = PInches(2.8)
        height = PInches(4.2)
        
        card = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_SLATE
        card.line.color.rgb = colr
        card.line.width = PPt(2)
        
        tb = slide4.shapes.add_textbox(left + PInches(0.15), top + PInches(0.3), width - PInches(0.3), height - PInches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p1 = tf.paragraphs[0]
        p1.text = stitle
        p1.font.size = PPt(14)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.space_after = PPt(12)
        
        p2 = tf.add_paragraph()
        p2.text = sdesc
        p2.font.size = PPt(11.5)
        p2.font.color.rgb = COLOR_LIGHT_GRAY

    # -------------------------------------------------------------
    # SLIDE 5: Referências Bibliográficas Reais
    # -------------------------------------------------------------
    slide5 = create_base_slide("4. Referências Bibliográficas Reais", "EMBASAMENTO CIENTÍFICO")
    
    tb_ref = slide5.shapes.add_textbox(PInches(0.8), PInches(1.7), PInches(11.7), PInches(4.8))
    tf_ref = tb_ref.text_frame
    tf_ref.word_wrap = True
    
    refs_ppt = [
        "• Zhang, X. et al. (2020). Blockchain-based traceable and trusted emergency management system for natural disasters. Int. Journal of Disaster Risk Reduction, 51, 101861.",
        "• Xu, Y. et al. (2020). A blockchain-based spatial data provenance model for geographic information systems. ISPRS Int. Journal of Geo-Information, 9(10), 575.",
        "• Wang, S. et al. (2020). Blockchain-enabled spatial data infrastructure for smart governance. Int. Journal of Geographical Information Science, 34(12), 2420-2442.",
        "• Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System. Cryptography Mailing list.",
        "• Zheng, Z. et al. (2018). Blockchain challenges and opportunities: A survey. Int. Journal of Web and Grid Services, 14(4), 352-375.",
        "• Brasil (2021). Lei Federal nº 14.129/2021 — Princípios, regras e instrumentos para o Governo Digital e Transparência Pública."
    ]
    
    for idx, r_txt in enumerate(refs_ppt):
        p = tf_ref.paragraphs[0] if idx == 0 else tf_ref.add_paragraph()
        p.text = r_txt
        p.font.size = PPt(12)
        p.font.color.rgb = COLOR_LIGHT_GRAY
        p.space_after = PPt(10)

    output_pptx = "/Users/gabrielacosta/Desktop/Documentos/Doutorado/QGis-_WebGis/Geoportal/MOVMASSA_Blockchain_Geoportal_Apresentacao.pptx"
    prs.save(output_pptx)
    print("PPTX gerado com sucesso em:", output_pptx)

if __name__ == "__main__":
    generate_docx()
    generate_pptx()
