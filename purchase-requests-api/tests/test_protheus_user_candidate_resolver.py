from purchase_requests_app.domain.services.protheus_user_candidate_resolver import (
    pick_protheus_user_candidate,
)


def test_pick_protheus_user_by_portal_name() -> None:
    candidates = [
        {
            "protheus_user_id": "000062",
            "code": "TAMIRIS",
            "name": "TAMIRIS DECKER",
            "email": "COMPRAS@DELPI.COM.BR",
        },
        {
            "protheus_user_id": "000234",
            "code": "YAGO.ROCHA",
            "name": "YAGO ROCHA",
            "email": "compras@delpi.com.br",
        },
    ]
    picked = pick_protheus_user_candidate(candidates, portal_user_name="Yago Rocha")
    assert picked is not None
    assert picked["protheus_user_id"] == "000234"
