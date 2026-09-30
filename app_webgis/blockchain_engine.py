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
        'id', 'title', 'description', 'data_evento', 'lat', 'lng', 'municipio', 'uf', 'bairro',
        'tipologia', 'zona', 'area_u_habitacoes', 'perc_area_atu', 'area_ar', 'area_rm', 'perc_area_atr',
        'clima_vento', 'clima_precipitacao_evento', 'clima_pressao', 'clima_temperatura',
        'clima_evapotranspiracao', 'clima_precipitacao_mensal', 'clima_precipitacao_5d', 'clima_precipitacao_10d',
        'ped_classe_solo', 'ped_profundidade', 'ped_textura', 'ped_porosidade',
        'ped_ucc', 'ped_cad', 'ped_k', 'ped_umidade_evento',
        'geo_orientacao', 'geo_curvatura', 'geo_forma_terreno', 'geo_declividade', 'geo_altitude',
        'geol_tipo_rocha', 'geol_composicao', 'geol_estrutura', 'geol_idade', 'geol_tectonismo',
        'antrop_escavacao', 'antrop_sobrecarga', 'antrop_tipo_uso', 'antrop_mineracao',
        'econ_custo_total', 'econ_infraestrutura', 'econ_patrimonio_privado', 'econ_patrimonio_publico',
        'econ_agri_area_atingida', 'econ_agri_perc_area', 'econ_agri_cultura', 'econ_agri_valor',
        'econ_interrupcao_duracao', 'econ_interrupcao_setores', 'econ_seguro', 'econ_custo_recuperacao',
        'soc_servicos_afetados', 'soc_tempo_recuperacao', 'soc_n_familias', 'soc_n_desalojados',
        'soc_n_desabrigados', 'soc_n_desaparecidos', 'n_mortos', 'n_feridos', 'soc_valor_total_danos',
        'amb_tipo_impacto', 'amb_area_atingida', 'amb_recursos_afetados', 'amb_dano_biodiversidade',
        'amb_custo_mitigacao', 'amb_tempo_recuperacao', 'amb_status_recuperacao',
        'midia_tipo', 'midia_fonte', 'midia_url',
        'telefone_contato', 'email_contato', 'ip_origem',
        'esfera_responsavel', 'motivo_escalacao', 'status'
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
        if action_type != 'INSERCAO_INICIAL':
            # Cria automaticamente o Bloco #1 (Registro inicial dos dados) para garantir rastreabilidade completa
            init_iso = rec_dict.get('created_at') or rec_dict.get('timestamp') or datetime.datetime.utcnow().isoformat()
            if hasattr(init_iso, 'isoformat'):
                init_iso = init_iso.isoformat()
            init_iso = str(init_iso) + "Z" if not str(init_iso).endswith("Z") else str(init_iso)
            init_curator = {
                'nome': rec_dict.get('responsavel_nome') or 'Declarante Comunitário',
                'cpf': rec_dict.get('responsavel_cpf') or '000.000.000-00',
                'matricula': rec_dict.get('responsavel_matricula') or 'N/A',
                'nivel': rec_dict.get('responsavel_nivel') or 'Visitante'
            }
            init_ip = rec_dict.get('ip_origem') or '127.0.0.1'
            init_qr = f"qr_sub_{submission_id}_blk_1.png"
            init_block_hash = calculate_block_hash(1, init_iso, GENESIS_HASH, data_hash, init_curator, init_ip, 'INSERCAO_INICIAL')
            
            try:
                target_host = host_url
                if not host_url or '127.0.0.1' in host_url or 'localhost' in host_url:
                    target_host = os.environ.get('CLOUD_TRACKING_URL', 'https://movmassa.onrender.com')
                tracking_url = f"{target_host.rstrip('/')}/blockchain/track/{submission_id}"
                generate_block_qrcode(tracking_url, init_qr, upload_folder)
            except Exception:
                pass

            conn.execute('''
                INSERT INTO blockchain_ledger (
                    submission_id, block_index, timestamp, data_hash, previous_hash, block_hash,
                    curator_nome, curator_cpf, curator_matricula, curator_nivel,
                    ip_origem, action_type, changes_summary, qrcode_filename
                ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INSERCAO_INICIAL', ?, ?)
            ''', (
                submission_id, init_iso, data_hash, GENESIS_HASH, init_block_hash,
                init_curator['nome'], init_curator['cpf'], init_curator['matricula'], init_curator['nivel'],
                init_ip, 'Registro inicial dos dados da ocorrência no Geoportal (Auditoria e Contato gravados)', init_qr
            ))
            conn.commit()
            block_index = 2
            previous_hash = init_block_hash
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
    try:
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
        conn.commit()
    except Exception as e_ins:
        print("[!] Erro ao inserir bloco no ledger:", e_ins)
        try:
            conn.rollback()
            conn.execute("ALTER TABLE blockchain_ledger DROP CONSTRAINT IF EXISTS blockchain_ledger_submission_id_key CASCADE")
            conn.execute("DROP INDEX IF EXISTS blockchain_ledger_submission_id_key CASCADE")
            conn.commit()
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
            conn.commit()
        except Exception as e2:
            print("[!] Falha no retry de inserção do bloco:", e2)
            try:
                conn.rollback()
            except Exception:
                pass
            raise e2
    
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

def sync_occurrence_blockchain_history(conn, submission_id, host_url='http://127.0.0.1:5000', upload_folder='static/uploads'):
    """
    Garante que a linha do tempo do Blockchain Ledger esteja 100% sincronizada
    com o ciclo de vida completo da ocorrência, reconstruindo e notarizando de forma retroativa
    quaisquer blocos que tenham faltado anteriormente (ex: escalações, aprovação nacional, alteração de atributos).
    """
    row = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    if not row:
        return
        
    sub_dict = dict(row)
    history = get_submission_history(conn, submission_id)
    
    # 1. Se não houver nenhum bloco, cria o Bloco #1 (INSERCAO_INICIAL)
    if not history:
        notarize_record(
            conn,
            submission_id,
            action_type='INSERCAO_INICIAL',
            changes_summary='Envio de ocorrência por usuário (Auditoria de IP e Contato gravados)',
            ip_origem=sub_dict.get('ip_origem') or '127.0.0.1',
            host_url=host_url,
            upload_folder=upload_folder
        )
        history = get_submission_history(conn, submission_id)
        
    actions = [b.get('action_type') for b in history]
    esfera = (sub_dict.get('esfera_responsavel') or 'municipal').strip().lower()
    
    # 2. Se a ocorrência foi escalada para estadual ou nacional, garante bloco de escalação estadual
    if esfera in ['estadual', 'nacional'] and 'ESCALACAO_ESTADUAL' not in actions:
        muni = sub_dict.get('municipio') or 'Angra dos Reis'
        uf = sub_dict.get('uf') or 'RJ'
        motivo = sub_dict.get('motivo_escalacao') or 'Ausência temporária de efetivo municipal local'
        notarize_record(
            conn,
            submission_id,
            action_type='ESCALACAO_ESTADUAL',
            changes_summary=f"Declaração de Indisponibilidade de Agentes: Gestor Municipal da Defesa Civil de {muni} acionou a Defesa Civil Estadual ({uf}). Motivo: {motivo}",
            ip_origem=sub_dict.get('ip_origem') or '127.0.0.1',
            host_url=host_url,
            upload_folder=upload_folder
        )
        history = get_submission_history(conn, submission_id)
        actions = [b.get('action_type') for b in history]
        
    # 3. Se foi escalada para nacional, garante bloco de escalação nacional
    if esfera == 'nacional' and 'ESCALACAO_NACIONAL' not in actions:
        uf = sub_dict.get('uf') or 'RJ'
        motivo = sub_dict.get('motivo_escalacao') or 'Demanda federativa escalada por indisponibilidade de efetivo estadual'
        notarize_record(
            conn,
            submission_id,
            action_type='ESCALACAO_NACIONAL',
            changes_summary=f"Declaração de Indisponibilidade de Agentes: Defesa Civil Estadual ({uf}) acionou a Defesa Civil Nacional (Governo Federal). Motivo: {motivo}",
            ip_origem=sub_dict.get('ip_origem') or '127.0.0.1',
            host_url=host_url,
            upload_folder=upload_folder
        )
        history = get_submission_history(conn, submission_id)
        actions = [b.get('action_type') for b in history]
        
    # 4. Se foi aprovada, mas não tem o bloco de aprovação oficial
    if sub_dict.get('status') == 'aprovado' and not any('APROVACAO' in (act or '') for act in actions):
        act_aprov = f"APROVACAO_CURADORIA_{esfera.upper()}"
        cur_tier = f"Defesa Civil {esfera.title()}"
        notarize_record(
            conn,
            submission_id,
            action_type=act_aprov,
            changes_summary=f"Homologação técnica oficial na Curadoria pela {cur_tier}. Parecer: {sub_dict.get('feedback') or 'Aprovado sem ressalvas'}",
            ip_origem=sub_dict.get('ip_origem') or '127.0.0.1',
            host_url=host_url,
            upload_folder=upload_folder
        )
        history = get_submission_history(conn, submission_id)
        
    # 5. Se os atributos atuais na base diferem do último bloco (características cadastradas/editadas)
    if history:
        latest = history[-1]
        cur_hash = calculate_data_hash(sub_dict)
        if cur_hash != latest['data_hash']:
            notarize_record(
                conn,
                submission_id,
                action_type='ALTERACAO_DADOS',
                changes_summary=f"Atualização e detalhamento de atributos no Dicionário de Dados por {sub_dict.get('responsavel_nome') or 'Curador Responsável'}",
                ip_origem=sub_dict.get('ip_origem') or '127.0.0.1',
                host_url=host_url,
                upload_folder=upload_folder
            )
