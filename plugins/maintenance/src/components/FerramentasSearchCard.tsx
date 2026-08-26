import { Lock } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MaintenanceActionButton, MaintenanceNativeCheckboxControl } from "../app/maintenanceUi";
import { DmNativeTextField } from "./dmFormFields";
import { DM_HELP } from "../content/helpTooltips";
import { MAINTENANCE_LIST_LAYOUT_KEYS } from "../content/listLayoutKeys";
import { FerramentaListCard } from "./listCards/MaintenanceListCards";
import { fetchFerramentas, type FerramentaItem } from "../data/api/maintenanceApi";
import { useMaintenanceFreshness } from "../hooks/useMaintenanceFreshness";
import { useServerTable } from "../hooks/useServerTable";
import { DataTableSection, FilterBar, type DataTableColumn } from "./data";

type FerramentasSearchCardProps = {
  filial: string;
  getAccessToken?: () => string | undefined;
  onNavigateToFerramenta: (codigo: string) => void;
  refreshSignal?: number;
  onLoadingChange?: (loading: boolean) => void;
};

export function FerramentasSearchCard({
  filial,
  getAccessToken,
  onNavigateToFerramenta,
  refreshSignal = 0,
  onLoadingChange,
}: FerramentasSearchCardProps) {
  const { touchFreshness } = useMaintenanceFreshness();
  const ferramentasTable = useServerTable({ defaultSortKey: "codigo" });
  const [codigo, setCodigo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [incluirBloqueados, setIncluirBloqueados] = useState(false);
  const [items, setItems] = useState<FerramentaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const columns = useMemo<DataTableColumn<FerramentaItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        headerHint: DM_HELP.miniAplicadores.buscaFerramentaCodigo,
        sortable: true,
        sortValue: (item) => item.codigo,
        render: (item) => (
          <span className="dm-ferramenta-codigo">
            {item.bloqueado ? (
              <Lock size={14} className="dm-ferramenta-codigo__lock" aria-hidden="true" />
            ) : null}
            <span>{item.codigo}</span>
          </span>
        ),
      },
      {
        key: "descricao",
        header: "Descrição",
        headerHint: DM_HELP.miniAplicadores.buscaFerramentaDescricao,
        sortable: true,
        sortValue: (item) => item.descricao,
        render: (item) => item.descricao,
      },
    ],
    [],
  );

  const loadFerramentas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFerramentas(
        {
          codigo: codigo.trim() || undefined,
          descricao: descricao.trim() || undefined,
          incluirBloqueados,
          filial,
          page: ferramentasTable.query.page,
          pageSize: ferramentasTable.query.pageSize,
          sortKey: ferramentasTable.query.sortKey,
          sortDirection: ferramentasTable.query.sortDirection,
        },
        getAccessToken,
      );
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
      touchFreshness();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Falha ao carregar ferramentas.";
      setError(message);
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [
    codigo,
    descricao,
    filial,
    incluirBloqueados,
    ferramentasTable.query,
    getAccessToken,
    touchFreshness,
  ]);

  useEffect(() => {
    onLoadingChange?.(loading);
  }, [loading, onLoadingChange]);

  useEffect(() => {
    ferramentasTable.resetPage();
  }, [filial, ferramentasTable.resetPage]);

  useEffect(() => {
    void loadFerramentas();
  }, [loadFerramentas, refreshSignal]);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    ferramentasTable.resetPage();
    await loadFerramentas();
  }

  return (
    <section className="dm-card">
      <div className="dm-section-header">
        <div className="dm-section-header__title-group">
          <h2 className="dm-section-header__title">Buscar ferramentas</h2>
          <p className="dm-section-header__hint">
            Ferramentas dos grupos 23 e 24. Use código, descrição ou inclua bloqueadas.
          </p>
        </div>
      </div>

      {error ? <p className="dm-inline-error">{error}</p> : null}

      <DataTableSection
            columnPreferencesKey="maintenance:MiniAplicadoresPage:miniaplicadorespage:v1"
            fontSizePreferencesKey="maintenance:mini-aplicadores:lista:table-font-size:v1"
            title="Ferramentas"
            titleHint={DM_HELP.miniAplicadores.listaTitle}
            columns={columns}
            rows={items}
            loading={loading}
            emptyMessage="Nenhuma ferramenta encontrada."
            getRowKey={(item) => item.codigo}
            getRowClassName={(item) => (item.bloqueado ? "is-blocked" : undefined)}
            onRowClick={(item) => onNavigateToFerramenta(item.codigo)}
            viewLayoutPreferencesKey={MAINTENANCE_LIST_LAYOUT_KEYS.ferramentas}
            renderCard={(item) => (
              <FerramentaListCard
                item={item}
                onActivate={() => onNavigateToFerramenta(item.codigo)}
              />
            )}
            embedded
            toolbar={
              <FilterBar onSubmit={handleSearch} className="dm-filter-bar--search">
                <DmNativeTextField
                  id="dm-busca-ferramenta-codigo"
                  label="Buscar por código"
                  hint={DM_HELP.miniAplicadores.buscaFerramentaCodigo}
                  value={codigo}
                  onChange={setCodigo}
                  placeholder="Ex.: 23 ou 23-026"
                />
                <DmNativeTextField
                  id="dm-busca-ferramenta-descricao"
                  label="Buscar por descrição"
                  hint={DM_HELP.miniAplicadores.buscaFerramentaDescricao}
                  value={descricao}
                  onChange={setDescricao}
                  placeholder="Ex.: 23-"
                />
                <div className="dm-filter-bar__actions">
                  <MaintenanceNativeCheckboxControl
                    className="dm-checkbox-field"
                    checked={incluirBloqueados}
                    onChange={(checked) => {
                      setIncluirBloqueados(checked);
                      ferramentasTable.resetPage();
                    }}
                    label="Mostrar bloqueadas"
                  />
                  <MaintenanceActionButton type="submit" variant="primary">
                    Buscar
                  </MaintenanceActionButton>
                </div>
              </FilterBar>
            }
            serverTable={{
              page: ferramentasTable.query.page,
              pageSize: ferramentasTable.query.pageSize,
              total,
              onPageChange: ferramentasTable.setPage,
              sortKey: ferramentasTable.query.sortKey,
              sortDirection: ferramentasTable.query.sortDirection,
              onSortChange: ferramentasTable.handleSortChange,
            }}
          />
    </section>
  );
}
