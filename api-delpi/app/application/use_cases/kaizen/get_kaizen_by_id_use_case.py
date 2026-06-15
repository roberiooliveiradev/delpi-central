from typing import Optional

from app.domain.entities.kaizen.kaizen import KaizenDetail
from app.domain.ports.kaizen.kaizen_query_port import KaizenQueryRepositoryPort


class GetKaizenByIdUseCase:
    def __init__(self, repository: KaizenQueryRepositoryPort):
        self.repository = repository

    def execute(self, kaizen_id: str) -> Optional[KaizenDetail]:
        return self.repository.get_kaizen_by_id(kaizen_id)
