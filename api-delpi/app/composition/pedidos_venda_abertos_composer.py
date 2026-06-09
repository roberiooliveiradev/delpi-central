from app.application.use_cases.pedidos_venda_abertos.list_pedidos_venda_abertos_use_case import (
    ListPedidosVendaAbertosUseCase,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.pedidos_venda_abertos_query_repository import (
    PedidosVendaAbertosQueryRepository,
)


def build_list_pedidos_venda_abertos_use_case() -> ListPedidosVendaAbertosUseCase:
    return ListPedidosVendaAbertosUseCase(
        repository=PedidosVendaAbertosQueryRepository(),
    )
