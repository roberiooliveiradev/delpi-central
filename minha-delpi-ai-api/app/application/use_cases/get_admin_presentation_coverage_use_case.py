from app.domain.services.chat_presentation_coverage_service import (
    ChatPresentationCoverageService,
)


class GetAdminPresentationCoverageUseCase:
    def execute(self) -> dict:
        return ChatPresentationCoverageService.build_report()
