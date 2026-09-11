import { ChevronDown, ChevronRight, Cpu, History } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchDeviceHardwareHistory,
  patchDeviceHardwareAssignment,
  type DeviceHardwareHistory,
  type HardwareAssignment,
} from "../../api/productionPulseApi";
import {
  PpActionButton,
  PpNativeSelectField,
  PpNativeTextAreaField,
  PpStateBox,
} from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/detailDisplay";
import { resolveProductionPulseError } from "../../utils/apiErrors";
import { DetailFactList, type DetailFact } from "./DetailFactList";
import { DetailLightCard } from "./DetailLightCard";

const REPLACEMENT_REASON_OPTIONS = [
  { value: "electronic_failure", label: "Falha eletrônica" },
  { value: "preventive_maintenance", label: "Manutenção preventiva" },
  { value: "hardware_upgrade", label: "Upgrade de hardware" },
  { value: "test", label: "Teste" },
  { value: "other", label: "Outro" },
] as const;

type DeviceHardwareTabProps = {
  deviceId: string;
  canManage?: boolean;
};

function formatDurationSeconds(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds) || seconds < 0) return "—";
  const total = Math.floor(seconds);
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m`;
  return `${total}s`;
}

function formatCount(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("pt-BR").format(value);
}

function firmwareLabel(row: HardwareAssignment): string {
  const last = (row.lastFirmwareVersion ?? "").trim();
  const first = (row.firstFirmwareVersion ?? "").trim();
  if (last && first && last !== first) return `${first} → ${last}`;
  return last || first || "—";
}

function replacementReasonLabel(reason: string | null | undefined): string {
  if (!reason) return "—";
  const found = REPLACEMENT_REASON_OPTIONS.find((opt) => opt.value === reason);
  return found?.label ?? reason;
}

function assignmentFacts(row: HardwareAssignment): DetailFact[] {
  return [
    {
      label: "MAC",
      value: (
        <code title={PP_HELP.detail.macAddress}>{row.macAddress?.trim() || "—"}</code>
      ),
    },
    {
      label: "UID",
      value: (
        <code title={PP_HELP.detail.hardwareUid}>{row.hardwareUid?.trim() || "—"}</code>
      ),
    },
    {
      label: "Instalado desde",
      value: formatDateTime(row.effectiveFrom),
    },
    ...(row.effectiveTo
      ? [{ label: "Removido em", value: formatDateTime(row.effectiveTo) }]
      : []),
    {
      label: "Firmware",
      value: firmwareLabel(row),
    },
    {
      label: "Golpes",
      value: (
        <span title={PP_HELP.detail.counterOnHardware}>{formatCount(row.counterDelta)}</span>
      ),
    },
    {
      label: "Tempo instalado",
      value: (
        <span title={PP_HELP.detail.installedTime}>
          {formatDurationSeconds(row.installedSeconds)}
        </span>
      ),
    },
    {
      label: "Tempo online",
      value: (
        <span title={PP_HELP.detail.onlineTime}>
          {formatDurationSeconds(row.onlineSeconds)}
        </span>
      ),
    },
    {
      label: "Reboots",
      value: formatCount(row.rebootCount),
    },
  ];
}

function AssignmentMetaForm({
  deviceId,
  assignment,
  onSaved,
}: {
  deviceId: string;
  assignment: HardwareAssignment;
  onSaved: (next: HardwareAssignment) => void;
}) {
  const [reason, setReason] = useState(assignment.replacementReason ?? "");
  const [notes, setNotes] = useState(assignment.replacementNotes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setReason(assignment.replacementReason ?? "");
    setNotes(assignment.replacementNotes ?? "");
    setError(null);
  }, [assignment.assignmentId, assignment.replacementReason, assignment.replacementNotes]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await patchDeviceHardwareAssignment(deviceId, assignment.assignmentId, {
        replacementReason: reason || null,
        replacementNotes: notes.trim() || null,
      });
      onSaved(updated);
    } catch (err) {
      setError(resolveProductionPulseError(err).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pp-hardware-meta-form">
      <PpNativeSelectField
        id={`hw-reason-${assignment.assignmentId}`}
        label="Motivo da substituição"
        value={reason}
        onChange={setReason}
        options={[...REPLACEMENT_REASON_OPTIONS]}
        placeholderOption="Selecione…"
        searchable={false}
      />
      <PpNativeTextAreaField
        id={`hw-notes-${assignment.assignmentId}`}
        label="Notas"
        value={notes}
        onChange={setNotes}
        rows={3}
      />
      {error ? <PpStateBox variant="error" title="Não foi possível salvar" message={error} /> : null}
      <div className="pp-hardware-meta-form__actions">
        <PpActionButton onClick={() => void handleSave()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar motivo"}
        </PpActionButton>
      </div>
    </div>
  );
}

function HistoryAssignmentRow({
  deviceId,
  assignment,
  expanded,
  onToggle,
  canManage,
  onUpdated,
}: {
  deviceId: string;
  assignment: HardwareAssignment;
  expanded: boolean;
  onToggle: () => void;
  canManage: boolean;
  onUpdated: (next: HardwareAssignment) => void;
}) {
  const title =
    assignment.hardwareUid?.trim() ||
    assignment.macAddress?.trim() ||
    assignment.assignmentId.slice(0, 8);

  return (
    <div className={`pp-hardware-item${expanded ? " pp-hardware-item--expanded" : ""}`}>
      <button
        type="button"
        className="pp-hardware-item__toggle"
        aria-expanded={expanded}
        onClick={onToggle}
      >
        {expanded ? <ChevronDown size={16} aria-hidden /> : <ChevronRight size={16} aria-hidden />}
        <span className="pp-hardware-item__title">
          <code>{title}</code>
        </span>
        <span className="pp-hardware-item__meta">
          {formatDateTime(assignment.effectiveFrom)}
          {assignment.effectiveTo ? ` → ${formatDateTime(assignment.effectiveTo)}` : ""}
          {" · "}
          {formatCount(assignment.counterDelta)} golpes
        </span>
      </button>
      {expanded ? (
        <div className="pp-hardware-item__body">
          <DetailFactList facts={assignmentFacts(assignment)} />
          {canManage ? (
            <AssignmentMetaForm
              deviceId={deviceId}
              assignment={assignment}
              onSaved={onUpdated}
            />
          ) : (
            <DetailFactList
              facts={[
                {
                  label: "Motivo",
                  value: replacementReasonLabel(assignment.replacementReason),
                },
                {
                  label: "Notas",
                  value: assignment.replacementNotes?.trim() || "—",
                },
              ]}
            />
          )}
        </div>
      ) : null}
    </div>
  );
}

export function DeviceHardwareTab({ deviceId, canManage = false }: DeviceHardwareTabProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DeviceHardwareHistory | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      return fetchDeviceHardwareHistory(deviceId, { signal })
        .then((payload) => {
          setData(payload);
          setLoading(false);
        })
        .catch((err) => {
          if (signal?.aborted) return;
          setError(resolveProductionPulseError(err).message);
          setLoading(false);
        });
    },
    [deviceId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const pastAssignments = useMemo(
    () => (data?.history ?? []).filter((row) => !row.active),
    [data],
  );

  const showLegacy =
    data != null &&
    ((data.summary.legacyUnidentifiedCounterDelta ?? 0) > 0 ||
      Boolean(data.summary.traceabilityStartedAt));

  const handleAssignmentUpdated = (next: HardwareAssignment) => {
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        current:
          prev.current?.assignmentId === next.assignmentId ? next : prev.current,
        history: prev.history.map((row) =>
          row.assignmentId === next.assignmentId ? next : row,
        ),
      };
    });
  };

  if (loading && !data) {
    return (
      <PpStateBox
        variant="loading"
        title="Carregando hardware…"
        message="Buscando histórico de placas neste ponto."
      />
    );
  }

  if (error && !data) {
    return <PpStateBox variant="error" title="Erro ao carregar hardware" message={error} />;
  }

  if (!data) {
    return (
      <PpStateBox
        variant="empty"
        title="Sem dados de hardware"
        message="Nenhuma informação de rastreabilidade disponível."
      />
    );
  }

  return (
    <div className="pp-detail-stack pp-hardware-tab">
      {showLegacy ? (
        <div className="pp-hardware-legacy" title={PP_HELP.detail.legacyUnidentified}>
          <p>
            {data.summary.traceabilityStartedAt
              ? `Rastreabilidade de hardware iniciada em ${formatDateTime(data.summary.traceabilityStartedAt)}.`
              : "Rastreabilidade de hardware ativa para este ponto."}
            {(data.summary.legacyUnidentifiedCounterDelta ?? 0) > 0
              ? ` Golpes anteriores sem identificação: ${formatCount(data.summary.legacyUnidentifiedCounterDelta)}.`
              : null}
          </p>
        </div>
      ) : null}

      <DetailLightCard icon={Cpu} title="Hardware atual" hint={PP_HELP.detail.hardwareCurrent}>
        {data.current ? (
          <DetailFactList facts={assignmentFacts(data.current)} />
        ) : (
          <PpStateBox
            variant="empty"
            title="Nenhuma placa identificada"
            message="Aguarde um poll com identidade (UID/MAC) ou verifique o firmware."
          />
        )}
      </DetailLightCard>

      <DetailLightCard icon={History} title="Histórico de placas" hint={PP_HELP.detail.hardwareHistory}>
        <p className="pp-muted pp-hardware-summary">
          {formatCount(data.summary.hardwareCount)} hardware(s) ·{" "}
          {formatCount(data.summary.macCount)} MAC(s) ·{" "}
          {formatCount(data.summary.replacementCount)} troca(s)
        </p>
        {pastAssignments.length === 0 ? (
          <PpStateBox
            variant="empty"
            title="Sem substituições"
            message="Ainda não houve troca de placa registrada neste ponto."
          />
        ) : (
          <div className="pp-hardware-list">
            {pastAssignments.map((row) => (
              <HistoryAssignmentRow
                key={row.assignmentId}
                deviceId={deviceId}
                assignment={row}
                expanded={expandedId === row.assignmentId}
                onToggle={() =>
                  setExpandedId((prev) =>
                    prev === row.assignmentId ? null : row.assignmentId,
                  )
                }
                canManage={canManage}
                onUpdated={handleAssignmentUpdated}
              />
            ))}
          </div>
        )}
      </DetailLightCard>
    </div>
  );
}
