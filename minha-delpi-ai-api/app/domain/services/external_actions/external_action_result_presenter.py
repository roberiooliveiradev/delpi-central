class ExternalActionResultPresenter:
    PRODUCT_ALIASES = {
        "code": "Código",
        "description": "Descrição",
        "type": "Tipo",
        "unit": "Unidade",
        "groupCode": "Grupo",
        "active": "Ativo",
        "defaultWarehouse": "Armazém padrão",
        "lastPurchasePrice": "Último preço de compra",
        "standardCost": "Custo padrão",
        "lastRevisionDate": "Última revisão",
        "ncm": "NCM",
    }

    STOCK_ALIASES = {
        "branch": "Filial",
        "warehouse": "Armazém",
        "current_quantity": "Quantidade atual",
        "available_quantity": "Quantidade disponível",
        "committed_quantity": "Quantidade empenhada",
        "reserved_quantity": "Quantidade reservada",
        "physical_location": "Localização física",
    }

    def present(self, data) -> dict:
        root = self._unwrap_data(data)
        product = root.get("product") if isinstance(root, dict) else None

        if isinstance(product, dict):
            return self._present_product(root, product)

        if isinstance(root, dict):
            lmp_page = self._present_lmp_page(root)

            if lmp_page:
                return lmp_page

            lmp_detail = self._present_lmp_detail(root)

            if lmp_detail:
                return lmp_detail

        if isinstance(root, list) and root:
            sql_result = self._present_sql_rows(root)

            if sql_result:
                return sql_result

        items = root.get("items") if isinstance(root, dict) else None

        if isinstance(items, list):
            if items and isinstance(items[0], dict) and "sale_number" in items[0]:
                return self._present_lmp_page(root)

            if items and isinstance(items[0], dict) and "order_number" in items[0]:
                return self._present_sale_orders(root, items)

            if items and isinstance(items[0], dict) and "code" in items[0] and "description" in items[0]:
                return self._present_product_search(root, items)

            return self._present_items(items)

        return {
            "titulo": "Resultado da API",
            "linhas": ["A API retornou dados autorizados para a consulta."],
            "dados": root,
        }

    def _unwrap_data(self, data):
        root = data

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        return root

    def _present_product(self, root: dict, product: dict) -> dict:
        product_summary = {
            "code": product.get("code"),
            "description": product.get("description"),
            "type": product.get("type"),
            "unit": product.get("unit"),
            "groupCode": product.get("group_code"),
            "active": product.get("active"),
            "defaultWarehouse": product.get("default_warehouse"),
            "lastPurchasePrice": product.get("last_purchase_price"),
            "standardCost": product.get("standard_cost"),
            "lastRevisionDate": product.get("last_revision_date"),
            "ncm": product.get("ncm_ipi_position"),
        }

        linhas = [
            f"Produto {product_summary['code']}: {product_summary['description']}.",
            f"Tipo {product_summary['type']}, unidade {product_summary['unit']}, grupo {product_summary['groupCode']}.",
            f"Status ativo: {product_summary['active']}. Armazém padrão: {product_summary['defaultWarehouse']}.",
            f"Último preço de compra: {product_summary['lastPurchasePrice']}. Custo padrão: {product_summary['standardCost']}.",
            f"Última revisão: {product_summary['lastRevisionDate']}. NCM: {product_summary['ncm']}.",
        ]

        for key in ["guide", "inspection", "structure", "customers", "suppliers"]:
            value = root.get(key)
            if isinstance(value, dict):
                total = value.get("total")
                if total is not None:
                    linhas.append(f"{self._label_collection(key)}: {total} registro(s).")

        return {
            "titulo": f"Informações do produto {product_summary['code']}",
            "linhas": [line for line in linhas if "None" not in line],
            "campos": self._alias_dict(product_summary, self.PRODUCT_ALIASES),
            "dados": {
                "product": product_summary,
                "guideTotal": self._total(root.get("guide")),
                "inspectionTotal": self._total(root.get("inspection")),
                "structureTotal": self._total(root.get("structure")),
            },
        }

    def _present_lmp_page(self, root: dict) -> dict | None:
        items = root.get("items")

        if not isinstance(items, list):
            return None

        if items and isinstance(items[0], dict) and "sale_number" not in items[0] and "saleNumber" not in items[0]:
            return None

        total = root.get("total")

        if not items and total in (0, None):
            return {
                "titulo": "Lista de LMPs",
                "linhas": ["Nenhuma LMP encontrada para os filtros informados."],
                "dados": root,
            }

        linhas = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            ov = item.get("sale_number") or item.get("saleNumber")
            desc = item.get("sale_description") or item.get("saleDescription") or ""
            status = item.get("status") or item.get("engineering_status") or ""
            kind = item.get("listing_kind") or item.get("listingKind") or ""
            branch = item.get("branch") or ""

            parts = [str(part) for part in [ov, kind, status, branch] if part]
            header = " · ".join(parts) if parts else "LMP"
            line = f"OV {header}: {desc}".strip(": ")

            if line:
                linhas.append(line.rstrip(": "))

        if total is not None:
            linhas.append(f"Total: {total} registro(s) (página {root.get('page', 1)}).")

        return {
            "titulo": "Lista de LMPs",
            "linhas": linhas or ["Nenhuma LMP na página atual."],
            "dados": {"total": total, "items": items[:12]},
        }

    def _present_lmp_detail(self, root: dict) -> dict | None:
        sale_number = root.get("sale_number") or root.get("saleNumber")

        if not sale_number:
            return None

        desc = root.get("sale_description") or root.get("saleDescription") or ""
        status = root.get("engineering_status") or root.get("status") or ""
        kind = root.get("listing_kind") or root.get("listingKind") or ""
        branch = root.get("branch") or ""
        customer = root.get("costumer_name") or root.get("customer_name") or ""
        seller = root.get("seller_name") or ""
        qtd_pi = root.get("qtd_pi")

        linhas = [
            f"OV {sale_number}: {desc}".strip(": "),
        ]

        if kind:
            linhas.append(f"Tipo: {kind}.")

        if branch:
            linhas.append(f"Filial: {branch}.")

        if status:
            linhas.append(f"Status engenharia: {status}.")

        if customer:
            linhas.append(f"Cliente: {customer}.")

        if seller:
            linhas.append(f"Vendedor: {seller}.")

        if qtd_pi is not None:
            linhas.append(f"Quantidade PI: {qtd_pi}.")

        products = root.get("list_products") or root.get("listProducts") or []

        if isinstance(products, list):
            linhas.append(f"Produtos na LMP: {len(products)} item(ns).")

        return {
            "titulo": f"LMP OV {sale_number}",
            "linhas": [line for line in linhas if line],
            "dados": root,
        }

    def _present_sql_rows(self, rows: list) -> dict | None:
        if not rows:
            return {
                "titulo": "Consulta SQL",
                "linhas": ["A consulta não retornou registros."],
                "dados": {"rows": []},
            }

        if not isinstance(rows[0], dict):
            return {
                "titulo": "Consulta SQL",
                "linhas": [f"A consulta retornou {len(rows)} registro(s)."],
                "dados": {"rows": rows[:100]},
            }

        linhas = [f"A consulta retornou {len(rows)} registro(s)."]

        for index, row in enumerate(rows[:8], start=1):
            if not isinstance(row, dict):
                continue

            preview = ", ".join(
                f"{key}={value}"
                for key, value in list(row.items())[:6]
                if value is not None
            )
            linhas.append(f"{index}. {preview}")

        if len(rows) > 8:
            linhas.append(f"… e mais {len(rows) - 8} registro(s).")

        return {
            "titulo": "Consulta SQL",
            "linhas": linhas,
            "dados": {"rows": rows[:100]},
        }

    def _present_product_search(self, root: dict, items: list) -> dict:
        total = root.get("total")

        if not items:
            return {
                "titulo": "Busca de produtos",
                "linhas": ["Nenhum produto encontrado para a busca."],
                "dados": root,
            }

        linhas = []

        for item in items[:15]:
            if not isinstance(item, dict):
                continue

            code = item.get("code") or "?"
            desc = item.get("description") or ""
            tipo = item.get("type") or ""
            unit = item.get("unit") or ""

            parts = [f"**{code}**"]
            if desc:
                parts.append(desc)
            if tipo:
                parts.append(f"({tipo})")
            if unit:
                parts.append(f"[{unit}]")

            linhas.append(" — ".join(parts[:2]) + (f" {parts[2]}" if len(parts) > 2 else "") + (f" {parts[3]}" if len(parts) > 3 else ""))

        if total is not None and total > len(items):
            linhas.append(f"Total encontrado: {total} produto(s).")

        return {
            "titulo": "Busca de produtos",
            "linhas": linhas or ["Nenhum produto encontrado."],
            "dados": {"total": total, "items": [{"code": i.get("code"), "description": i.get("description"), "type": i.get("type"), "unit": i.get("unit")} for i in items[:15]]},
        }

    def _present_sale_orders(self, root: dict, items: list) -> dict:
        total = root.get("total")

        if not items:
            return {
                "titulo": "Ordens de Venda",
                "linhas": ["Nenhuma ordem de venda encontrada para o período."],
                "dados": root,
            }

        linhas = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            order = item.get("order_number") or "?"
            desc = item.get("description") or ""
            branch = item.get("branch") or ""
            date = item.get("date") or ""
            stage = item.get("stage") or ""

            parts = [f"OV {order}"]
            if branch:
                parts.append(f"Fil. {branch}")
            if date:
                parts.append(date)
            if stage:
                parts.append(stage)

            header = " · ".join(parts)
            line = f"{header}: {desc}".rstrip(": ") if desc else header
            linhas.append(line)

        if total is not None:
            linhas.append(f"Total: {total} ordem(ns) (página {root.get('page', 1)}).")

        return {
            "titulo": "Ordens de Venda",
            "linhas": linhas or ["Nenhuma ordem de venda encontrada."],
            "dados": {"total": total, "items": items[:12]},
        }

    def _present_items(self, items: list) -> dict:
        linhas = [f"A API retornou {len(items)} registro(s)."]

        stock_lines = []
        for item in items[:8]:
            if not isinstance(item, dict):
                continue

            if "warehouse" in item and "available_quantity" in item:
                stock_lines.append(
                    "Filial {branch}, armazém {warehouse}: atual {current}, disponível {available}, empenhada {committed}. Local: {location}.".format(
                        branch=item.get("branch"),
                        warehouse=item.get("warehouse"),
                        current=item.get("current_quantity"),
                        available=item.get("available_quantity"),
                        committed=item.get("committed_quantity"),
                        location=item.get("physical_location") or "não informado",
                    )
                )

        if stock_lines:
            linhas = stock_lines

        return {
            "titulo": "Resultado operacional",
            "linhas": linhas,
            "dados": {
                "items": items[:10],
            },
        }

    def _alias_dict(self, payload: dict, aliases: dict) -> dict:
        return {
            aliases.get(key, key): value
            for key, value in payload.items()
            if value is not None
        }

    def _label_collection(self, key: str) -> str:
        labels = {
            "guide": "Roteiro",
            "inspection": "Inspeção",
            "structure": "Estrutura",
            "customers": "Clientes",
            "suppliers": "Fornecedores",
        }

        return labels.get(key, key)

    def _total(self, value):
        if isinstance(value, dict):
            return value.get("total")

        return None


    def build_presentation(self, data) -> dict | None:
        root = self._unwrap_data(data)

        if isinstance(root, list) and root and isinstance(root[0], dict):
            return self._build_items_table(root, title="Consulta SQL")

        if not isinstance(root, dict):
            return None

        product = root.get("product")
        if isinstance(product, dict):
            return self._build_product_table(product, root)

        items = root.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            if "sale_number" in items[0] or "saleNumber" in items[0]:
                return self._build_lmp_table(items, root)

            if "order_number" in items[0]:
                return self._build_sale_orders_table(items, root)

            if "code" in items[0] and "description" in items[0]:
                return self._build_product_search_table(items, root)

            return self._build_items_table(items)

        stock = root.get("stock")
        if isinstance(stock, dict) and isinstance(stock.get("items"), list):
            return self._build_items_table(
                stock.get("items") or [],
                title="Estoque do produto",
            )

        parents = root.get("parents")
        if isinstance(parents, list) and parents:
            return self._build_items_table(parents, title="Produtos pai (onde é usado)")

        structure = root.get("structure")
        if isinstance(structure, dict) and isinstance(structure.get("items"), list):
            return self._build_items_table(
                structure["items"],
                title="Estrutura do produto",
            )

        return None

    def _build_product_table(self, product: dict, root: dict) -> dict:
        columns = [
            {"key": "campo", "label": "Campo"},
            {"key": "valor", "label": "Valor"},
        ]

        field_map = [
            ("code", "Código"),
            ("description", "Descrição"),
            ("type", "Tipo"),
            ("unit", "Unidade"),
            ("group_code", "Grupo"),
            ("active", "Ativo"),
            ("default_warehouse", "Armazém padrão"),
            ("last_purchase_price", "Último preço compra"),
            ("standard_cost", "Custo padrão"),
            ("last_revision_date", "Última revisão"),
            ("ncm_ipi_position", "NCM"),
        ]

        rows = [
            {"campo": label, "valor": product.get(key)}
            for key, label in field_map
            if product.get(key) is not None
        ]

        for key in ("guide", "inspection", "structure", "customers", "suppliers"):
            value = root.get(key)
            if isinstance(value, dict) and value.get("total") is not None:
                rows.append({"campo": self._label_collection(key), "valor": f"{value['total']} registro(s)"})

        return {
            "type": "table",
            "title": f"Produto {product.get('code', '')}",
            "columns": columns,
            "rows": rows,
        }

    def _build_lmp_table(self, items: list, root: dict) -> dict:
        columns = [
            {"key": "sale_number", "label": "OV"},
            {"key": "branch", "label": "Filial"},
            {"key": "listing_kind", "label": "Tipo"},
            {"key": "status", "label": "Status"},
            {"key": "sale_description", "label": "Descrição"},
        ]

        rows = []
        for item in items[:100]:
            if not isinstance(item, dict):
                continue
            rows.append({
                "sale_number": item.get("sale_number") or item.get("saleNumber"),
                "branch": item.get("branch"),
                "listing_kind": item.get("listing_kind") or item.get("listingKind"),
                "status": item.get("status") or item.get("engineering_status"),
                "sale_description": item.get("sale_description") or item.get("saleDescription"),
            })

        return {
            "type": "table",
            "title": f"LMPs ({root.get('total', len(rows))} registro(s))",
            "columns": columns,
            "rows": rows,
        }

    def _build_sale_orders_table(self, items: list, root: dict) -> dict:
        columns = [
            {"key": "order_number", "label": "Pedido"},
            {"key": "branch", "label": "Filial"},
            {"key": "description", "label": "Descrição"},
            {"key": "date", "label": "Data", "dataType": "date"},
            {"key": "stage", "label": "Etapa"},
        ]

        rows = [item for item in items[:100] if isinstance(item, dict)]

        return {
            "type": "table",
            "title": f"Ordens de Venda ({root.get('total', len(rows))} registro(s))",
            "columns": columns,
            "rows": rows,
        }

    def _build_product_search_table(self, items: list, root: dict) -> dict:
        columns = [
            {"key": "code", "label": "Código"},
            {"key": "description", "label": "Descrição"},
            {"key": "type", "label": "Tipo"},
            {"key": "unit", "label": "Unidade"},
        ]

        rows = [
            {"code": i.get("code"), "description": i.get("description"), "type": i.get("type"), "unit": i.get("unit")}
            for i in items[:100]
            if isinstance(i, dict)
        ]

        return {
            "type": "table",
            "title": f"Busca de produtos ({root.get('total', len(rows))} resultado(s))",
            "columns": columns,
            "rows": rows,
        }

    _COLUMN_TYPE_MAP = {
        "currency": (
            "valor", "preco", "price", "custo", "cost", "total", "revenue",
            "faturamento", "receita", "vlr", "vl_", "last_purchase_price",
            "standard_cost", "unit_price", "net_value", "gross_value",
        ),
        "percent": (
            "pct", "percent", "taxa", "rate", "margem", "margin", "otd",
            "giro", "eficiencia", "yield",
        ),
        "date": (
            "data", "date", "emissao", "criacao", "atualizacao", "inicio",
            "fim", "vencimento", "dt_", "created", "updated", "last_revision",
        ),
        "quantity": (
            "qtd", "quantidade", "qty", "quantity", "saldo", "disponivel",
            "reservado", "estoque", "volume", "current_quantity",
            "available_quantity", "committed_quantity", "reserved_quantity",
        ),
    }

    def _infer_column_type(self, key: str) -> str | None:
        lowered = key.lower()
        for data_type, tokens in self._COLUMN_TYPE_MAP.items():
            if any(token in lowered for token in tokens):
                return data_type
        return None

    def _enrich_column(self, key: str, label: str) -> dict:
        col = {"key": key, "label": label}
        data_type = self._infer_column_type(key)
        if data_type:
            col["dataType"] = data_type
        return col

    def _build_items_table(self, items: list, title: str = "Dados retornados") -> dict | None:
        if not items:
            return None

        first = next((item for item in items if isinstance(item, dict)), None)

        if not first:
            return None

        preferred_columns = [
            ("branch", "Filial"),
            ("warehouse", "Armazém"),
            ("product_code", "Produto"),
            ("current_quantity", "Qtd. atual"),
            ("available_quantity", "Qtd. disponível"),
            ("committed_quantity", "Qtd. empenhada"),
            ("reserved_quantity", "Qtd. reservada"),
            ("physical_location", "Localização"),
            ("cost_center", "Centro de custo"),
        ]

        columns = [
            self._enrich_column(key, label)
            for key, label in preferred_columns
            if key in first
        ]

        if not columns:
            columns = [
                self._enrich_column(key, self._humanize_key(key))
                for key in list(first.keys())[:12]
            ]

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": items[:100],
        }

    def _humanize_key(self, key: str) -> str:
        return str(key).replace("_", " ").strip().capitalize()

    def build_chart_presentation(self, data, *, path: str = "") -> dict | None:
        """Gera presentation tipo chart quando os dados são adequados para visualização gráfica."""
        root = self._unwrap_data(data)

        if not isinstance(root, dict):
            if isinstance(root, list) and root and isinstance(root[0], dict):
                return self._try_chart_from_rows(root)
            return None

        items = root.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            if self._is_stock_data(items[0]):
                return self._build_stock_chart(items)

            return self._try_chart_from_rows(items)

        if self._looks_like_kpi_response(root, path):
            return self._build_kpi_chart(root, path)

        return None

    def _is_stock_data(self, row: dict) -> bool:
        return "warehouse" in row and (
            "available_quantity" in row or "current_quantity" in row
        )

    def _build_stock_chart(self, items: list) -> dict | None:
        if len(items) < 2:
            return None

        chart_data = []
        for item in items[:20]:
            if not isinstance(item, dict):
                continue
            label = f"Fil.{item.get('branch', '?')}/{item.get('warehouse', '?')}"
            chart_data.append({
                "name": label,
                "Qtd. atual": item.get("current_quantity") or 0,
                "Disponível": item.get("available_quantity") or 0,
                "Empenhada": item.get("committed_quantity") or 0,
            })

        if not chart_data:
            return None

        return {
            "type": "chart",
            "title": "Estoque por filial/armazém",
            "chartType": "bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": ["Qtd. atual", "Disponível", "Empenhada"],
                "colors": ["#0ea5e9", "#10b981", "#f59e0b"],
                "legend": True,
            },
        }

    def _looks_like_kpi_response(self, root: dict, path: str) -> bool:
        kpi_paths = ("cpv", "otd", "inventory-turnover", "stock-value", "giro", "turnover", "kpi", "indicator")
        if any(token in path for token in kpi_paths):
            return True

        kpi_keys = ("value", "percentage", "current", "previous", "target", "meta")
        has_series = any(k in root for k in ("periods", "series", "history"))
        kpi_count = sum(1 for k in kpi_keys if k in root)
        return kpi_count >= 2 or (kpi_count >= 1 and has_series)

    def _build_kpi_chart(self, root: dict, path: str) -> dict | None:
        periods = root.get("periods") or root.get("series") or root.get("history")
        if isinstance(periods, list) and len(periods) >= 2:
            return {
                "type": "chart",
                "title": self._kpi_title(path),
                "chartType": "line",
                "data": periods[:24],
                "config": {
                    "xAxis": "period",
                    "legend": True,
                },
            }

        value = root.get("value") or root.get("percentage") or root.get("current")
        target = root.get("target") or root.get("meta")
        previous = root.get("previous") or root.get("anterior")
        unit = root.get("unit") or root.get("unidade") or ""

        if value is not None:
            cards = []
            trend = None
            delta = None

            if previous is not None:
                try:
                    diff = float(value) - float(previous)
                    if diff > 0:
                        trend = "up"
                        delta = f"+{self._format_num(diff)}{unit}"
                    elif diff < 0:
                        trend = "down"
                        delta = f"{self._format_num(diff)}{unit}"
                    else:
                        trend = "stable"
                except (ValueError, TypeError):
                    pass

            cards.append({
                "label": "Atual",
                "value": value,
                "unit": unit,
                "trend": trend,
                "delta": delta,
                "color": "#0ea5e9",
            })

            if target is not None:
                cards.append({
                    "label": "Meta",
                    "value": target,
                    "unit": unit,
                    "color": "#10b981",
                })

            if previous is not None:
                cards.append({
                    "label": "Anterior",
                    "value": previous,
                    "unit": unit,
                    "color": "#94a3b8",
                })

            if cards:
                return {
                    "type": "kpi",
                    "title": self._kpi_title(path),
                    "cards": cards,
                }

        return None

    def _format_num(self, value) -> str:
        try:
            num = float(value)
            if num == int(num):
                return str(int(num))
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return str(value)

    def _kpi_title(self, path: str) -> str:
        if "cpv" in path:
            return "CPV — Custo de Produção Vendido"
        if "otd" in path:
            return "OTD — On Time Delivery"
        if "inventory-turnover" in path:
            return "Giro de Estoque (IDD)"
        if "stock-value" in path:
            return "Valor Total de Estoque"
        return "Indicador"

    def _try_chart_from_rows(self, rows: list) -> dict | None:
        if len(rows) < 2 or not isinstance(rows[0], dict):
            return None

        first = rows[0]
        numeric_keys = [k for k, v in first.items() if isinstance(v, (int, float))]
        string_keys = [k for k, v in first.items() if isinstance(v, str)]

        if not numeric_keys or not string_keys:
            return None

        if len(rows) > 12:
            return None

        return {
            "type": "chart",
            "title": "Visualização dos dados",
            "chartType": "bar",
            "data": rows[:20],
            "config": {
                "xAxis": string_keys[0],
                "yAxis": numeric_keys[:3],
                "legend": len(numeric_keys) > 1,
            },
        }
