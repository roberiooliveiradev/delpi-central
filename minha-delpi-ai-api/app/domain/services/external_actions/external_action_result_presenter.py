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

        items = root.get("items") if isinstance(root, dict) else None

        if isinstance(items, list):
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

        if not isinstance(root, dict):
            return None

        product = root.get("product")
        if isinstance(product, dict):
            return {
                "type": "json",
                "title": f"Produto {product.get('code') or ''}".strip(),
                "data": self.present(data),
            }

        items = root.get("items")
        if isinstance(items, list) and items:
            return self._build_items_table(items)

        stock = root.get("stock")
        if isinstance(stock, dict) and isinstance(stock.get("items"), list):
            return self._build_items_table(
                stock.get("items") or [],
                title="Estoque do produto",
            )

        return None

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
            {"key": key, "label": label}
            for key, label in preferred_columns
            if key in first
        ]

        if not columns:
            columns = [
                {"key": key, "label": self._humanize_key(key)}
                for key in list(first.keys())[:12]
            ]

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": items[:50],
        }

    def _humanize_key(self, key: str) -> str:
        return str(key).replace("_", " ").strip().capitalize()
