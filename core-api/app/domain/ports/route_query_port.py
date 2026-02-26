# app/domain/ports/route_query_port.py

from abc import ABC, abstractmethod
from typing import List


class RouteQueryPort(ABC):

    @abstractmethod
    def list_active_menu_routes(self) -> List:
        """
        Retorna rotas:
        - active == True
        - show_in_menu == True
        - com app carregado
        """
        pass