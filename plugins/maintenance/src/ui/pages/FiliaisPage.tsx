import { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, RefreshCw } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import {
  type DataTableColumn,
  DataTableSection,
  FilterBar,
  PendingChangeBadge,
  StateBox,
} from "../../components/data";
import { EditableCell } from "../../components/EditableCell";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import {
  createFilial,
  deleteFilial,
  fetchFiliaisAdmin,
  updateFilial,
  type FilialItem,
} from "../../data/api/maintenanceApi";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import { useServerTable } from "../../hooks/useServerTable";

type FiliaisPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

type FilialDraft = {
  nome_filial: string;
  status_filial: "ativo" | "inativo";
};

function isFilialDirty(item: FilialItem, edits: Record<number, FilialDraft>): boolean {
  const draft = edits[item.filial_id];
  if (!draft) return false;
  return draft.nome_filial !== item.nome_filial || draft.status_filial !== item.status_filial;
}

export function FiliaisPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
}: FiliaisPageProps) {
  const { canManageFiliais, loading: scopeLoading } = useMaintenanceActiveFilial(
    getAccessToken,
    filialScope,
  );
  const filiaisTable = useServerTable({ defaultSortKey: "codigo" });
  const [filiais, setFiliais] = useState<FilialItem[]>([]);
  const [filiaisTotal, setFiliaisTotal] = useState(0);
  const [edits, setEdits] = useState<Record<number, FilialDraft>>({});
  const [novoCodigo, setNovoCodigo] = useState("");
  const [novoNome, setNovoNome] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFiliaisAdmin(
        {
          page: filiaisTable.query.page,
          pageSize: filiaisTable.query.pageSize,
          sortKey: filiaisTable.query.sortKey,
          sortDirection: filiaisTable.query.sortDirection,
        },
        getAccessToken,
        true,
      );
      const items = data.items ?? [];
      setFiliais(items);
      setFiliaisTotal(data.total ?? 0);
      setEdits((current) => {
        const next = { ...current };
        for (const item of items) {
          if (!next[item.filial_id]) {
            next[item.filial_id] = {
              nome_filial: item.nome_filial,
              status_filial: item.status_filial,
            };
          }
        }
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar filiais.");
      setFiliais([]);
      setFiliaisTotal(0);
      setEdits({});
    } finally {
      setLoading(false);
    }
  }, [filiaisTable.query, getAccessToken]);

  useEffect(() => {
    if (canManageFiliais) {
      void loadData();
    }
  }, [canManageFiliais, loadData]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    const codigo = novoCodigo.trim();
    const nome = novoNome.trim();
    if (!/^[0-9]{2}$/.test(codigo) || !nome) {
      setError("Informe código com 2 dígitos e nome da filial.");
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      await createFilial({ codigo_filial: codigo, nome_filial: nome }, getAccessToken);
      setNovoCodigo("");
      setNovoNome("");
      setSuccess("Filial criada.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar filial.");
    }
  }

  async function handleSave(filialId: number) {
    const draft = edits[filialId];
    if (!draft) return;
    setError(null);
    setSuccess(null);
    try {
      await updateFilial(filialId, draft, getAccessToken);
      setSuccess("Filial atualizada.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar filial.");
    }
  }

  async function handleDelete(item: FilialItem) {
    if (!window.confirm(`Excluir filial ${item.codigo_filial} — ${item.nome_filial}?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteFilial(item.filial_id, getAccessToken);
      setSuccess("Filial excluída.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir filial.");
    }
  }

  const columns = useMemo<DataTableColumn<FilialItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        sortable: true,
        sortValue: (item) => item.codigo_filial,
        render: (item) => item.codigo_filial,
      },
      {
        key: "nome",
        header: "Nome",
        sortable: true,
        sortValue: (item) => (edits[item.filial_id] ?? item).nome_filial,
        render: (item) => {
          const draft = edits[item.filial_id] ?? item;
          return (
            <EditableCell
              value={draft.nome_filial}
              aria-label={`Nome da filial ${item.codigo_filial}`}
              onChange={(nome_filial) =>
                setEdits((prev) => ({
                  ...prev,
                  [item.filial_id]: {
                    ...draft,
                    nome_filial,
                  },
                }))
              }
              badge={<PendingChangeBadge visible={isFilialDirty(item, edits)} />}
            />
          );
        },
      },
      {
        key: "status",
        header: "Status",
        sortable: true,
        sortValue: (item) => (edits[item.filial_id] ?? item).status_filial,
        render: (item) => {
          const draft = edits[item.filial_id] ?? item;
          return (
            <EditableCell
              as="select"
              value={draft.status_filial}
              aria-label={`Status da filial ${item.codigo_filial}`}
              onChange={(status_filial) =>
                setEdits((prev) => ({
                  ...prev,
                  [item.filial_id]: {
                    ...draft,
                    status_filial: status_filial as FilialDraft["status_filial"],
                  },
                }))
              }
              options={[
                { value: "ativo", label: "Ativo" },
                { value: "inativo", label: "Inativo" },
              ]}
            />
          );
        },
      },
      {
        key: "acoes",
        header: "Ações",
        interactive: true,
        render: (item) => (
          <div className="dm-row-actions">
            <button type="button" className="dm-ghost-btn" onClick={() => void handleSave(item.filial_id)}>
              Salvar
            </button>
            <button
              type="button"
              className="dm-ghost-btn dm-ghost-btn--danger"
              onClick={() => void handleDelete(item)}
            >
              Excluir
            </button>
          </div>
        ),
      },
    ],
    [edits],
  );

  if (scopeLoading) {
    return (
      <MaintenanceShell>
        <PageHeader
          title="Filiais"
          subtitle="Cadastro de filiais operacionais do módulo Manutenção."
          icon={Building2}
          currentPath={pathname}
          filialScope={filialScope}
          onNavigate={onNavigate}
        />
        <StateBox>Carregando…</StateBox>
      </MaintenanceShell>
    );
  }

  if (!canManageFiliais) {
    return (
      <MaintenanceShell>
        <PageHeader
          title="Filiais"
          subtitle="Cadastro de filiais operacionais do módulo Manutenção."
          icon={Building2}
          currentPath={pathname}
          filialScope={filialScope}
          onNavigate={onNavigate}
        />
        <StateBox variant="error">
          Acesso restrito. É necessária a permissão <code>maintenance.manage</code>.
        </StateBox>
      </MaintenanceShell>
    );
  }

  return (
    <MaintenanceShell>
      <PageHeader
        title="Filiais"
        subtitle="Cadastro de filiais operacionais. Os nomes cadastrados aqui aparecem no seletor de filial e nas telas do módulo."
        icon={Building2}
        currentPath={pathname}
        filialScope={filialScope}
        onNavigate={onNavigate}
        actions={
          <button type="button" className="dm-primary-btn" onClick={() => void loadData()} disabled={loading}>
            <RefreshCw size={16} className={loading ? "dm-spin" : undefined} />
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        }
      />

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

      <DataTableSection
        title="Catálogo de filiais"
        hint="Filial inativa não aparece no seletor operacional. Exclusão só é permitida sem motivos, status ou reposições vinculados."
        toolbar={
          <FilterBar embedded onSubmit={handleCreate}>
            <label className="dm-field">
              <span>Código</span>
              <NativeTextControl
                value={novoCodigo}
                onChange={(value) => setNovoCodigo(value.replace(/\D/g, "").slice(0, 2))}
                placeholder="01"
                inputMode="numeric"
                maxLength={2}
              />
            </label>
            <label className="dm-field">
              <span>Nome</span>
              <NativeTextControl
                value={novoNome}
                onChange={setNovoNome}
                placeholder="Matriz"
              />
            </label>
            <button type="submit" className="dm-primary-btn">
              Adicionar filial
            </button>
          </FilterBar>
        }
        columns={columns}
        rows={filiais}
        loading={loading}
        emptyMessage="Nenhuma filial cadastrada."
        getRowKey={(item) => String(item.filial_id)}
        serverTable={{
          page: filiaisTable.query.page,
          pageSize: filiaisTable.query.pageSize,
          total: filiaisTotal,
          onPageChange: filiaisTable.setPage,
          sortKey: filiaisTable.query.sortKey,
          sortDirection: filiaisTable.query.sortDirection,
          onSortChange: filiaisTable.handleSortChange,
        }}
      />
    </MaintenanceShell>
  );
}
