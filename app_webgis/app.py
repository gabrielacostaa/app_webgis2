from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import shutil
import tempfile
import zipfile
import geopandas as gpd
from shapely.geometry import Point
from pdf_generator import generate_occurrence_pdf

app = Flask(__name__)
app.config['SECRET_KEY'] = 'geoportal_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['LAYERS_FOLDER'] = '../'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
            self.conn = sqlite3.connect('database.db')
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

class User(UserMixin):
    def __init__(self, id, username, role, role_level='user', email='', nome_completo='', telefone='', matricula='', cpf=''):
        self.id = id
        self.username = username
        self.role = role
        self.role_level = role_level
        self.email = email
        self.nome_completo = nome_completo
        self.telefone = telefone
        self.matricula = matricula
        self.cpf = cpf

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
            cpf=u.get('cpf', '')
        )
    return None

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
        print("Aviso na criacao da tabela users:", e)

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
                responsavel_nivel TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
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
        print("Aviso na criacao da tabela layers:", e)

    # Seed default users if empty
    try:
        res = conn.execute('SELECT COUNT(*) FROM users').fetchone()
        count = res[0] if res else 0
        if count == 0:
            default_users = [
                ('admin', generate_password_hash('Admin@123'), 'admin', 'admin_geral', 'admin.geral@geoportal.gov.br', 'Administrador Geral MOVMASSA', '(24) 99999-0000', 'ADM-GERAL-001', '000.000.000-00'),
                ('defesa_nacional', generate_password_hash('Defesa@123'), 'admin', 'admin_nacional', 'nacional@defesacivil.gov.br', 'Agente Defesa Civil Nacional', '(61) 3333-1000', 'GOV-DCN-2026', '111.111.111-11'),
                ('defesa_estadual', generate_password_hash('Defesa@123'), 'admin', 'admin_estadual', 'estadual@defesacivil.rj.gov.br', 'Agente Defesa Civil Estadual RJ', '(21) 2222-2000', 'EST-DCE-2026', '222.222.222-22'),
                ('defesa_municipal', generate_password_hash('Defesa@123'), 'admin', 'admin_municipal', 'defesacivil@angra.rj.gov.br', 'Agente Defesa Civil Municipal Angra', '(24) 3365-3000', 'MUN-DCM-2026', '333.333.333-33'),
                ('org', generate_password_hash('Org@123'), 'org', 'org', 'contato@orgamb.org.br', 'Organização Técnica Ambientalista', '(24) 98888-4000', 'ORG-ANG-2026', '444.444.444-44'),
                ('user', generate_password_hash('User@123'), 'user', 'user', 'usuario@email.com', 'Usuário Comum de Campo', '(24) 97777-5000', 'N/A', '555.555.555-55')
            ]
            for u in default_users:
                conn.execute('''
                    INSERT INTO users (username, password_hash, role, role_level, email, nome_completo, telefone, matricula, cpf)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', u)
            conn.commit()
    except Exception as e:
        print("Aviso no seed de usuarios:", e)

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
        
        # Responsável & Origem
        ('origem', 'TEXT DEFAULT "Curadoria"'),
        ('responsavel_nome', 'TEXT'),
        ('responsavel_cpf', 'TEXT'),
        ('responsavel_matricula', 'TEXT'),
        ('responsavel_nivel', 'TEXT')
    ]
    for col, col_type in sub_cols:
        try:
            conn.execute(f'ALTER TABLE submissions ADD COLUMN {col} {col_type}')
            conn.commit()
        except Exception:
            conn.rollback()
            
    conn.close()

upgrade_db()

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    conn = get_db_connection()
    layers = conn.execute('SELECT * FROM layers WHERE is_active = 1').fetchall()
    conn.close()
    return render_template('index.html', layers=layers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            u = dict(user)
            user_obj = User(
                id=u['id'],
                username=u['username'],
                role=u['role'],
                role_level=u.get('role_level', 'user'),
                email=u.get('email', ''),
                nome_completo=u.get('nome_completo', ''),
                telefone=u.get('telefone', ''),
                matricula=u.get('matricula', ''),
                cpf=u.get('cpf', '')
            )
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Verifique suas credenciais.', 'danger')
            
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
@login_required
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(base_dir, filename)
    
    # Se não achar na raiz, tenta na pasta de uploads configurada
    upload_folder = app.config.get('UPLOAD_FOLDER', '')
    if upload_folder and os.path.exists(os.path.join(upload_folder, filename)):
        return send_from_directory(upload_folder, filename)
        
    abort(404)

@app.route('/<path:filename>')
def serve_direct_geojson(filename):
    if filename.endswith('.geojson'):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return send_from_directory(base_dir, filename)
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
@login_required
def upload_point():
    title = request.form.get('title')
    description = request.form.get('description')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    data_evento = request.form.get('data_evento')
    
    file = request.files.get('media_file')
    media_filename = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        import time
        media_filename = f"media_{int(time.time())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], media_filename))
        
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO submissions (
            user_id, title, description, submission_type, lat, lng, media_filename, filename, data_evento, municipio, uf,
            origem, responsavel_nome, responsavel_cpf, responsavel_matricula, responsavel_nivel
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        current_user.id, title, description, 'point', lat, lng, media_filename, '', data_evento, 'Angra dos Reis', 'RJ',
        'Curadoria',
        current_user.nome_completo or current_user.username,
        current_user.cpf or 'N/A',
        current_user.matricula or 'N/A',
        current_user.role_level or current_user.role
    ))
    conn.commit()
    conn.close()
    
    flash('Ocorrência reportada com sucesso! Aguardando aprovação na Curadoria.', 'success')
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
                    current_user.id, str(title), str(desc), 'point', float(lat), float(lng), '', 'aprovado',
                    'Curadoria', str(tipologia), 'Angra dos Reis', 'RJ',
                    current_user.nome_completo or current_user.username,
                    current_user.cpf or 'N/A',
                    current_user.matricula or 'N/A',
                    current_user.role_level or current_user.role
                ))
                count += 1

            conn.commit()
            conn.close()

            flash(f'Sucesso! {count} pontos de ocorrência importados do Shapefile (.zip) e adicionados diretamente à Curadoria.', 'success')

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
        reader = csv.DictReader(io.StringIO(content))
        
        if not reader.fieldnames or len(reader.fieldnames) == 1:
            first_line = content.splitlines()[0] if content.splitlines() else ''
            delimiter = ';' if ';' in first_line else ','
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

        fieldnames = [f.strip() for f in (reader.fieldnames or [])]
        field_map = {f.lower(): f for f in fieldnames}

        # Identifica colunas de Latitude e Longitude
        # Prioridade 1: X e Y (Y = Latitude, X = Longitude)
        lat_col = None
        lng_col = None

        if 'y' in field_map and 'x' in field_map:
            lat_col = field_map['y']
            lng_col = field_map['x']
        elif 'lat' in field_map and 'lng' in field_map:
            lat_col = field_map['lat']
            lng_col = field_map['lng']
        elif 'latitude' in field_map and 'longitude' in field_map:
            lat_col = field_map['latitude']
            lng_col = field_map['longitude']
        elif 'lat' in field_map and 'lon' in field_map:
            lat_col = field_map['lat']
            lng_col = field_map['lon']
        elif 'y_coord' in field_map and 'x_coord' in field_map:
            lat_col = field_map['y_coord']
            lng_col = field_map['x_coord']
        else:
            for f_low, f_orig in field_map.items():
                if f_low in ['y', 'lat', 'latitude']:
                    lat_col = f_orig
                elif f_low in ['x', 'lng', 'lon', 'longitude']:
                    lng_col = f_orig

        if not lat_col or not lng_col:
            flash('Erro: Não foi possível identificar as colunas de coordenadas no CSV. Certifique-se de que a tabela possui colunas de Coordenadas como X e Y ou Latitude e Longitude.', 'warning')
            return redirect(url_for('index'))

        conn = get_db_connection()
        inserted_count = 0

        for idx, row in enumerate(reader):
            try:
                raw_lat = str(row.get(lat_col, '')).replace(',', '.').strip()
                raw_lng = str(row.get(lng_col, '')).replace(',', '.').strip()
                if not raw_lat or not raw_lng:
                    continue

                lat = float(raw_lat)
                lng = float(raw_lng)

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
                    ) VALUES (?, ?, ?, 'point', ?, ?, '', 'aprovado', 'Curadoria', ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            flash(f'Sucesso! {inserted_count} pontos de ocorrência da tabela CSV foram importados e integrados à Curadoria.', 'success')
        else:
            flash('Nenhum ponto válido com coordenadas numéricas foi encontrado no arquivo CSV.', 'warning')

    except Exception as e:
        print(f"Erro no processamento do CSV: {e}")
        flash(f'Erro ao processar o arquivo CSV: {str(e)}', 'danger')

    return redirect(url_for('index'))

@app.route('/api/occurrences')
@login_required
def get_occurrences():
    conn = get_db_connection()
    points = conn.execute("SELECT * FROM submissions WHERE submission_type = 'point' AND status = 'aprovado'").fetchall()
    conn.close()
    
    features = []
    for p in points:
        p_dict = dict(p)
        media_url = url_for('serve_layer', filename=p['media_filename']) if p['media_filename'] else p_dict.get('midia_url')
        
        can_delete = (current_user.role_level == 'admin_geral') or (current_user.id == p['user_id'])
        
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
            "lat": p['lat'],
            "lng": p['lng'],
            "zona": p_dict.get('zona'),
            "origem": p_dict.get('origem') or 'Curadoria',
            "responsavel_nome": p_dict.get('responsavel_nome') or 'Defesa Civil',
            "responsavel_cpf": p_dict.get('responsavel_cpf') or 'N/A',
            "responsavel_matricula": p_dict.get('responsavel_matricula') or 'N/A',
            "responsavel_nivel": p_dict.get('responsavel_nivel') or 'Geral',
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
            "media_url": media_url,
            "media_filename": p['media_filename']
        }
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(p['lng']), float(p['lat'])] if p['lng'] and p['lat'] else [0, 0]
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
    conn.close()
    
    if not point:
        flash('Ocorrência não encontrada.', 'danger')
        return redirect(url_for('index'))
        
    p_dict = dict(point)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, f"relatorio_ocorrencia_{point_id}.pdf")
        generate_occurrence_pdf(p_dict, pdf_path, upload_folder=app.config['UPLOAD_FOLDER'])
        
        return send_from_directory(
            tmpdir,
            f"relatorio_ocorrencia_{point_id}.pdf",
            as_attachment=True,
            mimetype='application/pdf'
        )

# --- Curadoria ---

@app.route('/curadoria')
@login_required
def curadoria():
    if current_user.role not in ['admin', 'org']:
        flash('Acesso negado. Apenas curadores podem acessar esta seção.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    submissions = conn.execute('''
        SELECT s.*, u.username, u.role_level as u_role_level
        FROM submissions s 
        JOIN users u ON s.user_id = u.id 
        ORDER BY s.timestamp DESC
    ''').fetchall()
    conn.close()
    
    return render_template('curadoria.html', submissions=submissions)

@app.route('/curadoria/update/<int:sub_id>', methods=['POST'])
@login_required
def curadoria_update(sub_id):
    if current_user.role not in ['admin', 'org']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    f = request.form
    
    conn = get_db_connection()
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
            
            midia_tipo = ?, midia_fonte = ?, midia_url = ?
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
        
        sub_id
    ))
    conn.commit()
    conn.close()
    
    flash('Todas as informações do Dicionário de Dados foram atualizadas!', 'success')
    return redirect(url_for('curadoria'))

@app.route('/curadoria/action/<int:sub_id>', methods=['POST'])
@login_required
def curadoria_action(sub_id):
    if current_user.role not in ['admin', 'org']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    action = request.form.get('action')
    feedback = request.form.get('feedback', '')
    
    conn = get_db_connection()
    submission = conn.execute('SELECT * FROM submissions WHERE id = ?', (sub_id,)).fetchone()
    
    if not submission:
        conn.close()
        return jsonify({'error': 'Submission not found'}), 404
        
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
        
        sub_dict = dict(submission)
        if sub_dict.get('submission_type') == 'layer':
            conn.execute('INSERT INTO layers (name, filename, category, is_active) VALUES (?, ?, ?, 1)',
                         (submission['title'], submission['filename'], 'Contribuição de Usuários'))
                         
        conn.commit()
        flash('Submissão aprovada e adicionada à camada com Origem = Curadoria!', 'success')
        
    elif action == 'reject':
        conn.execute('UPDATE submissions SET status = ?, feedback = ? WHERE id = ?', ('rejeitado', feedback, sub_id))
        conn.commit()
        flash('Submissão rejeitada.', 'warning')
        
    conn.close()
    return redirect(url_for('curadoria'))

@app.route('/delete_occurrence/<int:sub_id>', methods=['POST'])
@login_required
def delete_occurrence(sub_id):
    conn = get_db_connection()
    sub = conn.execute('SELECT * FROM submissions WHERE id = ?', (sub_id,)).fetchone()
    
    if not sub:
        conn.close()
        flash('Ocorrência não encontrada.', 'danger')
        return redirect(url_for('index'))

    is_admin_geral = (current_user.role_level == 'admin_geral')
    is_owner = (current_user.id == sub['user_id'])

    if not (is_admin_geral or is_owner):
        conn.close()
        flash('Acesso Negado: Apenas o Administrador Geral ou o próprio usuário responsável pelo cadastro podem excluir esta ocorrência.', 'danger')
        return redirect(url_for('index'))

    conn.execute('DELETE FROM submissions WHERE id = ?', (sub_id,))
    conn.commit()
    conn.close()

    flash(f'Ocorrência #{sub_id} removida do sistema com sucesso.', 'success')
    return redirect(request.referrer or url_for('index'))

# --- Download / Exportação ---

@app.route('/download_export', methods=['GET', 'POST'])
@login_required
def download_export():
    layer_type = request.values.get('layer_type', 'occurrences')
    municipio_filter = request.values.get('municipio', 'Todos')
    export_format = request.values.get('format', 'shapefile')
    
    if layer_type == 'occurrences':
        conn = get_db_connection()
        query = "SELECT * FROM submissions WHERE submission_type = 'point' AND status = 'aprovado'"
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
            return send_from_directory(tmpdir, f"{filename_base}.geojson", as_attachment=True)

# --- Admin ---

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
