def truncate_ip(ip: str | None) -> str | None:
    """Remove o último octeto do IPv4 ou os últimos 80 bits do IPv6.

    LGPD Art. 6º III (minimização): armazena apenas o necessário para
    auditoria de segurança, sem permitir identificação direta do titular.
    """
    if not ip:
        return None
    ip = ip.strip()
    if ":" in ip:
        parts = ip.split(":")
        if len(parts) > 4:
            return ":".join(parts[:4]) + "::"
        return ip
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3]) + ".0"
    return ip
