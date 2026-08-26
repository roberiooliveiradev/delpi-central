import { ChevronDown, ChevronRight, Lock } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { MaintenanceActionButton } from "../app/maintenanceUi";
import { DmNativeTextField } from "./dmFormFields";
import { DmTablePagination } from "./dmPaginationKit";
import { FilterBar } from "./data";
import { DM_HELP } from "../content/helpTooltips";
import {
  fetchPecasReposicao,
  type FerramentaItem,
  type PecaReposicaoItem,
} from "../data/api/maintenanceApi";
import { useServerTable } from "../hooks/useServerTable";
import { fetchAllFerramentasForPeca } from "../utils/fetchAllFerramentasForPeca";
import { resolveAutoExpandedPecaCodes } from "../utils/pecaSearchTreeUtils";
import { formatCodigoDescricao } from "../utils/pecaOptions";

type FerramentasPorPecaSearchCardProps = {
  filial: string;
  getAccessToken?: () => string | undefined;
  onNavigateToFerramenta: (codigo: string) => void;
  refreshSignal?: number;
  onLoadingChange?: (loading: boolean) => void;
};

type FerramentasCache = Map<string, FerramentaItem[]>;

type PecaFerramentasBranchProps = {
  filial: string;
  codigoPeca: string;
  cache: FerramentasCache;
  onCacheUpdate: (codigoPeca: string, items: FerramentaItem[]) => void;
  onNavigateToFerramenta: (codigo: string) => void;
  getAccessToken?: () => string | undefined;
};

function PecaFerramentasBranch({
  filial,
  codigoPeca,
  cache,
  onCacheUpdate,
  onNavigateToFerramenta,
  getAccessToken,
}: PecaFerramentasBranchProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef(0);

  const cachedItems = cache.get(codigoPeca);

  useEffect(() => {
    if (cachedItems) return;

    const requestId = requestRef.current + 1;
    requestRef.current = requestId;
    setLoading(true);
    setError(null);

    void fetchAllFerramentasForPeca(filial, codigoPeca, getAccessToken)
      .then((items) => {
        if (requestRef.current !== requestId) return;
        onCacheUpdate(codigoPeca, items);
      })
      .catch((err) => {
        if (requestRef.current !== requestId) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar ferramentas da peça.");
      })
      .finally(() => {
        if (requestRef.current === requestId) {
          setLoading(false);
        }
      });
  }, [cachedItems, codigoPeca, filial, getAccessToken, onCacheUpdate]);

  if (loading && !cachedItems) {
    return (
      <div className="dm-peca-ferramentas-tree__branch-state" aria-busy="true">
        Carregando ferramentas…
      </div>
    );
  }

  if (error) {
    return (
      <div className="dm-peca-ferramentas-tree__branch-state dm-peca-ferramentas-tree__branch-state--error">
        {error}
      </div>
    );
  }

  const items = cachedItems ?? [];

  if (items.length === 0) {
    return (
      <div className="dm-peca-ferramentas-tree__branch-state">
        Nenhuma ferramenta amarrada a esta peça.
      </div>
    );
  }

  return (
    <ul className="dm-peca-ferramentas-tree__branch-list">
      {items.map((item) => (
        <li key={item.codigo}>
          <button
            type="button"
            className="dm-peca-ferramentas-tree__ferramenta"
            onClick={() => onNavigateToFerramenta(item.codigo)}
          >
            <span className="dm-peca-ferramentas-tree__ferramenta-codigo">
              {item.bloqueado ? (
                <Lock size={14} className="dm-ferramenta-codigo__lock" aria-hidden="true" />
              ) : null}
              {item.codigo}
            </span>
            <span className="dm-peca-ferramentas-tree__ferramenta-desc">{item.descricao}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export function FerramentasPorPecaSearchCard({
  filial,
  getAccessToken,
  onNavigateToFerramenta,
  refreshSignal = 0,
  onLoadingChange,
}: FerramentasPorPecaSearchCardProps) {
  const pecasTable = useServerTable({ defaultSortKey: "codigo" });
  const [codigoDraft, setCodigoDraft] = useState("");
  const [descricaoDraft, setDescricaoDraft] = useState("");
  const [codigoFiltro, setCodigoFiltro] = useState("");
  const [descricaoFiltro, setDescricaoFiltro] = useState("");
  const [items, setItems] = useState<PecaReposicaoItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [expandedPecas, setExpandedPecas] = useState<Set<string>>(() => new Set());
  const [ferramentasCache, setFerramentasCache] = useState<FerramentasCache>(() => new Map());

  const handleCacheUpdate = useCallback((codigoPeca: string, ferramentas: FerramentaItem[]) => {
    setFerramentasCache((current) => {
      const next = new Map(current);
      next.set(codigoPeca, ferramentas);
      return next;
    });
  }, []);

  const loadPecas = useCallback(
    async (filters?: { codigo?: string; descricao?: string }) => {
      const codigo = filters?.codigo ?? codigoFiltro;
      const descricao = filters?.descricao ?? descricaoFiltro;
      setLoading(true);
      setError(null);
      try {
        const data = await fetchPecasReposicao(
          filial,
          {
            page: pecasTable.query.page,
            pageSize: pecasTable.query.pageSize,
            sortKey: pecasTable.query.sortKey,
            sortDirection: pecasTable.query.sortDirection,
          },
          {
            codigo: codigo.trim() || undefined,
            descricao: descricao.trim() || undefined,
          },
          getAccessToken,
        );
        const nextItems = data.items ?? [];
        setItems(nextItems);
        setTotal(data.total ?? 0);
        return nextItems;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar peças.");
        setItems([]);
        setTotal(0);
        return [];
      } finally {
        setLoading(false);
      }
    },
    [
      codigoFiltro,
      descricaoFiltro,
      filial,
      getAccessToken,
      pecasTable.query,
    ],
  );

  useEffect(() => {
    onLoadingChange?.(loading);
  }, [loading, onLoadingChange]);

  useEffect(() => {
    pecasTable.resetPage();
    setExpandedPecas(new Set());
    setFerramentasCache(new Map());
  }, [filial, pecasTable.resetPage]);

  useEffect(() => {
    void loadPecas();
  }, [loadPecas, refreshSignal]);

  function togglePecaExpanded(codigo: string) {
    setExpandedPecas((current) => {
      const next = new Set(current);
      if (next.has(codigo)) {
        next.delete(codigo);
      } else {
        next.add(codigo);
      }
      return next;
    });
  }

  function expandAllVisible() {
    setExpandedPecas(new Set(items.map((item) => item.codigo)));
  }

  function collapseAllVisible() {
    setExpandedPecas(new Set());
  }

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    const nextCodigo = codigoDraft.trim();
    const nextDescricao = descricaoDraft.trim();
    setCodigoFiltro(nextCodigo);
    setDescricaoFiltro(nextDescricao);
    pecasTable.resetPage();
    const loadedItems = await loadPecas({ codigo: nextCodigo, descricao: nextDescricao });
    setExpandedPecas(
      resolveAutoExpandedPecaCodes(loadedItems, { codigo: nextCodigo, descricao: nextDescricao }),
    );
  }

  function handleClearFilters() {
    setCodigoDraft("");
    setDescricaoDraft("");
    setCodigoFiltro("");
    setDescricaoFiltro("");
    pecasTable.resetPage();
    setExpandedPecas(new Set());
    void loadPecas({ codigo: "", descricao: "" });
  }

  return (
    <section className={`dm-card dm-collapsible-card${expanded ? "" : " is-collapsed"}`}>
      <div className="dm-section-header dm-collapsible-card__header">
        <button
          type="button"
          className="dm-collapsible-card__trigger"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
        >
          <ChevronDown
            size={18}
            aria-hidden="true"
            className={expanded ? "dm-collapsible-card__chevron is-open" : "dm-collapsible-card__chevron"}
          />
          <div className="dm-section-header__title-group">
            <h2 className="dm-section-header__title">Buscar ferramentas por peça</h2>
            <p className="dm-section-header__hint">
              Peças cadastradas no grupo 3019 (catálogo Protheus). Expanda uma peça para ver as
              ferramentas amarradas.
            </p>
          </div>
        </button>
        {expanded && items.length > 0 ? (
          <div className="dm-peca-ferramentas-tree__bulk-actions">
            <MaintenanceActionButton variant="ghost" className="dm-btn--sm" onClick={expandAllVisible}>
              Expandir tudo
            </MaintenanceActionButton>
            <MaintenanceActionButton variant="ghost" className="dm-btn--sm" onClick={collapseAllVisible}>
              Recolher tudo
            </MaintenanceActionButton>
          </div>
        ) : null}
      </div>

      {expanded ? (
        <>
          {error ? <p className="dm-inline-error">{error}</p> : null}

          <FilterBar onSubmit={handleSearch} className="dm-filter-bar--search">
            <DmNativeTextField
              id="dm-busca-peca-codigo"
              label="Código da peça"
              hint={DM_HELP.miniAplicadores.buscaPeca}
              value={codigoDraft}
              onChange={setCodigoDraft}
              placeholder="Ex.: 3019 ou 30190036"
            />
            <DmNativeTextField
              id="dm-busca-peca-descricao"
              label="Descrição da peça"
              hint={DM_HELP.miniAplicadores.buscaPeca}
              value={descricaoDraft}
              onChange={setDescricaoDraft}
              placeholder="Ex.: GRAMPEADOR"
            />
            <div className="dm-filter-bar__actions">
              {codigoFiltro || descricaoFiltro ? (
                <MaintenanceActionButton variant="ghost" onClick={handleClearFilters}>
                  Limpar filtros
                </MaintenanceActionButton>
              ) : null}
              <MaintenanceActionButton type="submit" variant="primary">
                Buscar peças
              </MaintenanceActionButton>
            </div>
          </FilterBar>

          {loading && items.length === 0 ? (
            <p className="dm-inline-hint" aria-busy="true">
              Carregando peças…
            </p>
          ) : null}

          {!loading && items.length === 0 ? (
            <p className="dm-inline-hint">Nenhuma peça 3019 encontrada com os filtros informados.</p>
          ) : null}

          {items.length > 0 ? (
            <div className="dm-peca-ferramentas-tree" aria-busy={loading}>
              <p className="dm-peca-ferramentas-tree__count">{total} peça(s)</p>
              <ul className="dm-peca-ferramentas-tree__list" role="tree">
                {items.map((peca) => {
                  const isOpen = expandedPecas.has(peca.codigo);
                  return (
                    <li key={peca.codigo} className="dm-peca-ferramentas-tree__item" role="treeitem">
                      <button
                        type="button"
                        className="dm-peca-ferramentas-tree__peca-trigger"
                        aria-expanded={isOpen}
                        onClick={() => togglePecaExpanded(peca.codigo)}
                      >
                        {isOpen ? (
                          <ChevronDown size={16} aria-hidden="true" />
                        ) : (
                          <ChevronRight size={16} aria-hidden="true" />
                        )}
                        <span className="dm-peca-ferramentas-tree__peca-label">
                          {formatCodigoDescricao(peca.codigo, peca.descricao)}
                        </span>
                      </button>
                      {isOpen ? (
                        <PecaFerramentasBranch
                          filial={filial}
                          codigoPeca={peca.codigo}
                          cache={ferramentasCache}
                          onCacheUpdate={handleCacheUpdate}
                          onNavigateToFerramenta={onNavigateToFerramenta}
                          getAccessToken={getAccessToken}
                        />
                      ) : null}
                    </li>
                  );
                })}
              </ul>

              {(pecasTable.query.pageSize ?? 20) < total ? (
                <DmTablePagination
                  page={pecasTable.query.page ?? 1}
                  pageSize={pecasTable.query.pageSize ?? 20}
                  total={total}
                  onPageChange={pecasTable.setPage}
                />
              ) : null}
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
