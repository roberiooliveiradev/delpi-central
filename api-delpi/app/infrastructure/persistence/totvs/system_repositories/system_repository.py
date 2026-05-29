# app/infrastructure/persistence/totvs/system_repository.py

from difflib import SequenceMatcher
import re

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.domain.ports.system.system_repository_port import SystemRepositoryPort
from app.core.exceptions import BusinessLogicError
from app.utils.logger import log_info


class SystemRepository(BaseRepository, SystemRepositoryPort):
    """
    Repositório responsável por consultas sobre tabelas, colunas, índices
    e relacionamentos do Protheus / SQL Server.
    """

    @staticmethod
    def _resolve_physical_table_name(table_name: str) -> str:
        normalized = str(table_name or "").strip().upper()

        if not normalized:
            return normalized

        if re.fullmatch(r"[A-Z]{2,4}\d{3,4}", normalized):
            return normalized

        if re.fullmatch(r"[A-Z]{2,4}\d{0,2}", normalized):
            return f"{normalized}010"

        return normalized

    def get_table(self, table_name: str) -> list[dict]:
        table_name = self._resolve_physical_table_name(table_name)
        log_info(f"Buscando informações da tabela {table_name}.")

        query = """
            SELECT
                t.name AS TableName,
                X2.*
            FROM sys.tables t
            LEFT JOIN SX2010 X2
                ON X2.X2_ARQUIVO = t.name
            WHERE
                t.name = ?
                AND X2.D_E_L_E_T_ = ''
        """

        with self as repo:
            table = repo.execute_query(query, (table_name,))

        if not table:
            raise BusinessLogicError(
                f"Tabela com código '{table_name}' não encontrada."
            )

        return table

    def get_columns_table(
        self,
        table_name: str,
        page: int = 1,
        page_size: int = 50
    ) -> dict:
        table_name = self._resolve_physical_table_name(table_name)
        log_info(
            f"Buscando colunas da tabela {table_name} "
            f"(página {page}, limite {page_size})..."
        )

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 200:
            page_size = 50

        offset = (page - 1) * page_size

        count_query = """
            SELECT COUNT(*) AS total
            FROM SX3010 AS X3
            INNER JOIN SX2010 AS X2
                ON X3.X3_ARQUIVO = X2.X2_CHAVE
            WHERE
                X2.X2_ARQUIVO = ?
                AND X3.D_E_L_E_T_ = ''
                AND X2.D_E_L_E_T_ = ''
        """

        query = """
            SELECT
                X3.*
            FROM SX3010 AS X3
            INNER JOIN SX2010 AS X2
                ON X3.X3_ARQUIVO = X2.X2_CHAVE
            WHERE
                X2.X2_ARQUIVO = ?
                AND X3.D_E_L_E_T_ = ''
                AND X2.D_E_L_E_T_ = ''
            ORDER BY X3.X3_ORDEM
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:
            total_result = repo.execute_query(count_query, (table_name,))
            total = total_result[0]["total"] if total_result else 0

            columns = repo.execute_query(query, (table_name, offset, page_size))

        if not columns:
            raise BusinessLogicError(
                f"Colunas da tabela '{table_name}' não encontradas."
            )

        total_pages = (total + page_size - 1) // page_size

        return {
            "success": True,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
            "results": columns,
        }

    def search_table_by_description(
        self,
        description: str,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 200:
            page_size = 20

        offset = (page - 1) * page_size
        terms = [t.strip().upper() for t in re.split(r"\s+", description) if t.strip()]

        if not terms:
            raise BusinessLogicError(
                "Descrição inválida — forneça ao menos uma palavra para busca."
            )

        like_clauses = []
        params = []

        for term in terms:
            like_clauses.append("UPPER(X2.X2_NOME) LIKE UPPER(?)")
            params.append(f"%{term}%")

        where_clause = " OR ".join(like_clauses)

        query = f"""
            SELECT
                X2.X2_ARQUIVO,
                X2.X2_NOME,
                X2.X2_CHAVE
            FROM SX2010 AS X2
            WHERE
                ({where_clause})
                AND X2.D_E_L_E_T_ = ''
            ORDER BY X2.X2_NOME
        """

        with self as repo:
            results = repo.execute_query(query, tuple(params))

            if not results or len(results) < 10:
                log_info(
                    f"Poucos resultados ({len(results)}). "
                    f"Ativando fallback total de SX2010."
                )

                query_fallback = """
                    SELECT
                        X2.X2_ARQUIVO,
                        X2.X2_NOME,
                        X2.X2_CHAVE
                    FROM SX2010 AS X2
                    WHERE X2.D_E_L_E_T_ = ''
                    ORDER BY X2.X2_NOME
                """

                results = repo.execute_query(query_fallback, ())

        desc_upper = description.upper()
        desc_terms = desc_upper.split()

        for row in results:
            nome = row.get("X2_NOME", "")
            nome_upper = nome.upper()

            seq_ratio = SequenceMatcher(None, desc_upper, nome_upper).ratio()
            matched_terms = [t for t in desc_terms if t in nome_upper]
            coverage = len(matched_terms) / len(desc_terms)

            order_score = 0
            last_pos = -1

            for term in desc_terms:
                pos = nome_upper.find(term)
                if pos >= 0 and pos > last_pos:
                    order_score += 1
                    last_pos = pos

            order_ratio = order_score / len(desc_terms)
            len_ratio = min(len(desc_upper), len(nome_upper)) / max(len(desc_upper), len(nome_upper))

            total_score = (
                seq_ratio * 60 +
                coverage * 25 +
                order_ratio * 10 +
                len_ratio * 5
            ) * 100

            row["similarity_ratio"] = round(seq_ratio, 3)
            row["coverage_ratio"] = round(coverage, 3)
            row["order_ratio"] = round(order_ratio, 3)
            row["length_ratio"] = round(len_ratio, 3)
            row["total_score"] = round(total_score, 2)

        results.sort(key=lambda x: x["total_score"], reverse=True)

        total = len(results)
        paginated_results = results[offset: offset + page_size]

        return {
            "success": True,
            "page": page,
            "page_size": page_size,
            "total_records": total,
            "total_pages": (total // page_size) + (1 if total % page_size else 0),
            "data": paginated_results,
        }

    def get_table_indexes(self, table_name: str) -> list[dict]:
        table_name = self._resolve_physical_table_name(table_name)
        log_info(f"Buscando índices da tabela {table_name}...")

        query = """
            SELECT
                SIX.*
            FROM SIX010 AS SIX
            INNER JOIN SX2010 AS SX2
                ON SIX.INDICE = SX2.X2_CHAVE
            WHERE
                SX2.X2_ARQUIVO = ?
                AND SIX.D_E_L_E_T_ = ''
                AND SX2.D_E_L_E_T_ = ''
            ORDER BY SIX.ORDEM
        """

        with self as repo:
            return repo.execute_query(query, (table_name,))

    def get_table_relations(self, table_name: str) -> list[dict]:
        table_name = self._resolve_physical_table_name(table_name)
        log_info(f"Buscando relacionamentos da tabela {table_name}...")

        query = """
            SELECT
                SX9.*
            FROM SX9010 AS SX9
            INNER JOIN SX2010 AS SX2
                ON SX9.X9_DOM = SX2.X2_CHAVE
            WHERE
                SX2.X2_ARQUIVO = ?
                AND SX9.D_E_L_E_T_ = ''
                AND SX2.D_E_L_E_T_ = ''
            ORDER BY SX9.X9_DOM
        """

        with self as repo:
            return repo.execute_query(query, (table_name,))

    def search_columns_in_table(self, table_name: str, text: str) -> list[dict]:
        table_name = self._resolve_physical_table_name(table_name)
        log_info(
            f"Buscando colunas da tabela {table_name} contendo '{text}'..."
        )

        query = """
            SELECT
                X3.X3_CAMPO,
                X3.X3_DESCRIC,
                X3.X3_ORDEM,
                X3.X3_TIPO,
                X3.X3_TAMANHO,
                X3.X3_DECIMAL
            FROM SX3010 AS X3
            INNER JOIN SX2010 AS X2
                ON X3.X3_ARQUIVO = X2.X2_CHAVE
            WHERE
                X2.X2_ARQUIVO = ?
                AND X3.D_E_L_E_T_ = ''
                AND X2.D_E_L_E_T_ = ''
                AND (
                    UPPER(X3.X3_CAMPO) LIKE UPPER(?) OR
                    UPPER(X3.X3_DESCRIC) LIKE UPPER(?)
                )
            ORDER BY X3.X3_ORDEM
        """

        text_like = f"%{text}%"

        with self as repo:
            return repo.execute_query(query, (table_name, text_like, text_like))

    def search_columns_by_description(
        self,
        description: str,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        log_info(f"Buscando colunas por descrição: '{description}'")

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 200:
            page_size = 20

        offset = (page - 1) * page_size
        terms = [t.strip().upper() for t in re.split(r"\s+", description) if t.strip()]

        if not terms:
            raise BusinessLogicError(
                "Informe ao menos um termo para pesquisa."
            )

        like_clauses = []
        params = []

        for term in terms:
            like_clauses.append("UPPER(X3.X3_DESCRIC) LIKE UPPER(?)")
            params.append(f"%{term}%")

        where_clause = " OR ".join(like_clauses)

        query = f"""
            SELECT
                X2.X2_ARQUIVO AS table_name,
                X2.X2_NOME AS table_description,
                X3.X3_CAMPO AS column_name,
                X3.X3_DESCRIC AS column_description
            FROM SX3010 X3
            INNER JOIN SX2010 X2
                ON X3.X3_ARQUIVO = X2.X2_CHAVE
            WHERE
                ({where_clause})
                AND X3.D_E_L_E_T_ = ''
                AND X2.D_E_L_E_T_ = ''
        """

        with self as repo:
            results = repo.execute_query(query, tuple(params))

            if not results or len(results) < 20:
                log_info("Poucos resultados. Ativando fallback global em SX3010.")

                query_fallback = """
                    SELECT
                        X2.X2_ARQUIVO AS table_name,
                        X2.X2_NOME AS table_description,
                        X3.X3_CAMPO AS column_name,
                        X3.X3_DESCRIC AS column_description
                    FROM SX3010 X3
                    INNER JOIN SX2010 X2
                        ON X3.X3_ARQUIVO = X2.X2_CHAVE
                    WHERE
                        X3.D_E_L_E_T_ = ''
                        AND X2.D_E_L_E_T_ = ''
                """

                results = repo.execute_query(query_fallback, ())

        desc_upper = description.upper()
        desc_terms = desc_upper.split()

        for row in results:
            text = f"{row.get('column_description', '')}".upper()

            seq_ratio = SequenceMatcher(None, desc_upper, text).ratio()
            matched_terms = [t for t in desc_terms if t in text]
            coverage = len(matched_terms) / len(desc_terms)

            order_score = 0
            last_pos = -1

            for term in desc_terms:
                pos = text.find(term)
                if pos >= 0 and pos > last_pos:
                    order_score += 1
                    last_pos = pos

            order_ratio = order_score / len(desc_terms)
            len_ratio = (
                min(len(desc_upper), len(text)) / max(len(desc_upper), len(text))
                if text else 0
            )

            total_score = (
                seq_ratio * 60 +
                coverage * 25 +
                order_ratio * 10 +
                len_ratio * 5
            ) * 100

            row["similarity_ratio"] = round(seq_ratio, 3)
            row["coverage_ratio"] = round(coverage, 3)
            row["order_ratio"] = round(order_ratio, 3)
            row["length_ratio"] = round(len_ratio, 3)
            row["total_score"] = round(total_score, 2)

        results.sort(key=lambda x: x["total_score"], reverse=True)

        total = len(results)
        paginated = results[offset: offset + page_size]

        return {
            "success": True,
            "page": page,
            "page_size": page_size,
            "total_records": total,
            "total_pages": (total // page_size) + (1 if total % page_size else 0),
            "data": paginated,
        }