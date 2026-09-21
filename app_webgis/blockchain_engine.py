"""
MOVMASSA WebGIS - Motor Criptográfico de Blockchain e Cadeia de Custódia
Implementação de Notarização Digital e Rastreabilidade Espacial para Gestão de Riscos e Defesa Civil
"""
import hashlib
import json
import datetime

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def calculate_data_hash(record_dict):
    """
    Calcula o hash SHA-256 canônico dos dados da ocorrência.
    Garante que qualquer alteração de coordenadas, solo, declividade, vítimas ou mídias altere o hash.
    """
    # Seleção de campos canônicos essenciais
    canonical_keys = [
        'id', 'title', 'data_evento', 'lat', 'lng', 'municipio', 'uf', 'bairro',
        'tipologia', 'zona', 'ped_classe_solo', 'ped_textura', 'ped_profundidade',
        'geo_declividade', 'geo_altitude', 'geo_forma_terreno', 'geol_tipo_rocha',
        'clima_precipitacao_evento', 'clima_precipitacao_mensal',
        'n_mortos', 'n_feridos', 'soc_n_familias', 'econ_custo_total', 'amb_tipo_impacto'
    ]
    
    clean_dict = {}
    for k in canonical_keys:
        val = record_dict.get(k)
        clean_dict[k] = str(val) if val is not None else ""
        
    serialized = json.dumps(clean_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def calculate_block_hash(block_index, timestamp_iso, previous_hash, data_hash, curator_info):
    """
    Gera o hash do bloco encadeado (Block Hash).
    Combina índice, carimbo de tempo, hash do bloco anterior, hash dos dados e dados do curador.
    """
    block_string = f"{block_index}|{timestamp_iso}|{previous_hash}|{data_hash}|{json.dumps(curator_info, sort_keys=True)}"
    return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

def notarize_record(conn, submission_id, curator_user=None):
    """
    Registra e encadeia uma ocorrência no Blockchain Ledger do MOVMASSA.
    Retorna o dicionário com os dados do bloco criado.
    """
    # 1. Obter dados da ocorrência
    row = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    if not row:
        return None
        
    rec_dict = dict(row)
    data_hash = calculate_data_hash(rec_dict)
    
    # 2. Obter último bloco da cadeia para encadeamento
    last_block = conn.execute("SELECT block_index, block_hash FROM blockchain_ledger ORDER BY block_index DESC LIMIT 1").fetchone()
    
    if last_block:
        block_index = last_block['block_index'] + 1
        previous_hash = last_block['block_hash']
    else:
        block_index = 1
        previous_hash = GENESIS_HASH
        
    timestamp_iso = datetime.datetime.utcnow().isoformat() + "Z"
    
    curator_nome = (curator_user.nome_completo if curator_user and hasattr(curator_user, 'nome_completo') else None) or rec_dict.get('responsavel_nome') or 'Curadoria Técnica Defesa Civil'
    curator_cpf = (curator_user.cpf if curator_user and hasattr(curator_user, 'cpf') else None) or rec_dict.get('responsavel_cpf') or '000.000.000-00'
    curator_matricula = (curator_user.matricula if curator_user and hasattr(curator_user, 'matricula') else None) or rec_dict.get('responsavel_matricula') or 'DEF-ANG-001'
    curator_nivel = (curator_user.role_level if curator_user and hasattr(curator_user, 'role_level') else None) or rec_dict.get('responsavel_nivel') or 'admin_geral'
    
    curator_info = {
        'nome': curator_nome,
        'cpf': curator_cpf,
        'matricula': curator_matricula,
        'nivel': curator_nivel
    }
    
    block_hash = calculate_block_hash(block_index, timestamp_iso, previous_hash, data_hash, curator_info)
    
    # 3. Salvar ou atualizar no Blockchain Ledger
    existing = conn.execute("SELECT id FROM blockchain_ledger WHERE submission_id = ?", (submission_id,)).fetchone()
    if existing:
        conn.execute('''
            UPDATE blockchain_ledger SET 
                timestamp = ?, data_hash = ?, previous_hash = ?, block_hash = ?,
                curator_nome = ?, curator_cpf = ?, curator_matricula = ?, curator_nivel = ?
            WHERE submission_id = ?
        ''', (timestamp_iso, data_hash, previous_hash, block_hash, curator_nome, curator_cpf, curator_matricula, curator_nivel, submission_id))
    else:
        conn.execute('''
            INSERT INTO blockchain_ledger (
                submission_id, block_index, timestamp, data_hash, previous_hash, block_hash,
                curator_nome, curator_cpf, curator_matricula, curator_nivel
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (submission_id, block_index, timestamp_iso, data_hash, previous_hash, block_hash, curator_nome, curator_cpf, curator_matricula, curator_nivel))
        
    conn.commit()
    
    return {
        'submission_id': submission_id,
        'block_index': block_index,
        'timestamp': timestamp_iso,
        'data_hash': data_hash,
        'previous_hash': previous_hash,
        'block_hash': block_hash,
        'curator_info': curator_info
    }

def verify_record_integrity(conn, submission_id):
    """
    Verifica se o registro atual no banco coincide com a assinatura e o hash gravados no Blockchain.
    Detecta qualquer adulteração posterior.
    """
    row_sub = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    row_block = conn.execute("SELECT * FROM blockchain_ledger WHERE submission_id = ?", (submission_id,)).fetchone()
    
    if not row_sub or not row_block:
        return {'status': 'not_notarized', 'valid': False, 'message': 'Registro não notarizado em blockchain.'}
        
    rec_dict = dict(row_sub)
    block_dict = dict(row_block)
    
    current_data_hash = calculate_data_hash(rec_dict)
    
    if current_data_hash == block_dict['data_hash']:
        return {
            'status': 'verified',
            'valid': True,
            'message': 'Autenticidade e integridade criptográfica verificadas com sucesso. Documento 100% íntegro.',
            'block_index': block_dict['block_index'],
            'block_hash': block_dict['block_hash'],
            'data_hash': block_dict['data_hash'],
            'previous_hash': block_dict['previous_hash'],
            'timestamp': block_dict['timestamp'],
            'curator_nome': block_dict['curator_nome'],
            'curator_nivel': block_dict['curator_nivel']
        }
    else:
        return {
            'status': 'tampered',
            'valid': False,
            'message': 'ALERTA: Inconsistência detectada! Os dados atuais no banco de dados não coincidem com o hash imutável registrado no Blockchain.',
            'current_data_hash': current_data_hash,
            'original_data_hash': block_dict['data_hash'],
            'block_hash': block_dict['block_hash']
        }
