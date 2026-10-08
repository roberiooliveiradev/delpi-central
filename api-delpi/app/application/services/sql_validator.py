# app/application/services/sql_validator.py
import re
import json
import os
from pathlib import Path

import sqlglot
from sqlglot import exp

from app.utils.logger import log_error, log_info

# Perfis de política estrutural (S1)
PROFILE_LEGACY_READONLY = "legacy_readonly"
PROFILE_DAVI_GOVERNED = "davi_governed"


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
    # 🔹 Política estrutural (AST — sqlglot tsql)
    # ------------------------------------------------------------------
    # A camada lexical acima permanece como defesa em profundidade; a
    # autoridade para tipos de statement e fontes físicas é estrutural.
    _LEGACY_ALLOWED_STATEMENTS = (
        exp.Select, exp.Union, exp.Declare, exp.Set, exp.Semicolon,
    )
    _GOVERNED_ALLOWED_STATEMENTS = (exp.Select, exp.Union)

    # Limites do perfil governado (fallback analítico DAVI)
    GOVERNED_MAX_STATEMENT_CHARS = 8000
    GOVERNED_MAX_TABLES = 8
    GOVERNED_MAX_JOINS = 8

    def _declared_table_vars(self, stmt) -> set[str]:
        names: set[str] = set()
        for item in stmt.find_all(exp.DeclareItem):
            declared = item.this if isinstance(item.this, list) else [item.this]
            for entry in declared:
                if isinstance(entry, exp.Parameter):
                    names.add(entry.name.upper().lstrip("@"))
        return names

    def _check_physical_table(
        self,
        table: exp.Table,
        cte_names: set[str],
        declared_vars: set[str],
        governed: bool,
    ) -> str | None:
        """Classifica uma fonte AST. Retorna o nome físico ou None (não-física)."""
        # @variável de tabela local (DECLARE @T TABLE) — apenas legacy
        if isinstance(table.this, exp.Parameter):
            if governed:
                raise PermissionError(
                    "Variáveis de tabela não são permitidas no perfil governed."
                )
            name = table.name.upper()
            if name in declared_vars:
                return None
            raise PermissionError(
                f"Variável de tabela '@{name}' não declarada."
            )

        # Fontes sem nome (OPENROWSET, OPENQUERY, funções) não são
        # governáveis — deny incondicional em ambos os perfis.
        if not table.name:
            raise PermissionError(
                "Sintaxe de fonte de dados não suportada pelo validador "
                "read-only."
            )

        # Qualificação (schema/db/servidor) não é suportada.
        if table.args.get("db") or table.args.get("catalog"):
            raise PermissionError(
                "Qualificação de objeto não é suportada pelo validador "
                "read-only."
            )

        # Identificadores delimitados ([t], "t") — deny até suporte explícito.
        if getattr(table.this, "quoted", False):
            raise PermissionError(
                "Sintaxe de fonte de dados não suportada pelo validador "
                "read-only (identificador delimitado)."
            )

        name = table.name.upper()

        # Referência a CTE não é fonte física.
        if name in cte_names:
            return None

        if governed and table.args.get("hints"):
            raise PermissionError(
                "Hints de tabela não são permitidas no perfil governed."
            )

        if name not in self.allowed_tables:
            raise PermissionError(
                f"Tabela '{name}' não autorizada (fora da whitelist)."
            )

        return name

    def _validate_ast_policy(self, statements: list, profile: str) -> set[str]:
        """Aplica a política estrutural e retorna as fontes físicas
        resolvidas (útil para observabilidade)."""
        governed = profile == PROFILE_DAVI_GOVERNED
        allowed_types = (
            self._GOVERNED_ALLOWED_STATEMENTS
            if governed
            else self._LEGACY_ALLOWED_STATEMENTS
        )

        physical_tables: set[str] = set()
        join_count = 0

        # Variáveis de tabela são batch-scoped (DECLARE no statement N,
        # uso no N+1).
        declared_vars: set[str] = set()
        for stmt in statements:
            declared_vars |= self._declared_table_vars(stmt)

        for stmt in statements:
            if isinstance(stmt, exp.Semicolon):
                continue
            if not isinstance(stmt, allowed_types):
                raise PermissionError(
                    "O perfil governed permite somente um único SELECT/WITH "
                    "analítico."
                    if governed
                    else "Somente instruções DECLARE, SET, SELECT ou WITH são "
                    "permitidas."
                )

            # SELECT INTO — deny estrutural em ambos os perfis.
            for sel in stmt.find_all(exp.Select):
                if sel.args.get("into") is not None:
                    raise PermissionError("Comando proibido detectado: INTO")
                if governed and (sel.args.get("for_") or sel.args.get("lock")):
                    raise PermissionError(
                        "Cláusulas FOR/LOCK não são permitidas no perfil "
                        "governed."
                    )

            # CROSS/OUTER APPLY — deny estrutural.
            if stmt.find(exp.Lateral) is not None:
                raise PermissionError(
                    "CROSS APPLY / OUTER APPLY não são permitidos pelo "
                    "validador read-only."
                )

            # PIVOT não pertence à gramática governada.
            if governed and stmt.find(exp.Pivot) is not None:
                raise PermissionError(
                    "PIVOT não é permitido no perfil governed."
                )

            # Comma join → sqlglot modela como Join de Table sem
            # on/kind/side/method (JOIN real sempre tem `on` ou
            # kind/side explícitos).
            for join in stmt.find_all(exp.Join):
                if isinstance(join.this, exp.Lateral):
                    raise PermissionError(
                        "CROSS APPLY / OUTER APPLY não são permitidos pelo "
                        "validador read-only."
                    )
                if not (
                    join.args.get("on")
                    or join.args.get("kind")
                    or join.args.get("side")
                    or join.args.get("method")
                ):
                    raise PermissionError(
                        "Fontes de dados separadas por vírgula não são "
                        "permitidas pelo validador read-only."
                    )
                join_count += 1

            cte_names = {
                cte.alias.upper()
                for cte in stmt.find_all(exp.CTE)
                if cte.alias
            }

            for table in stmt.find_all(exp.Table):
                name = self._check_physical_table(
                    table, cte_names, declared_vars, governed
                )
                if name:
                    physical_tables.add(name)

        if governed:
            if len(physical_tables) > self.GOVERNED_MAX_TABLES:
                raise PermissionError(
                    "Consulta excede o limite de tabelas do perfil governed."
                )
            if join_count > self.GOVERNED_MAX_JOINS:
                raise PermissionError(
                    "Consulta excede o limite de joins do perfil governed."
                )

        return physical_tables

    # ------------------------------------------------------------------
    # 🔹 Validação principal
    # ------------------------------------------------------------------
    def validate(self, sql: str, *, profile: str = PROFILE_LEGACY_READONLY) -> bool:
        if not sql or not isinstance(sql, str):
            raise ValueError("SQL inválido ou vazio.")

        governed = profile == PROFILE_DAVI_GOVERNED

        # 1️⃣ Remove comentários ANTES de tudo
        sql_no_comments = self._strip_sql_comments(sql)
        sql_clean = sql_no_comments.strip()
        sql_up = sql_clean.upper()

        # 2️⃣ Validação inicial
        if not sql_up.startswith(("DECLARE", "SET", "WITH", "SELECT")):
            raise PermissionError(
                "Somente instruções DECLARE, SET, SELECT ou WITH são permitidas."
            )

        if governed and len(sql_clean) > self.GOVERNED_MAX_STATEMENT_CHARS:
            raise PermissionError(
                "Consulta excede o limite de tamanho do perfil governed."
            )

        # 3️⃣ Bloqueio de keywords proibidas
        for kw in self.BANNED_KEYWORDS:
            if re.search(rf"\b{kw}\b", sql_up):
                raise PermissionError(f"Comando proibido detectado: {kw}")

        # 4️⃣ Parse estrutural — fail closed
        try:
            parsed = sqlglot.parse(sql_clean, dialect="tsql")
        except Exception:
            raise PermissionError(
                "Sintaxe SQL não suportada pelo validador read-only."
            )

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

        # Governed: exatamente um statement analítico.
        if governed:
            core = [s for s in parsed if not isinstance(s, exp.Semicolon)]
            if len(core) != 1:
                raise PermissionError(
                    "O perfil governed permite somente um único SELECT/WITH "
                    "analítico."
                )

        # APPLY: deny incondicional — também vigente em
        # DATA_SQL_SKIP_TABLE_WHITELIST.
        if re.search(r"\b(CROSS|OUTER)\s+APPLY\b", sql_up):
            raise PermissionError(
                "CROSS APPLY / OUTER APPLY não são permitidos pelo "
                "validador read-only."
            )

        # 6️⃣ Validação de tabelas físicas (whitelist)
        if self.skip_table_whitelist():
            if governed:
                raise PermissionError(
                    "Política governed indisponível enquanto "
                    "DATA_SQL_SKIP_TABLE_WHITELIST estiver ativa."
                )
            log_info(
                "[SQL_VALIDATOR] DATA_SQL_SKIP_TABLE_WHITELIST ativo — "
                "allowlist de tabelas ignorada (somente SELECT)."
            )
            return True

        self._validate_ast_policy(parsed, profile)

        return True
