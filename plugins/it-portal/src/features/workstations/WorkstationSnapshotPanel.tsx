import { useQuery } from "@tanstack/react-query";

import { itPortalApi } from "../../api/itPortalApi";
import { formatDateTime } from "../../app/format";
import { ItpSectionCard } from "../../app/itPortalUi";
import { queryKeys } from "../../app/queryKeys";
import { DetailField } from "../inventory/InventoryDialogs";

function gib(bytes: number | null | undefined): string {
  if (bytes == null || !Number.isFinite(bytes)) return "Não informado";
  return `${(bytes / (1024 ** 3)).toFixed(1)} GB`;
}

/** Observado != conectado: a ultima coleta nao representa sessao online. */
export function WorkstationSnapshotPanel({ workstationId }: { workstationId: string }) {
  const query = useQuery({
    queryKey: queryKeys.workstationSnapshot(workstationId),
    queryFn: ({ signal }) => itPortalApi.getWorkstationSnapshot(workstationId, signal),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
  const row = query.data;
  const snapshot = row?.snapshot;

  return (
    <ItpSectionCard
      title="Inventário automático"
      subtitle="Última coleta observada do Windows. Não indica presença online."
    >
      {query.isPending ? <p className="itp-muted">Consultando inventário…</p> : null}
      {query.isError ? <p role="alert">Não foi possível consultar o inventário automático.</p> : null}
      {!query.isPending && !query.isError && !snapshot ? (
        <p className="itp-muted">Nenhuma coleta automática registrada para este computador.</p>
      ) : null}
      {snapshot && row ? (
        <>
          <dl className="itp-field-list">
            <DetailField label="Observado em" value={formatDateTime(row.observed_at)} />
            <DetailField label="Recebido em" value={formatDateTime(row.received_at)} />
            <DetailField label="Atualidade" value={row.freshness === "stale" ? "Desatualizado" : "Coleta recente"} />
            <DetailField label="Resultado" value={row.status === "complete" ? "Completo" : row.status === "partial" ? "Parcial" : "Falhou"} />
            <DetailField label="Fabricante" value={snapshot.hardware?.manufacturer ?? "Não informado"} />
            <DetailField label="Modelo" value={snapshot.hardware?.model ?? "Não informado"} />
            <DetailField label="Processador" value={snapshot.hardware?.cpu_name ?? "Não informado"} />
            <DetailField label="Memória RAM" value={gib(snapshot.hardware?.memory_total_bytes)} />
            <DetailField label="Sistema" value={snapshot.os?.name ?? "Não informado"} />
            <DetailField label="Build do Windows" value={snapshot.os?.build_number ?? "Não informado"} />
          </dl>
          {snapshot.volumes.length ? (
            <div>
              <strong>Discos locais</strong>
              <ul>
                {snapshot.volumes.map((disk) => (
                  <li key={disk.mount_point}>
                    {disk.mount_point} | Total: {gib(disk.capacity_bytes)} | Livre: {gib(disk.free_bytes)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {snapshot.network.private_ipv4.length ? (
            <p className="itp-muted">IP(s) privado(s) observado(s): {snapshot.network.private_ipv4.join(", ")}</p>
          ) : null}
          <p className="itp-muted">
            Esta informação foi declarada pelo coletor; não altera o cadastro manual
            e não autoriza acesso remoto.
          </p>
        </>
      ) : null}
    </ItpSectionCard>
  );
}
