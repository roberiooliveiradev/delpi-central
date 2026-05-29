from app.domain.services.chat_fast_path_service import ChatFastPathService


def test_fast_path_skips_refinement_messages():
    assert not ChatFastPathService.should_use("proxima pagina", enabled=True, max_chars=30)
    assert not ChatFastPathService.should_use("filial 01", enabled=True, max_chars=30)
    assert not ChatFastPathService.should_use("filtre filial 02", enabled=True, max_chars=30)
    assert not ChatFastPathService.should_use("completo de novo", enabled=True, max_chars=30)


def test_fast_path_allows_small_talk():
    assert ChatFastPathService.should_use("olá", enabled=True, max_chars=30)
    assert ChatFastPathService.is_small_talk("olá, tudo bem?")
