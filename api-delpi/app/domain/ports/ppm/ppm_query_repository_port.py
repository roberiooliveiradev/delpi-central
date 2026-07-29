from abc import ABC, abstractmethod


class PpmQueryRepositoryPort(ABC):

    @abstractmethod
    def get_returned_totals(
        self,
        *,
        ppm_type: str,
        branch: str | None,
        date_start: str | None,
        date_end: str | None,
        product_prefix: str | None = None,
    ) -> dict:
        raise NotImplementedError

    def get_nc_returned_total(self, request) -> float:
        """Compat — preferir ``get_returned_totals`` / ``GetReturnedQuantityUseCase``."""
        totals = self.get_returned_totals(
            ppm_type=request.type,
            branch=request.branch,
            date_start=request.date_start,
            date_end=request.date_end,
            product_prefix=getattr(request, "product_prefix", None),
        )
        return float(totals.get("qty_returned_un") or 0)

    @abstractmethod
    def list_items(self, request):
        raise NotImplementedError

    @abstractmethod
    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        raise NotImplementedError
