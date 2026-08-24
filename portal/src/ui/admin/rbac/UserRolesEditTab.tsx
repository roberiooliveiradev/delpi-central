// portal/src/ui/admin/rbac/UserRolesEditTab.tsx

import type { AdminRole } from "../../../data/adminApi";
import { Alert } from "../../../ui-kit";
import { RelationshipPicker } from "../../../components/RelationshipPicker";

type Props = {
  roles: AdminRole[];
  selectedRoleIds: string[];
  busy: boolean;
  onChange: (ids: string[]) => void;
};

export function UserRolesEditTab({
  roles,
  selectedRoleIds,
  busy,
  onChange,
}: Props) {
  return (
    <div className="user-rbac-edit-tab">
      <Alert tone="info">
        Somente papéis concedidos diretamente ao usuário. Papéis herdados via
        grupos são gerenciados na aba Grupos.
      </Alert>

      <RelationshipPicker<AdminRole>
        title="Papéis diretos do Usuário"
        availableTitle="Papéis disponíveis"
        selectedTitle="Papéis vinculados ao usuário"
        searchPlaceholder="Buscar papel..."
        emptyAvailableText="Nenhum papel disponível para adicionar."
        emptySelectedText="Nenhum papel direto vinculado a este usuário."
        items={roles}
        selectedIds={selectedRoleIds}
        disabled={busy}
        getId={(role) => role.id}
        getTitle={(role) => role.name}
        getDescription={(role) => role.description ?? null}
        onChange={onChange}
      />
    </div>
  );
}
