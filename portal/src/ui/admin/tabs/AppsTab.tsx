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

export const AppsTab = () => {
  const { token } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const [manifestModal, setManifestModal] = useState<{
    open: boolean;
    mode: "register" | "edit";
    initialManifest?: any;
  }>({ open: false, mode: "register" });

  const api = useMemo(() => {
    if (!token) return null;
    return new AdminApi(new ApiClient("", () => token));
  }, [token]);

  const appsResource = usePaginatedResource<AdminApp>(
    ({ page, pageSize }) =>
      api!.listApps({ page, pageSize, q: search, sort: "name", direction: "asc" }),
    10,
    [search]
  );

  if (!api) return null;

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

  const handleBulkDelete = async () => {
    await api.bulkDeleteApps(selected);
    setSelected([]);
    setConfirmDelete(false);
    appsResource.refetch();
  };

  return (
    <div>
      <h2>Aplicações ({appsResource.pagination?.total ?? 0})</h2>

      <DataTable
        columns={[
          { key: "name", header: "Nome", sortable: true },
          { key: "version", header: "Versão", sortable: true },
          { key: "base_path", header: "Base Path" },
          {
            key: "active",
            header: "Status",
            sortable: true,
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
          <ActionButtons onEdit={() => openEdit(row)} />
        )}
        toolbar={
          selected.length > 0 ? (
            <>
              <button
                onClick={async () => {
                  await api.bulkActivateApps(selected);
                  setSelected([]);
                  appsResource.refetch();
                }}
              >
                Ativar ({selected.length})
              </button>

              <button
                onClick={async () => {
                  await api.bulkDeactivateApps(selected);
                  setSelected([]);
                  appsResource.refetch();
                }}
              >
                Desativar ({selected.length})
              </button>

              <button
                className="btn-danger"
                onClick={() => setConfirmDelete(true)}
              >
                Excluir ({selected.length})
              </button>
            </>
          ) : (
            <button onClick={openRegister}>Adicionar Plugin</button>
          )
        }
        pagination={
          appsResource.pagination && {
            page: appsResource.page,
            totalPages: appsResource.pagination.total_pages,
            total: appsResource.pagination.total,
            pageSize: 10,
          }
        }
        onPageChange={appsResource.setPage}
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
        open={confirmDelete}
        title="Excluir aplicações"
        message={`Deseja excluir ${selected.length} aplicações?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmDelete(false)}
        onConfirm={handleBulkDelete}
      />
    </div>
  );
};