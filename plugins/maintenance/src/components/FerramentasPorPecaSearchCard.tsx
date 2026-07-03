import { ChevronDown } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchPecasReposicao,
  type PecaReposicaoItem,
} from "../data/api/maintenanceApi";
import { useServerTable } from "../hooks/useServerTable";
import { formatCodigoDescricao } from "../utils/pecaOptions";
import { DataTableSection, FilterBar, type DataTableColumn } from "./data";

type FerramentasPorPecaSearchCardProps = {
  filial: string;
  selectedPecaCodigo: string | null;
  onSelectPeca: (peca: { codigo: string; descricao: string } | null) => void;
  getAccessToken?: () => string | undefined;
};

export function FerramentasPorPecaSearchCard({
  filial,
  selectedPecaCodigo,
  onSelectPeca,
  getAccessToken,
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

  const columns = useMemo<DataTableColumn<PecaReposicaoItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        sortable: true,
        sortValue: (item) => item.codigo,
        render: (item) => item.codigo,
      },
      {
        key: "descricao",
        header: "Descrição",
        sortable: true,
        sortValue: (item) => item.descricao,
        render: (item) => item.descricao,
      },
    ],
    [],
  );

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
        setItems(data.items ?? []);
        setTotal(data.total ?? 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar peças.");
        setItems([]);
        setTotal(0);
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
    pecasTable.resetPage();
  }, [filial, pecasTable.resetPage]);

  useEffect(() => {
    void loadPecas();
  }, [loadPecas]);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    const nextCodigo = codigoDraft.trim();
    const nextDescricao = descricaoDraft.trim();
    setCodigoFiltro(nextCodigo);
    setDescricaoFiltro(nextDescricao);
    pecasTable.resetPage();
    await loadPecas({ codigo: nextCodigo, descricao: nextDescricao });
  }

  function handleClearFilters() {
    setCodigoDraft("");
    setDescricaoDraft("");
    setCodigoFiltro("");
    setDescricaoFiltro("");
    pecasTable.resetPage();
    void loadPecas({ codigo: "", descricao: "" });
  }

  function handleSelectPeca(item: PecaReposicaoItem) {
    if (selectedPecaCodigo === item.codigo) {
      onSelectPeca(null);
      return;
    }
    onSelectPeca({ codigo: item.codigo, descricao: item.descricao });
  }

  const selectedLabel = selectedPecaCodigo
    ? formatCodigoDescricao(
        selectedPecaCodigo,
        items.find((item) => item.codigo === selectedPecaCodigo)?.descricao,
      )
    : null;

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
              Peças cadastradas no grupo 3019 (catálogo Protheus). Selecione uma linha para filtrar
              as ferramentas abaixo.
            </p>
          </div>
        </button>
        {selectedPecaCodigo ? (
          <button
            type="button"
            className="dm-ghost-btn dm-ghost-btn--sm"
            onClick={() => onSelectPeca(null)}
          >
            Limpar peça selecionada
          </button>
        ) : null}
      </div>

      {selectedLabel ? (
        <p className="dm-inline-hint">
          Ferramentas filtradas pela peça <strong>{selectedLabel}</strong>.
        </p>
      ) : null}

      {expanded ? (
        <>
          {error ? <p className="dm-inline-error">{error}</p> : null}

          <FilterBar onSubmit={handleSearch} className="dm-filter-bar--search">
            <label className="dm-field">
              <span>Código da peça</span>
              <input
                value={codigoDraft}
                onChange={(event) => setCodigoDraft(event.target.value)}
                placeholder="Ex.: 3019 ou 30190036"
              />
            </label>
            <label className="dm-field">
              <span>Descrição da peça</span>
              <input
                value={descricaoDraft}
                onChange={(event) => setDescricaoDraft(event.target.value)}
                placeholder="Ex.: GRAMPEADOR"
              />
            </label>
            <div className="dm-filter-bar__actions">
              {(codigoFiltro || descricaoFiltro) ? (
                <button type="button" className="dm-ghost-btn" onClick={handleClearFilters}>
                  Limpar filtros
                </button>
              ) : null}
              <button type="submit" className="dm-primary-btn">
                Buscar peças
              </button>
            </div>
          </FilterBar>

          <DataTableSection
            title="Peças amarradas"
            countBadgeLabel="peça(s)"
            columns={columns}
            rows={items}
            loading={loading}
            emptyMessage="Nenhuma peça 3019 encontrada com os filtros informados."
            getRowKey={(item) => item.codigo}
            getRowClassName={(item) =>
              selectedPecaCodigo === item.codigo ? "is-selected" : undefined
            }
            embedded
            onRowClick={handleSelectPeca}
            serverTable={{
              page: pecasTable.query.page,
              pageSize: pecasTable.query.pageSize,
              total,
              onPageChange: pecasTable.setPage,
              sortKey: pecasTable.query.sortKey,
              sortDirection: pecasTable.query.sortDirection,
              onSortChange: pecasTable.handleSortChange,
            }}
          />
        </>
      ) : null}
    </section>
  );
}
