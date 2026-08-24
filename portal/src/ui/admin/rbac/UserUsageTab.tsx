// portal/src/ui/admin/rbac/UserUsageTab.tsx

import { UserUsagePanel } from "../../usage/UserUsagePanel";
import { USER_USAGE_LABELS } from "../../usage/userUsageLabels";
import { useAdminUserUsageStats } from "../../usage/useAdminUserUsageStats";

type UserUsageTabProps = {
  userId: string;
  active: boolean;
};

export function UserUsageTab({ userId, active }: UserUsageTabProps) {
  const { data, loading, error, periodDays, changePeriod, load } = useAdminUserUsageStats(
    userId,
    30,
    active,
  );

  return (
    <div className="user-rbac-usage">
      <section className="user-rbac-panel user-rbac-usage-intro">
        <div className="user-rbac-panel-header">
          <div>
            <h4>{USER_USAGE_LABELS.adminPanelTitle}</h4>
            <p>{USER_USAGE_LABELS.adminPanelHint}</p>
          </div>
        </div>
      </section>

      <UserUsagePanel
        variant="admin"
        data={data}
        loading={loading}
        error={error}
        periodDays={periodDays}
        onPeriodChange={changePeriod}
        onRefresh={() => void load()}
      />
    </div>
  );
}
