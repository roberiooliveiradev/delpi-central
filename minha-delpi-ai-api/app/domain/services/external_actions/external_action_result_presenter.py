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

    def present(self, data, *, path: str = "") -> dict:
        error = self._detect_api_error(data)
        if error:
            return error

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
            if not items:
                title = self._infer_items_title([], path) or "Consulta"
                return {
                    "titulo": title,
                    "linhas": [f"Nenhum registro encontrado para esta consulta."],
                    "dados": root,
                }

            if items and isinstance(items[0], dict) and "sale_number" in items[0]:
                return self._present_lmp_page(root)

            if items and isinstance(items[0], dict) and "order_number" in items[0]:
                return self._present_sale_orders(root, items)

            title = self._infer_items_title(items, path)
            if items and isinstance(items[0], dict) and "code" in items[0] and "description" in items[0]:
                return self._present_product_search(root, items, title=title)

            return self._present_items(items, title=title)

        if isinstance(root, dict) and self._looks_like_kpi_response(root, path):
            kpi = self._build_kpi_chart(root, path)
            if kpi:
                return {
                    "titulo": kpi.get("title", "Indicador"),
                    "linhas": [f"{kpi.get('title', 'Indicador')}: veja os dados abaixo."],
                    "dados": root,
                    "apresentacao": kpi,
                }

        if isinstance(root, dict) and root:
            fallback = self._present_dict_fallback(root, path)
            if fallback:
                return fallback

        return {
            "titulo": self._fallback_title(path) or "Resultado da API",
            "linhas": ["A API retornou dados autorizados para a consulta."],
            "dados": root,
        }

    def _fallback_title(self, path: str) -> str | None:
        if not path:
            return None
        lowered = path.lower()
        if "dashboard" in lowered:
            if "lmp" in lowered:
                return "Dashboard de LMPs"
            return "Dashboard"
        if "/commercial/" in lowered:
            return "Indicador Comercial"
        if "/financial/" in lowered or "/finacial/" in lowered:
            return "Indicador Financeiro"
        if "/production/" in lowered:
            return "Indicador de Produção"
        if "/hr/" in lowered:
            return "Indicador de RH"
        if "/quality/" in lowered:
            return "Indicador de Qualidade"
        return None

    def _present_dict_fallback(self, root: dict, path: str) -> dict | None:
        if not root:
            return None

        linhas = []
        title = self._fallback_title(path) or "Resultado da consulta"

        for key, value in root.items():
            if isinstance(value, dict):
                sub_items = [f"{k}: {v}" for k, v in value.items()]
                label = self._humanize_key(key)
                linhas.append(f"**{label}:** {', '.join(sub_items[:8])}")
            elif isinstance(value, list) and value:
                linhas.append(f"**{self._humanize_key(key)}:** {len(value)} item(ns)")
            elif value is not None:
                linhas.append(f"**{self._humanize_key(key)}:** {value}")

        if linhas:
            return {
                "titulo": title,
                "linhas": linhas[:12],
                "dados": root,
            }

        return None

    def _infer_items_title(self, items: list, path: str) -> str | None:
        if not path:
            if items and isinstance(items[0], dict):
                if "level" in items[0] or "quantity" in items[0]:
                    if "code" in items[0]:
                        return "Estrutura do produto"
                if "branch" in items[0] or "warehouse" in items[0]:
                    return "Estoque do produto"
            return None

        lowered = path.lower()
        if "/structure" in lowered:
            return "Estrutura do produto"
        if "/parents" in lowered:
            return "Produtos pai (onde é usado)"
        if "/stock" in lowered:
            return "Estoque do produto"
        if "/suppliers" in lowered:
            return "Fornecedores do produto"
        if "/customers" in lowered:
            return "Clientes do produto"
        if "/guide" in lowered:
            return "Roteiro do produto"
        if "/inspection" in lowered:
            return "Inspeção do produto"
        if "/internal-movements" in lowered:
            return "Movimentações internas"
        if "/inbound-invoice" in lowered:
            return "Notas fiscais de entrada"
        if "/outbound-invoice" in lowered:
            return "Notas fiscais de saída"
        if "/purchases" in lowered:
            return "Compras do produto"
        if "/sales" in lowered:
            return "Vendas do produto"
        if "/lmp" in lowered or "/production" in lowered:
            return "Lista de LMPs"
        if "/sale-order" in lowered or "/orders" in lowered:
            return "Ordens de venda"
        return None

    def _detect_api_error(self, data) -> dict | None:
        if not isinstance(data, dict):
            return None

        detail = data.get("detail") or data.get("error") or data.get("message")
        status = data.get("status_code") or data.get("status")

        is_error_detail = isinstance(detail, str) and detail.lower() in (
            "not found", "unauthorized", "forbidden", "internal server error",
            "bad request", "service unavailable",
        )

        is_error_status = isinstance(status, int) and status >= 400

        if not is_error_detail and not is_error_status:
            if isinstance(data.get("success"), bool) and not data["success"]:
                msg = str(data.get("message") or "Erro desconhecido na API.")
                return {
                    "titulo": "Erro na consulta",
                    "linhas": [msg],
                    "dados": None,
                }
            return None

        error_messages = {
            "not found": "O recurso solicitado não foi encontrado. "
                         "O código informado pode não existir ou não ter dados cadastrados.",
            "unauthorized": "Sem autorização para acessar este recurso.",
            "forbidden": "Acesso negado ao recurso solicitado.",
        }

        if isinstance(detail, str):
            msg = error_messages.get(detail.lower(), f"A API retornou um erro: {detail}")
        else:
            msg = f"A API retornou erro (status {status})."

        return {
            "titulo": "Erro na consulta",
            "linhas": [msg],
            "dados": None,
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

        detail_list = self._extract_product_detail_list(root)

        if detail_list:
            return self._present_product_with_details(product_summary, detail_list, root)

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

    def _extract_product_detail_list(self, root: dict) -> list | None:
        detail_keys = (
            "prices", "stock", "purchases", "sales", "billing",
            "suppliers", "customers", "movements", "invoices",
            "open_orders", "items",
        )
        for key in detail_keys:
            value = root.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        return None

    def _present_product_with_details(
        self, product_summary: dict, detail_list: list, root: dict
    ) -> dict:
        code = product_summary.get("code") or ""
        desc = product_summary.get("description") or ""

        linhas = [f"Produto {code}: {desc}."]

        for item in detail_list[:5]:
            preview = ", ".join(
                f"{k}={v}" for k, v in list(item.items())[:6] if v is not None
            )
            linhas.append(f"- {preview}")

        if len(detail_list) > 5:
            linhas.append(f"… e mais {len(detail_list) - 5} registro(s).")

        all_keys = {}
        for item in detail_list[:100]:
            for k in item:
                if k not in all_keys:
                    all_keys[k] = True

        columns = [self._enrich_column(k, self._humanize_key(k)) for k in all_keys]
        rows = detail_list[:100]

        title = f"Dados do produto {code}"
        if "prices" in root:
            title = f"Preços do produto {code}"
        elif "stock" in root:
            title = f"Estoque do produto {code}"
        elif "purchases" in root:
            title = f"Compras do produto {code}"
        elif "sales" in root or "billing" in root:
            title = f"Vendas do produto {code}"
        elif "open_orders" in root:
            title = f"Pedidos em aberto do produto {code}"

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": {"product": product_summary, "items": rows},
            "apresentacao": {
                "type": "table",
                "title": title,
                "columns": columns,
                "rows": rows,
            },
        }

    def _present_lmp_page(self, root: dict) -> dict | None:
        items = root.get("items")

        if not isinstance(items, list):
            return None

        if items and isinstance(items[0], dict) and "sale_number" not in items[0] and "saleNumber" not in items[0]:
            return None

        if not items:
            return None

        total = root.get("total")
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

    def _present_product_search(self, root: dict, items: list, *, title: str | None = None) -> dict:
        titulo = title or "Busca de produtos"
        total = root.get("total")
        is_hierarchy = titulo and ("pai" in titulo.lower() or "estrutura" in titulo.lower())

        if not items:
            return {
                "titulo": titulo,
                "linhas": ["Nenhum produto encontrado para a busca."],
                "dados": root,
            }

        linhas = []

        for item in items[:25]:
            if not isinstance(item, dict):
                continue

            code = item.get("code") or "?"
            desc = item.get("description") or ""
            tipo = item.get("type") or ""
            unit = item.get("unit") or ""
            qty = item.get("quantity")
            level = item.get("level")

            parts = [f"**{code}**"]
            if desc:
                parts.append(desc)
            if tipo:
                parts.append(f"({tipo})")
            if unit:
                parts.append(f"[{unit}]")

            line = " — ".join(parts[:2]) + (f" {parts[2]}" if len(parts) > 2 else "") + (f" {parts[3]}" if len(parts) > 3 else "")

            if is_hierarchy:
                extras = []
                if qty is not None:
                    extras.append(f"Qtd: {qty}")
                if level is not None:
                    extras.append(f"Nível: {level}")
                if extras:
                    line += f" | {', '.join(extras)}"

            linhas.append(line)

        if total is not None and total > len(items):
            linhas.append(f"\nTotal encontrado: {total} produto(s).")

        return {
            "titulo": titulo,
            "linhas": linhas or ["Nenhum produto encontrado."],
            "dados": {"total": total, "items": [{"code": i.get("code"), "description": i.get("description"), "type": i.get("type"), "unit": i.get("unit")} for i in items[:25]]},
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

    def _present_items(self, items: list, *, title: str | None = None) -> dict:
        titulo = title or "Resultado operacional"
        linhas = [f"A API retornou {len(items)} registro(s)."]

        detail_lines = []
        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            if "warehouse" in item and "available_quantity" in item:
                if not title:
                    titulo = "Estoque do produto"
                detail_lines.append(
                    "Filial {branch}, armazém {warehouse}: atual {current}, disponível {available}, empenhada {committed}. Local: {location}.".format(
                        branch=item.get("branch"),
                        warehouse=item.get("warehouse"),
                        current=item.get("current_quantity"),
                        available=item.get("available_quantity"),
                        committed=item.get("committed_quantity"),
                        location=item.get("physical_location") or "não informado",
                    )
                )
            elif "supplier_name" in item or "supplier_code" in item:
                name = item.get("supplier_name") or item.get("supplier_code") or "?"
                lead = item.get("registered_lead_time_days") or item.get("real_avg_lead_time_days")
                price = item.get("last_price")
                parts = [f"**{name}**"]
                if lead is not None:
                    parts.append(f"Lead time: {lead}d")
                if price is not None:
                    parts.append(f"Últ. preço: R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                detail_lines.append(" | ".join(parts))
            elif "customer_name" in item or "customer_code" in item:
                name = item.get("customer_name") or item.get("customer_code") or "?"
                detail_lines.append(f"**{name}**")
            else:
                label_keys = ["name", "description", "supplier_name", "customer_name", "code", "number"]
                label = next((str(item[k]) for k in label_keys if item.get(k)), None)
                if label:
                    detail_lines.append(label)

        if detail_lines:
            linhas = detail_lines

        return {
            "titulo": titulo,
            "linhas": linhas,
            "dados": {
                "items": items[:15],
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


    def build_presentation(self, data, *, path: str = "") -> dict | None:
        root = self._unwrap_data(data)

        if isinstance(root, list) and root and isinstance(root[0], dict):
            return self._build_items_table(root, title="Consulta SQL")

        if not isinstance(root, dict):
            return None

        product = root.get("product")
        if isinstance(product, dict):
            detail_list = self._extract_product_detail_list(root)
            if detail_list:
                return self._build_product_detail_table(product, detail_list, root)
            return self._build_product_table(product, root)

        items = root.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            if "sale_number" in items[0] or "saleNumber" in items[0]:
                return self._build_lmp_table(items, root)

            if "order_number" in items[0]:
                return self._build_sale_orders_table(items, root)

            title = self._infer_items_title(items, path)

            if "code" in items[0] and "description" in items[0]:
                if len(items) >= 3:
                    return self._build_product_search_table(items, root, title=title)
                return self._build_product_search_table(items, root, title=title)

            if len(items) >= 2 or self._is_tabular_data(items[0]):
                return self._build_items_table(items, title=title)

            return None

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

    def _build_product_detail_table(self, product: dict, detail_list: list, root: dict) -> dict:
        code = product.get("code", "")

        title = f"Dados do produto {code}"
        if "prices" in root:
            title = f"Preços do produto {code}"
        elif "stock" in root:
            title = f"Estoque do produto {code}"
        elif "purchases" in root:
            title = f"Compras do produto {code}"
        elif "sales" in root or "billing" in root:
            title = f"Vendas do produto {code}"
        elif "open_orders" in root:
            title = f"Pedidos em aberto do produto {code}"

        all_keys = {}
        for item in detail_list[:100]:
            for k in item:
                if k not in all_keys:
                    all_keys[k] = True

        columns = [self._enrich_column(k, self._humanize_key(k)) for k in all_keys]
        rows = detail_list[:100]

        return {
            "type": "table",
            "title": title,
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

    def _flatten_nested_field(self, items: list) -> list:
        """Converte campos complexos (list/dict) em texto legível para tabela."""
        flattened = []
        for item in items:
            if not isinstance(item, dict):
                flattened.append(item)
                continue
            row = {}
            for k, v in item.items():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    codes = [sub.get("code") or sub.get("description") or str(sub) for sub in v[:5]]
                    row[k] = " → ".join(codes)
                    if len(v) > 5:
                        row[k] += f" (+{len(v) - 5})"
                elif isinstance(v, dict):
                    row[k] = v.get("code") or v.get("description") or str(v)
                else:
                    row[k] = v
            flattened.append(row)
        return flattened

    def _build_product_search_table(self, items: list, root: dict, *, title: str | None = None) -> dict:
        first = items[0] if items else {}
        has_extra = any(k in first for k in ("quantity", "level", "lot_quantity"))

        if has_extra:
            flat_items = self._flatten_nested_field(items[:100])
            first_flat = flat_items[0] if flat_items else {}
            all_keys = {}
            for item in flat_items:
                for k in item:
                    if k not in all_keys:
                        all_keys[k] = True
            columns = [self._enrich_column(k, self._humanize_key(k)) for k in all_keys]
            rows = flat_items
        else:
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

        table_title = title or f"Busca de produtos ({root.get('total', len(rows))} resultado(s))"

        return {
            "type": "table",
            "title": table_title,
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

    _STOCK_PREFERRED_COLUMNS = [
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

    _SUPPLIER_PREFERRED_COLUMNS = [
        ("supplier_code", "Cód. fornecedor"),
        ("supplier_name", "Fornecedor"),
        ("supplier_part_number", "Part number"),
        ("last_price", "Últ. preço"),
        ("last_price_date", "Data últ. preço"),
        ("real_avg_lead_time_days", "Lead time médio (dias)"),
        ("registered_lead_time_days", "Lead time cadastrado"),
        ("real_lead_time_sample_size", "Amostras"),
    ]

    _CUSTOMER_PREFERRED_COLUMNS = [
        ("customer_code", "Cód. cliente"),
        ("customer_name", "Cliente"),
        ("customer_store", "Loja"),
        ("last_sale_date", "Data últ. venda"),
        ("last_sale_price", "Últ. preço venda"),
        ("total_quantity", "Qtd. total"),
        ("total_value", "Valor total"),
    ]

    _GUIDE_PREFERRED_COLUMNS = [
        ("sequence", "Sequência"),
        ("step", "Etapa"),
        ("step_description", "Descrição etapa"),
        ("machine_code", "Cód. máquina"),
        ("machine_name", "Máquina"),
        ("setup_time", "Tempo setup"),
        ("operation_time", "Tempo operação"),
    ]

    _INSPECTION_PREFERRED_COLUMNS = [
        ("inspection_type", "Tipo inspeção"),
        ("sequence", "Sequência"),
        ("characteristic", "Característica"),
        ("specification", "Especificação"),
        ("method", "Método"),
        ("frequency", "Frequência"),
        ("result", "Resultado"),
    ]

    _MOVEMENT_PREFERRED_COLUMNS = [
        ("movement_date", "Data"),
        ("operation", "Operação"),
        ("origin_warehouse", "Armazém origem"),
        ("destination_warehouse", "Armazém destino"),
        ("quantity", "Quantidade"),
        ("document", "Documento"),
        ("lot", "Lote"),
    ]

    _INVOICE_PREFERRED_COLUMNS = [
        ("invoice_number", "Nº nota"),
        ("invoice_series", "Série"),
        ("supplier_name", "Fornecedor"),
        ("customer_name", "Cliente"),
        ("issue_date", "Data emissão"),
        ("quantity", "Quantidade"),
        ("unit_price", "Preço unitário"),
        ("total_value", "Valor total"),
    ]

    _PRICE_PREFERRED_COLUMNS = [
        ("table_code", "Cód. tabela"),
        ("table_description", "Tabela"),
        ("sale_price", "Preço venda"),
        ("max_price", "Preço máx."),
        ("discount_value", "Desconto"),
        ("discount_percent", "% Desconto"),
    ]

    def _build_items_table(self, items: list, title: str = "Dados retornados") -> dict | None:
        if not items:
            return None

        first = next((item for item in items if isinstance(item, dict)), None)

        if not first:
            return None

        is_stock = "current_quantity" in first or "available_quantity" in first
        is_invoice = "invoice_number" in first
        is_guide = "step" in first and "sequence" in first
        is_inspection = "inspection_type" in first or ("characteristic" in first and "specification" in first)
        is_movement = "origin_warehouse" in first or "destination_warehouse" in first
        is_price = "table_code" in first or "sale_price" in first
        is_supplier = ("supplier_name" in first or "supplier_code" in first) and not is_invoice
        is_customer = ("customer_name" in first or "customer_code" in first) and not is_invoice

        preferred = None
        if is_stock:
            preferred = self._STOCK_PREFERRED_COLUMNS
        elif is_invoice:
            preferred = self._INVOICE_PREFERRED_COLUMNS
        elif is_guide:
            preferred = self._GUIDE_PREFERRED_COLUMNS
        elif is_inspection:
            preferred = self._INSPECTION_PREFERRED_COLUMNS
        elif is_movement:
            preferred = self._MOVEMENT_PREFERRED_COLUMNS
        elif is_price:
            preferred = self._PRICE_PREFERRED_COLUMNS
        elif is_supplier:
            preferred = self._SUPPLIER_PREFERRED_COLUMNS
        elif is_customer:
            preferred = self._CUSTOMER_PREFERRED_COLUMNS

        if preferred:
            columns = [
                self._enrich_column(key, label)
                for key, label in preferred
                if key in first
            ]
        else:
            columns = []

        if not columns:
            flat_items = self._flatten_nested_field(items[:100])
            first_flat = flat_items[0] if flat_items else first
            columns = [
                self._enrich_column(key, self._humanize_key(key))
                for key in list(first_flat.keys())[:15]
                if not isinstance(first_flat.get(key), (list, dict))
            ]
            col_keys = {c["key"] for c in columns}
            rows = [
                {k: item.get(k) for k in col_keys}
                for item in flat_items
                if isinstance(item, dict)
            ]
        else:
            col_keys = {c["key"] for c in columns}
            rows = [
                {k: item.get(k) for k in col_keys}
                for item in items[:100]
                if isinstance(item, dict)
            ]

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": rows,
        }

    _KEY_LABELS = {
        "code": "Código",
        "description": "Descrição",
        "type": "Tipo",
        "unit": "Unidade",
        "quantity": "Quantidade",
        "level": "Nível",
        "parents": "Pais",
        "lot_quantity": "Qtd. lote",
        "branch": "Filial",
        "warehouse": "Armazém",
        "product_code": "Produto",
        "product_description": "Descrição produto",
        "current_quantity": "Qtd. atual",
        "available_quantity": "Qtd. disponível",
        "committed_quantity": "Qtd. empenhada",
        "reserved_quantity": "Qtd. reservada",
        "physical_location": "Localização",
        "cost_center": "Centro de custo",
        "price": "Preço",
        "cost": "Custo",
        "total": "Total",
        "status": "Status",
        "date": "Data",
        "supplier": "Fornecedor",
        "supplier_code": "Cód. fornecedor",
        "supplier_name": "Fornecedor",
        "supplier_store": "Loja",
        "supplier_part_number": "Part number",
        "customer": "Cliente",
        "customer_code": "Cód. cliente",
        "customer_name": "Cliente",
        "customer_store": "Loja",
        "registered_lead_time_days": "Lead time (dias)",
        "real_avg_lead_time_days": "Lead time real (média)",
        "real_min_lead_time_days": "Lead time mín.",
        "real_max_lead_time_days": "Lead time máx.",
        "real_lead_time_sample_size": "Amostras",
        "last_price": "Últ. preço",
        "last_price_date": "Data últ. preço",
        "catalog_code": "Cód. catálogo",
        "barcode": "Cód. barras",
        "sale_price": "Preço venda",
        "max_price": "Preço máx.",
        "discount_value": "Desconto",
        "discount_percent": "% Desconto",
        "table_code": "Cód. tabela",
        "table_description": "Tabela",
        "order_number": "Nº pedido",
        "issue_date": "Data emissão",
        "delivery_date": "Data entrega",
        "invoice_number": "Nº nota",
        "invoice_series": "Série",
        "operation": "Operação",
        "movement_date": "Data movimentação",
        "origin_warehouse": "Armazém origem",
        "destination_warehouse": "Armazém destino",
        "last_sale_date": "Data últ. venda",
        "last_purchase_date": "Data últ. compra",
        "total_quantity": "Qtd. total",
        "total_value": "Valor total",
        "average_price": "Preço médio",
        "state": "Estado",
        "opening_date": "Data abertura",
        "sequence": "Sequência",
        "step": "Etapa",
        "step_description": "Descrição etapa",
        "inspection_type": "Tipo inspeção",
        "result": "Resultado",
        "approved": "Aprovado",
        "rejected": "Rejeitado",
        "lot": "Lote",
        "lot_quantity": "Qtd. lote",
    }

    def _humanize_key(self, key: str) -> str:
        if key in self._KEY_LABELS:
            return self._KEY_LABELS[key]
        return str(key).replace("_", " ").strip().capitalize()

    _NO_CHART_PATHS = (
        "/suppliers", "/customers", "/structure", "/parents",
        "/guide", "/inspection", "/search",
        "/purchases", "/sales", "/internal-movements",
        "/inbound-invoice", "/outbound-invoice", "/prices",
    )

    def build_chart_presentation(self, data, *, path: str = "", force: bool = False) -> dict | None:
        """Gera presentation tipo chart APENAS quando dados são naturalmente visuais."""
        if not force:
            lowered_path = (path or "").lower()
            if any(token in lowered_path for token in self._NO_CHART_PATHS):
                return None

        root = self._unwrap_data(data)

        if not isinstance(root, dict):
            if isinstance(root, list) and root and isinstance(root[0], dict):
                return self._try_chart_from_rows(root, force=force)
            return None

        items = root.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            if self._is_stock_data(items[0]):
                return self._build_stock_chart(items)

            return self._try_chart_from_rows(items, force=force)

        if self._looks_like_kpi_response(root, path):
            return self._build_kpi_chart(root, path)

        return None

    def _is_tabular_data(self, row: dict) -> bool:
        """Dados que naturalmente beneficiam de apresentação em tabela mesmo com 1 registro."""
        tabular_markers = [
            "warehouse", "current_quantity", "available_quantity",
            "supplier_code", "supplier_name", "customer_code", "customer_name",
            "table_code", "sale_price", "invoice_number",
            "order_number", "sale_number",
            "step", "sequence", "inspection_type", "characteristic",
            "origin_warehouse", "destination_warehouse", "movement_date",
        ]
        return any(k in row for k in tabular_markers)

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
        kpi_paths = (
            "cpv", "otd", "inventory-turnover", "stock-value", "giro",
            "turnover", "kpi", "indicator", "snapshot",
            "ebitda", "pmr", "pdi", "completion",
            "closing-rate", "new-clients", "new-business",
            "depreciation", "labor_cost", "production_cost",
            "effectiveness", "delivery",
        )
        if any(token in path for token in kpi_paths):
            return True

        kpi_keys = ("value", "percentage", "current", "previous", "target", "meta")
        has_series = any(k in root for k in ("periods", "series", "history"))
        kpi_count = sum(1 for k in kpi_keys if k in root)
        if kpi_count >= 2 or (kpi_count >= 1 and has_series):
            return True

        has_nested = any(isinstance(v, (dict, list)) for v in root.values())
        if not root.get("items") and not has_nested and len(root) <= 8:
            numeric_count = sum(1 for v in root.values() if isinstance(v, (int, float)))
            if numeric_count >= 2:
                return True

        return False

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

        cards = self._build_generic_kpi_cards(root, path)
        if cards:
            return {
                "type": "kpi",
                "title": self._kpi_title(path),
                "cards": cards,
            }

        return None

    def _build_generic_kpi_cards(self, root: dict, path: str) -> list | None:
        colors = ["#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
        cards = []
        idx = 0
        for key, val in root.items():
            if not isinstance(val, (int, float)):
                continue
            cards.append({
                "label": self._humanize_key(key),
                "value": val,
                "unit": "%" if "pct" in key or "percent" in key or "rate" in key else "",
                "color": colors[idx % len(colors)],
            })
            idx += 1
            if idx >= 6:
                break
        return cards if len(cards) >= 2 else None

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
        if "closing-rate" in path:
            return "Taxa de Conversão de Vendas"
        if "ebitda" in path:
            return "EBITDA"
        if "pmr" in path:
            return "PMR — Prazo Médio de Recebimento"
        if "fixed_cost" in path:
            return "Custo Fixo"
        if "new-clients" in path:
            return "Novos Clientes"
        if "new-business" in path:
            return "Novos Negócios"
        if "snapshot" in path:
            return "Indicadores de RH"
        if "pdi" in path:
            return "PDIs Ativos"
        if "completion" in path:
            return "Avaliações de Desempenho"
        if "depreciation" in path:
            return "Depreciação"
        if "labor_cost" in path or "direct_labor" in path:
            return "Custo de Mão de Obra"
        if "production_cost" in path:
            return "Custo de Produção"
        if "effectiveness" in path or "oee" in path:
            return "OEE — Eficiência de Equipamentos"
        if "delivery" in path:
            return "OTD — Entrega no Prazo"
        if "lmp" in path:
            return "Dashboard de LMPs"
        if "/commercial/" in path:
            return "Indicador Comercial"
        if "/financial/" in path or "/finacial/" in path:
            return "Indicador Financeiro"
        if "/production/" in path:
            return "Indicador de Produção"
        if "/hr/" in path:
            return "Indicador de RH"
        if "/quality/" in path:
            return "Indicador de Qualidade"
        return "Indicador"

    _CHART_WORTHY_NUMERIC_KEYS = {
        "quantity", "value", "total", "amount", "price", "cost",
        "revenue", "count", "percentage", "rate", "margin",
        "qtd", "valor", "preco", "custo", "receita", "faturamento",
        "saldo", "volume", "peso", "weight",
    }

    def _try_chart_from_rows(self, rows: list, *, force: bool = False) -> dict | None:
        """Gera gráfico APENAS quando os dados são naturalmente visuais (ou force=True)."""
        if len(rows) < 2 or not isinstance(rows[0], dict):
            return None

        if not force and len(rows) > 12:
            return None

        first = rows[0]
        numeric_keys = [k for k, v in first.items() if isinstance(v, (int, float))]
        string_keys = [k for k, v in first.items() if isinstance(v, str)]

        if not numeric_keys or not string_keys:
            return None

        if force:
            chart_numeric = numeric_keys[:3]
        else:
            chart_numeric = [
                k for k in numeric_keys
                if any(token in k.lower() for token in self._CHART_WORTHY_NUMERIC_KEYS)
            ]
            if not chart_numeric:
                return None

        label_key = string_keys[0]
        labels = [str(r.get(label_key, "")) for r in rows[:12]]
        if len(set(labels)) < 2:
            return None

        return {
            "type": "chart",
            "title": "Visualização dos dados",
            "chartType": "bar",
            "data": rows[:12],
            "config": {
                "xAxis": label_key,
                "yAxis": chart_numeric[:3],
                "legend": len(chart_numeric) > 1,
            },
        }
