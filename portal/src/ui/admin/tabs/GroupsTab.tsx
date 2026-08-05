// src/ui/admin/tabs/GroupsTab.tsx

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Edit, ShieldCheck, Trash2, UsersRound } from "lucide-react";

import type { AdminGroup } from "../../../data/adminApi";

import { useAdminApi } from "../../../hooks/useAdminApi";
import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { AdminEntityList } from "../../../components/admin/AdminEntityList";

type GroupSortField = "name" | "description";

const PAGE_SIZE = 10;

const getGroupInitials = (group: AdminGroup) => {
  const parts = (group.name || "?").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
};

export const GroupsTab = () => {
  const navigate = useNavigate();

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{
    sort?: GroupSortField;
    direction?: "asc" | "desc";
  }>({
    sort: "name",
    direction: "asc",
  });

  const [selected, setSelected] = useState<string[]>([]);
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [deleteOneId, setDeleteOneId] = useState<string | null>(null);

  const api = useAdminApi();

  const groupsResource = usePaginatedResource<AdminGroup>(
    ({ page, pageSize }) =>
      api.listGroups({
        page,
        pageSize,
        q: search,
        sort: sort.sort,
        direction: sort.direction,
      }),
    PAGE_SIZE,
    [search, sort.sort, sort.direction]
  );

  const groups = groupsResource.data ?? [];
  const totalGroups = groupsResource.pagination?.total ?? groups.length;
  const totalPages = groupsResource.pagination?.total_pages ?? 1;
  const currentPage = groupsResource.page;

  const openGroup = (group: AdminGroup) => {
    navigate(`/admin/groups/${group.id}`);
  };

  const openNew = () => {
    navigate("/admin/groups/new");
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    groupsResource.setPage(1);
  };

  const toggleSort = (field: GroupSortField) => {
    setSort((prev) => {
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

    groupsResource.setPage(1);
  };

  const toggleGroupSelection = (groupId: string) => {
    setSelected((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    );
  };

  const clearSelection = () => {
    setSelected([]);
  };

  const selectVisibleGroups = () => {
    const visibleIds = groups.map((group) => group.id);

    setSelected((prev) => {
      const next = new Set(prev);
      visibleIds.forEach((id) => next.add(id));
      return Array.from(next);
    });
  };

  const handleDeleteOne = async () => {
    if (!deleteOneId) return;
    await api.deleteGroup(deleteOneId);
    setDeleteOneId(null);
    groupsResource.refetch();
  };

  const handleBulkDelete = async () => {
    if (selected.length === 0) return;
    await api.bulkDeleteGroups(selected);
    setSelected([]);
    setConfirmBulk(false);
    groupsResource.refetch();
  };

  const goToPreviousPage = () => {
    groupsResource.setPage(Math.max(1, currentPage - 1));
  };

  const goToNextPage = () => {
    groupsResource.setPage(Math.min(totalPages, currentPage + 1));
  };

  const sortLabel = sort.direction === "asc" ? "A-Z" : "Z-A";

  return (
    <>
      <AdminEntityList<AdminGroup>
        title="Grupos"
        description="Administre agrupamentos de usuários e os papéis herdados por cada grupo."
        summary={[
          { value: totalGroups, label: "grupos" },
          { value: groups.length, label: "nesta página" },
          { value: selected.length, label: "selecionados" },
        ]}
        search={{
          value: search,
          placeholder: "Buscar por nome ou descrição...",
          onChange: handleSearchChange,
        }}
        toolbarActions={[
          {
            label: `Nome ${sort.sort === "name" ? sortLabel : ""}`,
            active: sort.sort === "name",
            onClick: () => toggleSort("name"),
          },
          {
            label: `Descrição ${
              sort.sort === "description" ? sortLabel : ""
            }`,
            active: sort.sort === "description",
            onClick: () => toggleSort("description"),
          },
          {
            label: "Novo Grupo",
            primary: true,
            onClick: openNew,
          },
        ]}
        listTitle="Listagem de grupos"
        listSubtitle={`Página ${currentPage} de ${totalPages}`}
        items={groups}
        loading={groupsResource.loading}
        emptyText="Nenhum grupo encontrado."
        getId={(group) => group.id}
        selectedIds={selected}
        selectionLabel="grupos selecionados"
        onToggleSelected={toggleGroupSelection}
        onSelectVisible={selectVisibleGroups}
        onClearSelection={clearSelection}
        bulkActions={[
          {
            label: (
              <>
                <Trash2 size={14} />
                Excluir selecionados
              </>
            ),
            danger: true,
            onClick: () => setConfirmBulk(true),
          },
        ]}
        pagination={
          groupsResource.pagination
            ? {
                page: currentPage,
                totalPages,
                onPrevious: goToPreviousPage,
                onNext: goToNextPage,
              }
            : undefined
        }
        renderIcon={getGroupInitials}
        renderTitle={(group) => group.name}
        renderSubtitle={(group) => group.id}
        renderBadges={() => [
          {
            label: (
              <>
                <UsersRound size={12} />
                Grupo RBAC
              </>
            ),
          },
        ]}
        renderDescription={(group) =>
          group.description || "Sem descrição cadastrada."
        }
        renderMeta={() => [
          <>
            <ShieldCheck size={13} />
            Usuários e papéis na página do grupo
          </>,
        ]}
        renderActions={(group) => [
          {
            label: (
              <>
                <Edit size={14} />
                Editar
              </>
            ),
            onClick: () => openGroup(group),
          },
          {
            label: (
              <>
                <Trash2 size={14} />
                Excluir
              </>
            ),
            danger: true,
            onClick: () => setDeleteOneId(group.id),
          },
        ]}
      />

      <ConfirmDialog
        open={!!deleteOneId}
        title="Excluir grupo"
        message="Deseja realmente excluir este grupo?"
        confirmText="Excluir"
        danger
        onCancel={() => setDeleteOneId(null)}
        onConfirm={handleDeleteOne}
      />

      <ConfirmDialog
        open={confirmBulk}
        title="Excluir grupos"
        message={`Deseja excluir ${selected.length} grupos?`}
        confirmText="Excluir"
        danger
        onCancel={() => setConfirmBulk(false)}
        onConfirm={handleBulkDelete}
      />
    </>
  );
};
