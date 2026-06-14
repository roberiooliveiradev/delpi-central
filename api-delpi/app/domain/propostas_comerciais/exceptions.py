class PropostaComercialNotFoundError(Exception):
    """Proposta comercial inexistente ou inativa."""

    def __init__(self, proposta_interna: str):
        self.proposta_interna = proposta_interna
        super().__init__(f"Proposta comercial {proposta_interna} não encontrada.")
