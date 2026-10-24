from src.utils.logger import obter_logger


class NotificacaoService:
    """Canal de notificações (e-mail/SMS/push). Hoje apenas registra em log; injetável e substituível."""

    def __init__(self, logger=None):
        self.logger = logger or obter_logger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self.logger.info("email: pedido %s criado para usuario %s", pedido_id, usuario_id)
        self.logger.info("sms: pedido %s recebido", pedido_id)
        self.logger.info("push: novo pedido %s recebido pelo sistema", pedido_id)

    def pedido_aprovado(self, pedido_id):
        self.logger.info("notificacao: pedido %s aprovado, preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        self.logger.info("notificacao: pedido %s cancelado, devolver estoque", pedido_id)
