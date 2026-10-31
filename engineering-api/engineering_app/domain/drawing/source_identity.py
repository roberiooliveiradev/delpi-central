"""Document source comparability (doc 71 §4.2).

Visual observations may only be confronted with textual extraction when
the two sources' identity is verifiable. A distinct revision is never
the same source, and a lone product code never proves identity.
"""

from __future__ import annotations

from enum import StrEnum


class SourceMatch(StrEnum):
    SAME_DOCUMENT_VERIFIED = "same_document_verified"
    POSSIBLE_MATCH = "possible_match"
    DIFFERENT_DOCUMENT = "different_document"
    UNKNOWN = "unknown"


def classify_source_match(
    *,
    attachment_hash: str | None,
    attachment_revision: str | None,
    attachment_document_ref: str | None,
    attachment_product_code: str | None,
    official_hash: str | None,
    official_revision: str | None,
    official_document_ref: str | None,
    official_product_code: str | None,
) -> SourceMatch:
    """Classify how the consumer attachment relates to the official PDF."""
    if attachment_hash and official_hash:
        return (
            SourceMatch.SAME_DOCUMENT_VERIFIED
            if attachment_hash == official_hash
            else SourceMatch.DIFFERENT_DOCUMENT
        )
    att_rev = (attachment_revision or "").strip()
    off_rev = (official_revision or "").strip()
    att_code = (attachment_product_code or "").strip()
    off_code = (official_product_code or "").strip()
    if att_rev and off_rev and att_rev != off_rev:
        return SourceMatch.DIFFERENT_DOCUMENT
    if (
        att_code
        and off_code
        and att_code == off_code
        and att_rev
        and off_rev
        and att_rev == off_rev
        and attachment_document_ref
        and official_document_ref
        and attachment_document_ref == official_document_ref
    ):
        return SourceMatch.SAME_DOCUMENT_VERIFIED
    if att_code and off_code and att_code == off_code and (
        not att_rev or not off_rev or att_rev == off_rev
    ):
        return SourceMatch.POSSIBLE_MATCH
    if att_code and off_code and att_code != off_code:
        return SourceMatch.DIFFERENT_DOCUMENT
    return SourceMatch.UNKNOWN
