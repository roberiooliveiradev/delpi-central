# app/interfaces/http/utils/pagination.py


from flask import request, jsonify
from math import ceil

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


def get_pagination_params():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", DEFAULT_PAGE_SIZE))
    except ValueError:
        return None, None, jsonify({"error": "page e page_size devem ser inteiros"}), 400

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE

    return page, page_size, None, None


def paginate_query(query, serializer):
    page, page_size, error_response, status = get_pagination_params()

    if error_response:
        return error_response, status

    total = query.count()

    rows = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    total_pages = ceil(total / page_size) if total > 0 else 1

    return jsonify({
        "data": [serializer(row) for row in rows],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    })