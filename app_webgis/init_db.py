import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = 'database.db'

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create Users Table with 4-tier Defesa Civil Admin roles & contact info
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            role_level TEXT NOT NULL DEFAULT 'user',
            email TEXT,
            nome_completo TEXT,
            telefone TEXT,
            matricula TEXT,
            cpf TEXT
        )
    ''')
    
    # Pre-seed users with mandatory registration info
    users = [
        ('admin', generate_password_hash('Admin@123'), 'admin', 'admin_geral', 'admin.geral@geoportal.gov.br', 'Administrador Geral MOVMASSA', '(24) 99999-0000', 'ADM-GERAL-001', '000.000.000-00'),
        ('defesa_nacional', generate_password_hash('Defesa@123'), 'admin', 'admin_nacional', 'nacional@defesacivil.gov.br', 'Agente Defesa Civil Nacional', '(61) 3333-1000', 'GOV-DCN-2026', '111.111.111-11'),
        ('defesa_estadual', generate_password_hash('Defesa@123'), 'admin', 'admin_estadual', 'estadual@defesacivil.rj.gov.br', 'Agente Defesa Civil Estadual RJ', '(21) 2222-2000', 'EST-DCE-2026', '222.222.222-22'),
        ('defesa_municipal', generate_password_hash('Defesa@123'), 'admin', 'admin_municipal', 'defesacivil@angra.rj.gov.br', 'Agente Defesa Civil Municipal Angra', '(24) 3365-3000', 'MUN-DCM-2026', '333.333.333-33'),
        ('org', generate_password_hash('Org@123'), 'org', 'org', 'contato@orgamb.org.br', 'Organização Técnica Ambientalista', '(24) 98888-4000', 'ORG-ANG-2026', '444.444.444-44'),
        ('user', generate_password_hash('User@123'), 'user', 'user', 'usuario@email.com', 'Usuário Comum de Campo', '(24) 97777-5000', 'N/A', '555.555.555-55')
    ]
    cursor.executemany('''
        INSERT INTO users (username, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', users)
    
    # 2. Create Layers Table
    cursor.execute('''
        CREATE TABLE layers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            category TEXT NOT NULL
        )
    ''')
    
    ordered_layers = [
        ('Angra dos Reis', 'angra.geojson', 1, 'Limite Municipal - IBGE'),
        ('Angra dos Reis Buffer (0,1 grau)', 'buffer_angra_geojson.geojson', 1, 'Limite Municipal (Buffer) - IBGE'),
        ('Hidrografia', 'hidrografia.geojson', 1, 'Hidrografia - IBGE'),
        ('Bacia Hidrográfica - Buffer', 'BHangra_buffer_GJ.geojson', 1, 'Hidrografia'),
        ('Área Urbanizada', 'areasurbanizadas.geojson', 1, 'IBGE'),
        ('Pontos de Deslizamento Registrados', 'pontos_angra.geojson', 1, 'Ocorrências')
    ]
        
    cursor.executemany('INSERT INTO layers (name, filename, is_active, category) VALUES (?, ?, ?, ?)', ordered_layers)

    # 3. Create Submissions Table (Curadoria & Points)
    cursor.execute('''
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            feedback TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            submission_type TEXT DEFAULT 'layer',
            lat REAL,
            lng REAL,
            media_filename TEXT,
            data_evento TEXT,
            id_pais TEXT DEFAULT 'Brasil',
            uf TEXT DEFAULT 'RJ',
            municipio TEXT DEFAULT 'Angra dos Reis',
            bairro TEXT,
            tipologia TEXT,
            zona TEXT,
            area_u_habitacoes TEXT,
            perc_area_atu TEXT,
            area_ar TEXT,
            area_rm TEXT,
            perc_area_atr TEXT,
            clima_vento TEXT,
            clima_precipitacao_evento TEXT,
            clima_pressao TEXT,
            clima_temperatura TEXT,
            clima_evapotranspiracao TEXT,
            clima_precipitacao_mensal TEXT,
            clima_precipitacao_5d TEXT,
            clima_precipitacao_10d TEXT,
            ped_classe_solo TEXT,
            ped_profundidade TEXT,
            ped_textura TEXT,
            ped_porosidade TEXT,
            ped_ucc TEXT,
            ped_cad TEXT,
            ped_k TEXT,
            ped_umidade_evento TEXT,
            geo_orientacao TEXT,
            geo_curvatura TEXT,
            geo_forma_terreno TEXT,
            geo_declividade TEXT,
            geo_altitude TEXT,
            geol_tipo_rocha TEXT,
            geol_composicao TEXT,
            geol_estrutura TEXT,
            geol_idade TEXT,
            geol_tectonismo TEXT,
            antrop_escavacao TEXT,
            antrop_sobrecarga TEXT,
            antrop_tipo_uso TEXT,
            antrop_mineracao TEXT,
            econ_custo_total TEXT,
            econ_infraestrutura TEXT,
            econ_patrimonio_privado TEXT,
            econ_patrimonio_publico TEXT,
            econ_agri_area_atingida TEXT,
            econ_agri_perc_area TEXT,
            econ_agri_cultura TEXT,
            econ_agri_valor TEXT,
            econ_interrupcao_duracao TEXT,
            econ_interrupcao_setores TEXT,
            econ_seguro TEXT,
            econ_custo_recuperacao TEXT,
            soc_servicos_afetados TEXT,
            soc_tempo_recuperacao TEXT,
            soc_n_familias TEXT,
            soc_n_desalojados TEXT,
            soc_n_desabrigados TEXT,
            soc_n_desaparecidos TEXT,
            n_mortos INTEGER DEFAULT 0,
            n_feridos INTEGER DEFAULT 0,
            soc_valor_total_danos TEXT,
            amb_tipo_impacto TEXT,
            amb_area_atingida TEXT,
            amb_recursos_afetados TEXT,
            amb_dano_biodiversidade TEXT,
            amb_custo_mitigacao TEXT,
            amb_tempo_recuperacao TEXT,
            amb_status_recuperacao TEXT,
            midia_tipo TEXT,
            midia_fonte TEXT,
            midia_url TEXT,
            origem TEXT DEFAULT 'Curadoria',
            responsavel_nome TEXT,
            responsavel_cpf TEXT,
            responsavel_matricula TEXT,
            responsavel_nivel TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados reinicializado com sucesso com suporte aos 4 níveis de Defesa Civil e campos do responsável!")

if __name__ == '__main__':
    init_db()
