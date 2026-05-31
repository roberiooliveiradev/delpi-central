from unittest.mock import MagicMock, patch

from app.application.services.chat_web_search_save_sources_service import (
    ChatWebSearchSaveSourcesService,
)


def test_is_save_request():
    assert ChatWebSearchSaveSourcesService.is_save_request("salve as fontes da pesquisa no projeto")
    assert not ChatWebSearchSaveSourcesService.is_save_request("pesquise na web sobre WEG")


def test_build_direct_answer_without_project():
    session = MagicMock(project_id=None)

    answer = ChatWebSearchSaveSourcesService.build_direct_answer(
        message="salvar fontes no projeto",
        user_id="user-1",
        session=session,
        previous_messages=[],
    )

    assert answer
    assert "projeto" in answer.lower()


def test_build_direct_answer_without_recent_search():
    session = MagicMock(project_id="11111111-1111-1111-1111-111111111111")

    answer = ChatWebSearchSaveSourcesService.build_direct_answer(
        message="salvar fontes",
        user_id="user-1",
        session=session,
        previous_messages=[{"role": "user", "content": "oi"}],
    )

    assert answer
    assert "pesquisa" in answer.lower()


@patch(
    "app.application.services.chat_web_search_save_sources_service.make_create_project_source_use_case"
)
def test_build_direct_answer_saves_sources(mock_factory):
    mock_use_case = MagicMock()
    mock_use_case.execute_text.return_value = MagicMock(title="Pesquisa web — teste")
    mock_factory.return_value = mock_use_case

    session = MagicMock(project_id="11111111-1111-1111-1111-111111111111")
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "webSearchResearch": {
                    "query": "manual WEG",
                    "sites": [
                        {
                            "title": "Manual CFW500",
                            "url": "https://weg.net/manual",
                            "hostname": "weg.net",
                            "isOfficial": True,
                        }
                    ],
                },
                "sources": [
                    {
                        "title": "Manual CFW500",
                        "sourceRef": "https://weg.net/manual",
                        "sourceType": "web",
                    }
                ],
            },
        }
    ]

    answer = ChatWebSearchSaveSourcesService.build_direct_answer(
        message="salve as fontes da pesquisa web no projeto",
        user_id="user-1",
        session=session,
        previous_messages=previous,
    )

    assert answer
    assert "Salvei" in answer
    mock_use_case.execute_text.assert_called_once()
    kwargs = mock_use_case.execute_text.call_args.kwargs
    assert "manual WEG" in kwargs["content"]
    assert kwargs["metadata"]["origin"] == "web_search"
