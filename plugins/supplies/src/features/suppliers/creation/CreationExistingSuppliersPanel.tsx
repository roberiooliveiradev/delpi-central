import { useCallback, useRef, useState } from "react";

import { buildSupplierDetailPath } from "../../../app/pluginRoutes";
import { SuppliesCompactPagination } from "../../../app/suppliesUi";
import { listExistingSuppliers } from "./api";
import { CREATION_CONTENT as C } from "./content";
import type { CreationDuplicateMatch } from "./types";

const PAGE_SIZE = 10;

type CreationExistingSuppliersPanelProps = {
  basePath: string;
  /** CNPJ consultado (dígitos normalizados) — identidade do preview atual. */
  taxId: string;
  /** Página 1 já retornada pelo preview — evita reconsulta. */
  initialMatches: CreationDuplicateMatch[];
  /** Total real informado pelo BFF (pode exceder o tamanho de `initialMatches`). */
  total: number;
  disabled?: boolean;
};

function matchKey(match: CreationDuplicateMatch, index: number) {
  return `${match.supplier_code ?? "?"}-${match.supplier_store ?? "?"}-${index}`;
}

export function CreationExistingSuppliersPanel({
  basePath,
  taxId,
  initialMatches,
  total,
  disabled,
}: CreationExistingSuppliersPanelProps) {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<CreationDuplicateMatch[]>(initialMatches);
  const [loading, setLoading] = useState(false);
  const [pageError, setPageError] = useState(false);
  // O parent remonta este painel com `key={taxId}` — cada CNPJ consultado
  // começa com cache e página zerados, sem reset imperativo.
  const cacheRef = useRef<Map<number, CreationDuplicateMatch[]>>(
    new Map([[1, initialMatches]]),
  );
  const requestSeqRef = useRef(0);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const loadPage = useCallback(
    async (target: number) => {
      const cached = cacheRef.current.get(target);
      if (cached) {
        setPage(target);
        setItems(cached);
        setPageError(false);
        return;
      }
      const seq = ++requestSeqRef.current;
      setLoading(true);
      setPageError(false);
      try {
        const result = await listExistingSuppliers(taxId, target, PAGE_SIZE);
        if (requestSeqRef.current !== seq) return;
        cacheRef.current.set(target, result.items);
        setPage(target);
        setItems(result.items);
      } catch {
        if (requestSeqRef.current !== seq) return;
        setPageError(true);
      } finally {
        if (requestSeqRef.current === seq) setLoading(false);
      }
    },
    [taxId],
  );

  return (
    <div className="sp-supplier-create__existing">
      <ul className="sp-supplier-create__assist-matches">
        {items.map((match, index) => {
          const detailHref =
            match.supplier_code && match.supplier_store
              ? buildSupplierDetailPath(
                  match.supplier_code,
                  match.supplier_store,
                  basePath,
                )
              : null;
          return (
            <li key={matchKey(match, index)}>
              <span>
                {match.supplier_name || match.supplier_code}
                {match.supplier_code
                  ? ` · ${match.supplier_code}/${match.supplier_store}`
                  : ""}
                {match.state ? ` · ${match.state}` : ""}
                {match.blocked ? ` · ${C.duplicateMatchBlocked}` : ""}
              </span>
              {detailHref ? (
                <a
                  href={detailHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sp-supplier-create__existing-review"
                >
                  {C.duplicateOpenMatch}
                </a>
              ) : null}
            </li>
          );
        })}
      </ul>
      {pageError ? (
        <p className="sp-supplier-create__assist-error" role="alert">
          {C.existingSuppliersPageLoadError}
        </p>
      ) : null}
      {!loading && !pageError && items.length === 0 && page > 1 ? (
        <p className="sp-supplier-create__assist-error" role="status">
          {C.existingSuppliersEmptyPage}
        </p>
      ) : null}
      {totalPages > 1 ? (
        <SuppliesCompactPagination
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
          totalPages={totalPages}
          onPageChange={loadPage}
          disabled={disabled || loading}
        />
      ) : null}
    </div>
  );
}
