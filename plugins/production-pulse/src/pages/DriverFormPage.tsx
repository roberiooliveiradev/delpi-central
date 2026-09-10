import { useEffect, useMemo, useState } from "react";

import {
  createDriver,
  patchDriver,
  type DriverListItem,
  type DriverMetricDef,
  type DriverProtocolKind,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpFormActions,
  PpNativeSelectField,
  PpNativeSwitchField,
  PpNativeTextAreaField,
  PpNativeTextField,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import { ProductionPulsePagePath } from "../components/ProductionPulsePagePath";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwareLinksPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type DriverFormPageProps = {
  mode?: "create" | "edit";
  initial?: DriverListItem | null;
  permissions: ProductionPulsePermissionFlags;
  embedded?: boolean;
  onDone?: (driver: DriverListItem) => void;
  onCancel?: () => void;
};

type MetricRow = {
  key: string;
  labelPt: string;
  type: "integer" | "number";
  primary: boolean;
};

const PROTOCOL_OPTIONS: { value: DriverProtocolKind; label: string }[] = [
  { value: "http_counter", label: "http_counter — contador" },
  { value: "http_gauge", label: "http_gauge — sensores" },
];

const ROLE_OPTIONS = [
  { value: "pulse_counter", label: "pulse_counter" },
  { value: "process_gauge", label: "process_gauge" },
  { value: "telemetry", label: "telemetry" },
];

const SURFACE_OPTIONS = [
  { value: "counter_pad", label: "counter_pad" },
  { value: "gauge_readout", label: "gauge_readout" },
  { value: "temperature_focus", label: "temperature_focus" },
  { value: "rotation_ring", label: "rotation_ring" },
  { value: "telemetry_stack", label: "telemetry_stack" },
];

const PROTOCOL_DEFAULTS: Record<
  DriverProtocolKind,
  {
    roleKey: string;
    operatorSurface: string;
    commands: string[];
    metrics: MetricRow[];
  }
> = {
  http_counter: {
    roleKey: "pulse_counter",
    operatorSurface: "counter_pad",
    commands: [
      "increment",
      "decrement",
      "reset",
      "set",
      "configure",
      "reboot",
      "factory_reset",
    ],
    metrics: [{ key: "counter", labelPt: "Golpes", type: "integer", primary: true }],
  },
  http_gauge: {
    roleKey: "process_gauge",
    operatorSurface: "gauge_readout",
    commands: [],
    metrics: [
      { key: "rpm", labelPt: "Rotação", type: "number", primary: true },
      { key: "temperature_c", labelPt: "Temperatura", type: "number", primary: false },
    ],
  },
};

function metricsFromDriver(item: DriverListItem): MetricRow[] {
  const rows = (item.metrics ?? []).map((metric) => ({
    key: metric.key,
    labelPt: metric.labelPt || metric.key,
    type: (metric.type === "integer" ? "integer" : "number") as "integer" | "number",
    primary: Boolean(metric.primary),
  }));
  return rows.length > 0 ? rows : PROTOCOL_DEFAULTS.http_counter.metrics;
}

function toApiMetrics(rows: MetricRow[]): DriverMetricDef[] {
  return rows
    .filter((row) => row.key.trim())
    .map((row) => ({
      key: row.key.trim(),
      labelPt: row.labelPt.trim() || row.key.trim(),
      type: row.type,
      primary: row.primary,
      monotonic: row.type === "integer",
    }));
}

export function DriverFormPage({
  mode = "create",
  initial = null,
  permissions,
  embedded = false,
  onDone,
  onCancel,
}: DriverFormPageProps) {
  const canManage = permissions.canManageDevices;
  const isCreate = mode === "create";

  const [driverKey, setDriverKey] = useState(initial?.key ?? "");
  const [protocolKind, setProtocolKind] = useState<DriverProtocolKind>(
    (initial?.protocolKind as DriverProtocolKind) || "http_counter",
  );
  const [roleKey, setRoleKey] = useState(
    initial?.roleKey ?? PROTOCOL_DEFAULTS.http_counter.roleKey,
  );
  const [labelPt, setLabelPt] = useState(initial?.labelPt ?? "");
  const [descriptionPt, setDescriptionPt] = useState(initial?.descriptionPt ?? "");
  const [operatorSurface, setOperatorSurface] = useState(
    initial?.operatorSurface ?? PROTOCOL_DEFAULTS.http_counter.operatorSurface,
  );
  const [operatorEligible, setOperatorEligible] = useState(
    initial?.operatorEligible ?? true,
  );
  const [timeoutMs, setTimeoutMs] = useState(
    String(initial?.poll?.timeoutMs ?? 3000),
  );
  const [metrics, setMetrics] = useState<MetricRow[]>(() =>
    initial ? metricsFromDriver(initial) : PROTOCOL_DEFAULTS.http_counter.metrics,
  );
  const [selectedCommands, setSelectedCommands] = useState<string[]>(
    initial?.commands ?? PROTOCOL_DEFAULTS.http_counter.commands,
  );
  const [commandsText, setCommandsText] = useState(
    (initial?.commands ?? PROTOCOL_DEFAULTS.http_counter.commands).join(", "),
  );
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!initial || isCreate) return;
    setDriverKey(initial.key);
    setProtocolKind((initial.protocolKind as DriverProtocolKind) || "http_counter");
    setRoleKey(initial.roleKey);
    setLabelPt(initial.labelPt);
    setDescriptionPt(initial.descriptionPt ?? "");
    setOperatorSurface(initial.operatorSurface);
    setOperatorEligible(Boolean(initial.operatorEligible));
    setTimeoutMs(String(initial.poll?.timeoutMs ?? 3000));
    setMetrics(metricsFromDriver(initial));
    setSelectedCommands(initial.commands ?? []);
    setCommandsText((initial.commands ?? []).join(", "));
  }, [initial, isCreate]);

  const protocolCommandOptions = useMemo(
    () => PROTOCOL_DEFAULTS[protocolKind]?.commands ?? [],
    [protocolKind],
  );

  const applyProtocolDefaults = (next: DriverProtocolKind) => {
    const defaults = PROTOCOL_DEFAULTS[next];
    setProtocolKind(next);
    setRoleKey(defaults.roleKey);
    setOperatorSurface(defaults.operatorSurface);
    setMetrics(defaults.metrics.map((row) => ({ ...row })));
    setSelectedCommands([...defaults.commands]);
    setCommandsText(defaults.commands.join(", "));
  };

  const hubPath = productionPulseFirmwareLinksPath({ branch: "01", panel: "drivers" });

  const goBack = () => {
    if (onCancel) {
      onCancel();
      return;
    }
    navigateProductionPulse(hubPath);
  };

  const updateMetric = (index: number, patch: Partial<MetricRow>) => {
    setMetrics((rows) =>
      rows.map((row, i) => {
        if (i !== index) {
          if (patch.primary === true) return { ...row, primary: false };
          return row;
        }
        return { ...row, ...patch };
      }),
    );
  };

  const addMetric = () => {
    setMetrics((rows) => [
      ...rows,
      { key: "", labelPt: "", type: "number", primary: rows.length === 0 },
    ]);
  };

  const removeMetric = (index: number) => {
    setMetrics((rows) => {
      const next = rows.filter((_, i) => i !== index);
      if (next.length > 0 && !next.some((row) => row.primary)) {
        next[0] = { ...next[0], primary: true };
      }
      return next;
    });
  };

  const resolveCommands = (): string[] => {
    if (protocolCommandOptions.length > 0) {
      return selectedCommands;
    }
    return commandsText
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  };

  const submit = async () => {
    if (!canManage || !labelPt.trim()) return;
    if (isCreate && !driverKey.trim()) return;

    const pollTimeout = Number.parseInt(timeoutMs, 10);
    const bodyMetrics = toApiMetrics(metrics);
    if (bodyMetrics.length === 0) {
      setFormError("Informe ao menos uma métrica.");
      return;
    }

    setSubmitting(true);
    setFormError(null);
    try {
      let saved: DriverListItem;
      if (isCreate) {
        saved = await createDriver({
          driverKey: driverKey.trim(),
          protocolKind,
          roleKey,
          labelPt: labelPt.trim(),
          descriptionPt: descriptionPt.trim() || null,
          metrics: bodyMetrics,
          commands: resolveCommands(),
          operatorSurface,
          operatorEligible,
          poll: { timeoutMs: Number.isFinite(pollTimeout) ? pollTimeout : 3000 },
        });
      } else if (initial) {
        saved = await patchDriver(initial.key, {
          roleKey,
          labelPt: labelPt.trim(),
          descriptionPt: descriptionPt.trim() || null,
          metrics: bodyMetrics,
          commands: resolveCommands(),
          operatorSurface,
          operatorEligible,
          poll: { timeoutMs: Number.isFinite(pollTimeout) ? pollTimeout : 3000 },
        });
      } else {
        throw new Error("Driver inicial ausente para edição.");
      }
      if (onDone) {
        onDone(saved);
        return;
      }
      navigateProductionPulse(hubPath);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Falha ao salvar tipo de driver.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!canManage) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title={PP_HELP.drivers.breadcrumbCreate} badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para cadastrar tipos de driver."
        />
      </div>
    );
  }

  return (
    <div className={`pp-page-stack pp-form-page${embedded ? " pp-form-page--embedded" : ""}`}>
      {!embedded ? (
        <>
          <ProductionPulsePagePath
            panelHref={PRODUCTION_PULSE_BASE_PATH}
            items={[{ id: "hub", label: "Admin", href: hubPath }]}
            current={
              isCreate ? PP_HELP.drivers.breadcrumbCreate : PP_HELP.drivers.breadcrumbDetail
            }
          />
          <PpPageHero
            title={
              isCreate ? PP_HELP.drivers.breadcrumbCreate : PP_HELP.drivers.breadcrumbDetail
            }
            description={PP_HELP.drivers.hero}
            badge={ppShellIcon}
          />
        </>
      ) : null}

      {formError ? (
        <PpStateBox variant="error" title="Não foi possível salvar" message={formError} />
      ) : null}

      <div className="pp-form-layout">
        <PpSectionCard title="Identificação" hint={PP_HELP.drivers.sectionIdentity}>
          <div className="pp-form-grid pp-form-grid--pair">
            {isCreate ? (
              <PpNativeTextField
                id="driver-new-key"
                label="Chave (driverKey)"
                hint={PP_HELP.drivers.driverKey}
                value={driverKey}
                onChange={setDriverKey}
                placeholder="esp32c3_counter_v2"
              />
            ) : (
              <div>
                <p className="pp-muted">{PP_HELP.drivers.driverKey}</p>
                <p>
                  <code>{driverKey}</code>
                </p>
              </div>
            )}
            {isCreate ? (
              <PpNativeSelectField
                id="driver-protocol"
                label="Protocolo"
                hint={PP_HELP.drivers.protocolKind}
                value={protocolKind}
                onChange={(value) => applyProtocolDefaults(value as DriverProtocolKind)}
                options={PROTOCOL_OPTIONS}
                searchable={false}
              />
            ) : (
              <div>
                <p className="pp-muted">{PP_HELP.drivers.protocolKind}</p>
                <p>
                  <code>{protocolKind}</code>
                </p>
              </div>
            )}
            <PpNativeSelectField
              id="driver-role"
              label="Role"
              hint={PP_HELP.drivers.roleKey}
              value={roleKey}
              onChange={setRoleKey}
              options={ROLE_OPTIONS}
              searchable={false}
            />
            <PpNativeTextField
              id="driver-label"
              label="Rótulo (PT)"
              hint={PP_HELP.drivers.labelPt}
              value={labelPt}
              onChange={setLabelPt}
              placeholder="ESP32-C3 — contador"
            />
            <PpNativeTextAreaField
              id="driver-description"
              label="Descrição"
              hint={PP_HELP.drivers.descriptionPt}
              value={descriptionPt}
              onChange={setDescriptionPt}
              rows={3}
              span
            />
            <PpNativeSelectField
              id="driver-surface"
              label="Superfície do operador"
              hint={PP_HELP.drivers.operatorSurface}
              value={operatorSurface}
              onChange={setOperatorSurface}
              options={SURFACE_OPTIONS}
              searchable={false}
            />
            <PpNativeSwitchField
              id="driver-eligible"
              label="Elegível no operador"
              hint={PP_HELP.drivers.operatorEligible}
              checked={operatorEligible}
              onChange={setOperatorEligible}
            />
            <PpNativeTextField
              id="driver-timeout"
              label="Poll timeout (ms)"
              hint={PP_HELP.drivers.pollTimeout}
              type="number"
              min={500}
              max={60000}
              value={timeoutMs}
              onChange={setTimeoutMs}
            />
          </div>
        </PpSectionCard>

        <PpSectionCard title="Métricas" hint={PP_HELP.drivers.sectionMetrics}>
          <div className="pp-form-grid">
            {metrics.map((row, index) => (
              <div key={`metric-${index}`} className="pp-form-grid pp-form-grid--pair">
                <PpNativeTextField
                  id={`driver-metric-key-${index}`}
                  label="Chave"
                  hint={PP_HELP.drivers.metricKey}
                  value={row.key}
                  onChange={(value) => updateMetric(index, { key: value })}
                />
                <PpNativeTextField
                  id={`driver-metric-label-${index}`}
                  label="Rótulo"
                  hint={PP_HELP.drivers.metricLabel}
                  value={row.labelPt}
                  onChange={(value) => updateMetric(index, { labelPt: value })}
                />
                <PpNativeSelectField
                  id={`driver-metric-type-${index}`}
                  label="Tipo"
                  hint={PP_HELP.drivers.metricType}
                  value={row.type}
                  onChange={(value) =>
                    updateMetric(index, {
                      type: value === "integer" ? "integer" : "number",
                    })
                  }
                  options={[
                    { value: "integer", label: "integer" },
                    { value: "number", label: "number" },
                  ]}
                  searchable={false}
                />
                <PpNativeSwitchField
                  id={`driver-metric-primary-${index}`}
                  label="Primária"
                  hint={PP_HELP.drivers.metricPrimary}
                  checked={row.primary}
                  onChange={(checked) => updateMetric(index, { primary: checked })}
                />
                <div className="pp-inline-actions">
                  <PpActionButton
                    variant="ghost"
                    disabled={metrics.length <= 1}
                    onClick={() => removeMetric(index)}
                  >
                    Remover
                  </PpActionButton>
                </div>
              </div>
            ))}
            <PpActionButton variant="ghost" onClick={addMetric}>
              Adicionar métrica
            </PpActionButton>
          </div>
        </PpSectionCard>

        <PpSectionCard title="Comandos" hint={PP_HELP.drivers.sectionCommands}>
          <div className="pp-form-grid">
            {protocolCommandOptions.length > 0 ? (
              protocolCommandOptions.map((command) => (
                <PpNativeSwitchField
                  key={command}
                  id={`driver-command-${command}`}
                  label={command}
                  hint={PP_HELP.drivers.commands}
                  checked={selectedCommands.includes(command)}
                  onChange={(checked) => {
                    setSelectedCommands((current) => {
                      const next = checked
                        ? current.includes(command)
                          ? current
                          : [...current, command]
                        : current.filter((item) => item !== command);
                      setCommandsText(next.join(", "));
                      return next;
                    });
                  }}
                />
              ))
            ) : (
              <PpNativeTextField
                id="driver-commands-text"
                label="Comandos"
                hint={PP_HELP.drivers.commands}
                value={commandsText}
                onChange={setCommandsText}
                placeholder="reboot, configure"
                span
              />
            )}
          </div>
        </PpSectionCard>
      </div>

      <div className="pp-form-footer">
        <PpFormActions>
          <PpActionButton variant="ghost" onClick={goBack} disabled={submitting}>
            Cancelar
          </PpActionButton>
          <PpActionButton
            variant="primary"
            disabled={
              submitting || !labelPt.trim() || (isCreate && !driverKey.trim())
            }
            onClick={() => void submit()}
          >
            {submitting ? "Salvando…" : isCreate ? "Cadastrar" : "Salvar"}
          </PpActionButton>
        </PpFormActions>
      </div>
    </div>
  );
}
