// portal/src/ui/admin/rbac/UserGroupsViewTab.tsx

import type { UserAccessProfile } from "../../../data/userAccessProfileTypes";
import { Alert, Button, Spinner } from "../../../ui-kit";

import { RbacAccessTree } from "./RbacAccessTree";

type Props = {
  profile: UserAccessProfile | null;
  loading: boolean;
  error: string | null;
  onEditGroups: () => void;
  onOpenRole?: (roleId: string) => void;
  onOpenGroup?: (groupId: string) => void;
};

export function UserGroupsViewTab({
  profile,
  loading,
  error,
  onEditGroups,
  onOpenRole,
  onOpenGroup,
}: Props) {
  if (loading) {
    return <Spinner label="Carregando grupos vinculados…" />;
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
          <h4>Grupos vinculados</h4>
          <p>Membership e papéis herdados — papéis só diretos não aparecem aqui.</p>
        </div>
        <Button variant="secondary" onClick={onEditGroups}>
          Editar grupos
        </Button>
      </div>

      <RbacAccessTree
        variant="groups"
        profile={profile}
        onOpenRole={onOpenRole}
        onOpenGroup={onOpenGroup}
      />
    </div>
  );
}
