# app/infrastructure/persistence/pagination.py

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000


def paginate(page: int, page_size: int):

    page = max(page or 1, 1)

    page_size = page_size or DEFAULT_PAGE_SIZE
    page_size = min(page_size, MAX_PAGE_SIZE)
    page_size = max(page_size, 1)

    offset = (page - 1) * page_size

    return {
        "page": page,
        "page_size": page_size,
        "offset": offset
    }


def build_page_response(items, total, page, page_size):

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }