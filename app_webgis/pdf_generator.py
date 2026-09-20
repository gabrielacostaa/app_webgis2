import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
import datetime

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total pages and render page numbers."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Footer text
        footer_text = f"Geoportal WebGIS MOVMASSA • Angra dos Reis - RJ • Emissão: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
        page_text = f"Página {self._pageNumber} de {page_count}"
        
        # Footer line
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 36, 612 - 36, 36)
        
        self.drawString(36, 24, footer_text)
        self.drawRightString(612 - 36, 24, page_text)
        self.restoreState()


def generate_occurrence_pdf(data, output_path, upload_folder="static/uploads"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    primary_color = colors.HexColor("#1E365D")   # Deep Navy
    secondary_color = colors.HexColor("#2E6B9E") # Slate Blue
    accent_color = colors.HexColor("#DC2626")    # Red accent
    bg_light = colors.HexColor("#F8FAFC")        # Card background
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.white,
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#CBD5E1")
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4
    )
    
    cell_bold = ParagraphStyle(
        'CellBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )
    
    cell_normal = ParagraphStyle(
        'CellNormal',
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#334155")
    )

    story = []
    
    # ---------------------------------------------------------
    # 1. HEADER BANNER
    # ---------------------------------------------------------
    header_data = [
        [
            Paragraph("<b>MOVMASSA - RELATÓRIO TÉCNICO DE OCORRÊNCIA</b>", title_style),
        ],
        [
            Paragraph("Sistema de Geoprocessamento WebGIS e Curadoria de Riscos em Encostas • Angra dos Reis - RJ", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('PADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,1), (-1,1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    # ---------------------------------------------------------
    # 2. IDENTIFICAÇÃO GERAL & RESPONSÁVEL
    # ---------------------------------------------------------
    level_label = {
        'admin_geral': 'Administrador Geral',
        'admin_nacional': 'Defesa Civil Nacional',
        'admin_estadual': 'Defesa Civil Estadual',
        'admin_municipal': 'Defesa Civil Municipal',
        'org': 'Organização Parceira',
        'user': 'Usuário Comum'
    }.get(data.get('responsavel_nivel'), data.get('responsavel_nivel') or 'Agente Registrador')

    info_grid = [
        [
            Paragraph("<b>ID Ocorrência:</b>", cell_bold), Paragraph(f"#{data.get('id', 'N/A')}", cell_normal),
            Paragraph("<b>Data do Evento:</b>", cell_bold), Paragraph(str(data.get('data_evento') or 'Não informada'), cell_normal)
        ],
        [
            Paragraph("<b>Tipologia do Evento:</b>", cell_bold), Paragraph(str(data.get('tipologia') or data.get('title') or 'Deslizamento'), cell_normal),
            Paragraph("<b>Status Curadoria:</b>", cell_bold), Paragraph(f"<font color='#16A34A'><b>Aprovado (Origem: {data.get('origem', 'Curadoria')})</b></font>", cell_normal)
        ],
        [
            Paragraph("<b>Município / UF:</b>", cell_bold), Paragraph(f"{data.get('municipio', 'Angra dos Reis')} - {data.get('uf', 'RJ')}", cell_normal),
            Paragraph("<b>Bairro / Local:</b>", cell_bold), Paragraph(str(data.get('bairro') or 'N/A'), cell_normal)
        ],
        [
            Paragraph("<b>Coordenadas WGS84:</b>", cell_bold), Paragraph(f"Lat: {data.get('lat', 0)} | Lng: {data.get('lng', 0)}", cell_normal),
            Paragraph("<b>Zona de Risco:</b>", cell_bold), Paragraph(str(data.get('zona') or 'Periourbana / Encosta'), cell_normal)
        ]
    ]
    t_info = Table(info_grid, colWidths=[110, 160, 110, 160])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 8))
    
    # Responsável Box
    resp_grid = [
        [
            Paragraph("<b>Responsável pelo Cadastro / Curadoria:</b>", cell_bold),
            Paragraph(f"{data.get('responsavel_nome') or 'Servidor Público Responsável'}", cell_normal),
            Paragraph("<b>Nível de Atuação:</b>", cell_bold),
            Paragraph(f"<b>{level_label}</b>", cell_normal)
        ],
        [
            Paragraph("<b>CPF do Responsável:</b>", cell_bold),
            Paragraph(str(data.get('responsavel_cpf') or '***.***.***-**'), cell_normal),
            Paragraph("<b>Matrícula Oficial:</b>", cell_bold),
            Paragraph(str(data.get('responsavel_matricula') or 'MAT-REGISTRO'), cell_normal)
        ]
    ]
    t_resp = Table(resp_grid, colWidths=[140, 130, 110, 160])
    t_resp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_resp)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 3. DICIONÁRIO DE DADOS (10 DOMÍNIOS)
    # ---------------------------------------------------------
    
    def build_domain_table(title, rows):
        table_data = [[Paragraph(f"<b>{title}</b>", ParagraphStyle('TTitle', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)), ""]]
        for label, val in rows:
            table_data.append([
                Paragraph(f"<b>{label}</b>", cell_bold),
                Paragraph(str(val if val not in [None, '', 'None'] else '-'), cell_normal)
            ])
        t = Table(table_data, colWidths=[200, 340])
        t.setStyle(TableStyle([
            ('SPAN', (0,0), (1,0)),
            ('BACKGROUND', (0,0), (1,0), secondary_color),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    # Domínio 1 & 2: Clima & Pedologia
    t_clima = build_domain_table("1. Fatores Climáticos e Pluviosidade", [
        ("Precipitação do Evento (mm):", data.get('clima_precipitacao_evento')),
        ("Precipitação Mensal (mm):", data.get('clima_precipitacao_mensal')),
        ("Acumulado 5 Dias / 10 Dias (mm):", f"{data.get('clima_precipitacao_5d') or '-'} mm / {data.get('clima_precipitacao_10d') or '-'} mm"),
        ("Vento (m/s) / Temperatura (ºC) / Pressão:", f"{data.get('clima_vento') or '-'} m/s | {data.get('clima_temperatura') or '-'} ºC | {data.get('clima_pressao') or '-'} atm")
    ])
    
    t_pedologia = build_domain_table("2. Pedologia (Caracterização do Solo)", [
        ("Classe de Solo (Embrapa):", data.get('ped_classe_solo')),
        ("Profundidade do Regolito / Textura:", f"{data.get('ped_profundidade') or '-'} | {data.get('ped_textura') or '-'}"),
        ("Porosidade / Umidade no Evento:", f"{data.get('ped_porosidade') or '-'} % | {data.get('ped_umidade_evento') or '-'}")
    ])

    story.append(KeepTogether([t_clima, Spacer(1, 8), t_pedologia, Spacer(1, 10)]))

    # Domínio 3 & 4: Geomorfologia & Geologia
    t_geo = build_domain_table("3. Geomorfologia e Relevo", [
        ("Declividade Encosta (% ou Graus):", data.get('geo_declividade')),
        ("Altitude (metros) / Orientação:", f"{data.get('geo_altitude') or '-'} m | {data.get('geo_orientacao') or '-'}"),
        ("Forma do Terreno / Curvatura:", f"{data.get('geo_forma_terreno') or '-'} | {data.get('geo_curvatura') or '-'}")
    ])
    
    t_geol = build_domain_table("4. Geologia e Substrato Rochoso", [
        ("Tipo de Rocha Predominante:", data.get('geol_tipo_rocha')),
        ("Composição Litológica / Estrutura:", f"{data.get('geol_composicao') or '-'} | {data.get('geol_estrutura') or '-'}"),
        ("Idade Geológica / Tectonismo:", f"{data.get('geol_idade') or '-'} | Tectonismo: {data.get('geol_tectonismo') or '-'}")
    ])

    story.append(KeepTogether([t_geo, Spacer(1, 8), t_geol, Spacer(1, 10)]))

    # Domínio 5 & 6: Fatores Antrópicos & Sociais
    t_antrop = build_domain_table("5. Fatores Antrópicos e Uso do Solo", [
        ("Cortes / Escavações na Encosta:", data.get('antrop_escavacao')),
        ("Sobrecarga no Topo / Tipo de Uso:", f"{data.get('antrop_sobrecarga') or '-'} | {data.get('antrop_tipo_uso') or '-'}"),
        ("Mineração / Desmatamento:", data.get('antrop_mineracao'))
    ])
    
    t_soc = build_domain_table("6. Impactos Sociais e Vítimas", [
        ("Vítimas Fatais / Feridos:", f"{data.get('n_mortos') or 0} mortos | {data.get('n_feridos') or 0} feridos"),
        ("Famílias Afetadas / Desalojados:", f"{data.get('soc_n_familias') or '-'} famílias | {data.get('soc_n_desalojados') or '-'} desalojados"),
        ("Desabrigados / Desaparecidos:", f"{data.get('soc_n_desabrigados') or '-'} desabrigados | {data.get('soc_n_desaparecidos') or '-'} desaparecidos")
    ])

    story.append(KeepTogether([t_antrop, Spacer(1, 8), t_soc, Spacer(1, 10)]))

    # Domínio 7 & 8: Econômicos & Ambientais
    t_econ = build_domain_table("7. Impactos Econômicos e Danos Materiais", [
        ("Estimativa Custo Total Danos:", data.get('econ_custo_total')),
        ("Infraestrutura Pública Atingida:", data.get('econ_infraestrutura')),
        ("Danos Agrícolas / Cultura Atingida:", f"{data.get('econ_agri_cultura') or '-'} (Área: {data.get('econ_agri_area_atingida') or '-'})")
    ])

    t_amb = build_domain_table("8. Impactos Ambientais", [
        ("Tipo de Impacto Ambiental:", data.get('amb_tipo_impacto')),
        ("Área Atingida (ha) / Recursos Afetados:", f"{data.get('amb_area_atingida') or '-'} ha | {data.get('amb_recursos_afetados') or '-'}"),
        ("Dano à Biodiversidade / Status Recuperação:", f"{data.get('amb_dano_biodiversidade') or '-'} | {data.get('amb_status_recuperacao') or '-'}")
    ])

    story.append(KeepTogether([t_econ, Spacer(1, 8), t_amb, Spacer(1, 10)]))

    # ---------------------------------------------------------
    # 4. DESCRIÇÃO E EVIDÊNCIA FOTOGRÁFICA
    # ---------------------------------------------------------
    story.append(Paragraph("<b>9. Descrição Técnica Detalhada</b>", section_heading))
    desc_p = Paragraph(data.get('description') or 'Nenhuma descrição complementar cadastrada para esta ocorrência.', cell_normal)
    t_desc = Table([[desc_p]], colWidths=[540])
    t_desc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_desc)
    story.append(Spacer(1, 10))

    # Check for image media
    media_filename = data.get('media_filename')
    if media_filename:
        media_path = os.path.join(upload_folder, media_filename)
        if os.path.exists(media_path) and media_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            try:
                img = Image(media_path, width=4.5*inch, height=3.0*inch)
                img.hAlign = 'CENTER'
                story.append(KeepTogether([
                    Paragraph("<b>10. Evidência Fotográfica Registrada em Campo</b>", section_heading),
                    img,
                    Spacer(1, 8)
                ]))
            except Exception as e:
                print(f"Erro ao incluir imagem no PDF: {e}")

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path
