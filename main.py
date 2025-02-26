from flask import Flask, request, jsonify, redirect, url_for, send_from_directory, session, render_template


from flask_cors import CORS
from flask import session as flask_session
from flask_session import Session
from mysql.connector import connect, Error
import bcrypt
import re
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import wraps

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__, static_folder='.')
app.secret_key = 'your-secret-key'


app.config['SESSION_TYPE'] = 'filesystem'  # Armazena a sessão no servidor localmente
app.config['SESSION_FILE_DIR'] = './flask_session'  # Diretório para armazenar as sessões
app.config['SESSION_PERMANENT'] = True  # Mantém a sessão ativa
app.config['SESSION_USE_SIGNER'] = True  # Protege os cookies da sessão
app.config['SESSION_KEY_PREFIX'] = "session:"  # Prefixo da sessão
app.config['SESSION_COOKIE_NAME'] = "session"
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protege contra ataques XSS
app.config['SESSION_COOKIE_SAMESITE'] = "None"
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 🔥 Garante que o cookie não pode ser acessado por JS
app.config['SESSION_COOKIE_PATH'] = "/"  # 🔥 Garante que o cookie é válido para todas as rotas

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # 🔥 Expiração da sessão de 1 dia

Session(app)  # Inicializa as sessões no Flask

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000"])


@app.after_request
def apply_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:5000"  # 🔥 Permite requisições do frontend
    response.headers["Access-Control-Allow-Credentials"] = "true"  # 🔥 Permite o envio de cookies
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"  # 🔥 Permite cabeçalhos essenciais
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"  # 🔥 Métodos aceites
    return response


# Configuração da base de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD', 'duarte1234'),
    'database': 'hotel_db'
}

def get_db_connection():
    try:
        return connect(**DB_CONFIG)
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Separar cada instrução SQL numa lista
            statements = [
                '''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    senha VARCHAR(255) NOT NULL,
                    tipo ENUM('cliente', 'admin') DEFAULT 'cliente',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS quartos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero VARCHAR(10) NOT NULL UNIQUE,
                    nome VARCHAR(100) NOT NULL,  -- Novo campo para nome do quarto
                    tipo ENUM('single', 'double', 'suite') NOT NULL,
                    preco_noite DECIMAL(10,2) NOT NULL,
                    descricao TEXT,
                    imagem VARCHAR(255),  -- Novo campo para armazenar a imagem do quarto
                    status ENUM('disponivel', 'ocupado', 'manutencao') DEFAULT 'disponivel'
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS reservas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    quarto_id INT NOT NULL,
                    data_checkin DATE NOT NULL,
                    data_checkout DATE NOT NULL,
                    status ENUM('pendente', 'confirmada', 'cancelada') DEFAULT 'pendente',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                    FOREIGN KEY (quarto_id) REFERENCES quartos(id) ON DELETE CASCADE
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS pagamentos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    reserva_id INT NOT NULL,
                    valor DECIMAL(10,2) NOT NULL,
                    metodo_pagamento ENUM('cartao_credito', 'paypal', 'dinheiro') NOT NULL,
                    status ENUM('pago', 'pendente', 'falhado') DEFAULT 'pendente',
                    data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON DELETE CASCADE
                )
                '''
            ]
            # Executar cada instrução individualmente
            for statement in statements:
                cursor.execute(statement)
            conn.commit()
        except Error as e:
            print(f"Erro ao inicializar a base de dados: {e}")
        finally:
            conn.close()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Rotas para servir ficheiros estáticos
@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/index.html')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# Rota para registo de utilizador
@app.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({'error': 'Content-Type deve ser application/json'}), 415
        
    data = request.get_json()
    
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    
    if not all([nome, email, senha]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'error': 'Email inválido'}), 400
    
    if not is_strong_password(senha):
        return jsonify({
            'error': 'A senha deve ter pelo menos 8 caracteres, incluindo maiúsculas, minúsculas, números e caracteres especiais'
        }), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Erro de conexão com a base de dados'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email já cadastrado'}), 409
        
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(senha.encode('utf-8'), salt)
        
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
            (nome, email, hashed_password.decode('utf-8'))
        )
        conn.commit()
        
        return jsonify({'message': 'Utilizador registado com sucesso'}), 201
        
    except Error as e:
        return jsonify({'error': f'Erro ao registar utilizador: {str(e)}'}), 500
    finally:
        conn.close()

# Rota para login
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        print("❌ Erro: Requisição não é JSON")
        return jsonify({'error': 'Content-Type deve ser application/json'}), 415

    data = request.get_json()
    print(f"📩 Dados recebidos no login: {data}")  # Depuração

    email = data.get('email')
    senha = data.get('senha')

    if not all([email, senha]):
        print("❌ Erro: Campos vazios no login")
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    conn = get_db_connection()
    if not conn:
        print("❌ Erro: Falha na conexão com o banco de dados")
        return jsonify({'error': 'Erro de conexão com a base de dados'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email, senha FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            print("❌ Erro: Utilizador não encontrado")
            return jsonify({'error': 'Utilizador não encontrado'}), 401

        print(f"🔍 Senha inserida: {senha}")
        print(f"🔍 Senha armazenada: {user['senha']}")

        if bcrypt.checkpw(senha.encode('utf-8'), user['senha'].encode('utf-8')):
            session.clear()
            session['user_id'] = user['id']
            session['logged_in'] = True
            session.modified = True
            session.permanent = True
            print(f"✅ Sessão gravada para utilizador ID: {session.get('user_id')}")
            print(f"🔵 Sessão após login: {dict(session)}")
            return jsonify({
                'message': 'Login efetuado com sucesso',
                'redirect': '/utilizador.html'
            })
        else:
            print("❌ Erro: Senha incorreta")
            return jsonify({'error': 'Senha incorreta'}), 401
    except Error as e:
        print(f"❌ Erro no login: {str(e)}")
        return jsonify({'error': 'Erro interno ao efetuar login'}), 500
    finally:
        conn.close()

# Rota para obter o perfil do utilizador
@app.route('/utilizador', methods=['GET'])
def profile():
    print("🔍 Verificando sessão do utilizador...")
    
    token = request.headers.get("Authorization")
    print(f"🟢 Token Recebido: {token}")

    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]

    print(f"🔹 Conteúdo da sessão antes da verificação: {dict(session)}")

    if 'user_id' not in session:
        print("❌ Erro: Nenhum usuário autenticado!")
        return jsonify({'error': 'Utilizador não autenticado'}), 401

    print(f"✅ Sessão ativa para o utilizador ID: {session.get('user_id')}")

    conn = get_db_connection()
    if not conn:
        print("❌ Erro: Falha na conexão com a base de dados!")
        return jsonify({'error': 'Erro de conexão com a base de dados'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email FROM usuarios WHERE id = %s", (session.get('user_id'),))
        user = cursor.fetchone()

        if not user:
            print("❌ Erro: Utilizador não encontrado na base de dados!")
            return jsonify({'error': 'Utilizador não encontrado'}), 404

        print(f"✅ Utilizador encontrado: {user['nome']} ({user['email']})")

        response = jsonify({
            'id': user['id'],
            'nome': user['nome'],
            'email': user['email']
        })
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    except Error as e:
        print(f"❌ Erro ao obter perfil: {str(e)}")
        return jsonify({'error': f'Erro ao obter perfil: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/update_user', methods=['POST'])
def update_user():
    print("🔍 Verificando sessão do utilizador antes da atualização...")
    print("Sessão atual:", dict(session))  # Debug: Ver estado da sessão

    if 'user_id' not in session:
        print("❌ Erro: Usuário não autenticado!")
        return jsonify({'error': 'Não autorizado', 'session_data': dict(session)}), 401


    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    
    if not nome or not email:
        return jsonify({'error': 'Nome e Email são obrigatórios'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Erro de conexão com a base de dados'}), 500

    try:
        cursor = conn.cursor()
        
        if senha:
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(senha.encode('utf-8'), salt)
            cursor.execute("UPDATE usuarios SET nome = %s, email = %s, senha = %s WHERE id = %s", 
                           (nome, email, hashed_password.decode('utf-8'), session['user_id']))
        else:
            cursor.execute("UPDATE usuarios SET nome = %s, email = %s WHERE id = %s", 
                           (nome, email, session['user_id']))
        
        conn.commit()
        print("✅ Informações do utilizador atualizadas com sucesso!")
        return jsonify({'message': 'Informações atualizadas com sucesso!'}), 200
    except Error as e:
        print(f"❌ Erro ao atualizar informações: {str(e)}")
        return jsonify({'error': f'Erro ao atualizar informações: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/quartos', methods=['GET'])
def get_quartos():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Erro de conexão com a base de dados'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quartos")
        quartos = cursor.fetchall()
        return jsonify(quartos), 200
    except Error as e:
        return jsonify({'error': f'Erro ao buscar quartos: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/quarto/<int:id>', methods=['GET'])
def get_quarto(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Erro de conexão com a base de dados'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quartos WHERE id = %s", (id,))
        quarto = cursor.fetchone()
        if not quarto:
            return jsonify({'error': 'Quarto não encontrado'}), 404
        return jsonify(quarto), 200
    except Error as e:
        return jsonify({'error': f'Erro ao buscar o quarto: {str(e)}'}), 500
    finally:
        conn.close()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Rota para logout
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout efetuado com sucesso'}), 200

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

if __name__ == '__main__':
    init_db()
    app.run(debug=True)