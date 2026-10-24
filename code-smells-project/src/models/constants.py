"""Constantes de regra de negócio compartilhadas por models, services e validadores."""

API_VERSION = "1.0.0"

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO = (STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO)

TIPO_USUARIO_PADRAO = "cliente"
TIPO_USUARIO_ADMIN = "admin"

# Faixas de desconto do relatório de vendas: (faturamento acima de, percentual). Ordem importa.
FAIXAS_DESCONTO = ((10000, 0.1), (5000, 0.05), (1000, 0.02))

PRODUTO_DESCONHECIDO = "Desconhecido"
