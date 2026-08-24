ALLOWED_USAGE_SESSION_SOURCES = frozenset(
    {
        "socket_close",
        "socket_disconnect",
        "ttl_flush",
    }
)

DEFAULT_MAX_SESSION_DURATION_SECONDS = 8 * 60 * 60
