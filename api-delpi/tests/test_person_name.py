from app.shared.utils.person_name import first_given_name, format_person_name


def test_format_person_name_title_case_and_particles() -> None:
    assert format_person_name("MARIA DA SILVA") == "Maria da Silva"


def test_first_given_name_skips_particles() -> None:
    assert first_given_name("Maria da Silva") == "Maria"
    assert first_given_name("de Souza") == "Souza"
    assert first_given_name("") == "—"
