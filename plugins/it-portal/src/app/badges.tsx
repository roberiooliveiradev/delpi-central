import type {
  ActionPriority,
  ActionStatus,
  AdministrativeStatus,
  Criticality,
  Environment,
  ServiceKind,
} from "../api/itPortalApi";
import {
  ACTION_PRIORITY_LABELS,
  ACTION_STATUS_LABELS,
  ADMINISTRATIVE_STATUS_LABELS,
  CRITICALITY_LABELS,
  ENVIRONMENT_LABELS,
  SERVICE_KIND_LABELS,
} from "../content/labels";
import { ItpStatusBadge } from "./itPortalUi";

type Variant = "neutral" | "info" | "success" | "warning" | "danger";

const CRITICALITY_VARIANT: Record<Criticality, Variant> = {
  low: "neutral",
  medium: "info",
  high: "warning",
  critical: "danger",
};

const ENVIRONMENT_VARIANT: Record<Environment, Variant> = {
  production: "info",
  staging: "neutral",
  development: "neutral",
};

const ADMIN_STATUS_VARIANT: Record<AdministrativeStatus, Variant> = {
  planned: "neutral",
  in_operation: "success",
  maintenance: "warning",
  decommissioning: "neutral",
};

const PRIORITY_VARIANT: Record<ActionPriority, Variant> = {
  low: "neutral",
  medium: "info",
  high: "warning",
  urgent: "danger",
};

const ACTION_STATUS_VARIANT: Record<ActionStatus, Variant> = {
  pending: "neutral",
  in_progress: "info",
  done: "success",
  cancelled: "neutral",
};

export function CriticalityBadge({ value }: { value: Criticality }) {
  return <ItpStatusBadge label={CRITICALITY_LABELS[value]} variant={CRITICALITY_VARIANT[value]} />;
}

export function EnvironmentBadge({ value }: { value: Environment }) {
  return <ItpStatusBadge label={ENVIRONMENT_LABELS[value]} variant={ENVIRONMENT_VARIANT[value]} />;
}

export function AdministrativeStatusBadge({ value }: { value: AdministrativeStatus }) {
  return <ItpStatusBadge label={ADMINISTRATIVE_STATUS_LABELS[value]} variant={ADMIN_STATUS_VARIANT[value]} />;
}

export function PriorityBadge({ value }: { value: ActionPriority }) {
  return <ItpStatusBadge label={ACTION_PRIORITY_LABELS[value]} variant={PRIORITY_VARIANT[value]} />;
}

export function ActionStatusBadge({ value, overdue }: { value: ActionStatus; overdue?: boolean }) {
  return (
    <span className="itp-badge-group">
      <ItpStatusBadge label={ACTION_STATUS_LABELS[value]} variant={ACTION_STATUS_VARIANT[value]} />
      {overdue ? <ItpStatusBadge label="Atrasado" variant="danger" /> : null}
    </span>
  );
}

export function ServiceKindBadge({ value }: { value: ServiceKind }) {
  return (
    <ItpStatusBadge
      label={SERVICE_KIND_LABELS[value]}
      variant={value === "business_application" ? "info" : "neutral"}
    />
  );
}

export function ArchivedBadge() {
  return <ItpStatusBadge label="Arquivado" variant="neutral" />;
}
