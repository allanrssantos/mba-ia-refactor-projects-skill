from src.models.constants import TIPO_USUARIO_PADRAO
from src.models.seguranca import gerar_hash_senha, verificar_senha

# Allow-list de campos públicos: a senha (ou seu hash) nunca sai do model.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def serializar_usuario(linha):
    return {campo: linha[campo] for campo in CAMPOS_PUBLICOS}


def serializar_login(linha):
    return {campo: linha[campo] for campo in CAMPOS_LOGIN}


class UsuarioModel:
    def __init__(self, db):
        self.db = db

    def listar(self):
        linhas = self.db.conexao().execute("SELECT * FROM usuarios").fetchall()
        return [serializar_usuario(linha) for linha in linhas]

    def buscar_por_id(self, usuario_id):
        linha = self.db.conexao().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return serializar_usuario(linha) if linha else None

    def criar(self, nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
        conexao = self.db.conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, gerar_hash_senha(senha), tipo),
            )
            return cursor.lastrowid

    def autenticar(self, email, senha):
        """Busca pelo e-mail e confere a senha em código; senhas legadas são regravadas com hash."""
        conexao = self.db.conexao()
        linhas = conexao.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
        for linha in linhas:
            confere, precisa_rehash = verificar_senha(linha["senha"], senha)
            if not confere:
                continue
            if precisa_rehash:
                with conexao:
                    conexao.execute(
                        "UPDATE usuarios SET senha = ? WHERE id = ?", (gerar_hash_senha(senha), linha["id"])
                    )
            return serializar_login(linha)
        return None

    def contar(self):
        return self.db.conexao().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
