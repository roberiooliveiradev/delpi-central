// src/ui/admin/tabs/AppsTab.tsx

import { useContext, useMemo, useState } from "react";
import {
  Code2,
  Edit,
  LayoutGrid,
  PackagePlus,
  Power,
  PowerOff,
  Trash2,
  UserRound,
} from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient, HttpError } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminApp } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { ManifestRegisterModal } from "../modals/ManifestRegisterModal";
import { resolveIcon } from "../../../utils/iconResolver";
import { AdminEntityList } from "../../../components/admin/AdminEntityList";

type AppSortField =
  | "name"
  | "version"
  | "active"
  | "created_at"
  | "updated_at";

type AppDateFilters = {
  createdFrom: string;
  createdTo: string;
  updatedFrom: string;
  updatedTo: string;
};

const EMPTY_DATE_FILTERS: AppDateFilters = {
  createdFrom: "",
  createdTo: "",
  updatedFrom: "",
  updatedTo: "",
};

const SORT_OPTIONS: { field: AppSortField; label: string }[] = [
  { field: "name", label: "Nome" },
  { field: "version", label: "Versão" },
  { field: "active", label: "Status" },
  { field: "created_at", label: "Criado em" },
  { field: "updated_at", label: "Atualizado em" },
];

const PAGE_SIZE = 10;

const normalizeAppTypeLabel = (type?: string | null) => {
  if (!type) return "Não informado";

  if (type === "iframe") return "Iframe";
  if (type === "microfrontend") return "Microfrontend";
  if (type === "backend-only") return "Backend-only";

  return type;
};

const getAppStatusLabel = (app: AdminApp) => {
  return app.active === false ? "Inativa" : "Ativa";
};

const formatBrazilDateTime = (value?: string | null) => {
  if (!value) return "Não informado";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Data inválida";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const formatResponsibleUser = (app: AdminApp) => {
  const updatedName = app.updated_by_name?.trim();
  const createdName = app.created_by_name?.trim();

  if (updatedName) return updatedName;
  if (createdName) return createdName;

  return "Não informado";
};

const buildAppAuditMeta = (app: AdminApp): string[] => {
  const lines = [
    `Criado em: ${formatBrazilDateTime(app.created_at)}`,
    `Atualizado em: ${formatBrazilDateTime(app.updated_at)}`,
  ];

  if (app.created_by_name && app.created_by_name !== app.updated_by_name) {
    lines.push(`Criado por: ${app.created_by_name}`);
  }

  return lines;
};

const getSortDirectionLabel = (
  field: AppSortField,
  direction: "asc" | "desc"
) => {
  if (field === "name" || field === "version") {
    return direction === "asc" ? "A-Z" : "Z-A";
  }

  if (field === "active") {
    return direction === "asc" ? "Inativas" : "Ativas";
  }

  return direction === "asc" ? "Antigas" : "Recentes";
};

const hasActiveDateFilters = (filters: AppDateFilters) =>
  Boolean(
    filters.createdFrom ||
      filters.createdTo ||
      filters.updatedFrom ||
      filters.updatedTo
  );

export const AppsTab = () => {
  const { getAccessToken } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false);
  const [deleteOneId, setDeleteOneId] = useState<string | null>(null);

  const [manifestModal, setManifestModal] = useState<{
    open: boolean;
    mode: "register" | "edit";
    initialManifest?: any;
  }>({ open: false, mode: "register" });

  const [sortState, setSortState] = useState<{
    sort: AppSortField;
    direction: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
  });

  const [dateFilters, setDateFilters] =
    useState<AppDateFilters>(EMPTY_DATE_FILTERS);

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const appsResource = usePaginatedResource<AdminApp>(
    ({ page, pageSize }) =>
      api.listApps({
        page,
        pageSize,
        q: search,
        sort: sortState.sort,
        direction: sortState.direction,
        createdFrom: dateFilters.createdFrom || undefined,
        createdTo: dateFilters.createdTo || undefined,
        updatedFrom: dateFilters.updatedFrom || undefined,
        updatedTo: dateFilters.updatedTo || undefined,
      }),
    PAGE_SIZE,
    [
      search,
      sortState.sort,
      sortState.direction,
      dateFilters.createdFrom,
      dateFilters.createdTo,
      dateFilters.updatedFrom,
      dateFilters.updatedTo,
    ]
  );

  const apps = appsResource.data ?? [];

  const totalApps = appsResource.pagination?.total ?? apps.length;
  const totalPages = appsResource.pagination?.total_pages ?? 1;
  const currentPage = appsResource.page;

  const activeCount = apps.filter((app) => app.active !== false).length;
  const inactiveCount = apps.filter((app) => app.active === false).length;

  const openRegister = () =>
    setManifestModal({ open: true, mode: "register" });

  const openEdit = async (app: AdminApp) => {
    const manifest = await api.getPluginManifest(app.id);

    setManifestModal({
      open: true,
      mode: "edit",
      initialManifest: manifest,
    });
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    appsResource.setPage(1);
  };

  const toggleSort = (field: AppSortField) => {
    setSortState((prev) => {
      if (prev.sort === field) {
        return {
          sort: field,
          direction: prev.direction === "asc" ? "desc" : "asc",
        };
      }

      return {
        sort: field,
        direction: "asc",
      };
    });

    appsResource.setPage(1);
  };

  const applyDateFilters = (patch: Partial<AppDateFilters>) => {
    setDateFilters((prev) => ({
      ...prev,
      ...patch,
    }));
    appsResource.setPage(1);
  };

  const clearDateFilters = () => {
    setDateFilters(EMPTY_DATE_FILTERS);
    appsResource.setPage(1);
  };

  const toggleAppSelection = (appId: string) => {
    setSelected((prev) =>
      prev.includes(appId)
        ? prev.filter((id) => id !== appId)
        : [...prev, appId]
    );
  };

  const clearSelection = () => {
    setSelected([]);
  };

  const selectVisibleApps = () => {
    const visibleIds = apps.map((app) => app.id);

    setSelected((prev) => {
      const next = new Set(prev);

      visibleIds.forEach((id) => {
        next.add(id);
      });

      return Array.from(next);
    });
  };

  const handleBulkActivate = async () => {
    if (selected.length === 0) return;

    try {
      await api.bulkActivatePlugins(selected);
      setSelected([]);
      appsResource.refetch();
    } catch (err) {
      if (err instanceof HttpError) {
        alert(err.message);
      } else {
        alert("Erro inesperado ao ativar aplicações.");
      }
    }
  };

  const handleBulkDeactivate = async () => {
    if (selected.length === 0) return;

    try {
      await api.bulkDeactivatePlugins(selected);
      setSelected([]);
      appsResource.refetch();
    } catch (err) {
      if (err instanceof HttpError) {
        alert(err.message);
      } else {
        alert("Erro inesperado ao desativar aplicações.");
      }
    }
  };

  const handleBulkDelete = async () => {
    if (selected.length === 0) return;

    try {
      await api.bulkUnregisterPlugins(selected);
      setSelected([]);
      appsResource.refetch();
    } catch (err) {
      if (err instanceof HttpError) {
        alert(err.message);
      } else {
        alert("Erro inesperado ao excluir aplicações.");
      }
    } finally {
      setConfirmBulkDelete(false);
    }
  };

  const handleDeleteOne = async () => {
    if (!deleteOneId) return;

    try {
      await api.deletePlugin(deleteOneId);
      appsResource.refetch();
    } catch (err) {
      if (err instanceof HttpError) {
        alert(err.message);
      } else {
        alert("Erro inesperado ao excluir aplicação.");
      }
    } finally {
      setDeleteOneId(null);
    }
  };

  const goToPreviousPage = () => {
    appsResource.setPage(Math.max(1, currentPage - 1));
  };

  const goToNextPage = () => {
    appsResource.setPage(Math.min(totalPages, currentPage + 1));
  };

  const sortLabel = getSortDirectionLabel(sortState.sort, sortState.direction);

  return (
    <>
      <AdminEntityList<AdminApp>
        title="Aplicações"
        description="Gerencie plugins, manifestos, versões, status e disponibilidade das aplicações integradas à DELPI Central."
        summary={[
          { value: totalApps, label: "aplicações" },
          { value: activeCount, label: "ativas nesta página" },
          { value: inactiveCount, label: "inativas nesta página" },
        ]}
        search={{
          value: search,
          placeholder: "Buscar por nome, id ou base path...",
          onChange: handleSearchChange,
        }}
        toolbarActions={[
          ...SORT_OPTIONS.map(({ field, label }) => ({
            label: `Ordenar: ${label}${
              sortState.sort === field ? ` ${sortLabel}` : ""
            }`,
            active: sortState.sort === field,
            onClick: () => toggleSort(field),
          })),
          {
            label: (
              <>
                <PackagePlus size={15} />
                Adicionar Plugin
              </>
            ),
            primary: true,
            onClick: openRegister,
          },
        ]}
        filterSlot={
          <>
            <div className="admin-entity-filters__group">
              <span className="admin-entity-filters__label">Criado em:</span>
              <input
                type="date"
                value={dateFilters.createdFrom}
                onChange={(event) =>
                  applyDateFilters({ createdFrom: event.target.value })
                }
                aria-label="Data inicial de criação"
              />
              <span className="admin-entity-filters__range-separator">até</span>
              <input
                type="date"
                value={dateFilters.createdTo}
                onChange={(event) =>
                  applyDateFilters({ createdTo: event.target.value })
                }
                aria-label="Data final de criação"
              />
            </div>
            <div className="admin-entity-filters__group">
              <span className="admin-entity-filters__label">Atualizado em:</span>
              <input
                type="date"
                value={dateFilters.updatedFrom}
                onChange={(event) =>
                  applyDateFilters({ updatedFrom: event.target.value })
                }
                aria-label="Data inicial de atualização"
              />
              <span className="admin-entity-filters__range-separator">até</span>
              <input
                type="date"
                value={dateFilters.updatedTo}
                onChange={(event) =>
                  applyDateFilters({ updatedTo: event.target.value })
                }
                aria-label="Data final de atualização"
              />
            </div>
            {hasActiveDateFilters(dateFilters) ? (
              <div className="admin-entity-filters__group">
                <button type="button" onClick={clearDateFilters}>
                  Limpar filtros de data
                </button>
              </div>
            ) : null}
          </>
        }
        listTitle="Catálogo de aplicações"
        listSubtitle={`Página ${currentPage} de ${totalPages}`}
        items={apps}
        loading={appsResource.loading}
        emptyText="Nenhuma aplicação encontrada."
        getId={(app) => app.id}
        selectedIds={selected}
        selectionLabel="aplicações selecionadas"
        onToggleSelected={toggleAppSelection}
        onSelectVisible={selectVisibleApps}
        onClearSelection={clearSelection}
        bulkActions={[
          {
            label: (
              <>
                <Power size={14} />
                Ativar
              </>
            ),
            onClick: handleBulkActivate,
          },
          {
            label: (
              <>
                <PowerOff size={14} />
                Desativar
              </>
            ),
            onClick: handleBulkDeactivate,
          },
          {
            label: (
              <>
                <Trash2 size={14} />
                Excluir
              </>
            ),
            danger: true,
            onClick: () => setConfirmBulkDelete(true),
          },
        ]}
        pagination={
          appsResource.pagination
            ? {
                page: currentPage,
                totalPages,
                onPrevious: goToPreviousPage,
                onNext: goToNextPage,
              }
            : undefined
        }
        renderIcon={(app) => {
          const Icon = resolveIcon(app.icon) || LayoutGrid;
          return <Icon size={20} strokeWidth={2.2} />;
        }}
        renderTitle={(app) => app.name}
        renderSubtitle={(app) => app.id}
        renderBadges={(app) => [
          {
            label: getAppStatusLabel(app),
            tone: app.active === false ? "danger" : "success",
          },
          {
            label: normalizeAppTypeLabel(app.type),
          },
        ]}
        renderDescription={(app) => (
          <>
            <Code2 size={13} />
            {app.base_path || "Sem base path"}
          </>
        )}
        renderMeta={(app) => [
          `Versão: ${app.version || "Não informada"}`,
          `Ícone: ${app.icon || "Padrão"}`,
          ...buildAppAuditMeta(app),
          <>
            <UserRound size={13} />
            Responsável: {formatResponsibleUser(app)}
          </>,
        ]}
        renderActions={(app) => [
          {
            label: (
              <>
                <Edit size={14} />
                Editar
              </>
            ),
            onClick: () => openEdit(app),
          },
          {
            label: (
              <>
                <Trash2 size={14} />
                Excluir
              </>
            ),
            danger: true,
            onClick: () => setDeleteOneId(app.id),
          },
        ]}
      />

      <ManifestRegisterModal
        open={manifestModal.open}
        mode={manifestModal.mode}
        initialManifest={manifestModal.initialManifest}
        onClose={() =>
          setManifestModal({ open: false, mode: "register" })
        }
        onSubmit={async (manifest) => {
          if (manifestModal.mode === "edit") {
            await api.updatePluginManifest(manifest.id, manifest);
          } else {
            await api.registerManifest(manifest);
          }

          appsResource.refetch();
        }}
      />

      <ConfirmDialog
        open={confirmBulkDelete}
        title="Excluir aplicações"
        message={`Deseja excluir ${selected.length} aplicações?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmBulkDelete(false)}
        onConfirm={handleBulkDelete}
      />

      <ConfirmDialog
        open={!!deleteOneId}
        title="Excluir aplicação"
        message="Deseja realmente excluir esta aplicação?"
        confirmText="Excluir"
        danger
        onCancel={() => setDeleteOneId(null)}
        onConfirm={handleDeleteOne}
      />
    </>
  );
};