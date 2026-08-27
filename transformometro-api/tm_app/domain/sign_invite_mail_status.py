"""Constantes de status de e-mail por convite — espelham CHECK constraints da migration V044."""

MAIL_SEND_PENDING = "pending"
MAIL_SEND_SKIPPED_NO_EMAIL = "skipped_no_email"
MAIL_SEND_SKIPPED_MAIL_DISABLED = "skipped_mail_disabled"
MAIL_SEND_SKIPPED_GRAPH_UNCONFIGURED = "skipped_graph_unconfigured"
MAIL_SEND_FAILED = "failed"
MAIL_SEND_ACCEPTED = "accepted"

MAIL_DELIVERY_NOT_APPLICABLE = "not_applicable"
MAIL_DELIVERY_TRACE_PENDING = "trace_pending"
MAIL_DELIVERY_DELIVERED = "delivered"
MAIL_DELIVERY_BOUNCED = "bounced"
MAIL_DELIVERY_UNKNOWN = "unknown"
