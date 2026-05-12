from ipaddress import ip_address
from urllib.parse import urlparse


class ExternalProviderUrlPolicy:
    INTERNAL_HOSTS = {
        "api-delpi",
        "core-api",
        "minha-delpi-ai-api",
        "gateway",
        "localhost",
        "127.0.0.1",
    }

    def validate(self, url: str, provider_type: str) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError("URL scheme must be http or https")

        if not parsed.hostname:
            raise ValueError("URL host is required")

        if provider_type == "external" and parsed.scheme != "https":
            raise ValueError("External providers must use HTTPS")

        if provider_type == "internal":
            return

        if self._is_private_host(parsed.hostname):
            raise ValueError("External providers cannot use private/internal hosts")

    def _is_private_host(self, hostname: str) -> bool:
        if hostname in self.INTERNAL_HOSTS:
            return True

        try:
            address = ip_address(hostname)
        except ValueError:
            return False

        return address.is_private or address.is_loopback or address.is_link_local
