// portal/src/ui/admin/rbac/UserGroupsEditTab.tsx

import type { AdminGroup } from "../../../data/adminApi";
import { RelationshipPicker } from "../../../components/RelationshipPicker";

type Props = {
  groups: AdminGroup[];
  selectedGroupIds: string[];
  busy: boolean;
  onChange: (ids: string[]) => void;
};

export function UserGroupsEditTab({
  groups,
  selectedGroupIds,
  busy,
  onChange,
}: Props) {
  return (
    <div className="user-rbac-edit-tab">
      <RelationshipPicker<AdminGroup>
        title="Grupos do Usuário"
        availableTitle="Grupos disponíveis"
        selectedTitle="Grupos vinculados ao usuário"
        searchPlaceholder="Buscar grupo..."
        emptyAvailableText="Nenhum grupo disponível para adicionar."
        emptySelectedText="Nenhum grupo vinculado a este usuário."
        items={groups}
        selectedIds={selectedGroupIds}
        disabled={busy}
        getId={(group) => group.id}
        getTitle={(group) => group.name}
        getDescription={(group) => group.description ?? null}
        onChange={onChange}
      />
    </div>
  );
}
