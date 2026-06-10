from app.application.use_cases.pedidos_venda_abertos.list_pedidos_venda_abertos_use_case import (
    ListPedidosVendaAbertosUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.list_ops_abertas_use_case import (
    ListOpsAbertasUseCase,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.ops_abertas_query_repository import (
    OpsAbertasQueryRepository,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.pedidos_venda_abertos_query_repository import (
    PedidosVendaAbertosQueryRepository,
)


def build_list_pedidos_venda_abertos_use_case() -> ListPedidosVendaAbertosUseCase:
    return ListPedidosVendaAbertosUseCase(
        repository=PedidosVendaAbertosQueryRepository(),
    )


def build_list_ops_abertas_use_case() -> ListOpsAbertasUseCase:
    return ListOpsAbertasUseCase(
        repository=OpsAbertasQueryRepository(),
    )
