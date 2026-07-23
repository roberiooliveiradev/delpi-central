import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Cpu, Plus, Trash2 } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import {
  type DataTableColumn,
  DataTableSection,
  FilterBar,
  StateBox,
} from "../../components/data";
import { FilialSwitcher } from "../../components/FilialSwitcher";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import {
  createProgramaMaquinaProduto,
  deleteProgramaMaquinaProduto,
  fetchProgramasMaquinasProdutos,
  fetchProgramasMaquinasRanking,
  updateProgramaMaquinaProduto,
  type ProgramaMaquinaProduto,
  type RankingIntermediarioItem,
} from "../../data/api/maintenanceApi";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import { useServerTable } from "../../hooks/useServerTable";
import {
  resolveFilialDisplayName,
  setStoredFilial,
} from "../../utils/maintenanceFilialSelection";

type ProgramasMaquinasPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

function formatQty(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(value);
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return parsed.toLocaleString("pt-BR");
}

export function ProgramasMaquinasPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
}: ProgramasMaquinasPageProps) {
  const {
    filiais,
    activeFilial,
    setActiveFilial,
    submodules,
    loading: scopeLoading,
  } = useMaintenanceActiveFilial(getAccessToken, filialScope);

  const canManage = useMemo(() => {
    const sub = submodules.find((item) => item.id === "programas-maquinas");
    return Boolean(sub?.can_manage);
  }, [submodules]);

  const rankingTable = useServerTable({
    defaultSortKey: "qty_produced",
    defaultSortDirection: "desc",
    pageSize: 10,
  });
  const cadastroTable = useServerTable({ defaultSortKey: "codigo_intermediario" });

  const [rankingCodigo, setRankingCodigo] = useState("");
  const [rankingSearch, setRankingSearch] = useState("");
  const [rankingItems, setRankingItems] = useState<RankingIntermediarioItem[]>([]);
  const [rankingTotal, setRankingTotal] = useState(0);
  const [rankingLoading, setRankingLoading] = useState(false);

  const [cadastroCodigo, setCadastroCodigo] = useState("");
  const [cadastroSearch, setCadastroSearch] = useState("");
  const [cadastroItems, setCadastroItems] = useState<ProgramaMaquinaProduto[]>([]);
  const [cadastroTotal, setCadastroTotal] = useState(0);
  const [cadastroLoading, setCadastroLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [addingCode, setAddingCode] = useState<string | null>(null);

  const filial = activeFilial ?? filiais[0]?.id;

  const loadRanking = useCallback(async () => {
    if (!filial) return;
    setRankingLoading(true);
    setError(null);
    try {
      const data = await fetchProgramasMaquinasRanking(
        {
          filial,
          search: rankingSearch || undefined,
          page: rankingTable.query.page,
          pageSize: rankingTable.query.pageSize,
          sortKey: rankingTable.query.sortKey ?? undefined,
          sortDirection: rankingTable.query.sortDirection,
        },
        getAccessToken,
      );
      setRankingItems(data.items ?? []);
      setRankingTotal(data.total ?? 0);
    } catch (err) {
      setRankingItems([]);
      setRankingTotal(0);
      setError(err instanceof Error ? err.message : "Falha ao carregar ranking.");
    } finally {
      setRankingLoading(false);
    }
  }, [filial, getAccessToken, rankingSearch, rankingTable.query]);

  const loadCadastro = useCallback(async () => {
    if (!filial) return;
    setCadastroLoading(true);
    try {
      const data = await fetchProgramasMaquinasProdutos(
        {
          filial,
          search: cadastroSearch || undefined,
          page: cadastroTable.query.page,
          pageSize: cadastroTable.query.pageSize,
          sortKey: cadastroTable.query.sortKey ?? undefined,
          sortDirection: cadastroTable.query.sortDirection,
          incluirInativos: true,
        },
        getAccessToken,
      );
      setCadastroItems(data.items ?? []);
      setCadastroTotal(data.total ?? 0);
    } catch (err) {
      setCadastroItems([]);
      setCadastroTotal(0);
      setError(err instanceof Error ? err.message : "Falha ao carregar cadastro.");
    } finally {
      setCadastroLoading(false);
    }
  }, [cadastroSearch, cadastroTable.query, filial, getAccessToken]);

  useEffect(() => {
    void loadRanking();
  }, [loadRanking]);

  useEffect(() => {
    void loadCadastro();
  }, [loadCadastro]);

  const handleFilialChange = (next: string) => {
    setActiveFilial(next);
    setStoredFilial(next);
  };

  const handleToggleAtivo = useCallback(
    async (item: ProgramaMaquinaProduto) => {
      if (!canManage) return;
      const itemFilial = (item.filial || filial || "").trim();
      if (!itemFilial) return;
      setError(null);
      setSuccess(null);
      try {
        await updateProgramaMaquinaProduto(
          item.id,
          { filial: itemFilial, ativo: !item.ativo },
          getAccessToken,
        );
        setSuccess("Cadastro atualizado.");
        await Promise.all([loadRanking(), loadCadastro()]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao atualizar.");
      }
    },
    [canManage, filial, getAccessToken, loadCadastro, loadRanking],
  );

  const handleDelete = useCallback(
    async (item: ProgramaMaquinaProduto) => {
      if (!canManage) return;
      const itemFilial = (item.filial || filial || "").trim();
      if (!itemFilial) return;
      if (!window.confirm(`Remover ${item.codigo_intermediario} do cadastro?`)) return;
      setError(null);
      setSuccess(null);
      try {
        await deleteProgramaMaquinaProduto(item.id, itemFilial, getAccessToken);
        setSuccess("Produto removido.");
        await Promise.all([loadRanking(), loadCadastro()]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao remover.");
      }
    },
    [canManage, filial, getAccessToken, loadCadastro, loadRanking],
  );

  const handleAdd = useCallback(
    async (item: RankingIntermediarioItem) => {
      if (!filial || !canManage) return;
      const code = item.intermediate_code?.trim();
      if (!code) return;
      setAddingCode(code);
      setError(null);
      setSuccess(null);
      try {
        await createProgramaMaquinaProduto(
          {
            filial,
            codigo_intermediario: code,
            descricao_intermediario: item.intermediate_description || null,
            codigo_produto_acabado: item.finished_product_code || null,
            codigo_ct_corte: item.cutting_work_center || null,
          },
          getAccessToken,
        );
        setSuccess(`Produto ${code} adicionado ao cadastro.`);
        await Promise.all([loadRanking(), loadCadastro()]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao cadastrar produto.");
      } finally {
        setAddingCode(null);
      }
    },
    [canManage, filial, getAccessToken, loadCadastro, loadRanking],
  );

  const rankingColumns = useMemo<DataTableColumn<RankingIntermediarioItem>[]>(
    () => [
      {
        key: "intermediate_code",
        header: "Intermediário",
        sortable: true,
        render: (row) => (
          <span>
            <strong>{row.intermediate_code}</strong>
            {row.intermediate_description ? (
              <> — {row.intermediate_description}</>
            ) : null}
          </span>
        ),
      },
      {
        key: "finished_product_code",
        header: "Produto acabado",
        sortable: true,
        render: (row) => row.finished_product_code || "—",
      },
      {
        key: "cutting_work_center",
        header: "CT corte",
        sortable: true,
        render: (row) => row.cutting_work_center || "—",
      },
      {
        key: "has_open_production_order",
        header: "OP aberta",
        render: (row) => (row.has_open_production_order ? "Sim" : "Não"),
      },
      {
        key: "qty_produced",
        header: "Qtd produzida",
        sortable: true,
        align: "right",
        render: (row) => formatQty(row.qty_produced),
      },
      {
        key: "actions",
        header: "Ações",
        interactive: true,
        render: (row) =>
          canManage ? (
            <button
              type="button"
              className="dm-ghost-btn"
              disabled={Boolean(row.already_registered) || addingCode === row.intermediate_code}
              onClick={() => void handleAdd(row)}
            >
              <Plus size={16} aria-hidden />{" "}
              {row.already_registered ? "Já cadastrado" : "Adicionar"}
            </button>
          ) : row.already_registered ? (
            "Cadastrado"
          ) : (
            "—"
          ),
      },
    ],
    [addingCode, canManage, handleAdd],
  );

  const cadastroColumns = useMemo<DataTableColumn<ProgramaMaquinaProduto>[]>(
    () => [
      {
        key: "codigo_intermediario",
        header: "Intermediário",
        sortable: true,
        render: (row) => row.codigo_intermediario,
      },
      {
        key: "descricao_intermediario",
        header: "Descrição",
        sortable: true,
        render: (row) => row.descricao_intermediario || "—",
      },
      {
        key: "codigo_produto_acabado",
        header: "PA",
        sortable: true,
        render: (row) => row.codigo_produto_acabado || "—",
      },
      {
        key: "codigo_ct_corte",
        header: "CT",
        sortable: true,
        render: (row) => row.codigo_ct_corte || "—",
      },
      {
        key: "data_ativacao",
        header: "Ativação",
        sortable: true,
        render: (row) => formatDateTime(row.data_ativacao),
      },
      {
        key: "usuario_ativacao_nome",
        header: "Ativado por",
        sortable: true,
        render: (row) => row.usuario_ativacao_nome || "—",
      },
      {
        key: "ativo",
        header: "Ativo",
        sortable: true,
        render: (row) => (row.ativo ? "Sim" : "Não"),
      },
      {
        key: "actions",
        header: "Ações",
        interactive: true,
        render: (row) =>
          canManage ? (
            <span className="dm-row-actions">
              <button
                type="button"
                className="dm-ghost-btn"
                onClick={() => void handleToggleAtivo(row)}
              >
                {row.ativo ? "Desativar" : "Ativar"}
              </button>
              <button
                type="button"
                className="dm-ghost-btn dm-ghost-btn--danger"
                onClick={() => void handleDelete(row)}
                aria-label={`Remover ${row.codigo_intermediario}`}
              >
                <Trash2 size={16} />
              </button>
            </span>
          ) : (
            "—"
          ),
      },
    ],
    [canManage, handleDelete, handleToggleAtivo],
  );

  const subtitle = filial
    ? `Filial ${resolveFilialDisplayName(filiais, filial)} — cadastre os programas dos produtos mais produzidos nas máquinas para guardar informações de setup.`
    : "Selecione a filial para cadastrar os programas dos produtos e guardar informações de setup.";

  function handleRankingSearch(event: FormEvent) {
    event.preventDefault();
    setRankingSearch(rankingCodigo.trim());
    rankingTable.resetPage();
  }

  function handleCadastroSearch(event: FormEvent) {
    event.preventDefault();
    setCadastroSearch(cadastroCodigo.trim());
    cadastroTable.resetPage();
  }

  return (
    <MaintenanceShell>
      <PageHeader
        title="Programas de máquina"
        subtitle={subtitle}
        icon={Cpu}
        currentPath={pathname}
        filialScope={filialScope ?? filial}
        onNavigate={onNavigate}
        actions={
          filiais.length > 1 ? (
            <FilialSwitcher
              filiais={filiais}
              value={filial ?? ""}
              onChange={handleFilialChange}
              compact
            />
          ) : null
        }
      />

      {scopeLoading ? <p className="dm-home-banner">Carregando escopo…</p> : null}

      {error ? (
        <StateBox variant="error" onDismiss={() => setError(null)}>
          {error}
        </StateBox>
      ) : null}
      {success ? (
        <StateBox variant="success" onDismiss={() => setSuccess(null)}>
          {success}
        </StateBox>
      ) : null}

      <section className="dm-card">
        <FilterBar onSubmit={handleRankingSearch} className="dm-filter-bar--search">
          <label className="dm-field">
            <span>Buscar PI / PA</span>
            <NativeTextControl
              value={rankingCodigo}
              onChange={setRankingCodigo}
              placeholder="Código intermediário ou PA"
            />
          </label>
          <div className="dm-filter-bar__actions">
            <button type="submit" className="dm-primary-btn">
              Buscar
            </button>
          </div>
        </FilterBar>

        <DataTableSection
          columnPreferencesKey="maintenance:ProgramasMaquinasPage:ranking:v1"
          title="Ranking de produção"
          hint="Top 100 intermediários (PI com código iniciando em 5, últimos 6 meses), 10 por página. Use Adicionar para cadastrar no programa."
          columns={rankingColumns}
          rows={rankingItems}
          loading={rankingLoading}
          emptyMessage="Nenhum intermediário encontrado no período."
          getRowKey={(row) => row.intermediate_code}
          serverTable={{
            page: rankingTable.query.page,
            pageSize: rankingTable.query.pageSize,
            total: rankingTotal,
            onPageChange: rankingTable.setPage,
            sortKey: rankingTable.query.sortKey,
            sortDirection: rankingTable.query.sortDirection,
            onSortChange: rankingTable.handleSortChange,
          }}
        />
      </section>

      <section className="dm-card">
        <FilterBar onSubmit={handleCadastroSearch} className="dm-filter-bar--search">
          <label className="dm-field">
            <span>Buscar cadastro</span>
            <NativeTextControl
              value={cadastroCodigo}
              onChange={setCadastroCodigo}
              placeholder="Código ou nome do programa"
            />
          </label>
          <div className="dm-filter-bar__actions">
            <button type="submit" className="dm-primary-btn">
              Buscar
            </button>
          </div>
        </FilterBar>

        <DataTableSection
          columnPreferencesKey="maintenance:ProgramasMaquinasPage:cadastro:v1"
          title="Cadastrados para programas"
          hint="Produtos selecionados para programação nas máquinas."
          columns={cadastroColumns}
          rows={cadastroItems}
          loading={cadastroLoading}
          emptyMessage="Nenhum produto cadastrado ainda."
          getRowKey={(row) => row.id}
          serverTable={{
            page: cadastroTable.query.page,
            pageSize: cadastroTable.query.pageSize,
            total: cadastroTotal,
            onPageChange: cadastroTable.setPage,
            sortKey: cadastroTable.query.sortKey,
            sortDirection: cadastroTable.query.sortDirection,
            onSortChange: cadastroTable.handleSortChange,
          }}
        />
      </section>
    </MaintenanceShell>
  );
}
