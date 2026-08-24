// portal/src/ui/admin/rbac/UserRolesViewTab.tsx

import type { UserAccessProfile } from "../../../data/userAccessProfileTypes";
import { Alert, Button, Spinner } from "../../../ui-kit";

import { RbacAccessTree } from "./RbacAccessTree";

type Props = {
  profile: UserAccessProfile | null;
  loading: boolean;
  error: string | null;
  onEditDirectRoles: () => void;
  onOpenRole?: (roleId: string) => void;
  onOpenGroup?: (groupId: string) => void;
};

export function UserRolesViewTab({
  profile,
  loading,
  error,
  onEditDirectRoles,
  onOpenRole,
  onOpenGroup,
}: Props) {
  if (loading) {
    return <Spinner label="Carregando papéis efetivos…" />;
  }

  if (error) {
    return <Alert tone="danger">{error}</Alert>;
  }

  if (!profile) {
    return <Alert tone="info">Perfil de acesso indisponível.</Alert>;
  }

  return (
    <div className="user-rbac-view-tab">
      <div className="user-rbac-view-tab__intro">
        <div>
          <h4>Papéis efetivos</h4>
          <p>Origem indicada no badge — papéis diretos e herdados via grupos.</p>
        </div>
        <Button variant="secondary" onClick={onEditDirectRoles}>
          Editar papéis diretos
        </Button>
      </div>

      <RbacAccessTree
        variant="roles"
        profile={profile}
        onOpenRole={onOpenRole}
        onOpenGroup={onOpenGroup}
      />
    </div>
  );
}
