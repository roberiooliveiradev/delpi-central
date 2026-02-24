# app/interfaces/http/utils/pagination.py


from flask import request, jsonify
from math import ceil
from sqlalchemy import asc, desc

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


def get_pagination_params():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", DEFAULT_PAGE_SIZE))
    except ValueError:
        return None, None, None, None, jsonify(
            {"error": "page e page_size devem ser inteiros"}
        ), 400

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE

    sort = (request.args.get("sort") or "").strip() or None

    # compat: frontend pode mandar direction, backend antigo mandava order
    direction = (request.args.get("direction") or request.args.get("order") or "asc").lower()
    if direction not in ["asc", "desc"]:
        direction = "asc"

    return page, page_size, sort, direction, None, None


from sqlalchemy import asc, desc


def apply_sorting(query, model, allowed_sort_fields=None, sort=None, direction="asc"):
    """
    Suporta:
    ?sort=field
    ?sort=field1,field2
    ?sort=field1,-field2
    ?sort=field1:asc,field2:desc
    ?sort=field1,field2&direction=asc,desc
    """

    if not sort:
        return query

    sort_fields = [s.strip() for s in sort.split(",") if s.strip()]
    direction_list = []

    # direction pode vir como lista: asc,desc
    if direction and "," in direction:
        direction_list = [d.strip().lower() for d in direction.split(",")]
    else:
        direction_list = [direction] * len(sort_fields)

    order_clauses = []

    for idx, field_expr in enumerate(sort_fields):
        field_name = field_expr
        field_direction = None

        # caso: field:desc
        if ":" in field_expr:
            parts = field_expr.split(":")
            field_name = parts[0]
            field_direction = parts[1].lower()

        # caso: -field
        elif field_expr.startswith("-"):
            field_name = field_expr[1:]
            field_direction = "desc"

        # caso padrão
        else:
            if idx < len(direction_list):
                field_direction = direction_list[idx]
            else:
                field_direction = "asc"

        if allowed_sort_fields and field_name not in allowed_sort_fields:
            continue

        if not hasattr(model, field_name):
            continue

        column = getattr(model, field_name)

        if field_direction == "desc":
            order_clauses.append(desc(column))
        else:
            order_clauses.append(asc(column))

    if order_clauses:
        return query.order_by(*order_clauses)

    return query


def apply_filters(query, model, allowed_filter_fields=None):
    """
    Filtros estruturados via query params.
    Ex: ?active=true&type=microfrontend
    Observação: q (busca textual) deve ser tratada no controller (depende do modelo).
    """
    for key, value in request.args.items():
        if key in ["page", "page_size", "sort", "order", "direction", "q"]:
            continue

        if allowed_filter_fields and key not in allowed_filter_fields:
            continue

        if not hasattr(model, key):
            continue

        column = getattr(model, key)

        if isinstance(value, str) and value.lower() in ["true", "false"]:
            query = query.filter(column == (value.lower() == "true"))
        else:
            query = query.filter(column == value)

    return query


def paginate_query(
    query,
    serializer,
    model,
    allowed_sort_fields=None,
    allowed_filter_fields=None,
    default_sort=None,
    default_direction="asc",
):
    page, page_size, sort, direction, error_response, status = get_pagination_params()

    if error_response:
        return error_response, status

    # filtros (antes do count)
    query = apply_filters(query, model, allowed_filter_fields=allowed_filter_fields)

    total = query.count()

    # sorting (depois do count)
    sort_field = sort or default_sort
    sort_dir = direction or default_direction
    query = apply_sorting(
        query,
        model,
        allowed_sort_fields=allowed_sort_fields,
        sort=sort_field,
        direction=sort_dir,
    )

    rows = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    total_pages = ceil(total / page_size) if total > 0 else 1

    return jsonify({
        "data": [serializer(row) for row in rows if row is not None],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "sort": sort_field,
            "direction": sort_dir
        }
    })