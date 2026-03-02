import { useMemo, useState, useEffect } from "react";
import type { AdminGroup, AdminRole } from "../../../data/adminApi";
import { Modal } from "../../../components/Modal";
import { DataTable } from "../../../components/DataTable";
import "./GroupEditModal.css";

type Props = {
  open: boolean;
  group: AdminGroup | null;
  roles: AdminRole[];
  selectedRoleIds: string[];
  saving?: boolean;

  onClose: () => void;
  onSave: () => void;

  onChangeGroup: (patch: Partial<AdminGroup>) => void;
  onToggleRole: (roleId: string) => void;
};

export const GroupEditModal = ({
  open,
  group,
  roles,
  selectedRoleIds,
  saving = false,
  onClose,
  onSave,
  onChangeGroup,
  onToggleRole,
}: Props) => {
  const [roleSearch, setRoleSearch] = useState("");

  const [roleSort, setRoleSort] = useState<{
    sort?: string;
    direction?: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
  });

  const [rolePage, setRolePage] = useState(1);
  const [rolePageSize, setRolePageSize] = useState(10);

  // Reset página quando busca mudar
  useEffect(() => {
    setRolePage(1);
  }, [roleSearch]);

  // =========================
  // Processamento:
  // busca + selecionados primeiro + ordenação
  // =========================
  const processedRoles = useMemo(() => {
    const s = roleSearch.trim().toLowerCase();

    let base = s
      ? roles.filter((r) =>
          (r.name || "").toLowerCase().includes(s)
        )
      : [...roles];

    base.sort((a, b) => {
      // 🔥 1️⃣ Selecionados primeiro
      const aSel = selectedRoleIds.includes(a.id);
      const bSel = selectedRoleIds.includes(b.id);

      if (aSel && !bSel) return -1;
      if (!aSel && bSel) return 1;

      // 🔥 2️⃣ Ordenação ativa
      const key = roleSort.sort as keyof AdminRole;
      if (!key) return 0;

      const aVal = (a[key] ?? "").toString();
      const bVal = (b[key] ?? "").toString();

      const result = aVal.localeCompare(bVal);

      return roleSort.direction === "desc" ? -result : result;
    });

    return base;
  }, [roles, roleSearch, selectedRoleIds, roleSort]);

  // =========================
  // Paginação
  // =========================
  const roleTotalPages = Math.max(
    1,
    Math.ceil(processedRoles.length / rolePageSize)
  );

  const paginatedRoles = useMemo(() => {
    const start = (rolePage - 1) * rolePageSize;
    return processedRoles.slice(start, start + rolePageSize);
  }, [processedRoles, rolePage, rolePageSize]);

  if (!open || !group) return null;

  const isEdit = !!group.id;

  return (
    <Modal
      open={open}
      title={isEdit ? `Editar Grupo — ${group.name}` : "Novo Grupo"}
      onClose={onClose}
      size="xl"
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button onClick={onSave} disabled={saving || !group.name?.trim()}>
            Salvar
          </button>
        </>
      }
    >
      <div className="group-edit-body">
        {/* =========================
            Campos do grupo
        ========================= */}
        <label>
          Nome
          <input
            value={group.name}
            onChange={(e) =>
              onChangeGroup({ name: e.target.value })
            }
            disabled={saving}
          />
        </label>

        <label>
          Descrição
          <textarea
            value={group.description || ""}
            onChange={(e) =>
              onChangeGroup({ description: e.target.value })
            }
            disabled={saving}
          />
        </label>

        <div className="group-edit-divider" />

        {/* =========================
            DataTable de Papéis
        ========================= */}
        <DataTable<AdminRole>
          columns={[
            {
              key: "name",
              header: "Nome",
              sortable: true,
            },
            {
              key: "description",
              header: "Descrição",
              sortable: true,
              render: (r) => r.description ?? "-",
            },
          ]}
          data={paginatedRoles}
          loading={saving}
          searchValue={roleSearch}
          onSearchChange={setRoleSearch}
          sort={roleSort}
          onSortChange={setRoleSort}
          selectable
          getRowId={(r) => r.id}
          selectedRows={selectedRoleIds}
          onSelectionChange={(ids) => {
            const current = new Set(selectedRoleIds);
            const next = new Set(ids);

            // adicionados
            ids.forEach((id) => {
              if (!current.has(id)) onToggleRole(id);
            });

            // removidos
            selectedRoleIds.forEach((id) => {
              if (!next.has(id)) onToggleRole(id);
            });
          }}
          pagination={{
            page: rolePage,
            totalPages: roleTotalPages,
            total: processedRoles.length,
            pageSize: rolePageSize,
          }}
          onPageChange={setRolePage}
          onPageSizeChange={(size) => {
            setRolePageSize(size);
            setRolePage(1);
          }}
          pageSizeOptions={[5, 10, 20, 50]}
          emptyText="Nenhum papel encontrado"
          toolbar={
            <>
              <h4>Papéis do Grupo</h4>
              <div className="dt-muted">
                {processedRoles.length} papéis
              </div>
            </>
          }
        />
      </div>
    </Modal>
  );
};