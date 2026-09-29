"""
MOVMASSA WebGIS - Motor Criptográfico de Blockchain, Cadeia de Custódia e QR Code
Implementação de Notarização Digital, Rastreabilidade Temporal de Alterações e Prova Criptográfica
"""
import hashlib
import json
import datetime
import os
import qrcode

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def calculate_data_hash(record_dict):
    """
    Calcula o hash SHA-256 canônico dos dados da ocorrência.
    Qualquer alteração de coordenadas, solo, declividade, vítimas, contatos ou mídias altera o hash.
    """
    canonical_keys = [
        'id', 'title', 'data_evento', 'lat', 'lng', 'municipio', 'uf', 'bairro',
        'tipologia', 'zona', 'ped_classe_solo', 'ped_textura', 'ped_profundidade',
        'geo_declividade', 'geo_altitude', 'geo_forma_terreno', 'geol_tipo_rocha',
        'clima_precipitacao_evento', 'clima_precipitacao_mensal',
        'n_mortos', 'n_feridos', 'soc_n_familias', 'econ_custo_total', 'amb_tipo_impacto',
        'telefone_contato', 'email_contato', 'ip_origem'
    ]
    
    clean_dict = {}
    for k in canonical_keys:
        val = record_dict.get(k)
        clean_dict[k] = str(val).strip() if val is not None else ""
        
    serialized = json.dumps(clean_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def calculate_block_hash(block_index, timestamp_iso, previous_hash, data_hash, curator_info, ip_origem="", action_type=""):
    """
    Gera o hash do bloco encadeado (Block Hash).
    Combina índice, carimbo de tempo, hash anterior, hash dos dados, curador, IP e tipo de ação.
    """
    block_string = f"{block_index}|{timestamp_iso}|{previous_hash}|{data_hash}|{json.dumps(curator_info, sort_keys=True)}|{ip_origem}|{action_type}"
    return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

def generate_block_qrcode(tracking_url, filename, upload_folder):
    """
    Gera imagem PNG do QR Code apontando para o link público de auditoria e rastreamento.
    """
    try:
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(tracking_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
        img.save(filepath)
        return filename
    except Exception as e:
        print(f"[!] Erro ao gerar QR Code ({filename}): {e}")
        return ""

def notarize_record(conn, submission_id, curator_user=None, action_type='INSERCAO_INICIAL', changes_summary='', ip_origem=None, host_url='http://127.0.0.1:5000', upload_folder='static/uploads'):
    """
    Registra um novo bloco histórico no Blockchain Ledger do MOVMASSA.
    A cada inserção e a cada alteração, gera um novo bloco encadeado e um novo QR Code!
    """
    row = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    if not row:
        return None
        
    rec_dict = dict(row)
    data_hash = calculate_data_hash(rec_dict)
    
    # 1. Obter o último bloco específico desta ocorrência para formar o encadeamento
    last_block = conn.execute("""
        SELECT block_index, block_hash 
        FROM blockchain_ledger 
        WHERE submission_id = ? 
        ORDER BY block_index DESC LIMIT 1
    """, (submission_id,)).fetchone()
    
    if last_block:
        block_index = int(last_block['block_index']) + 1
        previous_hash = last_block['block_hash']
    else:
        block_index = 1
        previous_hash = GENESIS_HASH
        
    timestamp_iso = datetime.datetime.utcnow().isoformat() + "Z"
    
    # 2. Informações de autoria e IP
    curator_nome = (curator_user.nome_completo if curator_user and hasattr(curator_user, 'nome_completo') else None) or rec_dict.get('responsavel_nome') or 'Declarante Comunitário'
    curator_cpf = (curator_user.cpf if curator_user and hasattr(curator_user, 'cpf') else None) or rec_dict.get('responsavel_cpf') or '000.000.000-00'
    curator_matricula = (curator_user.matricula if curator_user and hasattr(curator_user, 'matricula') else None) or rec_dict.get('responsavel_matricula') or 'DEF-ANG-001'
    curator_nivel = (curator_user.role_level if curator_user and hasattr(curator_user, 'role_level') else None) or rec_dict.get('responsavel_nivel') or 'usuario_comum'
    
    ip_addr = ip_origem or rec_dict.get('ip_origem') or '127.0.0.1'
    
    curator_info = {
        'nome': curator_nome,
        'cpf': curator_cpf,
        'matricula': curator_matricula,
        'nivel': curator_nivel
    }
    
    block_hash = calculate_block_hash(block_index, timestamp_iso, previous_hash, data_hash, curator_info, ip_addr, action_type)
    
    # 3. Geração do QR Code exclusivo para este bloco/versão
    qr_filename = f"qr_sub_{submission_id}_blk_{block_index}.png"
    target_host = host_url
    if not host_url or '127.0.0.1' in host_url or 'localhost' in host_url:
        target_host = os.environ.get('CLOUD_TRACKING_URL', 'https://movmassa.onrender.com')
    tracking_url = f"{target_host.rstrip('/')}/blockchain/track/{submission_id}"
    generate_block_qrcode(tracking_url, qr_filename, upload_folder)
    
    # 4. Inserção do novo bloco histórico na tabela blockchain_ledger
    conn.execute('''
        INSERT INTO blockchain_ledger (
            submission_id, block_index, timestamp, data_hash, previous_hash, block_hash,
            curator_nome, curator_cpf, curator_matricula, curator_nivel,
            ip_origem, action_type, changes_summary, qrcode_filename
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        submission_id, block_index, timestamp_iso, data_hash, previous_hash, block_hash,
        curator_nome, curator_cpf, curator_matricula, curator_nivel,
        ip_addr, action_type, changes_summary or 'Atualização de ocorrência', qr_filename
    ))
    
    # 5. Atualizar na tabela submissions o ponteiro para o QR Code e IP mais recente
    conn.execute('''
        UPDATE submissions 
        SET qrcode_filename = ?,
            ip_origem = COALESCE(NULLIF(ip_origem, ''), ?)
        WHERE id = ?
    ''', (qr_filename, ip_addr, submission_id))
    
    conn.commit()
    
    return {
        'submission_id': submission_id,
        'block_index': block_index,
        'timestamp': timestamp_iso,
        'data_hash': data_hash,
        'previous_hash': previous_hash,
        'block_hash': block_hash,
        'curator_info': curator_info,
        'ip_origem': ip_addr,
        'action_type': action_type,
        'changes_summary': changes_summary,
        'qrcode_filename': qr_filename,
        'tracking_url': tracking_url
    }

def get_submission_history(conn, submission_id):
    """
    Retorna a linha do tempo completa de todos os blocos/alterações registrados para uma ocorrência.
    """
    rows = conn.execute("""
        SELECT * FROM blockchain_ledger 
        WHERE submission_id = ? 
        ORDER BY block_index ASC
    """, (submission_id,)).fetchall()
    return [dict(r) for r in rows]

def verify_record_integrity(conn, submission_id):
    """
    Verifica se o registro atual no banco coincide com a assinatura gravada no Blockchain
    e valida o encadeamento de todos os blocos históricos.
    """
    row_sub = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    history = get_submission_history(conn, submission_id)
    
    if not row_sub or not history:
        return {'status': 'not_notarized', 'valid': False, 'message': 'Registro não notarizado no Blockchain.'}
        
    rec_dict = dict(row_sub)
    latest_block = history[-1]
    
    current_data_hash = calculate_data_hash(rec_dict)
    
    # 1. Valida hash dos dados atuais contra o último bloco
    data_matches = (current_data_hash == latest_block['data_hash'])
    
    # 2. Valida encadeamento de blocos anteriores
    chain_valid = True
    for i in range(1, len(history)):
        if history[i]['previous_hash'] != history[i-1]['block_hash']:
            chain_valid = False
            break
            
    is_fully_valid = data_matches and chain_valid
    
    if is_fully_valid:
        return {
            'status': 'verified',
            'valid': True,
            'message': 'Autenticidade e integridade criptográfica 100% verificadas. Todos os blocos encadeados e dados íntegros.',
            'total_blocks': len(history),
            'latest_block': latest_block,
            'history': history
        }
    else:
        return {
            'status': 'tampered',
            'valid': False,
            'message': 'ALERTA DE SEGURANÇA: Inconsistência detectada! Os dados atuais ou a cadeia de blocos foram adulterados fora do fluxo oficial.',
            'current_data_hash': current_data_hash,
            'recorded_data_hash': latest_block['data_hash'],
            'chain_valid': chain_valid,
            'total_blocks': len(history),
            'latest_block': latest_block,
            'history': history
        }
