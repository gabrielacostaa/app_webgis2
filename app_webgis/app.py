# MOVMASSA WebGIS v2.5.1 Deployment Sync
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sys
import sqlite3
import os
import shutil
import tempfile
import zipfile
import datetime
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point

try:
    from pdf_generator import generate_occurrence_pdf
    import blockchain_engine
except ImportError:
    from app_webgis.pdf_generator import generate_occurrence_pdf
    import app_webgis.blockchain_engine as blockchain_engine

# Detection of runtime environment (PyInstaller frozen or standard Python)
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    APP_DATA_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DATA_DIR = BUNDLE_DIR

bundle_static = os.path.join(BUNDLE_DIR, 'app_webgis', 'static') if not os.path.exists(os.path.join(BUNDLE_DIR, 'static')) else os.path.join(BUNDLE_DIR, 'static')
bundle_templates = os.path.join(BUNDLE_DIR, 'app_webgis', 'templates') if not os.path.exists(os.path.join(BUNDLE_DIR, 'templates')) else os.path.join(BUNDLE_DIR, 'templates')

app = Flask(
    __name__,
    static_folder=bundle_static if os.path.exists(bundle_static) else 'static',
    template_folder=bundle_templates if os.path.exists(bundle_templates) else 'templates'
)
app.config['SECRET_KEY'] = 'geoportal_secret_key'
app.config['LAYERS_FOLDER'] = '../'

# Persistent database and uploads in user application folder
DB_PATH = os.path.join(APP_DATA_DIR, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(APP_DATA_DIR, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Copy pre-seeded database if running frozen and database.db doesn't exist yet
if getattr(sys, 'frozen', False) and not os.path.exists(DB_PATH):
    for candidate in [os.path.join(BUNDLE_DIR, 'app_webgis', 'database.db'), os.path.join(BUNDLE_DIR, 'database.db')]:
        if os.path.exists(candidate):
            try:
                shutil.copy2(candidate, DB_PATH)
            except Exception as e:
                print("Aviso ao copiar database.db empacotado:", e)
            break

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE_URL = os.environ.get('DATABASE_URL')

class DBWrapper:
    def __init__(self, is_postgres=False):
        self.is_postgres = is_postgres
        if self.is_postgres:
            import psycopg2
            import psycopg2.extras
            db_url = DATABASE_URL
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            self.conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.DictCursor)
        else:
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.row_factory = sqlite3.Row

    def execute(self, query, params=()):
        if self.is_postgres:
            pg_query = query.replace('?', '%s')
            cursor = self.conn.cursor()
            cursor.execute(pg_query, params)
            return cursor
        else:
            return self.conn.execute(query, params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def close(self):
        self.conn.close()

def get_db_connection():
    if DATABASE_URL:
        try:
            return DBWrapper(is_postgres=True)
        except Exception as e:
            print("Aviso: Conexão PostgreSQL falhou, utilizando SQLite local:", e)
            return DBWrapper(is_postgres=False)
    else:
        return DBWrapper(is_postgres=False)

RJ_MUNICIPALITIES = [
    'Angra dos Reis', 'Aperibé', 'Araruama', 'Areal', 'Armação dos Búzios', 'Arraial do Cabo',
    'Barra Mansa', 'Barra do Piraí', 'Belford Roxo', 'Bom Jardim', 'Bom Jesus do Itabapoana',
    'Cabo Frio', 'Cachoeiras de Macacu', 'Cambuci', 'Campos dos Goytacazes', 'Cantagalo',
    'Carapebus', 'Cardoso Moreira', 'Carmo', 'Casimiro de Abreu', 'Comendador Levy Gasparian',
    'Conceição de Macabu', 'Cordeiro', 'Duas Barras', 'Duque de Caxias',
    'Engenheiro Paulo de Frontin', 'Guapimirim', 'Iguaba Grande', 'Itaboraí', 'Itaguaí',
    'Italva', 'Itaocara', 'Itaperuna', 'Itatiaia', 'Japeri', 'Laje do Muriaé', 'Macaé',
    'Macuco', 'Magé', 'Mangaratiba', 'Maricá', 'Mendes', 'Mesquita', 'Miguel Pereira',
    'Miracema', 'Natividade', 'Nilópolis', 'Niterói', 'Nova Friburgo', 'Nova Iguaçu',
    'Paracambi', 'Paraty', 'Paraíba do Sul', 'Paty do Alferes', 'Petrópolis', 'Pinheiral',
    'Piraí', 'Porciúncula', 'Porto Real', 'Quatis', 'Queimados', 'Quissamã', 'Resende',
    'Rio Bonito', 'Rio Claro', 'Rio das Flores', 'Rio das Ostras', 'Rio de Janeiro',
    'Santa Maria Madalena', 'Santo Antônio de Pádua', 'Sapucaia', 'Saquarema', 'Seropédica',
    'Silva Jardim', 'Sumidouro', 'São Fidélis', 'São Francisco de Itabapoana', 'São Gonçalo',
    'São José de Ubá', 'São José do Vale do Rio Preto', 'São João da Barra', 'São João de Meriti',
    'São Pedro da Aldeia', 'São Sebastião do Alto', 'Tanguá', 'Teresópolis', 'Trajano de Moraes',
    'Três Rios', 'Valença', 'Varre-Sai', 'Vassouras', 'Volta Redonda'
]

BRAZIL_UFS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

class User(UserMixin):
    def __init__(self, id, username, role, role_level='user', email='', nome_completo='', telefone='', matricula='', cpf='', funcao='agente', municipio='Angra dos Reis', uf='RJ'):
        self.id = id
        self.username = username
        self.role = role
        self.role_level = role_level
        self.email = email
        self.nome_completo = nome_completo
        self.telefone = telefone
        self.matricula = matricula
        self.cpf = cpf
        self.funcao = funcao
        self.municipio = municipio or 'Angra dos Reis'
        self.uf = uf or 'RJ'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        u = dict(user)
        return User(
            id=u['id'],
            username=u['username'],
            role=u['role'],
            role_level=u.get('role_level', 'user'),
            email=u.get('email', ''),
            nome_completo=u.get('nome_completo', ''),
            telefone=u.get('telefone', ''),
            matricula=u.get('matricula', ''),
            cpf=u.get('cpf', ''),
            funcao=u.get('funcao', 'agente'),
            municipio=u.get('municipio', 'Angra dos Reis'),
            uf=u.get('uf', 'RJ')
        )
def parse_coordinate_value(val):
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None

    is_negative = ('-' in val_str) or ('S' in val_str.upper()) or ('W' in val_str.upper()) or ('O' in val_str.upper())

    if '.' in val_str and ',' in val_str:
        if val_str.rfind(',') > val_str.rfind('.'):
            val_str = val_str.replace('.', '').replace(',', '.')
        else:
            val_str = val_str.replace(',', '')
    else:
        val_str = val_str.replace(',', '.')

    import re
    cleaned = re.sub(r'[^0-9.]', '', val_str)
    if not cleaned:
        return None

    try:
        num = float(cleaned)
        return -num if is_negative else num
    except ValueError:
        return None

def utm_to_latlon(easting, northing, zone=23, northern=False):
    import math
    a = 6378137.0
    f = 1 / 298.257223563
    b = a * (1 - f)
    e = math.sqrt(1 - (b / a) ** 2)
    e_prime_sq = (e ** 2) / (1 - e ** 2)

    k0 = 0.9996
    x = easting - 500000.0
    y = northing if northern else northing - 10000000.0

    m = y / k0
    mu = m / (a * (1 - (e ** 2) / 4 - 3 * (e ** 4) / 64 - 5 * (e ** 6) / 256))
    e1 = (1 - math.sqrt(1 - e ** 2)) / (1 + math.sqrt(1 - e ** 2))

    phi1 = mu + (3 * e1 / 2 - 27 * (e1 ** 3) / 32) * math.sin(2 * mu) + \
           (21 * (e1 ** 2) / 16 - 55 * (e1 ** 4) / 32) * math.sin(4 * mu) + \
           (151 * (e1 ** 3) / 96) * math.sin(6 * mu) + \
           (1097 * (e1 ** 4) / 512) * math.sin(8 * mu)

    n1 = a / math.sqrt(1 - (e * math.sin(phi1)) ** 2)
    t1 = math.tan(phi1) ** 2
    c1 = e_prime_sq * (math.cos(phi1) ** 2)
    r1 = a * (1 - e ** 2) / math.pow(1 - (e * math.sin(phi1)) ** 2, 1.5)
    d = x / (n1 * k0)

    lat = phi1 - (n1 * t1 / r1) * (
        (d ** 2) / 2 -
        (5 + 3 * t1 + 10 * c1 - 4 * (c1 ** 2) - 9 * e_prime_sq) * (d ** 4) / 24 +
        (61 + 90 * t1 + 298 * c1 + 45 * (t1 ** 2) - 252 * e_prime_sq - 3 * (c1 ** 2)) * (d ** 6) / 720
    )
    lat = math.degrees(lat)

    lng_origin = (zone - 1) * 6 - 180 + 3
    lng = lng_origin + math.degrees((
        d -
        (1 + 2 * t1 + c1) * (d ** 3) / 6 +
        (5 - 2 * c1 + 28 * t1 - 3 * (c1 ** 2) + 8 * e_prime_sq + 24 * (t1 ** 2)) * (d ** 5) / 120
    ) / math.cos(phi1))

    return lat, lng

def get_client_ip():
    """
    Obtém o endereço IP real do cliente que enviou a requisição HTTP.
    Verifica headers de proxy reverso (X-Forwarded-For, X-Real-IP) e faz fallback seguro.
    """
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP').strip()
    return request.remote_addr or '127.0.0.1'

def upgrade_db():
    conn = get_db_connection()
    is_pg = getattr(conn, 'is_postgres', False)
    pk_type = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

    try:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                id {pk_type},
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                role_level TEXT DEFAULT 'user',
                email TEXT,
                nome_completo TEXT,
                telefone TEXT,
                matricula TEXT,
                cpf TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Aviso na criacao da tabela users:", e)

    # Drop NOT NULL constraint on legacy password column if present
    try:
        conn.execute('ALTER TABLE users ALTER COLUMN password DROP NOT NULL;')
        conn.commit()
    except Exception:
        conn.rollback()

    # Column migrations for legacy databases
    user_columns = [
        ('password', 'TEXT'),
        ('password_hash', 'TEXT'),
        ('role_level', "TEXT DEFAULT 'user'"),
        ('email', 'TEXT'),
        ('nome_completo', 'TEXT'),
        ('telefone', 'TEXT'),
        ('matricula', 'TEXT'),
        ('cpf', 'TEXT'),
        ('funcao', "TEXT DEFAULT 'agente'"),
        ('municipio', "TEXT DEFAULT 'Angra dos Reis'"),
        ('uf', "TEXT DEFAULT 'RJ'")
    ]
    for col_name, col_def in user_columns:
        try:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_def}')
            conn.commit()
        except Exception:
            conn.rollback()

    try:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS submissions (
                id {pk_type},
                user_id INTEGER,
                title TEXT,
                description TEXT,
                filename TEXT,
                status TEXT DEFAULT 'pendente',
                feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                origem TEXT DEFAULT 'Curadoria',
                responsavel_nome TEXT,
                responsavel_cpf TEXT,
                responsavel_matricula TEXT,
                responsavel_nivel TEXT,
                esfera_responsavel TEXT DEFAULT 'municipal',
                escalado_por INTEGER,
                motivo_escalacao TEXT,
                data_escalacao TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Aviso na criacao da tabela submissions:", e)

    try:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS layers (
                id {pk_type},
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                category TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Aviso na criacao da tabela layers:", e)

    # Migração estrutural da tabela blockchain_ledger para suportar múltiplos blocos por submissão
    try:
        if not is_pg:
            res = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='blockchain_ledger'").fetchone()
            if res and 'submission_id INTEGER UNIQUE' in res[0]:
                conn.execute("ALTER TABLE blockchain_ledger RENAME TO blockchain_ledger_legacy")
                conn.execute(f'''
                    CREATE TABLE blockchain_ledger (
                        id {pk_type},
                        submission_id INTEGER,
                        block_index INTEGER,
                        timestamp TEXT,
                        data_hash TEXT,
                        previous_hash TEXT,
                        block_hash TEXT,
                        curator_nome TEXT,
                        curator_cpf TEXT,
                        curator_matricula TEXT,
                        curator_nivel TEXT,
                        ip_origem TEXT,
                        action_type TEXT DEFAULT 'INSERCAO_INICIAL',
                        changes_summary TEXT,
                        qrcode_filename TEXT
                    )
                ''')
                conn.execute('''
                    INSERT INTO blockchain_ledger (
                        id, submission_id, block_index, timestamp, data_hash, previous_hash, block_hash,
                        curator_nome, curator_cpf, curator_matricula, curator_nivel
                    )
                    SELECT id, submission_id, block_index, timestamp, data_hash, previous_hash, block_hash,
                           curator_nome, curator_cpf, curator_matricula, curator_nivel
                    FROM blockchain_ledger_legacy
                ''')
                conn.execute("DROP TABLE blockchain_ledger_legacy")
                conn.commit()
    except Exception as e:
        conn.rollback()
        print("Aviso na migração estrutural do blockchain_ledger:", e)

    try:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS blockchain_ledger (
                id {pk_type},
                submission_id INTEGER,
                block_index INTEGER,
                timestamp TEXT,
                data_hash TEXT,
                previous_hash TEXT,
                block_hash TEXT,
                curator_nome TEXT,
                curator_cpf TEXT,
                curator_matricula TEXT,
                curator_nivel TEXT,
                ip_origem TEXT,
                action_type TEXT DEFAULT 'INSERCAO_INICIAL',
                changes_summary TEXT,
                qrcode_filename TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Aviso na criacao da tabela blockchain_ledger:", e)

    ledger_cols = [
        ('ip_origem', 'TEXT'),
        ('action_type', "TEXT DEFAULT 'INSERCAO_INICIAL'"),
        ('changes_summary', 'TEXT'),
        ('qrcode_filename', 'TEXT')
    ]
    for col, col_t in ledger_cols:
        try:
            conn.execute(f'ALTER TABLE blockchain_ledger ADD COLUMN {col} {col_t}')
            conn.commit()
        except Exception:
            conn.rollback()

    # Seed / Upsert default users
    default_users = [
        ('admin', generate_password_hash('Admin@123'), 'admin', 'admin_geral', 'admin.geral@geoportal.gov.br', 'Administrador Geral MOVMASSA', '(24) 99999-0000', 'ADM-GERAL-001', '000.000.000-00', 'gestor_agente', 'Angra dos Reis', 'RJ'),
        ('defesa_nacional', generate_password_hash('Defesa@123'), 'admin', 'admin_nacional', 'nacional@defesacivil.gov.br', 'Gestora Defesa Civil Nacional', '(61) 3333-1000', 'GOV-DCN-2026', '111.111.111-11', 'gestor_agente', 'Brasília', 'DF'),
        ('defesa_estadual', generate_password_hash('Defesa@123'), 'admin', 'admin_estadual', 'estadual@defesacivil.rj.gov.br', 'Gestora Defesa Civil Estadual RJ', '(21) 2222-2000', 'EST-DCE-2026', '222.222.222-22', 'gestor_agente', 'Rio de Janeiro', 'RJ'),
        ('defesa_municipal', generate_password_hash('Defesa@123'), 'admin', 'admin_municipal', 'defesacivil@angra.rj.gov.br', 'Gestora Defesa Civil Municipal Angra', '(24) 3365-3000', 'MUN-DCM-2026', '333.333.333-33', 'gestor_agente', 'Angra dos Reis', 'RJ'),
        ('defesa_rio', generate_password_hash('Defesa@123'), 'admin', 'admin_municipal', 'defesacivil@rio.rj.gov.br', 'Gestor Defesa Civil Municipal Rio de Janeiro', '(21) 2222-3333', 'MUN-RIO-2026', '666.666.666-66', 'gestor_agente', 'Rio de Janeiro', 'RJ'),
        ('defesa_petropolis', generate_password_hash('Defesa@123'), 'admin', 'admin_municipal', 'defesacivil@petropolis.rj.gov.br', 'Gestor Defesa Civil Municipal Petrópolis', '(24) 2246-9000', 'MUN-PET-2026', '777.777.777-77', 'gestor_agente', 'Petrópolis', 'RJ'),
        ('org', generate_password_hash('Org@123'), 'org', 'org', 'contato@orgamb.org.br', 'Organização Técnica Ambientalista', '(24) 98888-4000', 'ORG-ANG-2026', '444.444.444-44', 'gestor_agente', 'Angra dos Reis', 'RJ'),
        ('user', generate_password_hash('User@123'), 'user', 'user', 'usuario@email.com', 'Usuário Comum de Campo', '(24) 97777-5000', 'N/A', '555.555.555-55', 'agente', 'Angra dos Reis', 'RJ')
    ]
    for u in default_users:
        try:
            uname = u[0]
            existing = conn.execute('SELECT id FROM users WHERE username = ?', (uname,)).fetchone()
            if not existing:
                try:
                    conn.execute('''
                        INSERT INTO users (username, password, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (u[0], u[1], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8], u[9], u[10], u[11]))
                except Exception:
                    conn.rollback()
                    conn.execute('''
                        INSERT INTO users (username, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8], u[9], u[10], u[11]))
            else:
                try:
                    conn.execute('''
                        UPDATE users SET password = ?, password_hash = ?, role = ?, role_level = ?, funcao = ?, municipio = ?, uf = ? WHERE username = ?
                    ''', (u[1], u[1], u[2], u[3], u[9], u[10], u[11], uname))
                except Exception:
                    conn.rollback()
                    conn.execute('''
                        UPDATE users SET password_hash = ?, role = ?, role_level = ?, funcao = ?, municipio = ?, uf = ? WHERE username = ?
                    ''', (u[1], u[2], u[3], u[9], u[10], u[11], uname))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Aviso no seed do usuario {u[0]}:", e)

    if is_pg:
        try:
            conn.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));")
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("Aviso ao sincronizar sequence PostgreSQL de users:", e)

    # Seed default GIS layers if empty
    try:
        res = conn.execute('SELECT COUNT(*) FROM layers').fetchone()
        layers_count = res[0] if res else 0
        if layers_count == 0:
            ordered_layers = [
                ('Angra dos Reis', 'angra.geojson', 1, 'Limite Municipal - IBGE'),
                ('Angra dos Reis Buffer (0,1 grau)', 'buffer_angra_geojson.geojson', 1, 'Limite Municipal (Buffer) - IBGE'),
                ('Hidrografia', 'hidrografia.geojson', 1, 'Hidrografia - IBGE'),
                ('Bacia Hidrográfica - Buffer', 'BHangra_buffer_GJ.geojson', 1, 'Hidrografia'),
                ('Área Urbanizada', 'areasurbanizadas_angra.geojson', 1, 'IBGE'),
                ('Pontos de Deslizamento Registrados', 'pontos_angra.geojson', 1, 'Ocorrências')
            ]
            for l in ordered_layers:
                conn.execute('''
                    INSERT INTO layers (name, filename, is_active, category)
                    VALUES (?, ?, ?, ?)
                ''', l)
            conn.commit()
    except Exception as e:
        print("Aviso no seed de camadas:", e)
    users_cols = [
        ('role_level', 'TEXT DEFAULT "user"'),
        ('email', 'TEXT'),
        ('nome_completo', 'TEXT'),
        ('telefone', 'TEXT'),
        ('matricula', 'TEXT'),
        ('cpf', 'TEXT')
    ]
    for col, ctype in users_cols:
        try:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} {ctype}')
            conn.commit()
        except Exception:
            conn.rollback()

    # Check submissions table columns
    sub_cols = [
        ('timestamp', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ('submission_type', 'TEXT DEFAULT "layer"'),
        ('lat', 'REAL'),
        ('lng', 'REAL'),
        ('media_filename', 'TEXT'),
        ('data_evento', 'TEXT'),
        ('id_pais', 'TEXT DEFAULT "Brasil"'),
        ('uf', 'TEXT DEFAULT "RJ"'),
        ('municipio', 'TEXT DEFAULT "Angra dos Reis"'),
        ('bairro', 'TEXT'),
        ('tipologia', 'TEXT'),
        ('zona', 'TEXT'),
        ('area_u_habitacoes', 'TEXT'),
        ('perc_area_atu', 'TEXT'),
        ('area_ar', 'TEXT'),
        ('area_rm', 'TEXT'),
        ('perc_area_atr', 'TEXT'),
        
        # Clima
        ('clima_vento', 'TEXT'),
        ('clima_precipitacao_evento', 'TEXT'),
        ('clima_pressao', 'TEXT'),
        ('clima_temperatura', 'TEXT'),
        ('clima_evapotranspiracao', 'TEXT'),
        ('clima_precipitacao_mensal', 'TEXT'),
        ('clima_precipitacao_5d', 'TEXT'),
        ('clima_precipitacao_10d', 'TEXT'),
        
        # Pedologia
        ('ped_classe_solo', 'TEXT'),
        ('ped_profundidade', 'TEXT'),
        ('ped_textura', 'TEXT'),
        ('ped_porosidade', 'TEXT'),
        ('ped_ucc', 'TEXT'),
        ('ped_cad', 'TEXT'),
        ('ped_k', 'TEXT'),
        ('ped_umidade_evento', 'TEXT'),
        
        # Geomorfologia
        ('geo_orientacao', 'TEXT'),
        ('geo_curvatura', 'TEXT'),
        ('geo_forma_terreno', 'TEXT'),
        ('geo_declividade', 'TEXT'),
        ('geo_altitude', 'TEXT'),
        
        # Geologia
        ('geol_tipo_rocha', 'TEXT'),
        ('geol_composicao', 'TEXT'),
        ('geol_estrutura', 'TEXT'),
        ('geol_idade', 'TEXT'),
        ('geol_tectonismo', 'TEXT'),
        
        # Antrópicos
        ('antrop_escavacao', 'TEXT'),
        ('antrop_sobrecarga', 'TEXT'),
        ('antrop_tipo_uso', 'TEXT'),
        ('antrop_mineracao', 'TEXT'),
        
        # Econômicos
        ('econ_custo_total', 'TEXT'),
        ('econ_infraestrutura', 'TEXT'),
        ('econ_patrimonio_privado', 'TEXT'),
        ('econ_patrimonio_publico', 'TEXT'),
        ('econ_agri_area_atingida', 'TEXT'),
        ('econ_agri_perc_area', 'TEXT'),
        ('econ_agri_cultura', 'TEXT'),
        ('econ_agri_valor', 'TEXT'),
        ('econ_interrupcao_duracao', 'TEXT'),
        ('econ_interrupcao_setores', 'TEXT'),
        ('econ_seguro', 'TEXT'),
        ('econ_custo_recuperacao', 'TEXT'),
        
        # Sociais
        ('soc_servicos_afetados', 'TEXT'),
        ('soc_tempo_recuperacao', 'TEXT'),
        ('soc_n_familias', 'TEXT'),
        ('soc_n_desalojados', 'TEXT'),
        ('soc_n_desabrigados', 'TEXT'),
        ('soc_n_desaparecidos', 'TEXT'),
        ('n_mortos', 'INTEGER DEFAULT 0'),
        ('n_feridos', 'INTEGER DEFAULT 0'),
        ('soc_valor_total_danos', 'TEXT'),
        
        # Ambientais
        ('amb_tipo_impacto', 'TEXT'),
        ('amb_area_atingida', 'TEXT'),
        ('amb_recursos_afetados', 'TEXT'),
        ('amb_dano_biodiversidade', 'TEXT'),
        ('amb_custo_mitigacao', 'TEXT'),
        ('amb_tempo_recuperacao', 'TEXT'),
        ('amb_status_recuperacao', 'TEXT'),
        
        # Mídia
        ('midia_tipo', 'TEXT'),
        ('midia_fonte', 'TEXT'),
        ('midia_url', 'TEXT'),
        ('media_files_json', 'TEXT'),
        
        # Responsável & Origem & Auditoria / Rastreabilidade
        ('origem', "TEXT DEFAULT 'Curadoria'"),
        ('responsavel_nome', 'TEXT'),
        ('responsavel_cpf', 'TEXT'),
        ('responsavel_matricula', 'TEXT'),
        ('responsavel_nivel', 'TEXT'),
        ('telefone_contato', 'TEXT'),
        ('email_contato', 'TEXT'),
        ('ip_origem', 'TEXT'),
        ('qrcode_filename', 'TEXT'),
        ('esfera_responsavel', "TEXT DEFAULT 'municipal'"),
        ('escalado_por', 'INTEGER'),
        ('motivo_escalacao', 'TEXT'),
        ('data_escalacao', 'TEXT')
    ]
    for col, col_type in sub_cols:
        try:
            conn.execute(f'ALTER TABLE submissions ADD COLUMN {col} {col_type}')
            conn.commit()
        except Exception:
            conn.rollback()

    try:
        conn.execute("UPDATE submissions SET esfera_responsavel = 'municipal' WHERE esfera_responsavel IS NULL OR esfera_responsavel = ''")
        conn.commit()
    except Exception:
        conn.rollback()

    # Seed de ocorrências oficiais da Curadoria caso o banco esteja vazio
    seed_initial_curadoria(conn)
            
    conn.close()

def seed_initial_curadoria(conn):
    try:
        res = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()
        count = res[0] if res else 0
        if count > 0:
            return

        print("--> Inicializando banco com as 11 ocorrencias oficiais da Curadoria do MOVMASSA...")
        
        curated_points = [
            {
                "id": 204,
                "title": "Ponto Ocorrencia CSV #1",
                "status": "aprovado",
                "lat": -23.017027,
                "lng": -44.184746,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "425",
                "clima_precipitacao_mensal": "1500",
                "clima_precipitacao_5d": "100",
                "clima_precipitacao_10d": "580",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "Argissolo Vermelho Amarelo",
                "ped_profundidade": "2 metros",
                "ped_textura": "Argiloso",
                "ped_porosidade": "35",
                "ped_umidade_evento": "",
                "geo_declividade": "24",
                "geo_altitude": "500",
                "geo_forma_terreno": "",
                "antrop_escavacao": "Sim",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "app",
                "econ_custo_total": "2000000,00",
                "n_mortos": 150,
                "n_feridos": 432,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 205,
                "title": "Ponto Ocorrencia CSV #2",
                "status": "pendente",
                "lat": -22.98625,
                "lng": -44.30781,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 206,
                "title": "Ponto Ocorrencia CSV #3",
                "status": "pendente",
                "lat": -23.011347,
                "lng": -44.323,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 207,
                "title": "Ponto Ocorrencia CSV #4",
                "status": "pendente",
                "lat": -22.996155,
                "lng": -44.249306,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 208,
                "title": "Ponto Ocorrencia CSV #5",
                "status": "pendente",
                "lat": -22.9574,
                "lng": -44.44094,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 209,
                "title": "Ponto Ocorrencia CSV #6",
                "status": "pendente",
                "lat": -22.958912,
                "lng": -44.284492,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 210,
                "title": "Ponto Ocorrencia CSV #7",
                "status": "pendente",
                "lat": -23.00192,
                "lng": -44.313557,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 211,
                "title": "Ponto Ocorrencia CSV #8",
                "status": "pendente",
                "lat": -22.980824,
                "lng": -44.289955,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 212,
                "title": "Ponto Ocorrencia CSV #9",
                "status": "pendente",
                "lat": -22.960516,
                "lng": -44.440907,
                "tipologia": "Deslizamento de Encosta",
                "bairro": "Nao Informado",
                "zona": "Periourbana / Encosta",
                "data_evento": "2026-09-29",
                "description": "Ponto importado em lote via arquivo CSV por Administrador Geral.",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Administrador Geral",
                "responsavel_cpf": "000.000.000-00",
                "responsavel_matricula": "ADM-001",
                "responsavel_nivel": "admin_geral"
            },
            {
                "id": 215,
                "title": "DT",
                "status": "aprovado",
                "data_evento": "2026-09-29",
                "bairro": "Fzd Caxias",
                "zona": "Periourbana / Encosta",
                "lat": -22.759851,
                "lng": -43.69708,
                "tipologia": "Deslizamento de Encosta",
                "description": "",
                "clima_precipitacao_evento": "150",
                "clima_precipitacao_mensal": "250",
                "clima_precipitacao_5d": "100",
                "clima_precipitacao_10d": "150",
                "clima_vento": "10",
                "clima_temperatura": "20",
                "clima_pressao": "990",
                "ped_classe_solo": "Cambissolo",
                "ped_profundidade": "2",
                "ped_textura": "Franco-Argiloso",
                "ped_porosidade": "55",
                "ped_umidade_evento": "50%",
                "geo_declividade": "30",
                "geo_altitude": "1250",
                "geo_forma_terreno": "Concava ",
                "antrop_escavacao": "Nao",
                "antrop_sobrecarga": "Nao",
                "antrop_tipo_uso": "APP",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Visitante do Geoportal",
                "responsavel_cpf": "N/A",
                "responsavel_matricula": "N/A",
                "responsavel_nivel": "Visitante"
            },
            {
                "id": 216,
                "title": "PONTO_2",
                "status": "pendente",
                "data_evento": "2026-09-27",
                "bairro": "Angra dos Reis",
                "zona": "Periourbana / Encosta",
                "lat": -22.759851,
                "lng": -43.697086,
                "tipologia": "Deslizamento de Encosta",
                "description": "",
                "clima_precipitacao_evento": "",
                "clima_precipitacao_mensal": "",
                "clima_precipitacao_5d": "",
                "clima_precipitacao_10d": "",
                "clima_vento": "",
                "clima_temperatura": "",
                "clima_pressao": "",
                "ped_classe_solo": "",
                "ped_profundidade": "",
                "ped_textura": "",
                "ped_porosidade": "",
                "ped_umidade_evento": "",
                "geo_declividade": "",
                "geo_altitude": "",
                "geo_forma_terreno": "",
                "antrop_escavacao": "",
                "antrop_sobrecarga": "",
                "antrop_tipo_uso": "",
                "econ_custo_total": "",
                "n_mortos": 0,
                "n_feridos": 0,
                "telefone_contato": "(24) 99876-5432",
                "email_contato": "curadoria.defesa@angra.rj.gov.br",
                "ip_origem": "187.60.142.10",
                "responsavel_nome": "Visitante do Geoportal",
                "responsavel_cpf": "N/A",
                "responsavel_matricula": "N/A",
                "responsavel_nivel": "Visitante"
            }
        ]
        
        for p in curated_points:
            cur = conn.execute('''
                INSERT INTO submissions (
                    id, user_id, title, description, submission_type, status, lat, lng,
                    data_evento, id_pais, uf, municipio, bairro, tipologia, zona,
                    clima_precipitacao_evento, clima_precipitacao_mensal, clima_precipitacao_5d, clima_precipitacao_10d,
                    clima_vento, clima_temperatura, clima_pressao,
                    ped_classe_solo, ped_textura, ped_profundidade, ped_porosidade, ped_umidade_evento,
                    geo_declividade, geo_altitude, geo_forma_terreno,
                    antrop_escavacao, antrop_sobrecarga, antrop_tipo_uso,
                    n_mortos, n_feridos, econ_custo_total,
                    origem, telefone_contato, email_contato, ip_origem,
                    responsavel_nome, responsavel_cpf, responsavel_matricula, responsavel_nivel
                ) VALUES (
                    ?, 1, ?, ?, 'point', ?, ?, ?,
                    ?, 'Brasil', 'RJ', 'Angra dos Reis', ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    'Curadoria', ?, ?, ?,
                    ?, ?, ?, ?
                )
            ''', (
                p['id'], p['title'], p['description'], p['status'], p['lat'], p['lng'],
                p['data_evento'], p['bairro'], p['tipologia'], p['zona'],
                p['clima_precipitacao_evento'], p['clima_precipitacao_mensal'], p['clima_precipitacao_5d'], p['clima_precipitacao_10d'],
                p['clima_vento'], p['clima_temperatura'], p['clima_pressao'],
                p['ped_classe_solo'], p['ped_textura'], p['ped_profundidade'], p['ped_porosidade'], p['ped_umidade_evento'],
                p['geo_declividade'], p['geo_altitude'], p['geo_forma_terreno'],
                p['antrop_escavacao'], p['antrop_sobrecarga'], p['antrop_tipo_uso'],
                p['n_mortos'], p['n_feridos'], p['econ_custo_total'],
                p['telefone_contato'], p['email_contato'], p['ip_origem'],
                p['responsavel_nome'], p['responsavel_cpf'], p['responsavel_matricula'], p['responsavel_nivel']
            ))
            sub_id = p['id']
            
            # Notarização no Blockchain e geração do primeiro QR Code
            try:
                blockchain_engine.notarize_record(
                    conn,
                    sub_id,
                    action_type='INSERCAO_INICIAL',
                    changes_summary='Notarizacao cadastral oficial MOVMASSA',
                    ip_origem=p['ip_origem'],
                    upload_folder=app.config['UPLOAD_FOLDER']
                )
            except Exception as ne:
                print(f"Aviso ao notarizar ponto #{sub_id}:", ne)
                
        conn.commit()
        print(f"--> [OK] {len(curated_points)} pontos reais da Curadoria foram sincronizados e notarizados com QR Code!")
    except Exception as e:
        conn.rollback()
        print("[!] Erro no seed de pontos da curadoria:", e)

upgrade_db()

@app.route('/')
def index():
    conn = get_db_connection()
    layers = conn.execute('SELECT * FROM layers WHERE is_active = 1').fetchall()
    conn.close()
    return render_template('index.html', layers=layers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        uname_low = username.lower()
        
        BASE_ACCOUNTS = {
            'admin': {
                'username': 'admin',
                'passwords': ['Admin@123', 'admin123', 'admin'],
                'role': 'admin',
                'role_level': 'admin_geral',
                'email': 'admin.geral@geoportal.gov.br',
                'nome_completo': 'Administrador Geral MOVMASSA',
                'telefone': '(24) 99999-0000',
                'matricula': 'ADM-GERAL-001',
                'cpf': '000.000.000-00',
                'funcao': 'gestor_agente',
                'municipio': 'Angra dos Reis',
                'uf': 'RJ'
            },
            'defesa_nacional': {
                'username': 'defesa_nacional',
                'passwords': ['Defesa@123', 'defesa123', 'defesa'],
                'role': 'admin',
                'role_level': 'admin_nacional',
                'email': 'nacional@defesacivil.gov.br',
                'nome_completo': 'Gestora Defesa Civil Nacional',
                'telefone': '(61) 3333-1000',
                'matricula': 'GOV-DCN-2026',
                'cpf': '111.111.111-11',
                'funcao': 'gestor_agente',
                'municipio': 'Brasília',
                'uf': 'DF'
            },
            'defesa_estadual': {
                'username': 'defesa_estadual',
                'passwords': ['Defesa@123', 'defesa123', 'defesa'],
                'role': 'admin',
                'role_level': 'admin_estadual',
                'email': 'estadual@defesacivil.rj.gov.br',
                'nome_completo': 'Gestora Defesa Civil Estadual RJ',
                'telefone': '(21) 2222-2000',
                'matricula': 'EST-DCE-2026',
                'cpf': '222.222.222-22',
                'funcao': 'gestor_agente',
                'municipio': 'Rio de Janeiro',
                'uf': 'RJ'
            },
            'defesa_municipal': {
                'username': 'defesa_municipal',
                'passwords': ['Defesa@123', 'defesa123', 'defesa'],
                'role': 'admin',
                'role_level': 'admin_municipal',
                'email': 'defesacivil@angra.rj.gov.br',
                'nome_completo': 'Gestora Defesa Civil Municipal Angra',
                'telefone': '(24) 3365-3000',
                'matricula': 'MUN-DCM-2026',
                'cpf': '333.333.333-33',
                'funcao': 'gestor_agente',
                'municipio': 'Angra dos Reis',
                'uf': 'RJ'
            },
            'defesa_rio': {
                'username': 'defesa_rio',
                'passwords': ['Defesa@123', 'defesa123', 'defesa'],
                'role': 'admin',
                'role_level': 'admin_municipal',
                'email': 'defesacivil@rio.rj.gov.br',
                'nome_completo': 'Gestor Defesa Civil Municipal Rio de Janeiro',
                'telefone': '(21) 2222-3333',
                'matricula': 'MUN-RIO-2026',
                'cpf': '666.666.666-66',
                'funcao': 'gestor_agente',
                'municipio': 'Rio de Janeiro',
                'uf': 'RJ'
            },
            'defesa_petropolis': {
                'username': 'defesa_petropolis',
                'passwords': ['Defesa@123', 'defesa123', 'defesa'],
                'role': 'admin',
                'role_level': 'admin_municipal',
                'email': 'defesacivil@petropolis.rj.gov.br',
                'nome_completo': 'Gestor Defesa Civil Municipal Petrópolis',
                'telefone': '(24) 2246-9000',
                'matricula': 'MUN-PET-2026',
                'cpf': '777.777.777-77',
                'funcao': 'gestor_agente',
                'municipio': 'Petrópolis',
                'uf': 'RJ'
            },
            'org': {
                'username': 'org',
                'passwords': ['Org@123', 'org123', 'org'],
                'role': 'org',
                'role_level': 'org',
                'email': 'contato@orgamb.org.br',
                'nome_completo': 'Organização Técnica Ambientalista',
                'telefone': '(24) 98888-4000',
                'matricula': 'ORG-ANG-2026',
                'cpf': '444.444.444-44',
                'funcao': 'gestor_agente',
                'municipio': 'Angra dos Reis',
                'uf': 'RJ'
            },
            'user': {
                'username': 'user',
                'passwords': ['User@123', 'user123', 'user'],
                'role': 'user',
                'role_level': 'user',
                'email': 'usuario@email.com',
                'nome_completo': 'Usuário Comum de Campo',
                'telefone': '(24) 97777-5000',
                'matricula': 'N/A',
                'cpf': '555.555.555-55',
                'funcao': 'agente',
                'municipio': 'Angra dos Reis',
                'uf': 'RJ'
            }
        }
        
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?)', (username,)).fetchone()
        u_dict = dict(user_row) if user_row else None
        
        is_valid = False
        if u_dict:
            pwd_hash = u_dict.get('password_hash') or u_dict.get('password')
            if pwd_hash:
                try:
                    is_valid = check_password_hash(pwd_hash, password)
                except Exception:
                    is_valid = (pwd_hash == password)
        
        # Se nao validou pela hash ou se a conta base nao estava no banco
        if not is_valid and uname_low in BASE_ACCOUNTS:
            meta = BASE_ACCOUNTS[uname_low]
            if password in meta['passwords']:
                is_valid = True
                new_hash = generate_password_hash(meta['passwords'][0])
                if u_dict:
                    try:
                        conn.execute('''
                            UPDATE users SET password = ?, password_hash = ?, role = ?, role_level = ?, funcao = ?, municipio = ?, uf = ? WHERE id = ?
                        ''', (new_hash, new_hash, meta['role'], meta['role_level'], meta.get('funcao', 'gestor_agente'), meta.get('municipio', 'Angra dos Reis'), meta.get('uf', 'RJ'), u_dict['id']))
                        conn.commit()
                        u_dict['password_hash'] = new_hash
                        u_dict['role'] = meta['role']
                        u_dict['role_level'] = meta['role_level']
                        u_dict['funcao'] = meta.get('funcao', 'gestor_agente')
                        u_dict['municipio'] = meta.get('municipio', 'Angra dos Reis')
                        u_dict['uf'] = meta.get('uf', 'RJ')
                    except Exception as e:
                        conn.rollback()
                        print("Erro ao atualizar hash base:", e)
                else:
                    try:
                        conn.execute('''
                            INSERT INTO users (username, password, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            meta['username'], new_hash, new_hash, meta['role'], meta['role_level'],
                            meta['email'], meta['nome_completo'], meta['telefone'], meta['matricula'], meta['cpf'],
                            meta.get('funcao', 'gestor_agente'), meta.get('municipio', 'Angra dos Reis'), meta.get('uf', 'RJ')
                        ))
                        conn.commit()
                        inserted = conn.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?)', (meta['username'],)).fetchone()
                        if inserted:
                            u_dict = dict(inserted)
                    except Exception as e:
                        conn.rollback()
                        print("Erro ao inserir conta base:", e)
                        inserted = conn.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?)', (meta['username'],)).fetchone()
                        if inserted:
                            u_dict = dict(inserted)
        
        conn.close()

        if is_valid and u_dict:
            user_obj = User(
                id=u_dict['id'],
                username=u_dict['username'],
                role=u_dict['role'],
                role_level=u_dict.get('role_level', 'user'),
                email=u_dict.get('email', ''),
                nome_completo=u_dict.get('nome_completo', ''),
                telefone=u_dict.get('telefone', ''),
                matricula=u_dict.get('matricula', ''),
                cpf=u_dict.get('cpf', ''),
                funcao=u_dict.get('funcao', 'agente'),
                municipio=u_dict.get('municipio', 'Angra dos Reis'),
                uf=u_dict.get('uf', 'RJ')
            )
            login_user(user_obj)
            flash(f'Bem-vindo, {user_obj.nome_completo or user_obj.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        flash('Login inválido. Verifique suas credenciais.', 'danger')
            
    return render_template('login.html')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        nome_completo = request.form.get('nome_completo')
        cpf = request.form.get('cpf')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        matricula = request.form.get('matricula')
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE users SET nome_completo = ?, cpf = ?, email = ?, telefone = ?, matricula = ?
            WHERE id = ?
        ''', (nome_completo, cpf, email, telefone, matricula, current_user.id))
        conn.commit()
        conn.close()
        
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('index'))
        
    return render_template('profile.html')

# --- API e Uploads ---

@app.route('/api/layers')
def get_layers():
    conn = get_db_connection()
    layers = conn.execute('SELECT * FROM layers WHERE is_active = 1 ORDER BY id ASC').fetchall()
    conn.close()
    
    layers_data = []
    for row in layers:
        layers_data.append({
            'id': row['id'],
            'name': row['name'],
            'filename': row['filename'],
            'category': row['category']
        })
    return jsonify(layers_data)

@app.route('/api/layer/<path:filename>')
def serve_layer(filename):
    # Procura na pasta de dados do usuário
    user_file = os.path.join(APP_DATA_DIR, filename)
    if os.path.exists(user_file):
        return send_from_directory(APP_DATA_DIR, filename)
    
    # Se não achar na raiz, tenta na pasta de uploads configurada
    upload_folder = app.config.get('UPLOAD_FOLDER', '')
    if upload_folder and os.path.exists(os.path.join(upload_folder, filename)):
        return send_from_directory(upload_folder, filename)

    # Procura nos diretórios empacotados / código fonte
    for cand in [BUNDLE_DIR, os.path.join(BUNDLE_DIR, 'app_webgis'), os.path.dirname(os.path.abspath(__file__))]:
        cand_path = os.path.join(cand, filename)
        if os.path.exists(cand_path):
            return send_from_directory(cand, filename)
        
    abort(404)

@app.route('/<path:filename>')
def serve_direct_geojson(filename):
    if filename.endswith('.geojson'):
        # Procura na pasta de dados do usuário
        user_file = os.path.join(APP_DATA_DIR, filename)
        if os.path.exists(user_file):
            return send_from_directory(APP_DATA_DIR, filename)

        # Procura nos diretórios empacotados / código fonte
        for cand in [BUNDLE_DIR, os.path.join(BUNDLE_DIR, 'app_webgis'), os.path.dirname(os.path.abspath(__file__))]:
            cand_path = os.path.join(cand, filename)
            if os.path.exists(cand_path):
                return send_from_directory(cand, filename)
    abort(404)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if current_user.role not in ['admin', 'org']:
        flash('Apenas Administradores e Organizações podem enviar novas camadas.', 'danger')
        return redirect(url_for('index'))

    if 'file' not in request.files:
        flash('Nenhum arquivo enviado', 'danger')
        return redirect(url_for('index'))
        
    file = request.files['file']
    title = request.form.get('title')
    description = request.form.get('description')
    
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(url_for('index'))
        
    if file and file.filename.endswith('.geojson'):
        filename = secure_filename(file.filename)
        import time
        filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO submissions (user_id, title, description, filename, responsavel_nome, responsavel_cpf, responsavel_matricula, responsavel_nivel, origem)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id, title, description, filename,
            current_user.nome_completo or current_user.username,
            current_user.cpf or 'N/A',
            current_user.matricula or 'N/A',
            current_user.role_level or current_user.role,
            'Curadoria'
        ))
        conn.commit()
        conn.close()
        
        flash('Upload realizado com sucesso! Aguardando aprovação na Curadoria.', 'success')
    else:
        flash('Formato inválido. Apenas .geojson é permitido para camadas.', 'danger')
        
    return redirect(url_for('index'))

@app.route('/upload_point', methods=['POST'])
def upload_point():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    lat = parse_coordinate_value(request.form.get('lat'))
    lng = parse_coordinate_value(request.form.get('lng'))
    data_evento = request.form.get('data_evento')
    
    # Validação obrigatória de Telefone com DDD e E-mail para usuários sem cadastro
    telefone_contato = request.form.get('telefone_contato', '').strip()
    email_contato = request.form.get('email_contato', '').strip()
    client_ip = get_client_ip()

    if not current_user.is_authenticated:
        if not telefone_contato or not email_contato:
            flash('Para usuários sem cadastro, o preenchimento de Telefone (com DDD) e E-mail é OBRIGATÓRIO por motivos de auditoria e responsabilização civil/penal.', 'danger')
            return redirect(url_for('index'))
    else:
        if not telefone_contato:
            telefone_contato = getattr(current_user, 'telefone', '') or ''
        if not email_contato:
            email_contato = getattr(current_user, 'email', '') or ''

    if lat is None or lng is None:
        flash('Erro: Coordenadas geográficas inválidas ou não informadas. Por favor, clique no mapa ou insira latitude e longitude válidas.', 'danger')
        return redirect(url_for('index'))

    responsavel_nome = request.form.get('responsavel_nome', '').strip() or (current_user.nome_completo or current_user.username if current_user.is_authenticated else 'Cidadão / Usuário de Campo')
    responsavel_cpf = request.form.get('responsavel_cpf', '').strip() or (current_user.cpf if current_user.is_authenticated else 'N/A')
    user_id = current_user.id if current_user.is_authenticated else 1
    role_lvl = (current_user.role_level or current_user.role) if current_user.is_authenticated else 'Visitante'
    matricula = (current_user.matricula if current_user.is_authenticated else 'N/A')

    import json, time
    media_list = []
    
    file = request.files.get('media_file')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        m_filename = f"media_{int(time.time())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], m_filename))
        media_list.append(m_filename)

    photos = request.files.getlist('photos')
    photo_count = 0
    for p_file in photos:
        if p_file and p_file.filename != '' and photo_count < 5:
            fname = secure_filename(p_file.filename)
            saved_name = f"photo_{user_id}_{int(time.time())}_{fname}"
            p_file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_name))
            media_list.append(saved_name)
            photo_count += 1

    videos = request.files.getlist('videos')
    video_count = 0
    for v_file in videos:
        if v_file and v_file.filename != '' and video_count < 2:
            fname = secure_filename(v_file.filename)
            saved_name = f"video_{user_id}_{int(time.time())}_{fname}"
            v_file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_name))
            media_list.append(saved_name)
            video_count += 1

    media_json_str = json.dumps(media_list) if media_list else None
    media_filename = media_list[0] if media_list else None
        
    municipio_val = request.form.get('municipio', '').strip() or (getattr(current_user, 'municipio', 'Angra dos Reis') if current_user.is_authenticated else 'Angra dos Reis')
    uf_val = request.form.get('uf', '').strip().upper() or (getattr(current_user, 'uf', 'RJ') if current_user.is_authenticated else 'RJ')

    conn = get_db_connection()
    cur = conn.execute('''
        INSERT INTO submissions (
            user_id, title, description, submission_type, lat, lng, media_filename, media_files_json, filename, data_evento, municipio, uf,
            origem, responsavel_nome, responsavel_cpf, responsavel_matricula, responsavel_nivel,
            telefone_contato, email_contato, ip_origem, esfera_responsavel
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'municipal')
    ''', (
        user_id, title or 'Ocorrência Reportada em Campo', description, 'point', lat, lng, media_filename, media_json_str, '', data_evento, municipio_val, uf_val,
        'Curadoria',
        responsavel_nome,
        responsavel_cpf,
        matricula,
        role_lvl,
        telefone_contato,
        email_contato,
        client_ip
    ))
    sub_id = cur.lastrowid
    conn.commit()

    # Notarização imediata em Blockchain + Geração do Primeiro QR Code
    try:
        b_res = blockchain_engine.notarize_record(
            conn,
            sub_id,
            curator_user=current_user if current_user.is_authenticated else None,
            action_type='INSERCAO_INICIAL',
            changes_summary='Envio de ocorrência por usuário (Auditoria de IP e Contato gravados)',
            ip_origem=client_ip,
            host_url=request.host_url,
            upload_folder=app.config['UPLOAD_FOLDER']
        )
        qr_info = f" (Notarizada em Blockchain Bloco #{b_res['block_index']} com QR Code)" if b_res else ""
    except Exception as b_err:
        print("[!] Erro ao notarizar submissão:", b_err)
        qr_info = ""

    conn.close()
    
    try:
        import threading
        threading.Thread(target=sync_with_cloud, daemon=True).start()
    except Exception:
        pass
        
    flash(f'Ocorrência #{sub_id} reportada com sucesso!{qr_info} Registro sob auditoria de IP ({client_ip}). Aguardando homologação na Curadoria.', 'success')
    return redirect(url_for('index'))

@app.route('/upload_shapefile_bulk', methods=['POST'])
@login_required
def upload_shapefile_bulk():
    if current_user.role not in ['admin', 'org']:
        flash('Apenas Administradores e Organizações podem enviar nuvens de pontos em Shapefile.', 'danger')
        return redirect(url_for('index'))

    if 'shapefile_zip' not in request.files:
        flash('Nenhum arquivo Shapefile (.zip) foi selecionado.', 'danger')
        return redirect(url_for('index'))

    file = request.files['shapefile_zip']
    if file.filename == '' or not file.filename.endswith('.zip'):
        flash('Por favor, envie um arquivo compactado em formato .zip contendo os arquivos do Shapefile (.shp, .shx, .dbf, .prj).', 'danger')
        return redirect(url_for('index'))

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, secure_filename(file.filename))
            file.save(zip_path)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)

            shp_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(tmpdir) for f in filenames if f.endswith('.shp')]

            if not shp_files:
                flash('Nenhum arquivo .shp foi encontrado dentro do arquivo .zip enviado.', 'danger')
                return redirect(url_for('index'))

            shp_path = shp_files[0]
            gdf = gpd.read_file(shp_path)

            if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            conn = get_db_connection()
            count = 0
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom is None:
                    continue

                if geom.geom_type == 'Point':
                    lng, lat = geom.x, geom.y
                elif hasattr(geom, 'centroid'):
                    lng, lat = geom.centroid.x, geom.centroid.y
                else:
                    continue

                title = row.get('title') or row.get('NOME') or row.get('DESCRICAO') or f"Ponto Deslizamento #{idx+1}"
                desc = row.get('description') or row.get('OBS') or f"Ponto importado em lote via Shapefile por {current_user.nome_completo or current_user.username}"
                tipologia = row.get('tipologia') or row.get('TIPO') or "Deslizamento de Encosta"

                conn.execute('''
                    INSERT INTO submissions (
                        user_id, title, description, submission_type, lat, lng, filename, status,
                        origem, tipologia, municipio, uf,
                        responsavel_nome, responsavel_cpf, responsavel_matricula, responsavel_nivel
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    current_user.id, str(title), str(desc), 'point', float(lat), float(lng), '', 'pendente',
                    'Curadoria', str(tipologia), 'Angra dos Reis', 'RJ',
                    current_user.nome_completo or current_user.username,
                    current_user.cpf or 'N/A',
                    current_user.matricula or 'N/A',
                    current_user.role_level or current_user.role
                ))
                count += 1

            conn.commit()
            conn.close()

            flash(f'Sucesso! {count} pontos de ocorrência importados do Shapefile (.zip) e adicionados à fila da Curadoria (Aguardando Aprovação).', 'success')

    except Exception as e:
        print(f"Erro no processamento do Shapefile: {e}")
        flash(f'Erro ao processar o arquivo Shapefile: {str(e)}', 'danger')

    return redirect(url_for('curadoria'))

@app.route('/upload_bulk_csv', methods=['POST'])
@login_required
def upload_bulk_csv():
    if current_user.role not in ['admin', 'org']:
        flash('Acesso negado: apenas Administradores e Organizações podem enviar arquivos em lote.', 'danger')
        return redirect(url_for('index'))

    responsavel_nome = request.form.get('responsavel_nome', '').strip() or current_user.nome_completo or current_user.username
    responsavel_cpf = request.form.get('responsavel_cpf', '').strip() or current_user.cpf or 'N/A'

    if 'file' not in request.files:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.csv'):
        flash('Formato de arquivo inválido. Por favor, envie um arquivo .csv', 'danger')
        return redirect(url_for('index'))

    try:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"bulk_{tempfile.mktemp().split('/')[-1]}_{filename}")
        file.save(temp_path)

        content = None
        for encoding in ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1']:
            try:
                with open(temp_path, mode='r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if not content:
            flash('Erro ao ler a codificação do arquivo CSV.', 'danger')
            return redirect(url_for('index'))

        import io
        import csv

        first_line = content.splitlines()[0] if content.splitlines() else ''
        delimiter = ','
        if '\t' in first_line:
            delimiter = '\t'
        elif ';' in first_line:
            delimiter = ';'
        elif ',' in first_line:
            delimiter = ','
        else:
            try:
                dialect = csv.Sniffer().sniff(first_line)
                delimiter = dialect.delimiter
            except Exception:
                delimiter = ','

        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        fieldnames = [str(f).strip() for f in (reader.fieldnames or [])]
        field_map = {f.lower(): f for f in fieldnames}

        # Prioridade 1: Nomes explícitos de Latitude e Longitude
        lat_col = None
        lng_col = None

        if 'latitude' in field_map and 'longitude' in field_map:
            lat_col = field_map['latitude']
            lng_col = field_map['longitude']
        elif 'lat' in field_map and 'lng' in field_map:
            lat_col = field_map['lat']
            lng_col = field_map['lng']
        elif 'lat' in field_map and 'lon' in field_map:
            lat_col = field_map['lat']
            lng_col = field_map['lon']
        elif 'latitude' in field_map and 'lon' in field_map:
            lat_col = field_map['latitude']
            lng_col = field_map['lon']
        elif 'lat' in field_map and 'longitude' in field_map:
            lat_col = field_map['lat']
            lng_col = field_map['longitude']
        elif 'y' in field_map and 'x' in field_map:
            lat_col = field_map['y']
            lng_col = field_map['x']
        elif 'y_coord' in field_map and 'x_coord' in field_map:
            lat_col = field_map['y_coord']
            lng_col = field_map['x_coord']
        elif 'utms' in field_map and 'utmw' in field_map:
            lat_col = field_map['utms']
            lng_col = field_map['utmw']
        elif 'northing' in field_map and 'easting' in field_map:
            lat_col = field_map['northing']
            lng_col = field_map['easting']
        else:
            for f_low, f_orig in field_map.items():
                if f_low in ['latitude', 'lat']:
                    lat_col = f_orig
                elif f_low in ['longitude', 'lng', 'lon']:
                    lng_col = f_orig
            if not lat_col or not lng_col:
                for f_low, f_orig in field_map.items():
                    if f_low in ['y', 'utms', 'northing']:
                        lat_col = f_orig
                    elif f_low in ['x', 'utmw', 'easting']:
                        lng_col = f_orig

        if not lat_col or not lng_col:
            flash('Erro: Não foi possível identificar as colunas de coordenadas no CSV. Certifique-se de que a tabela possui colunas de Coordenadas como Latitude e Longitude, X e Y ou UTM.', 'warning')
            return redirect(url_for('index'))

        conn = get_db_connection()
        inserted_count = 0

        for idx, row in enumerate(reader):
            try:
                raw_lat_val = row.get(lat_col)
                raw_lng_val = row.get(lng_col)

                lat = parse_coordinate_value(raw_lat_val)
                lng = parse_coordinate_value(raw_lng_val)

                # Se lat/lng estiverem nulos ou fora de WGS84, busca se a linha possui colunas explícitas Latitude/Longitude
                if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    alt_lat_key = next((k for k in row.keys() if str(k).strip().lower() in ['latitude', 'lat']), None)
                    alt_lng_key = next((k for k in row.keys() if str(k).strip().lower() in ['longitude', 'lng', 'lon']), None)
                    if alt_lat_key and alt_lng_key:
                        alt_lat = parse_coordinate_value(row.get(alt_lat_key))
                        alt_lng = parse_coordinate_value(row.get(alt_lng_key))
                        if alt_lat is not None and alt_lng is not None and (-90 <= alt_lat <= 90) and (-180 <= alt_lng <= 180):
                            lat, lng = alt_lat, alt_lng

                # Se ainda fora de WGS84 mas estiver no intervalo UTM (ex: 500.000, 7.400.000)
                if lat is not None and lng is not None and (abs(lat) > 180 or abs(lng) > 180):
                    x_val, y_val = (lat, lng) if lng > lat else (lng, lat)
                    if 100000 <= x_val <= 900000 and 1000000 <= y_val <= 10000000:
                        try:
                            conv_lat, conv_lng = utm_to_latlon(x_val, y_val, zone=23, northern=False)
                            if -90 <= conv_lat <= 90 and -180 <= conv_lng <= 180:
                                lat, lng = conv_lat, conv_lng
                        except Exception as e:
                            print("Erro na conversao UTM:", e)

                if lat is None or lng is None:
                    continue

                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    if (-90 <= lng <= 90) and (-180 <= lat <= 180):
                        lat, lng = lng, lat
                    else:
                        continue

                title = row.get('title') or row.get('titulo') or row.get('nome') or f"Ponto Ocorrência CSV #{idx+1}"
                tipologia = row.get('tipologia') or row.get('tipo') or "Deslizamento de Encosta"
                bairro = row.get('bairro') or row.get('local') or "Não Informado"
                municipio = row.get('municipio') or "Angra dos Reis"
                uf = row.get('uf') or "RJ"
                data_evento = row.get('data') or row.get('data_evento') or row.get('data_ocorrencia') or ""
                description = row.get('descricao') or row.get('description') or row.get('obs') or f"Ponto importado em lote via arquivo CSV por {responsavel_nome}."

                conn.execute('''
                    INSERT INTO submissions (
                        user_id, title, description, submission_type, lat, lng, filename, status,
                        origem, tipologia, municipio, uf, bairro, data_evento,
                        responsavel_nome, responsavel_cpf, responsavel_matricula, responsavel_nivel
                    ) VALUES (?, ?, ?, 'point', ?, ?, '', 'pendente', 'Curadoria', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    current_user.id, str(title), str(description), float(lat), float(lng),
                    str(tipologia), str(municipio), str(uf), str(bairro), str(data_evento),
                    responsavel_nome, responsavel_cpf,
                    current_user.matricula or 'N/A',
                    current_user.role_level or current_user.role
                ))
                inserted_count += 1
            except (ValueError, TypeError):
                continue

        conn.commit()
        conn.close()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        if inserted_count > 0:
            flash(f'Sucesso! {inserted_count} pontos de ocorrência da tabela CSV foram importados e enviados para a fila da Curadoria (Aguardando Aprovação).', 'success')
        else:
            flash('Nenhum ponto válido com coordenadas numéricas foi encontrado no arquivo CSV.', 'warning')

    except Exception as e:
        print(f"Erro no processamento do CSV: {e}")
        flash(f'Erro ao processar o arquivo CSV: {str(e)}', 'danger')

    return redirect(url_for('index'))

@app.route('/api/occurrences')
def get_occurrences():
    conn = get_db_connection()
    points = conn.execute("""
        SELECT * FROM submissions 
        WHERE LOWER(TRIM(status)) = 'aprovado' 
          AND (
            submission_type = 'point' 
            OR (lat IS NOT NULL AND lng IS NOT NULL AND CAST(lat AS text) NOT IN ('', '0', '0.0', 'None', 'null'))
          )
    """).fetchall()
    conn.close()
    features = []
    for p in points:
        p_dict = dict(p)
        
        try:
            lat_val = float(p['lat'])
            lng_val = float(p['lng'])
        except (TypeError, ValueError):
            continue
            
        if not (-90 <= lat_val <= 90 and -180 <= lng_val <= 180) or (lat_val == 0 and lng_val == 0):
            continue

        import json
        m_list = []
        if p_dict.get('media_files_json'):
            try:
                m_list = json.loads(p_dict['media_files_json'])
            except Exception:
                m_list = []
        if p['media_filename'] and p['media_filename'] not in m_list:
            m_list.insert(0, p['media_filename'])

        media_urls = [url_for('serve_layer', filename=fn) for fn in m_list if fn]
        primary_media_url = media_urls[0] if media_urls else None
        is_admin_geral = current_user.is_authenticated and (current_user.role_level == 'admin_geral')
        is_gestor = current_user.is_authenticated and (current_user.role in ['admin', 'org'] or getattr(current_user, 'funcao', 'agente') in ['gestor', 'gestor_agente'])
        is_owner = current_user.is_authenticated and (current_user.id == p['user_id'])
        sub_sphere = p_dict.get('responsavel_nivel') or p_dict.get('u_role_level') or ''
        u_sphere = (getattr(current_user, 'role_level', '') or '').replace('agente_', 'admin_')
        s_sphere = sub_sphere.replace('agente_', 'admin_')
        is_same_sphere = bool(u_sphere and u_sphere == s_sphere)

        can_delete = is_admin_geral or (is_gestor and is_same_sphere) or is_owner
        
        props = {
            "id": p['id'],
            "title": p['title'],
            "description": p['description'],
            "data_evento": p_dict.get('data_evento'),
            "tipologia": p_dict.get('tipologia'),
            "id_pais": p_dict.get('id_pais') or 'Brasil',
            "uf": p_dict.get('uf') or 'RJ',
            "municipio": p_dict.get('municipio') or 'Angra dos Reis',
            "bairro": p_dict.get('bairro'),
            "lat": lat_val,
            "lng": lng_val,
            "zona": p_dict.get('zona'),
            "origem": p_dict.get('origem') or 'Curadoria',
            "responsavel_nome": p_dict.get('responsavel_nome') or 'Defesa Civil',
            "responsavel_cpf": p_dict.get('responsavel_cpf') or 'N/A',
            "responsavel_matricula": p_dict.get('responsavel_matricula') or 'N/A',
            "responsavel_nivel": p_dict.get('responsavel_nivel') or 'Geral',
            "telefone_contato": p_dict.get('telefone_contato') or 'Não informado',
            "email_contato": p_dict.get('email_contato') or 'Não informado',
            "ip_origem": p_dict.get('ip_origem') or '127.0.0.1',
            "qrcode_filename": p_dict.get('qrcode_filename'),
            "qrcode_url": url_for('serve_layer', filename=p_dict.get('qrcode_filename')) if p_dict.get('qrcode_filename') else None,
            "tracking_url": url_for('blockchain_track_view', sub_id=p['id']),
            "can_delete": can_delete,
            "area_u_habitacoes": p_dict.get('area_u_habitacoes'),
            "perc_area_atu": p_dict.get('perc_area_atu'),
            "area_ar": p_dict.get('area_ar'),
            "area_rm": p_dict.get('area_rm'),
            "perc_area_atr": p_dict.get('perc_area_atr'),
            
            # Clima
            "clima_vento": p_dict.get('clima_vento'),
            "clima_precipitacao_evento": p_dict.get('clima_precipitacao_evento'),
            "clima_pressao": p_dict.get('clima_pressao'),
            "clima_temperatura": p_dict.get('clima_temperatura'),
            "clima_evapotranspiracao": p_dict.get('clima_evapotranspiracao'),
            "clima_precipitacao_mensal": p_dict.get('clima_precipitacao_mensal'),
            "clima_precipitacao_5d": p_dict.get('clima_precipitacao_5d'),
            "clima_precipitacao_10d": p_dict.get('clima_precipitacao_10d'),
            
            # Pedologia
            "ped_classe_solo": p_dict.get('ped_classe_solo'),
            "ped_profundidade": p_dict.get('ped_profundidade'),
            "ped_textura": p_dict.get('ped_textura'),
            "ped_porosidade": p_dict.get('ped_porosidade'),
            "ped_ucc": p_dict.get('ped_ucc'),
            "ped_cad": p_dict.get('ped_cad'),
            "ped_k": p_dict.get('ped_k'),
            "ped_umidade_evento": p_dict.get('ped_umidade_evento'),
            
            # Geomorfologia
            "geo_orientacao": p_dict.get('geo_orientacao'),
            "geo_curvatura": p_dict.get('geo_curvatura'),
            "geo_forma_terreno": p_dict.get('geo_forma_terreno'),
            "geo_declividade": p_dict.get('geo_declividade'),
            "geo_altitude": p_dict.get('geo_altitude'),
            
            # Geologia
            "geol_tipo_rocha": p_dict.get('geol_tipo_rocha'),
            "geol_composicao": p_dict.get('geol_composicao'),
            "geol_estrutura": p_dict.get('geol_estrutura'),
            "geol_idade": p_dict.get('geol_idade'),
            "geol_tectonismo": p_dict.get('geol_tectonismo'),
            
            # Antrópicos
            "antrop_escavacao": p_dict.get('antrop_escavacao'),
            "antrop_sobrecarga": p_dict.get('antrop_sobrecarga'),
            "antrop_tipo_uso": p_dict.get('antrop_tipo_uso'),
            "antrop_mineracao": p_dict.get('antrop_mineracao'),
            
            # Econômicos
            "econ_custo_total": p_dict.get('econ_custo_total'),
            "econ_infraestrutura": p_dict.get('econ_infraestrutura'),
            "econ_patrimonio_privado": p_dict.get('econ_patrimonio_privado'),
            "econ_patrimonio_publico": p_dict.get('econ_patrimonio_publico'),
            "econ_agri_area_atingida": p_dict.get('econ_agri_area_atingida'),
            "econ_agri_perc_area": p_dict.get('econ_agri_perc_area'),
            "econ_agri_cultura": p_dict.get('econ_agri_cultura'),
            "econ_agri_valor": p_dict.get('econ_agri_valor'),
            "econ_interrupcao_duracao": p_dict.get('econ_interrupcao_duracao'),
            "econ_interrupcao_setores": p_dict.get('econ_interrupcao_setores'),
            "econ_seguro": p_dict.get('econ_seguro'),
            "econ_custo_recuperacao": p_dict.get('econ_custo_recuperacao'),
            
            # Sociais
            "soc_servicos_afetados": p_dict.get('soc_servicos_afetados'),
            "soc_tempo_recuperacao": p_dict.get('soc_tempo_recuperacao'),
            "soc_n_familias": p_dict.get('soc_n_familias'),
            "soc_n_desalojados": p_dict.get('soc_n_desalojados'),
            "soc_n_desabrigados": p_dict.get('soc_n_desabrigados'),
            "soc_n_desaparecidos": p_dict.get('soc_n_desaparecidos'),
            "n_mortos": p_dict.get('n_mortos') or 0,
            "n_feridos": p_dict.get('n_feridos') or 0,
            "soc_valor_total_danos": p_dict.get('soc_valor_total_danos'),
            
            # Ambientais
            "amb_tipo_impacto": p_dict.get('amb_tipo_impacto'),
            "amb_area_atingida": p_dict.get('amb_area_atingida'),
            "amb_recursos_afetados": p_dict.get('amb_recursos_afetados'),
            "amb_dano_biodiversidade": p_dict.get('amb_dano_biodiversidade'),
            "amb_custo_mitigacao": p_dict.get('amb_custo_mitigacao'),
            "amb_tempo_recuperacao": p_dict.get('amb_tempo_recuperacao'),
            "amb_status_recuperacao": p_dict.get('amb_status_recuperacao'),
            
            "midia_tipo": p_dict.get('midia_tipo'),
            "midia_fonte": p_dict.get('midia_fonte'),
            "media_url": primary_media_url,
            "media_urls": media_urls,
            "media_filename": p['media_filename']
        }
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lng_val, lat_val]
            },
            "properties": props
        })
        
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

@app.route('/api/occurrence/<int:point_id>/pdf')
@login_required
def occurrence_pdf(point_id):
    conn = get_db_connection()
    point = conn.execute('SELECT * FROM submissions WHERE id = ?', (point_id,)).fetchone()
    
    if not point:
        conn.close()
        flash('Ocorrência não encontrada.', 'danger')
        return redirect(url_for('index'))
        
    p_dict = dict(point)
    
    # Buscar ou gerar histórico e último bloco no Blockchain Ledger para o laudo
    history = blockchain_engine.get_submission_history(conn, point_id)
    if not history:
        try:
            b_info = blockchain_engine.notarize_record(
                conn,
                point_id,
                current_user,
                action_type='INSERCAO_INICIAL',
                changes_summary='Notarização para Emissão de Laudo Técnico',
                ip_origem=get_client_ip(),
                host_url=request.host_url,
                upload_folder=app.config['UPLOAD_FOLDER']
            )
            history = blockchain_engine.get_submission_history(conn, point_id)
        except Exception as e:
            print("Aviso ao notarizar no PDF:", e)
            
    if history:
        b_dict = history[-1]
        p_dict['block_hash'] = b_dict.get('block_hash')
        p_dict['data_hash'] = b_dict.get('data_hash')
        p_dict['previous_hash'] = b_dict.get('previous_hash')
        p_dict['block_index'] = b_dict.get('block_index')
        p_dict['blockchain_timestamp'] = b_dict.get('timestamp')
        p_dict['qrcode_filename'] = b_dict.get('qrcode_filename')
        p_dict['ip_origem'] = b_dict.get('ip_origem') or p_dict.get('ip_origem')
        
    conn.close()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, f"relatorio_ocorrencia_{point_id}.pdf")
        generate_occurrence_pdf(p_dict, pdf_path, upload_folder=app.config['UPLOAD_FOLDER'])
        
        return send_from_directory(
            tmpdir,
            f"relatorio_ocorrencia_{point_id}.pdf",
            as_attachment=False,
            mimetype='application/pdf'
        )

# --- Rotas de Auditoria Blockchain, Rastreabilidade e Cadeia de Custódia ---

@app.route('/blockchain/track/<int:sub_id>')
@app.route('/blockchain/track/<int:sub_id>', endpoint='blockchain_track')
def blockchain_track_view(sub_id):
    """
    Página pública de rastreamento e auditoria em Blockchain.
    Acessível via escaneamento do QR Code por qualquer cidadão ou autoridade.
    Exibe a linha do tempo completa de inserção e todas as alterações com respectivos QR Codes e hashes.
    """
    conn = get_db_connection()
    submission = conn.execute('SELECT * FROM submissions WHERE id = ?', (sub_id,)).fetchone()
    if not submission:
        conn.close()
        flash('Registro de ocorrência não encontrado.', 'warning')
        return redirect(url_for('index'))
    
    sub_dict = dict(submission)
    history = blockchain_engine.get_submission_history(conn, sub_id)
    if not history:
        try:
            blockchain_engine.notarize_record(
                conn,
                sub_id,
                action_type='INSERCAO_INICIAL',
                changes_summary='Notarização cadastral inicial de auditoria',
                ip_origem=sub_dict.get('ip_origem') or '127.0.0.1',
                host_url=request.host_url,
                upload_folder=app.config['UPLOAD_FOLDER']
            )
            history = blockchain_engine.get_submission_history(conn, sub_id)
        except Exception as e:
            print("Aviso ao notarizar visualização:", e)

    verification = blockchain_engine.verify_record_integrity(conn, sub_id)
    conn.close()

    latest_block = history[-1] if history else None
    
    return render_template(
        'blockchain_track.html',
        sub=sub_dict,
        submission=sub_dict,
        history=history,
        verification=verification,
        latest_block=latest_block
    )

@app.route('/api/occurrence/<int:sub_id>/blockchain')
def api_occurrence_blockchain(sub_id):
    conn = get_db_connection()
    history = blockchain_engine.get_submission_history(conn, sub_id)
    if not history:
        sub = conn.execute('SELECT status, ip_origem FROM submissions WHERE id = ?', (sub_id,)).fetchone()
        if sub:
            try:
                blockchain_engine.notarize_record(
                    conn,
                    sub_id,
                    action_type='INSERCAO_INICIAL',
                    changes_summary='Notarização sob demanda via API',
                    ip_origem=sub['ip_origem'] or get_client_ip(),
                    host_url=request.host_url,
                    upload_folder=app.config['UPLOAD_FOLDER']
                )
                history = blockchain_engine.get_submission_history(conn, sub_id)
            except Exception:
                pass
    conn.close()
    
    if not history:
        return jsonify({'notarized': False, 'message': 'Ocorrência ainda não notarizada em blockchain.'}), 404
        
    return jsonify({
        'notarized': True,
        'certificate': history[-1],
        'total_blocks': len(history),
        'history': history
    })

@app.route('/api/blockchain/verify/<int:sub_id>')
def api_blockchain_verify(sub_id):
    conn = get_db_connection()
    result = blockchain_engine.verify_record_integrity(conn, sub_id)
    conn.close()
    return jsonify(result)

@app.route('/api/blockchain/ledger')
def api_blockchain_ledger():
    conn = get_db_connection()
    blocks = conn.execute('SELECT * FROM blockchain_ledger ORDER BY block_index ASC').fetchall()
    conn.close()
    return jsonify({
        'total_blocks': len(blocks),
        'chain': [dict(b) for b in blocks]
    })

# --- Curadoria & Hierarquia Federativa da Defesa Civil ---

def check_curadoria_permissions(sub, user):
    """
    Determina permissões hierárquicas de Curadoria para o usuário sobre a submissão.
    Hierarquia:
      1. Esfera Municipal: Defesa Civil do Município da ocorrência (Angra dos Reis, Rio de Janeiro, Petrópolis, etc.)
         - Se indisponível, apenas o GESTOR Municipal pode escalar para a Defesa Civil Estadual.
      2. Esfera Estadual: Defesa Civil Estadual do Estado da ocorrência (ex: RJ, SP, etc.)
         - Se indisponível, apenas o GESTOR Estadual pode escalar para a Defesa Civil Nacional.
      3. Esfera Nacional: Defesa Civil Nacional (Governo Federal).
      4. Admin Geral: Acesso e autoridade plena de curadoria e escalação em qualquer nível.
    """
    sub_dict = dict(sub) if sub else {}
    sub_esfera = (sub_dict.get('esfera_responsavel') or 'municipal').strip().lower()
    sub_municipio = (sub_dict.get('municipio') or 'Angra dos Reis').strip()
    sub_uf = (sub_dict.get('uf') or 'RJ').strip()
    sub_status = sub_dict.get('status', 'pendente')
    sub_user_id = sub_dict.get('user_id')

    u_role_level = getattr(user, 'role_level', 'user') or 'user'
    u_funcao = getattr(user, 'funcao', 'agente') or 'agente'
    is_admin_geral = (u_role_level == 'admin_geral')
    is_gestor = (user.role in ['admin', 'org'] or u_funcao in ['gestor', 'gestor_agente'])
    is_owner = (user.id == sub_user_id) if (user.is_authenticated and sub_user_id) else False
    u_municipio = (getattr(user, 'municipio', 'Angra dos Reis') or 'Angra dos Reis').strip()
    u_uf = (getattr(user, 'uf', 'RJ') or 'RJ').strip()

    can_approve = False
    can_escalate = False
    escalate_target = None
    target_tier_name = None
    is_waiting_reason = ""
    current_tier_label = ""

    if sub_esfera == 'municipal':
        current_tier_label = f"Municipal ({sub_municipio})"
    elif sub_esfera == 'estadual':
        current_tier_label = f"Estadual ({sub_uf})"
    else:
        current_tier_label = "Nacional (Brasil)"

    if sub_status == 'pendente':
        if is_admin_geral:
            can_approve = True
            if sub_esfera == 'municipal':
                can_escalate = True
                escalate_target = 'estadual'
                target_tier_name = f"Defesa Civil Estadual ({sub_uf})"
            elif sub_esfera == 'estadual':
                can_escalate = True
                escalate_target = 'nacional'
                target_tier_name = "Defesa Civil Nacional (Governo Federal)"
        elif sub_esfera == 'municipal':
            matches_city = (u_municipio.lower() == sub_municipio.lower())
            if 'municipal' in u_role_level and matches_city:
                can_approve = True
                if is_gestor:
                    can_escalate = True
                    escalate_target = 'estadual'
                    target_tier_name = f"Defesa Civil Estadual ({sub_uf})"
                else:
                    can_escalate = False
            else:
                is_waiting_reason = f"Aguardando validação da Defesa Civil Municipal de {sub_municipio}."
        elif sub_esfera == 'estadual':
            matches_uf = (u_uf.upper() == sub_uf.upper())
            if 'estadual' in u_role_level and matches_uf:
                can_approve = True
                if is_gestor:
                    can_escalate = True
                    escalate_target = 'nacional'
                    target_tier_name = "Defesa Civil Nacional (Governo Federal)"
                else:
                    can_escalate = False
            else:
                is_waiting_reason = f"Aguardando validação da Defesa Civil Estadual ({sub_uf}) após escalação municipal."
        elif sub_esfera == 'nacional':
            if 'nacional' in u_role_level:
                can_approve = True
            else:
                is_waiting_reason = "Aguardando validação da Defesa Civil Nacional (Governo Federal) após escalação."

    can_edit = is_admin_geral or can_approve or is_owner
    can_delete = is_admin_geral or can_approve or is_owner

    return {
        'sub_esfera': sub_esfera,
        'sub_municipio': sub_municipio,
        'sub_uf': sub_uf,
        'can_approve': can_approve,
        'can_escalate': can_escalate,
        'escalate_target': escalate_target,
        'target_tier_name': target_tier_name,
        'current_tier_label': current_tier_label,
        'is_waiting_reason': is_waiting_reason,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'is_admin_geral': is_admin_geral,
        'is_gestor': is_gestor,
        'is_owner': is_owner
    }

@app.route('/curadoria')
@login_required
def curadoria():
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT s.*, u.username, u.role_level as u_role_level, u.municipio as u_municipio, u.uf as u_uf
        FROM submissions s 
        LEFT JOIN users u ON s.user_id = u.id 
        ORDER BY s.timestamp DESC
    ''').fetchall()
    conn.close()

    import json
    submissions = []
    for r in rows:
        r_dict = dict(r)
        m_list = []
        if r_dict.get('media_files_json'):
            try:
                m_list = json.loads(r_dict['media_files_json'])
            except Exception:
                m_list = []
        if r_dict.get('media_filename') and r_dict['media_filename'] not in m_list:
            m_list.insert(0, r_dict['media_filename'])
        r_dict['media_files_list'] = m_list
        
        perms = check_curadoria_permissions(r_dict, current_user)
        r_dict.update(perms)
        submissions.append(r_dict)
    
    return render_template('curadoria.html', submissions=submissions)

@app.route('/curadoria/escalate/<int:sub_id>', methods=['POST'])
@login_required
def curadoria_escalate(sub_id):
    motivo = request.form.get('motivo', '').strip()
    if not motivo:
        flash('É obrigatório informar a justificativa técnica / declaração de indisponibilidade de agentes para realizar a escalação.', 'danger')
        return redirect(url_for('curadoria'))

    conn = get_db_connection()
    submission = conn.execute('''
        SELECT s.*, u.role_level as u_role_level, u.municipio as u_municipio, u.uf as u_uf
        FROM submissions s 
        LEFT JOIN users u ON s.user_id = u.id 
        WHERE s.id = ?
    ''', (sub_id,)).fetchone()

    if not submission:
        conn.close()
        flash('Submissão não encontrada.', 'danger')
        return redirect(url_for('curadoria'))

    perms = check_curadoria_permissions(submission, current_user)
    if not perms['can_escalate']:
        conn.close()
        flash(f'Acesso negado. Apenas gestores responsáveis pela esfera atual possuem atribuição para escalar ocorrências. {perms["is_waiting_reason"]}', 'danger')
        return redirect(url_for('curadoria'))

    target_tier = perms['escalate_target']
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if target_tier == 'estadual':
        action_type = 'ESCALACAO_ESTADUAL'
        summary = f"Declaração de Indisponibilidade de Agentes: Gestor Municipal da Defesa Civil de {perms['sub_municipio']} declarou ausência de efetivo e acionou a Defesa Civil Estadual ({perms['sub_uf']}). Motivo: {motivo}"
    elif target_tier == 'nacional':
        action_type = 'ESCALACAO_NACIONAL'
        summary = f"Declaração de Indisponibilidade de Agentes: Gestor Estadual da Defesa Civil ({perms['sub_uf']}) declarou ausência de efetivo e acionou a Defesa Civil Nacional (Governo Federal). Motivo: {motivo}"
    else:
        conn.close()
        flash('Não há esfera superior disponível para escalação deste registro.', 'warning')
        return redirect(url_for('curadoria'))

    conn.execute('''
        UPDATE submissions 
        SET esfera_responsavel = ?,
            escalado_por = ?,
            motivo_escalacao = ?,
            data_escalacao = ?
        WHERE id = ?
    ''', (target_tier, current_user.id, motivo, now_str, sub_id))
    conn.commit()

    # Notarização em Blockchain com novo hash e novo QR Code
    b_res = None
    try:
        client_ip = get_client_ip()
        b_res = blockchain_engine.notarize_record(
            conn,
            sub_id,
            curator_user=current_user,
            action_type=action_type,
            changes_summary=summary,
            ip_origem=client_ip,
            host_url=request.host_url,
            upload_folder=app.config['UPLOAD_FOLDER']
        )
    except Exception as e:
        print("[!] Erro na notarização de escalação:", e)

    conn.close()

    try:
        import threading
        threading.Thread(target=sync_with_cloud, daemon=True).start()
    except Exception:
        pass

    blk_msg = f" (Bloco Blockchain #{b_res['block_index']} e novo QR Code gerado)" if b_res else ""
    flash(f'Ocorrência #{sub_id} escalada com sucesso para a {perms["target_tier_name"]}!{blk_msg}', 'success')
    return redirect(url_for('curadoria'))

@app.route('/curadoria/update/<int:sub_id>', methods=['POST'])
@login_required
def curadoria_update(sub_id):
    conn = get_db_connection()
    sub = conn.execute('''
        SELECT s.*, u.role_level as u_role_level, u.municipio as u_municipio, u.uf as u_uf
        FROM submissions s 
        LEFT JOIN users u ON s.user_id = u.id 
        WHERE s.id = ?
    ''', (sub_id,)).fetchone()
    
    if not sub:
        conn.close()
        return jsonify({'error': 'Submission not found'}), 404

    perms = check_curadoria_permissions(sub, current_user)
    if not perms['can_edit']:
        conn.close()
        return jsonify({'error': f'Unauthorized: Você não possui permissão para editar este registro. {perms["is_waiting_reason"]}'}), 403
        
    f = request.form
    client_ip = get_client_ip()
    tel_contato = f.get('telefone_contato')
    email_contato = f.get('email_contato')

    conn.execute('''
        UPDATE submissions SET 
            title = ?, description = ?, data_evento = ?, tipologia = ?, 
            id_pais = ?, uf = ?, municipio = ?, bairro = ?, lat = ?, lng = ?,
            zona = ?, area_u_habitacoes = ?, perc_area_atu = ?, area_ar = ?, area_rm = ?, perc_area_atr = ?,
            
            clima_vento = ?, clima_precipitacao_evento = ?, clima_pressao = ?, clima_temperatura = ?,
            clima_evapotranspiracao = ?, clima_precipitacao_mensal = ?, clima_precipitacao_5d = ?, clima_precipitacao_10d = ?,
            
            ped_classe_solo = ?, ped_profundidade = ?, ped_textura = ?, ped_porosidade = ?,
            ped_ucc = ?, ped_cad = ?, ped_k = ?, ped_umidade_evento = ?,
            
            geo_orientacao = ?, geo_curvatura = ?, geo_forma_terreno = ?, geo_declividade = ?, geo_altitude = ?,
            
            geol_tipo_rocha = ?, geol_composicao = ?, geol_estrutura = ?, geol_idade = ?, geol_tectonismo = ?,
            
            antrop_escavacao = ?, antrop_sobrecarga = ?, antrop_tipo_uso = ?, antrop_mineracao = ?,
            
            econ_custo_total = ?, econ_infraestrutura = ?, econ_patrimonio_privado = ?, econ_patrimonio_publico = ?,
            econ_agri_area_atingida = ?, econ_agri_perc_area = ?, econ_agri_cultura = ?, econ_agri_valor = ?,
            econ_interrupcao_duracao = ?, econ_interrupcao_setores = ?, econ_seguro = ?, econ_custo_recuperacao = ?,
            
            soc_servicos_afetados = ?, soc_tempo_recuperacao = ?, soc_n_familias = ?, soc_n_desalojados = ?,
            soc_n_desabrigados = ?, soc_n_desaparecidos = ?, n_mortos = ?, n_feridos = ?, soc_valor_total_danos = ?,
            
            amb_tipo_impacto = ?, amb_area_atingida = ?, amb_recursos_afetados = ?, amb_dano_biodiversidade = ?,
            amb_custo_mitigacao = ?, amb_tempo_recuperacao = ?, amb_status_recuperacao = ?,
            
            midia_tipo = ?, midia_fonte = ?, midia_url = ?,
            telefone_contato = COALESCE(NULLIF(?, ''), telefone_contato),
            email_contato = COALESCE(NULLIF(?, ''), email_contato)
        WHERE id = ?
    ''', (
        f.get('title'), f.get('description'), f.get('data_evento'), f.get('tipologia'),
        f.get('id_pais', 'Brasil'), f.get('uf', 'RJ'), f.get('municipio', 'Angra dos Reis'), f.get('bairro'), f.get('lat'), f.get('lng'),
        f.get('zona'), f.get('area_u_habitacoes'), f.get('perc_area_atu'), f.get('area_ar'), f.get('area_rm'), f.get('perc_area_atr'),
        
        f.get('clima_vento'), f.get('clima_precipitacao_evento'), f.get('clima_pressao'), f.get('clima_temperatura'),
        f.get('clima_evapotranspiracao'), f.get('clima_precipitacao_mensal'), f.get('clima_precipitacao_5d'), f.get('clima_precipitacao_10d'),
        
        f.get('ped_classe_solo'), f.get('ped_profundidade'), f.get('ped_textura'), f.get('ped_porosidade'),
        f.get('ped_ucc'), f.get('ped_cad'), f.get('ped_k'), f.get('ped_umidade_evento'),
        
        f.get('geo_orientacao'), f.get('geo_curvatura'), f.get('geo_forma_terreno'), f.get('geo_declividade'), f.get('geo_altitude'),
        
        f.get('geol_tipo_rocha'), f.get('geol_composicao'), f.get('geol_estrutura'), f.get('geol_idade'), f.get('geol_tectonismo'),
        
        f.get('antrop_escavacao'), f.get('antrop_sobrecarga'), f.get('antrop_tipo_uso'), f.get('antrop_mineracao'),
        
        f.get('econ_custo_total'), f.get('econ_infraestrutura'), f.get('econ_patrimonio_privado'), f.get('econ_patrimonio_publico'),
        f.get('econ_agri_area_atingida'), f.get('econ_agri_perc_area'), f.get('econ_agri_cultura'), f.get('econ_agri_valor'),
        f.get('econ_interrupcao_duracao'), f.get('econ_interrupcao_setores'), f.get('econ_seguro'), f.get('econ_custo_recuperacao'),
        
        f.get('soc_servicos_afetados'), f.get('soc_tempo_recuperacao'), f.get('soc_n_familias'), f.get('soc_n_desalojados'),
        f.get('soc_n_desabrigados'), f.get('soc_n_desaparecidos'), f.get('n_mortos', 0), f.get('n_feridos', 0), f.get('soc_valor_total_danos'),
        
        f.get('amb_tipo_impacto'), f.get('amb_area_atingida'), f.get('amb_recursos_afetados'), f.get('amb_dano_biodiversidade'),
        f.get('amb_custo_mitigacao'), f.get('amb_tempo_recuperacao'), f.get('amb_status_recuperacao'),
        
        f.get('midia_tipo'), f.get('midia_fonte'), f.get('midia_url'),
        tel_contato, email_contato,
        sub_id
    ))

    # Processa múltiplos uploads de Fotos (até 5) e Vídeos (até 2)
    photos = request.files.getlist('photos')
    videos = request.files.getlist('videos')

    import json, time
    existing_sub = conn.execute('SELECT media_files_json, media_filename FROM submissions WHERE id = ?', (sub_id,)).fetchone()
    current_media = []
    if existing_sub:
        ex_dict = dict(existing_sub)
        if ex_dict.get('media_files_json'):
            try:
                current_media = json.loads(ex_dict['media_files_json'])
            except Exception:
                current_media = []
        if ex_dict.get('media_filename') and ex_dict['media_filename'] not in current_media:
            current_media.insert(0, ex_dict['media_filename'])

    photo_count = sum(1 for f in current_media if any(str(f).lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']))
    video_count = sum(1 for f in current_media if any(str(f).lower().endswith(ext) for ext in ['.mp4', '.mov', '.webm', '.avi', '.mkv']))

    for p_file in photos:
        if p_file and p_file.filename != '' and photo_count < 5:
            fname = secure_filename(p_file.filename)
            saved_name = f"photo_{sub_id}_{int(time.time())}_{fname}"
            p_file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_name))
            current_media.append(saved_name)
            photo_count += 1

    for v_file in videos:
        if v_file and v_file.filename != '' and video_count < 2:
            fname = secure_filename(v_file.filename)
            saved_name = f"video_{sub_id}_{int(time.time())}_{fname}"
            v_file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_name))
            current_media.append(saved_name)
            video_count += 1

    media_json_str = json.dumps(current_media) if current_media else None
    first_file = current_media[0] if current_media else ''

    conn.execute('''
        UPDATE submissions SET media_files_json = ?, media_filename = COALESCE(NULLIF(media_filename, ''), ?) WHERE id = ?
    ''', (media_json_str, first_file, sub_id))

    conn.commit()

    # Notarização de Alteração no Blockchain (Gera NOVO bloco e NOVO QR Code exclusivo!)
    try:
        b_res = blockchain_engine.notarize_record(
            conn,
            sub_id,
            curator_user=current_user,
            action_type='ALTERACAO_DADOS',
            changes_summary=f"Alteração de atributos na Curadoria por {current_user.nome_completo or current_user.username}",
            ip_origem=client_ip,
            host_url=request.host_url,
            upload_folder=app.config['UPLOAD_FOLDER']
        )
        blk_msg = f" Notarizado novo Bloco #{b_res['block_index']} e novo QR Code gerado no Blockchain!" if b_res else ""
    except Exception as e:
        print("[!] Erro ao notarizar alteração:", e)
        blk_msg = ""

    conn.close()
    
    try:
        import threading
        threading.Thread(target=sync_with_cloud, daemon=True).start()
    except Exception:
        pass
        
    flash(f'Todas as informações do Dicionário de Dados foram atualizadas!{blk_msg}', 'success')
    return redirect(url_for('curadoria'))

@app.route('/curadoria/action/<int:sub_id>', methods=['POST'])
@login_required
def curadoria_action(sub_id):
    action = request.form.get('action')
    feedback = request.form.get('feedback', '')
    
    conn = get_db_connection()
    submission = conn.execute('''
        SELECT s.*, u.role_level as u_role_level, u.municipio as u_municipio, u.uf as u_uf
        FROM submissions s 
        LEFT JOIN users u ON s.user_id = u.id 
        WHERE s.id = ?
    ''', (sub_id,)).fetchone()
    
    if not submission:
        conn.close()
        return jsonify({'error': 'Submission not found'}), 404

    perms = check_curadoria_permissions(submission, current_user)
    if not perms['can_approve']:
        conn.close()
        return jsonify({'error': f'Unauthorized: Você não possui autoridade para homologar esta ocorrência. {perms["is_waiting_reason"]}'}), 403
        
    sub_dict = dict(submission)
    sub_esfera = perms['sub_esfera']

    if action == 'approve':
        conn.execute('''
            UPDATE submissions 
            SET status = 'aprovado', feedback = ?, origem = 'Curadoria',
                responsavel_nome = COALESCE(responsavel_nome, ?),
                responsavel_cpf = COALESCE(responsavel_cpf, ?),
                responsavel_matricula = COALESCE(responsavel_matricula, ?),
                responsavel_nivel = COALESCE(responsavel_nivel, ?)
            WHERE id = ?
        ''', (
            feedback,
            current_user.nome_completo or current_user.username,
            current_user.cpf or 'N/A',
            current_user.matricula or 'N/A',
            current_user.role_level or current_user.role,
            sub_id
        ))
        
        if sub_dict.get('submission_type') == 'layer':
            conn.execute('INSERT INTO layers (name, filename, category, is_active) VALUES (?, ?, ?, 1)',
                         (submission['title'], submission['filename'], 'Contribuição de Usuários'))
                         
        # Notarização Criptográfica de Aprovação no Blockchain (Gera novo bloco e novo QR Code)
        try:
            client_ip = get_client_ip()
            action_type = f"APROVACAO_CURADORIA_{sub_esfera.upper()}"
            changes_summary = f"Homologação técnica oficial na Curadoria pela {perms['current_tier_label']}. Parecer: {feedback or 'Aprovado sem ressalvas'}"
            b_res = blockchain_engine.notarize_record(
                conn,
                sub_id,
                curator_user=current_user,
                action_type=action_type,
                changes_summary=changes_summary,
                ip_origem=client_ip,
                host_url=request.host_url,
                upload_folder=app.config['UPLOAD_FOLDER']
            )
            if b_res:
                flash(f'Submissão #{sub_id} aprovada e NOTARIZADA no Blockchain Ledger (Bloco #{b_res["block_index"]}) com novo QR Code gerado!', 'success')
            else:
                flash('Submissão aprovada na Curadoria!', 'success')
        except Exception as b_err:
            print("Aviso ao notarizar no blockchain:", b_err)
            flash('Submissão aprovada na Curadoria!', 'success')
        
    elif action == 'reject':
        conn.execute('UPDATE submissions SET status = ?, feedback = ? WHERE id = ?', ('rejeitado', feedback, sub_id))
        conn.commit()
        try:
            client_ip = get_client_ip()
            blockchain_engine.notarize_record(
                conn,
                sub_id,
                curator_user=current_user,
                action_type='REJEICAO_CURADORIA',
                changes_summary=f"Ocorrência indeferida pela Curadoria ({perms['current_tier_label']}). Motivo: {feedback or 'Inconsistência técnica'}",
                ip_origem=client_ip,
                host_url=request.host_url,
                upload_folder=app.config['UPLOAD_FOLDER']
            )
        except Exception as b_err:
            print("Aviso ao notarizar rejeição:", b_err)
        flash('Submissão rejeitada na Curadoria.', 'warning')
        
    conn.close()
    
    try:
        import threading
        threading.Thread(target=sync_with_cloud, daemon=True).start()
    except Exception:
        pass
        
    return redirect(url_for('curadoria'))

@app.route('/curadoria/approve_all', methods=['POST'])
@login_required
def curadoria_approve_all():
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT s.*, u.role_level as u_role_level, u.municipio as u_municipio, u.uf as u_uf 
        FROM submissions s 
        LEFT JOIN users u ON s.user_id = u.id 
        WHERE s.status = 'pendente'
    ''').fetchall()

    approved_count = 0
    client_ip = get_client_ip()

    for r in rows:
        perms = check_curadoria_permissions(r, current_user)
        if perms['can_approve']:
            sub_id = r['id']
            sub_esfera = perms['sub_esfera']
            conn.execute('''
                UPDATE submissions 
                SET status = 'aprovado', origem = 'Curadoria',
                    responsavel_nome = COALESCE(responsavel_nome, ?),
                    responsavel_cpf = COALESCE(responsavel_cpf, ?),
                    responsavel_matricula = COALESCE(responsavel_matricula, ?),
                    responsavel_nivel = COALESCE(responsavel_nivel, ?)
                WHERE id = ?
            ''', (
                current_user.nome_completo or current_user.username,
                current_user.cpf or 'N/A',
                current_user.matricula or 'N/A',
                current_user.role_level or current_user.role,
                sub_id
            ))
            if r['submission_type'] == 'layer':
                conn.execute('INSERT INTO layers (name, filename, category, is_active) VALUES (?, ?, ?, 1)',
                             (r['title'], r['filename'], 'Contribuição de Usuários'))
            try:
                blockchain_engine.notarize_record(
                    conn,
                    sub_id,
                    curator_user=current_user,
                    action_type=f"APROVACAO_CURADORIA_{sub_esfera.upper()}",
                    changes_summary=f"Aprovação em lote por Gestor ({perms['current_tier_label']})",
                    ip_origem=client_ip,
                    host_url=request.host_url,
                    upload_folder=app.config['UPLOAD_FOLDER']
                )
            except Exception as b_err:
                print("Aviso ao notarizar aprovação em lote:", b_err)
            approved_count += 1

    conn.commit()
    conn.close()

    try:
        import threading
        threading.Thread(target=sync_with_cloud, daemon=True).start()
    except Exception:
        pass

    if approved_count > 0:
        flash(f'{approved_count} submissões sob sua jurisdição foram APROVADAS e NOTARIZADAS no Blockchain!', 'success')
    else:
        flash('Nenhuma ocorrência pendente sob sua jurisdição para aprovação.', 'info')

    return redirect(url_for('curadoria'))

@app.route('/curadoria/delete_all', methods=['POST'])
@login_required
def curadoria_delete_all():
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT s.*, u.role_level as u_role_level, u.municipio as u_municipio, u.uf as u_uf 
        FROM submissions s 
        LEFT JOIN users u ON s.user_id = u.id 
        WHERE s.submission_type = 'point'
    ''').fetchall()

    deleted_count = 0
    for r in rows:
        perms = check_curadoria_permissions(r, current_user)
        if perms['can_delete']:
            sub_id = r['id']
            conn.execute("DELETE FROM blockchain_ledger WHERE submission_id = ?", (sub_id,))
            conn.execute("DELETE FROM submissions WHERE id = ?", (sub_id,))
            deleted_count += 1

    conn.commit()
    conn.close()

    try:
        import threading
        threading.Thread(target=sync_with_cloud, daemon=True).start()
    except Exception:
        pass

    flash(f'{deleted_count} ocorrências sob sua jurisdição foram removidas.', 'warning')
    return redirect(url_for('curadoria'))

@app.route('/delete_occurrence/<int:sub_id>', methods=['POST'])
@login_required
def delete_occurrence(sub_id):
    conn = get_db_connection()
    sub = conn.execute('''
        SELECT s.*, u.role_level as u_role_level, u.municipio as u_municipio, u.uf as u_uf 
        FROM submissions s 
        LEFT JOIN users u ON s.user_id = u.id 
        WHERE s.id = ?
    ''', (sub_id,)).fetchone()
    
    if not sub:
        conn.close()
        flash('Ocorrência não encontrada.', 'danger')
        return redirect(url_for('index'))

    perms = check_curadoria_permissions(sub, current_user)
    if not perms['can_delete']:
        conn.close()
        flash(f'Acesso Negado: Você não possui autorização para excluir este registro. {perms["is_waiting_reason"]}', 'danger')
        return redirect(request.referrer or url_for('index'))

    conn.execute('DELETE FROM blockchain_ledger WHERE submission_id = ?', (sub_id,))
    conn.execute('DELETE FROM submissions WHERE id = ?', (sub_id,))
    conn.commit()
    conn.close()

    try:
        import threading
        threading.Thread(target=sync_with_cloud, daemon=True).start()
    except Exception:
        pass

    flash(f'Ocorrência #{sub_id} removida do sistema com sucesso.', 'success')
    return redirect(request.referrer or url_for('index'))

# --- Download / Exportação ---

@app.route('/download_export', methods=['GET', 'POST'])
def download_export():
    layer_type = request.values.get('layer_type', 'occurrences')
    municipio_filter = request.values.get('municipio', 'Todos')
    export_format = request.values.get('format', 'shapefile')
    
    if layer_type == 'occurrences':
        conn = get_db_connection()
        query = """
            SELECT * FROM submissions 
            WHERE LOWER(TRIM(status)) = 'aprovado' 
              AND (
                submission_type = 'point' 
                OR (lat IS NOT NULL AND lng IS NOT NULL AND CAST(lat AS text) NOT IN ('', '0', '0.0', 'None', 'null'))
              )
        """
        params = []
        if municipio_filter and municipio_filter != 'Todos':
            query += " AND municipio = ?"
            params.append(municipio_filter)
            
        points = conn.execute(query, params).fetchall()
        conn.close()
        
        if not points:
            flash('Nenhuma ocorrência encontrada para os filtros selecionados.', 'warning')
            return redirect(url_for('index'))
            
        data_list = []
        for p in points:
            p_dict = dict(p)
            data_list.append({
                'id_evento': p['id'],
                'title': p['title'],
                'descricao': p['description'],
                'origem': p_dict.get('origem') or 'Curadoria',
                'resp_nome': p_dict.get('responsavel_nome'),
                'resp_cpf': p_dict.get('responsavel_cpf'),
                'resp_matr': p_dict.get('responsavel_matricula'),
                'data_evt': p_dict.get('data_evento'),
                'tipologia': p_dict.get('tipologia'),
                'id_pais': p_dict.get('id_pais') or 'Brasil',
                'uf': p_dict.get('uf') or 'RJ',
                'municipio': p_dict.get('municipio') or 'Angra dos Reis',
                'bairro': p_dict.get('bairro'),
                'lat_wgs84': float(p['lat']) if p['lat'] else 0.0,
                'lng_wgs84': float(p['lng']) if p['lng'] else 0.0,
                'zona': p_dict.get('zona'),
                'area_u_hab': p_dict.get('area_u_habitacoes'),
                'perc_atu': p_dict.get('perc_area_atu'),
                'area_ar': p_dict.get('area_ar'),
                'area_rm': p_dict.get('area_rm'),
                'perc_atr': p_dict.get('perc_area_atr'),
                'cli_vento': p_dict.get('clima_vento'),
                'cli_precip': p_dict.get('clima_precipitacao_evento'),
                'cli_press': p_dict.get('clima_pressao'),
                'cli_temp': p_dict.get('clima_temperatura'),
                'cli_evap': p_dict.get('clima_evapotranspiracao'),
                'cli_pr_m': p_dict.get('clima_precipitacao_mensal'),
                'cli_pr_5d': p_dict.get('clima_precipitacao_5d'),
                'cli_pr_10d': p_dict.get('clima_precipitacao_10d'),
                'ped_solo': p_dict.get('ped_classe_solo'),
                'ped_prof': p_dict.get('ped_profundidade'),
                'ped_textur': p_dict.get('ped_textura'),
                'ped_poros': p_dict.get('ped_porosidade'),
                'ped_ucc': p_dict.get('ped_ucc'),
                'ped_cad': p_dict.get('ped_cad'),
                'ped_k': p_dict.get('ped_k'),
                'ped_umid': p_dict.get('ped_umidade_evento'),
                'geo_orient': p_dict.get('geo_orientacao'),
                'geo_curv': p_dict.get('geo_curvatura'),
                'geo_forma': p_dict.get('geo_forma_terreno'),
                'geo_decliv': p_dict.get('geo_declividade'),
                'geo_altit': p_dict.get('geo_altitude'),
                'geol_rocha': p_dict.get('geol_tipo_rocha'),
                'geol_comp': p_dict.get('geol_composicao'),
                'geol_estru': p_dict.get('geol_estrutura'),
                'geol_idade': p_dict.get('geol_idade'),
                'geol_tect': p_dict.get('geol_tectonismo'),
                'ant_escav': p_dict.get('antrop_escavacao'),
                'ant_sobrec': p_dict.get('antrop_sobrecarga'),
                'ant_uso': p_dict.get('antrop_tipo_uso'),
                'ant_miner': p_dict.get('antrop_mineracao'),
                'eco_custo': p_dict.get('econ_custo_total'),
                'eco_infra': p_dict.get('econ_infraestrutura'),
                'eco_pat_pr': p_dict.get('econ_patrimonio_privado'),
                'eco_pat_pu': p_dict.get('econ_patrimonio_publico'),
                'eco_agri_a': p_dict.get('econ_agri_area_atingida'),
                'eco_agri_p': p_dict.get('econ_agri_perc_area'),
                'eco_agri_c': p_dict.get('econ_agri_cultura'),
                'eco_agri_v': p_dict.get('econ_agri_valor'),
                'eco_int_d': p_dict.get('econ_interrupcao_duracao'),
                'eco_int_s': p_dict.get('econ_interrupcao_setores'),
                'eco_seguro': p_dict.get('econ_seguro'),
                'eco_c_rec': p_dict.get('econ_custo_recuperacao'),
                'soc_serv': p_dict.get('soc_servicos_afetados'),
                'soc_t_rec': p_dict.get('soc_tempo_recuperacao'),
                'soc_fam': p_dict.get('soc_n_familias'),
                'soc_desal': p_dict.get('soc_n_desalojados'),
                'soc_desab': p_dict.get('soc_n_desabrigados'),
                'soc_desap': p_dict.get('soc_n_desaparecidos'),
                'n_mortos': p_dict.get('n_mortos') or 0,
                'n_feridos': p_dict.get('n_feridos') or 0,
                'soc_v_dano': p_dict.get('soc_valor_total_danos'),
                'amb_tipo': p_dict.get('amb_tipo_impacto'),
                'amb_area': p_dict.get('amb_area_atingida'),
                'amb_rec': p_dict.get('amb_recursos_afetados'),
                'amb_biodiv': p_dict.get('amb_dano_biodiversidade'),
                'amb_c_mit': p_dict.get('amb_custo_mitigacao'),
                'amb_t_rec': p_dict.get('amb_tempo_recuperacao'),
                'amb_status': p_dict.get('amb_status_recuperacao'),
                'geometry': Point(float(p['lng']), float(p['lat'])) if p['lng'] and p['lat'] else None
            })
            
        gdf = gpd.GeoDataFrame(data_list, crs="EPSG:4326")
        filename_base = f"ocorrencias_{secure_filename(municipio_filter.lower())}"
    else:
        conn = get_db_connection()
        layer = conn.execute("SELECT * FROM layers WHERE id = ?", (layer_type,)).fetchone()
        conn.close()
        if not layer:
            flash("Camada não encontrada", "danger")
            return redirect(url_for('index'))
            
        filepath = os.path.join(app.config['LAYERS_FOLDER'], layer['filename'])
        if not os.path.exists(filepath):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], layer['filename'])
            
        if not os.path.exists(filepath):
            flash("Arquivo da camada não encontrado no servidor.", "danger")
            return redirect(url_for('index'))

        gdf = gpd.read_file(filepath)
        filename_base = secure_filename(layer['name'].lower())

    with tempfile.TemporaryDirectory() as tmpdir:
        if export_format == 'shapefile':
            shp_dir = os.path.join(tmpdir, filename_base)
            os.makedirs(shp_dir, exist_ok=True)
            shp_file = os.path.join(shp_dir, f"{filename_base}.shp")
            gdf.to_file(shp_file, driver='ESRI Shapefile')
            
            zip_path = shutil.make_archive(os.path.join(tmpdir, filename_base), 'zip', shp_dir)
            return send_from_directory(tmpdir, f"{filename_base}.zip", as_attachment=True)
            
        elif export_format == 'geopackage':
            gpkg_filepath = os.path.join(tmpdir, f"{filename_base}.gpkg")
            gdf.to_file(gpkg_filepath, driver='GPKG')
            return send_from_directory(tmpdir, f"{filename_base}.gpkg", as_attachment=True)
            
        else: # geojson
            geojson_filepath = os.path.join(tmpdir, f"{filename_base}.geojson")
            gdf.to_file(geojson_filepath, driver='GeoJSON')
# --- Sincronização Bidirecional Nuvem (Render / Web) <-> Desktop Local ---
SYNC_SECRET = os.environ.get('MOVMASSA_SYNC_SECRET', 'movmassa_angra_sync_key_2026')
CLOUD_SYNC_URL = os.environ.get('CLOUD_SYNC_URL', 'https://movmassa.onrender.com')

def get_full_database_dump():
    """Retorna todas as submissões, usuários e blocos do banco atual para sincronização."""
    conn = get_db_connection()
    try:
        users = [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]
        subs = [dict(r) for r in conn.execute("SELECT * FROM submissions").fetchall()]
        ledger = [dict(r) for r in conn.execute("SELECT * FROM blockchain_ledger").fetchall()]
        for s in subs:
            for k, v in list(s.items()):
                if hasattr(v, 'isoformat'):
                    s[k] = v.isoformat()
        for u in users:
            for k, v in list(u.items()):
                if hasattr(v, 'isoformat'):
                    u[k] = v.isoformat()
        for b in ledger:
            for k, v in list(b.items()):
                if hasattr(v, 'isoformat'):
                    b[k] = v.isoformat()
        return {'users': users, 'submissions': subs, 'ledger': ledger}
    finally:
        conn.close()

def apply_database_sync(incoming_data):
    """Aplica registros recebidos na base local/remota, fazendo upsert seguro."""
    conn = get_db_connection()
    is_pg = getattr(conn, 'is_postgres', False)
    try:
        # 1. Sincronizar usuários
        for u in incoming_data.get('users', []):
            username = u.get('username')
            if not username:
                continue
            existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,)).fetchone()
            if existing:
                conn.execute("""
                    UPDATE users SET 
                        password_hash = COALESCE(?, password_hash),
                        role = COALESCE(?, role),
                        role_level = COALESCE(?, role_level),
                        email = COALESCE(?, email),
                        nome_completo = COALESCE(?, nome_completo),
                        telefone = COALESCE(?, telefone),
                        matricula = COALESCE(?, matricula),
                        cpf = COALESCE(?, cpf),
                        funcao = COALESCE(?, funcao),
                        municipio = COALESCE(?, municipio),
                        uf = COALESCE(?, uf)
                    WHERE id = ?
                """, (
                    u.get('password_hash'), u.get('role'), u.get('role_level'),
                    u.get('email'), u.get('nome_completo'), u.get('telefone'),
                    u.get('matricula'), u.get('cpf'), u.get('funcao'),
                    u.get('municipio'), u.get('uf'), existing['id']
                ))
            else:
                conn.execute("""
                    INSERT INTO users (username, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    username, u.get('password_hash') or '', u.get('role', 'user'), u.get('role_level', 'user'),
                    u.get('email'), u.get('nome_completo'), u.get('telefone'), u.get('matricula'), u.get('cpf'),
                    u.get('funcao', 'agente'), u.get('municipio', 'Angra dos Reis'), u.get('uf', 'RJ')
                ))
        conn.commit()

        # 2. Sincronizar submissões
        if is_pg:
            cols_cur = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'submissions'")
            valid_cols = [r[0] for r in cols_cur.fetchall()]
        else:
            cols_cur = conn.execute("PRAGMA table_info(submissions)")
            valid_cols = [r[1] for r in cols_cur.fetchall()]

        for s in incoming_data.get('submissions', []):
            sub_id = s.get('id')
            if not sub_id:
                continue
            existing = conn.execute("SELECT id FROM submissions WHERE id = ?", (sub_id,)).fetchone()
            
            data_cols = [c for c in valid_cols if c in s and c != 'id']
            if existing:
                set_clause = ", ".join([f"{c} = ?" for c in data_cols])
                values = [s[c] for c in data_cols] + [sub_id]
                conn.execute(f"UPDATE submissions SET {set_clause} WHERE id = ?", values)
            else:
                all_cols = ['id'] + data_cols
                placeholders = ", ".join(["?"] * len(all_cols))
                values = [sub_id] + [s[c] for c in data_cols]
                conn.execute(f"INSERT INTO submissions ({', '.join(all_cols)}) VALUES ({placeholders})", values)
        conn.commit()

        if is_pg:
            try:
                conn.execute("SELECT setval(pg_get_serial_sequence('submissions', 'id'), COALESCE((SELECT MAX(id) FROM submissions), 1));")
                conn.commit()
            except Exception:
                pass

        # 3. Sincronizar blockchain ledger
        for b in incoming_data.get('ledger', []):
            sub_id = b.get('submission_id')
            blk_idx = b.get('block_index')
            if not sub_id or not blk_idx:
                continue
            existing = conn.execute("SELECT id FROM blockchain_ledger WHERE submission_id = ? AND block_index = ?", (sub_id, blk_idx)).fetchone()
            if not existing:
                conn.execute("""
                    INSERT INTO blockchain_ledger (
                        submission_id, block_index, timestamp, data_hash, previous_hash, block_hash,
                        curator_nome, curator_cpf, curator_matricula, curator_nivel,
                        ip_origem, action_type, changes_summary, qrcode_filename
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sub_id, blk_idx, b.get('timestamp'), b.get('data_hash'), b.get('previous_hash'), b.get('block_hash'),
                    b.get('curator_nome'), b.get('curator_cpf'), b.get('curator_matricula'), b.get('curator_nivel'),
                    b.get('ip_origem'), b.get('action_type'), b.get('changes_summary'), b.get('qrcode_filename')
                ))
            
            # Garantir existência do arquivo QR Code local
            qr_fn = b.get('qrcode_filename')
            if qr_fn:
                qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_fn)
                if not os.path.exists(qr_path):
                    try:
                        target_host = 'https://movmassa.onrender.com'
                        tracking_url = f"{target_host.rstrip('/')}/blockchain/track/{sub_id}"
                        blockchain_engine.generate_block_qrcode(tracking_url, qr_fn, app.config['UPLOAD_FOLDER'])
                    except Exception as e:
                        print("Aviso ao regenerar QR code:", e)
        conn.commit()
    finally:
        conn.close()

def sync_with_cloud():
    """
    Executa sincronização bidirecional entre a aplicação Desktop local e a Nuvem (Render).
    """
    import urllib.request
    import json
    
    if DATABASE_URL and 'render' in DATABASE_URL:
        return True, "Ambiente Nuvem ativo."
        
    sync_url = f"{CLOUD_SYNC_URL.rstrip('/')}/api/sync/exchange"
    try:
        local_dump = get_full_database_dump()
        payload = {
            'sync_token': SYNC_SECRET,
            'users': local_dump['users'],
            'submissions': local_dump['submissions'],
            'ledger': local_dump['ledger']
        }
        json_bytes = json.dumps(payload, default=str).encode('utf-8')
        req = urllib.request.Request(
            sync_url,
            data=json_bytes,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'MOVMASSA-Desktop-Sync/1.0'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                cloud_data = json.loads(response.read().decode('utf-8'))
                if cloud_data.get('status') == 'ok':
                    apply_database_sync(cloud_data)
                    return True, f"Sincronização com a Nuvem concluída com sucesso! ({len(cloud_data.get('submissions', []))} ocorrências alinhadas)"
        return False, "Resposta inválida do servidor na nuvem."
    except Exception as e:
        print("[!] Aviso na sincronização com a nuvem:", e)
        return False, f"Falha de conexão com a nuvem: {e}"

@app.route('/api/sync/exchange', methods=['POST'])
def api_sync_exchange():
    data = request.get_json(force=True, silent=True) or {}
    token = data.get('sync_token')
    if token != SYNC_SECRET and not (current_user.is_authenticated and getattr(current_user, 'role_level', '') == 'admin_geral'):
        return jsonify({'error': 'Unauthorized sync token'}), 403
        
    try:
        apply_database_sync(data)
        current_state = get_full_database_dump()
        return jsonify({
            'status': 'ok',
            'users': current_state['users'],
            'submissions': current_state['submissions'],
            'ledger': current_state['ledger']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sync_now', methods=['GET', 'POST'])
def sync_now():
    success, msg = sync_with_cloud()
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'warning')
    return redirect(request.referrer or url_for('index'))

# --- Admin & Gestão de Agentes / Funcionários ---

@app.route('/admin')
@login_required
def admin():
    if current_user.role not in ['admin', 'org']:
        flash('Acesso negado. Apenas gestores da Defesa Civil podem acessar a gestão de usuários.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if current_user.role_level == 'admin_geral':
        users = conn.execute('SELECT * FROM users ORDER BY id ASC').fetchall()
    else:
        sphere = current_user.role_level.replace('admin_', '')
        agente_level = f'agente_{sphere}'
        users = conn.execute(
            'SELECT * FROM users WHERE role_level = ? OR role_level = ? OR id = ? ORDER BY id ASC', 
            (current_user.role_level, agente_level, current_user.id)
        ).fetchall()
    conn.close()
    
    return render_template(
        'admin.html',
        users=users,
        rj_municipalities=RJ_MUNICIPALITIES,
        brazil_ufs=BRAZIL_UFS
    )

@app.route('/admin/create_user', methods=['POST'])
@login_required
def admin_create_user():
    if current_user.role not in ['admin', 'org'] and 'admin' not in getattr(current_user, 'role_level', ''):
        flash('Acesso negado. Apenas administradores e gestores de Defesa Civil podem cadastrar funcionários.', 'danger')
        return redirect(url_for('index'))
        
    email = request.form.get('email', '').strip().lower()
    username_input = request.form.get('username', '').strip()
    
    # O login de acesso (username) passa a ser automaticamente o e-mail
    username = email if email else username_input.lower()
    
    password = request.form.get('password', '').strip()
    nome_completo = request.form.get('nome_completo', '').strip()
    telefone = request.form.get('telefone', '').strip()
    matricula = request.form.get('matricula', '').strip()
    cpf = request.form.get('cpf', '').strip()
    funcao_requested = request.form.get('funcao', 'agente').strip()

    # Jurisdição geográfica
    municipio_input = request.form.get('municipio', '').strip()
    uf_input = request.form.get('uf', '').strip().upper()

    if current_user.role_level == 'admin_geral':
        selected_level = request.form.get('role_level', 'admin_municipal')
        if selected_level == 'admin_geral':
            role = 'admin'
            role_level = 'admin_geral'
            funcao = 'gestor_agente'
            municipio = municipio_input or 'Angra dos Reis'
            uf = uf_input or 'RJ'
        elif selected_level == 'org':
            role = 'org'
            role_level = 'org'
            funcao = 'gestor' if funcao_requested == 'gestor' else 'agente'
            municipio = municipio_input or 'Angra dos Reis'
            uf = uf_input or 'RJ'
        elif 'municipal' in selected_level:
            is_g = (funcao_requested == 'gestor')
            role = 'admin' if is_g else 'user'
            role_level = 'admin_municipal' if is_g else 'agente_municipal'
            funcao = 'gestor' if is_g else 'agente'
            municipio = municipio_input or 'Angra dos Reis'
            uf = uf_input or 'RJ'
        elif 'estadual' in selected_level:
            is_g = (funcao_requested == 'gestor')
            role = 'admin' if is_g else 'user'
            role_level = 'admin_estadual' if is_g else 'agente_estadual'
            funcao = 'gestor' if is_g else 'agente'
            municipio = municipio_input or 'Capital Estadual'
            uf = uf_input or 'RJ'
        elif 'nacional' in selected_level:
            is_g = (funcao_requested == 'gestor')
            role = 'admin' if is_g else 'user'
            role_level = 'admin_nacional' if is_g else 'agente_nacional'
            funcao = 'gestor' if is_g else 'agente'
            municipio = 'Brasília'
            uf = 'DF'
        else:
            role = 'user'
            role_level = 'user'
            funcao = 'agente'
            municipio = municipio_input or 'Angra dos Reis'
            uf = uf_input or 'RJ'
    else:
        # Funcionários cadastrados por gestores recebem a jurisdição do próprio gestor
        sphere = current_user.role_level.replace('admin_', '')
        role_level = f'agente_{sphere}'
        role = 'user'
        funcao = 'agente'
        municipio = getattr(current_user, 'municipio', 'Angra dos Reis') or 'Angra dos Reis'
        uf = getattr(current_user, 'uf', 'RJ') or 'RJ'

    if not username or not password or not nome_completo or not cpf or not matricula:
        flash('E-mail institucional (Login), Senha inicial, Nome completo, CPF e Matrícula são obrigatórios.', 'warning')
        return redirect(url_for('admin'))

    conn = None
    try:
        conn = get_db_connection()
        
        # 1. Bloqueio de CPF duplicado em qualquer esfera da Defesa Civil
        clean_cpf = cpf.replace('.', '').replace('-', '').replace(' ', '')
        if clean_cpf:
            users_all = conn.execute("SELECT username, nome_completo, role_level, cpf FROM users WHERE cpf IS NOT NULL AND cpf != ''").fetchall()
            for u_item in users_all:
                u_dict_item = dict(u_item)
                item_cpf = str(u_dict_item.get('cpf', '')).replace('.', '').replace('-', '').replace(' ', '')
                if item_cpf and item_cpf == clean_cpf:
                    sphere_name = {
                        'admin_geral': 'Administração Geral',
                        'admin_nacional': 'Defesa Civil Nacional',
                        'admin_estadual': 'Defesa Civil Estadual',
                        'admin_municipal': 'Defesa Civil Municipal',
                        'agente_nacional': 'Defesa Civil Nacional',
                        'agente_estadual': 'Defesa Civil Estadual',
                        'agente_municipal': 'Defesa Civil Municipal',
                        'org': 'Organização Parceira'
                    }.get(u_dict_item.get('role_level'), u_dict_item.get('role_level'))
                    conn.close()
                    flash(f'Bloqueio de Duplicidade: A pessoa com CPF "{cpf}" ({u_dict_item.get("nome_completo") or u_dict_item.get("username")}) já está cadastrada na {sphere_name} (Login: {u_dict_item.get("username")}). Jamais podem existir a mesma pessoa cadastrada em diferentes esferas da Defesa Civil.', 'danger')
                    return redirect(url_for('admin'))

        # 2. Bloqueio por E-mail / Username único
        existing_user = conn.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(?) OR (email IS NOT NULL AND email != '' AND LOWER(email) = LOWER(?))", 
            (username, username)
        ).fetchone()
        
        if existing_user:
            conn.close()
            flash(f'O e-mail / login "{username}" já está cadastrado no sistema para outro agente. Escolha outro e-mail.', 'danger')
            return redirect(url_for('admin'))

        pwd_hash = generate_password_hash(password)
        try:
            res = conn.execute('''
                INSERT INTO users (username, password, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, pwd_hash, pwd_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf))
        except Exception:
            conn.rollback()
            res = conn.execute('''
                INSERT INTO users (username, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, pwd_hash, role, role_level, email, nome_completo, telefone, matricula, cpf, funcao, municipio, uf))
        conn.commit()
        new_id = getattr(res, 'lastrowid', None)
        conn.close()

        try:
            import threading
            threading.Thread(target=sync_with_cloud, daemon=True).start()
        except Exception:
            pass

        id_str = f" (ID #{new_id})" if new_id else ""
        flash(f'Novo agente "{nome_completo}"{id_str} cadastrado com sucesso para {municipio}/{uf} com login "{username}"!', 'success')
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
        print("Erro ao cadastrar novo agente no banco:", e)
        flash(f'Erro ao cadastrar novo agente: {e}', 'danger')

    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role not in ['admin', 'org']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('admin'))

    if user_id == current_user.id:
        flash('Você não pode excluir sua própria conta enquanto estiver logado.', 'warning')
        return redirect(url_for('admin'))

    conn = get_db_connection()
    target = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not target:
        conn.close()
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin'))

    t_dict = dict(target)
    is_admin_geral = (current_user.role_level == 'admin_geral')
    is_same_level = (current_user.role_level == t_dict.get('role_level'))

    if not (is_admin_geral or is_same_level):
        conn.close()
        flash('Acesso negado: Você só pode excluir usuários do seu próprio nível ou esfera.', 'danger')
        return redirect(url_for('admin'))

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    flash(f'Usuário #{user_id} ({t_dict.get("username")}) removido com sucesso.', 'success')
    return redirect(url_for('admin'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pwd = request.form.get('current_password', '').strip()
        new_pwd = request.form.get('new_password', '').strip()
        confirm_pwd = request.form.get('confirm_password', '').strip()

        if new_pwd != confirm_pwd:
            flash('A nova senha e a confirmação não coincidem.', 'danger')
            return redirect(url_for('change_password'))

        conn = get_db_connection()
        user_row = conn.execute('SELECT password_hash FROM users WHERE id = ?', (current_user.id,)).fetchone()
        if not user_row:
            conn.close()
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('index'))

        pwd_hash = user_row['password_hash']
        is_valid = False
        try:
            is_valid = check_password_hash(pwd_hash, current_pwd)
        except Exception:
            is_valid = (pwd_hash == current_pwd)

        if not is_valid:
            conn.close()
            flash('Sua senha atual está incorreta.', 'danger')
            return redirect(url_for('change_password'))

        new_hash = generate_password_hash(new_pwd)
        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, current_user.id))
        conn.commit()
        conn.close()

        flash('Sua senha foi alterada com sucesso!', 'success')
        return redirect(url_for('profile'))

    return render_template('change_password.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
