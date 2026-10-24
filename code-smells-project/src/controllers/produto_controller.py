from flask import jsonify, request

from src.utils.errors import NotFoundError
from src.utils.logger import obter_logger
from src.utils.validators import validar_filtros_busca, validar_produto

logger = obter_logger(__name__)


class ProdutoController:
    def __init__(self, produto_model):
        self.produtos = produto_model

    def listar(self):
        produtos = self.produtos.listar()
        logger.info("listando %s produtos", len(produtos))
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def buscar(self, id):
        produto = self.produtos.buscar_por_id(id)
        if not produto:
            raise NotFoundError("Produto não encontrado", extra={"sucesso": False})
        return jsonify({"dados": produto, "sucesso": True}), 200

    def criar(self):
        entrada = validar_produto(request.get_json(silent=True))
        produto_id = self.produtos.criar(**entrada)
        logger.info("produto criado id=%s", produto_id)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, id):
        if not self.produtos.buscar_por_id(id):
            raise NotFoundError("Produto não encontrado")
        entrada = validar_produto(request.get_json(silent=True))
        self.produtos.atualizar(id, **entrada)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        if not self.produtos.buscar_por_id(id):
            raise NotFoundError("Produto não encontrado")
        self.produtos.deletar(id)
        logger.info("produto deletado id=%s", id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    def pesquisar(self):
        filtros = validar_filtros_busca(request.args)
        resultados = self.produtos.pesquisar(**filtros)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
