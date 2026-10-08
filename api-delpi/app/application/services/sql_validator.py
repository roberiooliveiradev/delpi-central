# app/application/services/sql_validator.py
import re
import json
import os
from pathlib import Path
from app.utils.logger import log_error, log_info


class SqlValidator:
    """
    Validador SQL seguro para SQL Server (Protheus).

    Permite:
    - DECLARE (variáveis escalares)
    - DECLARE @T TABLE (...) (controlado)
    - SET @X = literal | @Y
    - SELECT simples ou múltiplos SELECTs
    - WITH / CTE (inclusive múltiplas CTEs)
      -> nomes de CTE NÃO precisam estar na whitelist

    Bloqueia:
    - DDL / DML (inclui SELECT INTO)
    - EXEC / TRANSACTIONS
    - SETs perigosos
    """

    BANNED_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "CREATE", "TRUNCATE", "MERGE", "EXEC",
        "GRANT", "REVOKE",
        "BEGIN", "COMMIT", "ROLLBACK",
        "INTO",
    ]

    MAX_SELECTS = 10

    @staticmethod
    def skip_table_whitelist() -> bool:
        """Temporary bypass of physical-table allowlist (SELECT-only still enforced)."""
        raw = os.getenv("DATA_SQL_SKIP_TABLE_WHITELIST", "").strip().lower()
        return raw in {"1", "true", "yes", "on"}

    def __init__(self):
        self.allowed_tables = self._load_allowed_tables()

    # ------------------------------------------------------------------
    # 🔹 Config
    # ------------------------------------------------------------------
    def _load_allowed_tables(self) -> set[str]:
        try:
            configured_path = os.getenv("ALLOWED_TABLES_PATH")

            config_path = (
                Path(configured_path)
                if configured_path
                else Path(__file__).resolve().parents[2] / "config" / "allowed_tables.json"
            )

            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {t.upper() for t in data.get("allowed_tables", [])}
        except Exception as e:
            log_error(f"[SQL_VALIDATOR] Erro ao carregar allowed_tables.json: {e}")
            raise RuntimeError("Erro ao carregar whitelist de tabelas")

    # ------------------------------------------------------------------
    # 🔹 Remove comentários SQL (robusto)
    # ------------------------------------------------------------------
    def _strip_sql_comments(self, sql: str) -> str:
        """
        Remove TODOS os comentários SQL:
        - -- comentário
        - /* comentário */
        Preserva conteúdo dentro de strings.
        """
        result = []
        i = 0
        in_string = False
        length = len(sql)

        while i < length:
            ch = sql[i]
            next_ch = sql[i + 1] if i + 1 < length else ""

            # controle de strings
            if ch == "'":
                in_string = not in_string
                result.append(ch)
                i += 1
                continue

            if not in_string:
                # comentário --
                if ch == "-" and next_ch == "-":
                    i += 2
                    while i < length and sql[i] not in ("\n", "\r"):
                        i += 1
                    continue

                # comentário /* */
                if ch == "/" and next_ch == "*":
                    i += 2
                    while i + 1 < length and not (sql[i] == "*" and sql[i + 1] == "/"):
                        i += 1
                    i += 2
                    continue

            result.append(ch)
            i += 1

        return "".join(result)

    # ------------------------------------------------------------------
    # 🔹 Extrair nomes de CTEs
    # ------------------------------------------------------------------
    # Palavras que encerram a cláusula de fontes de dados (FROM/JOIN...ON)
    # em um mesmo nível de parênteses. Usado pelo scanner de table sources.
    _CLAUSE_ENDERS = {
        "WHERE", "GROUP", "ORDER", "HAVING",
        "UNION", "INTERSECT", "EXCEPT",
        "OPTION", "FOR",
    }

    # ------------------------------------------------------------------
    # 🔹 Resolução fail-closed de fontes físicas (S0)
    # ------------------------------------------------------------------
    # S0 não é um parser T-SQL. A gramática de fonte suportada é mínima:
    #   FROM/JOIN <token simples>   → validado contra allowlist / CTE / @var
    #   FROM/JOIN ( <subquery> )    → fontes internas validadas pelo próprio
    #                                 scan global de FROM/JOIN
    # Qualquer outra forma (identificador bracketed/quoted, vírgula na
    # cláusula de fontes, CROSS/OUTER APPLY, qualificação de schema/DB) é
    # rejeitada até que parsing estrutural exista (S1).
    def _resolve_single_source(self, sql_up: str, pos: int, cte_names: set[str]) -> None:
        n = len(sql_up)
        i = pos
        while i < n and sql_up[i] in " \t\r\n":
            i += 1
        if i >= n:
            raise PermissionError(
                "Fonte de dados ausente após FROM/JOIN."
            )

        ch = sql_up[i]

        if ch == "(":
            # Derived table / subquery: fontes internas são validadas pelos
            # próprios matches FROM/JOIN do scan global.
            return

        if ch in "[\"":
            raise PermissionError(
                "Sintaxe de fonte de dados não suportada pelo validador "
                "read-only (identificador delimitado)."
            )

        m = re.match(r"[A-Z0-9_@#]+", sql_up[i:])
        if not m:
            raise PermissionError(
                "Sintaxe de fonte de dados não suportada pelo validador "
                "read-only."
            )

        name = m.group(0)
        i += len(name)

        # S0 não suporta qualificação de objetos (schema/database/servidor
        # ou delimitadores pendentes). T-SQL permite whitespace em nomes
        # multipartes, então a continuação é checada após espaços também.
        if i < n and sql_up[i] in ".[\"":
            raise PermissionError(
                "Qualificação de objeto não é suportada pelo validador "
                "read-only."
            )
        j = i
        while j < n and sql_up[j] in " \t\r\n":
            j += 1
        if j < n and sql_up[j] == ".":
            raise PermissionError(
                "Qualificação de objeto não é suportada pelo validador "
                "read-only."
            )

        if name.startswith("@"):
            # Variável de tabela local — já governada pela validação de DECLARE.
            return

        if name in cte_names:
            return

        if name not in self.allowed_tables:
            raise PermissionError(
                f"Tabela '{name}' não autorizada (fora da whitelist)."
            )

    def _validate_table_sources(self, sql_up: str, cte_names: set[str]) -> None:
        """Valida TODAS as fontes físicas — fail closed.

        Regras S0:
          - toda fonte FROM/JOIN deve resolver para allowlist/CTE/@var;
          - vírgula dentro de cláusula de fontes (comma join) → rejeita;
          - identificador bracketed/quoted → rejeita;
          - CROSS/OUTER APPLY → rejeita (operando não governável sem AST);
          - sintaxe de fonte não reconhecida → rejeita.
        """
        n = len(sql_up)
        i = 0
        depth = 0
        in_string = False
        from_depths: set[int] = set()

        while i < n:
            ch = sql_up[i]

            if ch == "'":
                in_string = not in_string
                i += 1
                continue

            if in_string:
                i += 1
                continue

            if ch == "(":
                depth += 1
                i += 1
                continue

            if ch == ")":
                depth = max(0, depth - 1)
                from_depths = {d for d in from_depths if d <= depth}
                i += 1
                continue

            if ch == ";":
                from_depths.clear()
                i += 1
                continue

            if ch == "," and depth in from_depths:
                raise PermissionError(
                    "Fontes de dados separadas por vírgula não são "
                    "permitidas pelo validador read-only."
                )

            if ch.isalpha():
                j = i + 1
                while j < n and (sql_up[j].isalnum() or sql_up[j] == "_"):
                    j += 1
                word = sql_up[i:j]

                if word in ("FROM", "JOIN"):
                    self._resolve_single_source(sql_up, j, cte_names)
                    from_depths.add(depth)
                elif word in self._CLAUSE_ENDERS:
                    from_depths.discard(depth)

                i = j
                continue

            i += 1

    # ------------------------------------------------------------------
    # 🔹 Máscara de literais de string
    # ------------------------------------------------------------------
    def _mask_string_literals(self, sql: str) -> str:
        """
        Substitui todo o conteúdo de literais '...' por espaços,
        preservando tamanho/posições. Necessário porque extrações
        lexicais (ex.: nomes de CTE) nunca podem ser alimentadas por
        texto dentro de string — literais são dados, não sintaxe.
        """
        result = []
        in_string = False
        for ch in sql:
            if ch == "'":
                in_string = not in_string
                result.append(" ")
            elif in_string:
                result.append(" ")
            else:
                result.append(ch)
        return "".join(result)

    # ------------------------------------------------------------------
    # 🔹 Extrair nomes de CTEs
    # ------------------------------------------------------------------
    def _extract_cte_names(self, sql_up: str) -> set[str]:
        """
        Extrai nomes de CTEs do(s) bloco(s) WITH ... AS ( ... )
        """
        cte_names: set[str] = set()
        pos = 0

        while True:
            idx = sql_up.find("WITH", pos)
            if idx == -1:
                break

            i = idx + 4
            depth = 0

            while i < len(sql_up):
                if sql_up[i] == "(":
                    depth += 1
                elif sql_up[i] == ")":
                    depth = max(0, depth - 1)

                if depth == 0 and sql_up.startswith("SELECT", i):
                    break

                i += 1

            with_block = sql_up[idx:i]
            found = re.findall(r"\b([A-Z0-9_]+)\s+AS\s*\(", with_block)

            for name in found:
                cte_names.add(name.upper())

            pos = i

        return cte_names

    # ------------------------------------------------------------------
    # 🔹 Validação principal
    # ------------------------------------------------------------------
    def validate(self, sql: str) -> None:
        if not sql or not isinstance(sql, str):
            raise ValueError("SQL inválido ou vazio.")

        # 1️⃣ Remove comentários ANTES de tudo
        sql_no_comments = self._strip_sql_comments(sql)
        sql_clean = sql_no_comments.strip()
        sql_up = sql_clean.upper()

        # 2️⃣ Validação inicial
        if not sql_up.startswith(("DECLARE", "SET", "WITH", "SELECT")):
            raise PermissionError(
                "Somente instruções DECLARE, SET, SELECT ou WITH são permitidas."
            )

        # 3️⃣ Bloqueio de keywords proibidas
        for kw in self.BANNED_KEYWORDS:
            if re.search(rf"\b{kw}\b", sql_up):
                raise PermissionError(f"Comando proibido detectado: {kw}")

        # 4️⃣ Divide instruções
        statements = [s.strip() for s in sql_clean.split(";") if s.strip()]
        select_count = 0

        for stmt in statements:
            stmt_up = stmt.upper()

            # DECLARE
            if stmt_up.startswith("DECLARE"):
                if re.match(
                    r"^DECLARE\s+@[A-Z0-9_]+\s+[A-Z0-9()_,\s]+(\s*=\s*[^;]+)?$",
                    stmt_up,
                ):
                    continue

                if re.match(
                    r"^DECLARE\s+@[A-Z0-9_]+\s+TABLE\s*\([\s\S]*?\)$",
                    stmt_up,
                ):
                    if re.search(r"\b(SELECT|PRIMARY|FOREIGN|CONSTRAINT|INDEX)\b", stmt_up):
                        raise PermissionError(
                            "DECLARE TABLE contém definição não permitida."
                        )
                    continue

                raise PermissionError("DECLARE inválido ou não suportado.")

            # SET
            if stmt_up.startswith("SET"):
                if not re.match(
                    r"^SET\s+@[A-Z0-9_]+\s*=\s*(NULL|'[^']*'|\d+|@[A-Z0-9_]+)$",
                    stmt_up,
                ):
                    raise PermissionError("SET inválido ou não suportado.")
                continue

            # SELECT / WITH
            if stmt_up.startswith("WITH") or stmt_up.startswith("SELECT"):
                select_count += 1
                continue

            raise PermissionError(
                "Somente instruções DECLARE, SET, SELECT ou WITH são permitidas."
            )

        # 5️⃣ Regras finais de SELECT
        if select_count < 1:
            raise PermissionError("É obrigatório existir pelo menos um SELECT no SQL.")

        if select_count > self.MAX_SELECTS:
            raise PermissionError(
                f"Limite máximo de SELECTs excedido ({self.MAX_SELECTS})."
            )

        # APPLY: operando de fonte não governável sem parsing estrutural.
        # Deny incondicional — também vigente em DATA_SQL_SKIP_TABLE_WHITELIST.
        if re.search(r"\b(CROSS|OUTER)\s+APPLY\b", sql_up):
            raise PermissionError(
                "CROSS APPLY / OUTER APPLY não são permitidos pelo "
                "validador read-only."
            )

        # 6️⃣ Validação de tabelas físicas (whitelist)
        if self.skip_table_whitelist():
            log_info(
                "[SQL_VALIDATOR] DATA_SQL_SKIP_TABLE_WHITELIST ativo — "
                "allowlist de tabelas ignorada (somente SELECT)."
            )
            return True

        # Strings são dados, não sintaxe: nomes de CTE só podem vir de
        # texto SQL real — mascarar literais antes da extração lexical.
        cte_names = self._extract_cte_names(self._mask_string_literals(sql_up))

        self._validate_table_sources(sql_up, cte_names)

        return True
