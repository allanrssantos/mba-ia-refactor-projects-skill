"""Conexão SQLite por requisição, schema e seed inicial."""
import sqlite3

from flask import g

from src.models.constants import TIPO_USUARIO_ADMIN, TIPO_USUARIO_PADRAO
from src.models.seguranca import gerar_hash_senha

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

PRODUTOS_SEED = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

# Usuários de exemplo; a senha é gravada com hash (nunca em texto puro).
USUARIOS_SEED = (
    ("Admin", "admin@loja.com", "admin123", TIPO_USUARIO_ADMIN),
    ("João Silva", "joao@email.com", "123456", TIPO_USUARIO_PADRAO),
    ("Maria Santos", "maria@email.com", "senha123", TIPO_USUARIO_PADRAO),
)


class Database:
    """Fornece uma conexão por contexto de aplicação (flask.g) para o caminho configurado."""

    def __init__(self, caminho):
        self.caminho = caminho

    def init_app(self, app):
        app.teardown_appcontext(self._fechar)
        with app.app_context():
            self.criar_schema_e_seed(self.conexao())

    def conexao(self):
        if "db" not in g:
            g.db = sqlite3.connect(self.caminho)
            g.db.row_factory = sqlite3.Row
        return g.db

    @staticmethod
    def _fechar(_exc=None):
        conexao = g.pop("db", None)
        if conexao is not None:
            conexao.close()

    @staticmethod
    def criar_schema_e_seed(conexao):
        with conexao:
            for ddl in SCHEMA:
                conexao.execute(ddl)

        with conexao:
            total = conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
            if total == 0:
                conexao.executemany(
                    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                    PRODUTOS_SEED,
                )
                conexao.executemany(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    [(nome, email, gerar_hash_senha(senha), tipo) for nome, email, senha, tipo in USUARIOS_SEED],
                )
