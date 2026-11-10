import { itPortalApi } from "../../api/itPortalApi";
import { queryKeys } from "../../app/queryKeys";
import { HistorySection } from "../history/HistorySection";

export function ServerHistorySection({ serverId }: { serverId: string }) {
  return (
    <HistorySection
      queryKey={queryKeys.history(serverId)}
      queryFn={(signal) => itPortalApi.listHistory(serverId, signal)}
      subtitle="Últimos 50 eventos auditados deste servidor."
      ariaLabel="Histórico do servidor"
    />
  );
}
