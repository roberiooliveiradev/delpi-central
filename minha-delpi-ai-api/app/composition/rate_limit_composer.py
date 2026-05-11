from app.domain.services.rate_limit_service import InMemoryRateLimitService

_rate_limit_service = InMemoryRateLimitService()


def get_rate_limit_service() -> InMemoryRateLimitService:
    return _rate_limit_service
