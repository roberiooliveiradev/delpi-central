from __future__ import annotations

def paginate(page: int, page_size: int, *, max_page_size: int | None = None, tier_id: str = "infra_offset_50_1000"):
    page = max(page or 1, 1)
    cap = int(max_page_size) if max_page_size is not None else 1000
    if page_size is None or page_size == 0:
        page_size = 50
    else:
        page_size = int(page_size)
    page_size = min(max(page_size, 1), int(cap))
    offset = (page - 1) * page_size
    return {"page": page, "page_size": page_size, "offset": offset}

def build_page_response(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": total_pages}
