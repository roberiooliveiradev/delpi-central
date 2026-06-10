from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)


def test_humanized_data_response_bundle_keys_exist():
    assert ChatHumanizedDataResponseContentService.get("sections", "summaryHeader")
    assert ChatHumanizedDataResponseContentService.get("alertLevels", "attention") == "Atenção"
    assert ChatHumanizedDataResponseContentService.get("nextActions", "stock")
    assert ChatHumanizedDataResponseContentService.list("recommendations", "factory_status")
