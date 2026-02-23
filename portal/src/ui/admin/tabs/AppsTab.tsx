// src/ui/admin/tabs/AppsTab.tsx
import { useContext, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminApp } from "../../../data/adminApi";

import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { DataTable } from "../../../components/DataTable";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { ManifestRegisterModal } from "../modals/ManifestRegisterModal";
import { ActionButtons } from "../../../components/ActionButtons";

type ManifestModalState =
  | { open: false }
  | { open: true; mode: "register" | "edit"; appId?: string; initialManifest?: any };

export const AppsTab = () => {
  const { token } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const [manifestModal, setManifestModal] = useState<ManifestModalState>({ open: false });

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const appsResource = usePaginatedResource<AdminApp>(
    ({ page, pageSize }) => api!.listApps({ page, pageSize, q: search }),
    10,
    [search]
  );

  if (!api) return null;

  const handleRegisterOrUpdateManifest = async (manifest: any) => {
    await api.registerManifest(manifest);
    appsResource.refetch();
  };

  const handleBulkDelete = async () => {
    await api.bulkDeleteApps(selected);
    setSelected([]);
    setConfirmOpen(false);
    appsResource.refetch();
  };

  const openRegister = () => {
    setManifestModal({ open: true, mode: "register" });
  };

  const openEdit = async (app: AdminApp) => {
    // ✅ busca o manifesto real salvo no backend
    const manifest = await api.getPluginManifest(app.id);
    setManifestModal({
      open: true,
      mode: "edit",
      appId: app.id,
      initialManifest: manifest,
    });
  };

  return (
    <div>
      <h2>Aplicações ({appsResource.pagination?.total ?? 0})</h2>

      <DataTable
        columns={[
          { key: "name", header: "Nome" },
          { key: "version", header: "Versão" },
          { key: "base_path", header: "Base Path" },
          {
            key: "active",
            header: "Status",
            render: (row) => (row.active ? "Ativo" : "Inativo"),
          },
        ]}
        data={appsResource.data}
        loading={appsResource.loading}
        searchValue={search}
        onSearchChange={setSearch}
        selectable
        getRowId={(row) => row.id}
        selectedRows={selected}
        onSelectionChange={setSelected}
        actions={(row) => (
          <ActionButtons
            onEdit={() => openEdit(row)}
          />
        )}
        toolbar={
          selected.length > 0 ? (
            <button className="btn-danger" onClick={() => setConfirmOpen(true)}>
              Excluir ({selected.length})
            </button>
          ) : (
            <button className="btn-primary" onClick={openRegister}>
              + Registrar Plugin
            </button>
          )
        }
        pagination={
          appsResource.pagination
            ? {
                page: appsResource.page,
                totalPages: appsResource.pagination.total_pages,
                total: appsResource.pagination.total,
                pageSize: 10,
              }
            : undefined
        }
        onPageChange={appsResource.setPage}
      />

      {/* ✅ Um modal só: register + edit */}
      <ManifestRegisterModal
        open={manifestModal.open}
        mode={manifestModal.open ? manifestModal.mode : "register"}
        initialManifest={manifestModal.open ? manifestModal.initialManifest : undefined}
        title={manifestModal.open && manifestModal.mode === "edit" ? "Editar Plugin via Manifesto" : "Registrar Plugin via Manifesto"}
        onClose={() => setManifestModal({ open: false })}
        onSubmit={handleRegisterOrUpdateManifest}
      />

      <ConfirmDialog
        open={confirmOpen}
        message={`Deseja excluir ${selected.length} aplicações?`}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleBulkDelete}
      />
    </div>
  );
};