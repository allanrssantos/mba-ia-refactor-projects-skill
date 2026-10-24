"""Validadores puros de entrada. Mensagens e ordem de checagem preservam o contrato original."""
from src.models.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO,
)
from src.utils.errors import ValidationError


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _exigir_dicionario(dados, mensagem="Dados inválidos"):
    if not dados or not isinstance(dados, dict):
        raise ValidationError(mensagem)
    return dados


def validar_produto(dados):
    """Usado em criação e atualização de produto; devolve os campos normalizados."""
    dados = _exigir_dicionario(dados)
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not _eh_numero(preco):
        raise ValidationError("Preço inválido")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if not _eh_inteiro(estoque):
        raise ValidationError("Estoque inválido")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def _preco_opcional(valor):
    """Mesma semântica do original: valor vazio é ignorado; não numérico vira 400."""
    if not valor:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError("Preço inválido")


def validar_filtros_busca(args):
    return {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria", None),
        "preco_min": _preco_opcional(args.get("preco_min", None)),
        "preco_max": _preco_opcional(args.get("preco_max", None)),
    }


def validar_usuario(dados):
    dados = _exigir_dicionario(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(campo, str) for campo in (nome, email, senha)):
        raise ValidationError("Dados inválidos")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    mensagem = "Email e senha são obrigatórios"
    dados = _exigir_dicionario(dados, mensagem)
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError(mensagem)
    return {"email": email, "senha": senha}


def validar_pedido(dados):
    dados = _exigir_dicionario(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _eh_inteiro(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not itens or not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens_validados = []
    for item in itens:
        if (
            not isinstance(item, dict)
            or not _eh_inteiro(item.get("produto_id"))
            or not _eh_inteiro(item.get("quantidade"))
        ):
            raise ValidationError("Item inválido: produto_id e quantidade devem ser inteiros")
        itens_validados.append({"produto_id": item["produto_id"], "quantidade": item["quantidade"]})

    return {"usuario_id": usuario_id, "itens": itens_validados}


def validar_status_pedido(dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    return novo_status


def validar_query_admin(dados):
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")
    return query
