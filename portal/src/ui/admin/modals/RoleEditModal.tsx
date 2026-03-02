// src/ui/admin/modals/RoleEditModal.tsx
import { useMemo, useState, useEffect } from "react";
import type { AdminPermission, AdminRole } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import { DataTable } from "../../../components/DataTable";
import "./RoleEditModal.css";

type Props = {
  open: boolean;
  role: AdminRole | null;
  allPerms: AdminPermission[];
  selectedPermIds: string[];
  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeRole: (patch: Partial<AdminRole>) => void;
  onTogglePerm: (permId: string) => void;
};

export const RoleEditModal = ({
  open,
  role,
  allPerms,
  selectedPermIds,
  saving = false,
  onClose,
  onSave,
  onChangeRole,
  onTogglePerm,
}: Props) => {
  const [permSearch, setPermSearch] = useState("");

  const [permSort, setPermSort] = useState<{
    sort?: string;
    direction?: "asc" | "desc";
  }>({
    sort: "code",
    direction: "asc",
  });

  const [permPage, setPermPage] = useState(1);
  const [permPageSize, setPermPageSize] = useState(10);

  // Reset página ao pesquisar
  useEffect(() => {
    setPermPage(1);
  }, [permSearch]);

  // =========================
  // Processamento completo:
  // busca + selecionados primeiro + ordenação
  // =========================
  const processedPerms = useMemo(() => {
    const s = permSearch.trim().toLowerCase();

    let base = s
      ? allPerms.filter(
          (p) =>
            (p.code || "").toLowerCase().includes(s) ||
            (p.name || "").toLowerCase().includes(s)
        )
      : [...allPerms];

    base.sort((a, b) => {
      // 🔥 1️⃣ Selecionados primeiro
      const aSel = selectedPermIds.includes(a.id);
      const bSel = selectedPermIds.includes(b.id);

      if (aSel && !bSel) return -1;
      if (!aSel && bSel) return 1;

      // 🔥 2️⃣ Ordenação ativa
      const key = permSort.sort as keyof AdminPermission;
      if (!key) return 0;

      const aVal = (a[key] ?? "").toString();
      const bVal = (b[key] ?? "").toString();

      const result = aVal.localeCompare(bVal);

      return permSort.direction === "desc" ? -result : result;
    });

    return base;
  }, [allPerms, permSearch, selectedPermIds, permSort]);

  // =========================
  // Paginação
  // =========================
  const permTotalPages = Math.max(
    1,
    Math.ceil(processedPerms.length / permPageSize)
  );

  const paginatedPerms = useMemo(() => {
    const start = (permPage - 1) * permPageSize;
    return processedPerms.slice(start, start + permPageSize);
  }, [processedPerms, permPage, permPageSize]);

  if (!open || !role) return null;

  const isEdit = !!role.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Papel — ${role.name}` : "Novo Papel"}
      onClose={onClose}
      size="xl"
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button onClick={onSave} disabled={saving || !role.name?.trim()}>
            Salvar
          </button>
        </>
      }
    >
      <div className="role-edit-body">
        {/* =========================
            Campos do papel
        ========================= */}
        <label>
          Nome
          <input
            value={role.name}
            onChange={(e) => onChangeRole({ name: e.target.value })}
            disabled={saving}
          />
        </label>

        <label>
          Descrição
          <textarea
            value={role.description || ""}
            onChange={(e) =>
              onChangeRole({ description: e.target.value })
            }
            disabled={saving}
          />
        </label>

        <div className="role-edit-divider" />

        {/* =========================
            DataTable de Permissões
        ========================= */}
        <DataTable<AdminPermission>
          columns={[
            {
              key: "code",
              header: "Código",
              sortable: true,
              render: (p) => (
                <span className="role-edit-perm-code">
                  {p.code}
                </span>
              ),
            },
            {
              key: "name",
              header: "Nome",
              sortable: true,
              render: (p) => (
                <span className="role-edit-perm-name">
                  {p.name ?? "-"}
                </span>
              ),
            },
            {
              key: "module",
              header: "Módulo",
              sortable: true,
              render: (p) => p.module ?? "-",
            },
          ]}
          data={paginatedPerms}
          loading={saving}
          searchValue={permSearch}
          onSearchChange={setPermSearch}
          sort={permSort}
          onSortChange={setPermSort}
          selectable
          getRowId={(p) => p.id}
          selectedRows={selectedPermIds}
          onSelectionChange={(ids) => {
            const current = new Set(selectedPermIds);
            const next = new Set(ids);

            // adicionados
            ids.forEach((id) => {
              if (!current.has(id)) onTogglePerm(id);
            });

            // removidos
            selectedPermIds.forEach((id) => {
              if (!next.has(id)) onTogglePerm(id);
            });
          }}
          pagination={{
            page: permPage,
            totalPages: permTotalPages,
            total: processedPerms.length,
            pageSize: permPageSize,
          }}
          onPageChange={setPermPage}
          onPageSizeChange={(size) => {
            setPermPageSize(size);
            setPermPage(1);
          }}
          pageSizeOptions={[5, 10, 20, 50]}
          emptyText="Nenhuma permissão encontrada"
          toolbar={
            <>
              <h4>Permissões do Papel</h4>
              <div className="dt-muted">
                {processedPerms.length} permissões
              </div>
            </>
          }
        />
      </div>
    </Modal>
  );
};