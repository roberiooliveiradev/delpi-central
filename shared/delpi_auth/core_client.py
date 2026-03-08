# shared/delpi_auth/core_client.py
import requests
from .config import CORE_ME_ENDPOINT


def fetch_user_context(token: str) -> dict:

    response = requests.get(
        CORE_ME_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )

    if response.status_code != 200:
        raise Exception("Unable to fetch user context")

    return response.json()