from abc import ABC, abstractmethod
from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest


class StockValueQueryRepositoryPort(ABC):

    @abstractmethod
    def get_stock_value_summary(self, request: GetStockValueRequest) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_stock_value_by_branch(self, request: GetStockValueRequest) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_stock_value_by_location(self, request: GetStockValueRequest) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_top_products_by_stock_value(self, request: GetStockValueRequest) -> list[dict]:
        raise NotImplementedError