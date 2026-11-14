/** Modal CRUD de bandeira de produto acompanhado (record-scoped).
 * Diferenças do D16: encerradas são terminais (sem reopen), REMOVED
 * substitui o soft-delete como ação explícita e GENERAL é rejeitado
 * para novas bandeiras (somente legado/read). */

import { useEffect, useId, useMemo, useState, type ReactNode } from "react";
import { Flag, Pencil, Save, Trash2, X } from "lucide-react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringFormActions,
  EngineeringHostDialog,
  EngineeringStateBanner,
  EngineeringTextAreaField,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import { EngineeringConfirmDialog } from "../../../ui/EngineeringConfirmDialog";
import {
  closePrcRecordFlag,
  createPrcRecordFlag,
  updatePrcRecordFlag,
  type PrcFlagCreateBody,
  type PrcRecordFlag,
} from "../api/productRegistrationApi";
import {
  PRC_FIELD_LABELS,
  PRC_FLAG_ACTION_HELP,
  PRC_SUPPLIER_LABELS,
} from "../prcCopy";
import type { FlagTargetContext } from "./PrcFlagModal";

function newIdempotencyKey(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function formatWhen(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

function actorLabel(actor?: {
  subject?: string | null;
  displayName?: string | null;
} | null): string {
  if (!actor) return "—";
  return actor.displayName || actor.subject || "—";
}

function ActionLabel({
  icon,
  text,
  help,
}: {
  icon: ReactNode;
  text: string;
  help: string;
}) {
  return (
    <HelpTooltip content={help} ariaLabel={`Ajuda: ${text}`} wrap placement="top">
      <span className="engineering-prc__flag-action-row" tabIndex={0}>
        <span aria-hidden>{icon}</span>
        {text}
      </span>
    </HelpTooltip>
  );
}

function sameTarget(flag: PrcRecordFlag, target: FlagTargetContext): boolean {
  if (flag.subject !== target.subject) return false;
  if (target.subject === "FIELD") {
    return flag.targetPath === target.targetPath;
  }
  if (target.subject === "SUPPLIER_LINK") {
    return (
      flag.targetAttribute === target.targetAttribute &&
      flag.supplierKey?.supplierCode === target.supplierKey?.supplierCode &&
      flag.supplierKey?.store === target.supplierKey?.store
    );
  }
  return true;
}

const STATUS_LABEL: Record<PrcRecordFlag["status"], string> = {
  OPEN: "Aberta",
  RESOLVED: "Resolvida",
  REMOVED: "Removida",
};

export function PrcProductFlagModal({
  open,
  recordId,
  flag,
  target,
  historyFlags = [],
  allowedActions = [],
  onClose,
  onChanged,
}: {
  open: boolean;
  recordId: string;
  flag: PrcRecordFlag | null;
  target: FlagTargetContext;
  historyFlags?: PrcRecordFlag[];
  allowedActions?: string[];
  onClose: () => void;
  onChanged: () => void | Promise<void>;
}) {
  const formId = useId();
  const [active, setActive] = useState<PrcRecordFlag | null>(flag);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirmRemove, setConfirmRemove] = useState(false);

  const siblingClosed = useMemo(
    () =>
      historyFlags
        .filter(
          (f) =>
            f.status !== "OPEN" &&
            sameTarget(f, target) &&
            (!active || f.id !== active.id),
        )
        .sort((a, b) =>
          String(b.closedAt || b.updatedAt || "").localeCompare(
            String(a.closedAt || a.updatedAt || ""),
          ),
        ),
    [historyFlags, target, active],
  );

  useEffect(() => {
    if (!open) return;
    setActive(flag);
    setTitle(flag?.title || "");
    setDescription(flag?.description || "");
    setError("");
    setConfirmRemove(false);
  }, [open, flag]);

  if (!open) return null;

  const isCreate = !active;
  const terminal = active != null && active.status !== "OPEN";
  const canWrite =
    isCreate || (!terminal && allowedActions.includes("update"));
  const canResolve = allowedActions.includes("resolve");
  const canRemove = allowedActions.includes("remove");
  const canCreate = allowedActions.includes("create");

  const targetTitle =
    target.subject === "FIELD"
      ? target.fieldLabel ||
        PRC_FIELD_LABELS[target.targetPath || ""] ||
        target.targetPath ||
        "Campo"
      : target.subject === "SUPPLIER_LINK"
        ? `${PRC_SUPPLIER_LABELS[target.targetAttribute || "partNumber"] || target.targetAttribute} — ${target.supplierKey?.supplierCode || "?"} / ${target.supplierKey?.store || "?"}`
        : "Bandeira legada (sem campo)";

  const selectFlag = (next: PrcRecordFlag) => {
    setActive(next);
    setTitle(next.title || "");
    setDescription(next.description || "");
    setError("");
  };

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
      await onChanged();
      onClose();
    } catch (err) {
      setError(
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível concluir a operação.",
      );
    } finally {
      setBusy(false);
    }
  };

  const save = () =>
    run(async () => {
      const t = title.trim();
      const d = description.trim();
      if (!t || !d) {
        throw new HomeApiError(
          "contract_error",
          "Título e descrição são obrigatórios.",
          422,
        );
      }
      if (isCreate) {
        if (target.subject === "GENERAL") {
          throw new HomeApiError(
            "contract_error",
            "Novas bandeiras gerais não são permitidas.",
            422,
          );
        }
        const body: PrcFlagCreateBody = {
          title: t,
          description: d,
          subject: target.subject,
          targetPath: target.targetPath,
          targetAttribute: target.targetAttribute,
          supplierKey: target.supplierKey,
        };
        await createPrcRecordFlag(
          recordId,
          body,
          newIdempotencyKey("pflag-create"),
        );
      } else if (active) {
        await updatePrcRecordFlag(
          recordId,
          active.id,
          { expectedVersion: active.version, title: t, description: d },
          newIdempotencyKey("pflag-update"),
        );
      }
    });

  return (
    <>
      <EngineeringHostDialog
        open={open}
        onClose={busy ? () => undefined : onClose}
        title={isCreate ? "Nova bandeira" : "Bandeira de acompanhamento"}
        closeOnOverlayClick={!busy}
        footer={
          <EngineeringFormActions>
            <EngineeringActionButton
              variant="ghost"
              disabled={busy}
              onClick={onClose}
            >
              <ActionLabel
                icon={<X size={14} />}
                text="Fechar"
                help={PRC_FLAG_ACTION_HELP.close}
              />
            </EngineeringActionButton>
            {active?.status === "OPEN" && canResolve ? (
              <EngineeringActionButton
                variant="ghost"
                disabled={busy}
                onClick={() =>
                  run(() =>
                    closePrcRecordFlag(
                      recordId,
                      active.id,
                      "resolve",
                      { expectedVersion: active.version },
                      newIdempotencyKey("pflag-resolve"),
                    ),
                  )
                }
              >
                <ActionLabel
                  icon={<Flag size={14} color="#1a7f37" />}
                  text="Resolver"
                  help={PRC_FLAG_ACTION_HELP.resolve}
                />
              </EngineeringActionButton>
            ) : null}
            {active?.status === "OPEN" && canRemove ? (
              <EngineeringActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setConfirmRemove(true)}
              >
                <ActionLabel
                  icon={<Trash2 size={14} />}
                  text="Remover"
                  help={PRC_FLAG_ACTION_HELP.remove}
                />
              </EngineeringActionButton>
            ) : null}
            {canWrite && (isCreate ? canCreate : true) ? (
              <EngineeringActionButton
                variant="primary"
                disabled={busy}
                onClick={() => void save()}
              >
                <ActionLabel
                  icon={
                    isCreate ? (
                      <Flag size={14} color="#2563eb" />
                    ) : (
                      <Save size={14} />
                    )
                  }
                  text={isCreate ? "Criar" : "Salvar"}
                  help={
                    isCreate
                      ? PRC_FLAG_ACTION_HELP.add
                      : PRC_FLAG_ACTION_HELP.save
                  }
                />
              </EngineeringActionButton>
            ) : null}
          </EngineeringFormActions>
        }
      >
        <div className="engineering-prc__flag-modal" id={formId}>
          <ul
            className="engineering-prc__flag-legend"
            aria-label={PRC_FLAG_ACTION_HELP.legend}
          >
            <li>
              <span
                className="engineering-prc__flag-legend-swatch engineering-prc__flag-legend-swatch--add"
                aria-hidden
              >
                <Flag size={14} />
              </span>
              Adicionar acompanhamento
            </li>
            <li>
              <span
                className="engineering-prc__flag-legend-swatch engineering-prc__flag-legend-swatch--open"
                aria-hidden
              >
                <Flag size={14} />
              </span>
              Acompanhamento aberto
            </li>
            <li>
              <span
                className="engineering-prc__flag-legend-swatch engineering-prc__flag-legend-swatch--resolved"
                aria-hidden
              >
                <Flag size={14} />
              </span>
              Acompanhamento resolvido
            </li>
          </ul>

          <p className="engineering-prc__flag-modal-target">
            <Flag size={14} aria-hidden />
            <strong>{targetTitle}</strong>
          </p>
          {target.currentValue != null && target.currentValue !== "" ? (
            <p className="engineering-prc__muted">
              Valor atual (somente contexto): {target.currentValue}
            </p>
          ) : null}

          {siblingClosed.length > 0 ? (
            <div>
              <p className="engineering-prc__muted">
                Histórico encerrado neste alvo — selecione para consultar
                (ocorrências encerradas são definitivas):
              </p>
              <ul className="engineering-prc__flag-history">
                {siblingClosed.map((h) => (
                  <li key={h.id}>
                    <EngineeringActionButton
                      variant="ghost"
                      disabled={busy}
                      onClick={() => selectFlag(h)}
                    >
                      <Flag size={12} color="#1a7f37" aria-hidden /> {h.title} ·{" "}
                      {STATUS_LABEL[h.status]} ·{" "}
                      {formatWhen(h.closedAt || h.updatedAt)}
                    </EngineeringActionButton>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {active ? (
            <dl className="engineering-prc__flag-meta">
              <div>
                <dt>Estado</dt>
                <dd>{STATUS_LABEL[active.status]}</dd>
              </div>
              <div>
                <dt>Criada por</dt>
                <dd>
                  {actorLabel(active.createdBy)} ·{" "}
                  {formatWhen(active.createdAt)}
                </dd>
              </div>
              <div>
                <dt>Aberta em</dt>
                <dd>V{active.openedRevisionNumber}</dd>
              </div>
              {active.closedAt ? (
                <div>
                  <dt>Encerrada</dt>
                  <dd>
                    {actorLabel(active.closedBy)} ·{" "}
                    {formatWhen(active.closedAt)}
                    {active.closedRevisionNumber
                      ? ` · V${active.closedRevisionNumber}`
                      : ""}
                  </dd>
                </div>
              ) : null}
            </dl>
          ) : null}
          {error ? (
            <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
          ) : null}
          <EngineeringTextField
            id={`${formId}-title`}
            label="Título"
            hint={PRC_FLAG_ACTION_HELP.edit}
            value={title}
            onChange={setTitle}
            maxLength={120}
            required
            disabled={busy || terminal}
          />
          <EngineeringTextAreaField
            id={`${formId}-desc`}
            label="Descrição"
            hint={PRC_FLAG_ACTION_HELP.edit}
            value={description}
            onChange={setDescription}
            maxLength={1000}
            required
            disabled={busy || terminal}
            rows={5}
          />
          {active?.status === "OPEN" ? (
            <p className="engineering-prc__muted">
              <Pencil size={12} aria-hidden /> Edite título/descrição e salve,
              ou use Resolver/Remover para encerrar definitivamente.
            </p>
          ) : null}
        </div>
      </EngineeringHostDialog>
      <EngineeringConfirmDialog
        open={confirmRemove}
        title="Remover bandeira?"
        message="A remoção é definitiva e auditável — a bandeira some já nesta versão; ocorrências encerradas não podem ser reabertas."
        confirmLabel="Remover"
        cancelLabel="Cancelar"
        variant="danger"
        confirmBusy={busy}
        onCancel={() => setConfirmRemove(false)}
        onConfirm={() => {
          if (!active) return;
          void run(() =>
            closePrcRecordFlag(
              recordId,
              active.id,
              "remove",
              { expectedVersion: active.version },
              newIdempotencyKey("pflag-remove"),
            ),
          );
        }}
      />
    </>
  );
}
