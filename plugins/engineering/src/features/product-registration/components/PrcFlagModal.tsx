/** Modal CRUD contextual de bandeira — PRC-REF-018 / D16-REF-03. */

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
  createPrcFlag,
  deletePrcFlag,
  reopenPrcFlag,
  resolvePrcFlag,
  updatePrcFlag,
  type PrcAttendanceFlag,
  type PrcFlagCreateBody,
  type PrcFlagTargetAttribute,
} from "../api/productRegistrationApi";
import {
  PRC_FIELD_LABELS,
  PRC_FLAG_ACTION_HELP,
  PRC_SUPPLIER_LABELS,
} from "../prcCopy";

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

export type FlagTargetContext = {
  subject: "FIELD" | "SUPPLIER_LINK" | "GENERAL";
  targetPath?: string | null;
  targetAttribute?: PrcFlagTargetAttribute | null;
  supplierKey?: { supplierCode: string; store: string } | null;
  currentValue?: string | null;
  fieldLabel?: string;
};

function sameTarget(flag: PrcAttendanceFlag, target: FlagTargetContext): boolean {
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

export function PrcFlagModal({
  open,
  requestId,
  flag,
  target,
  historyFlags = [],
  onClose,
  onChanged,
}: {
  open: boolean;
  requestId: string;
  flag: PrcAttendanceFlag | null;
  target: FlagTargetContext;
  /** Todas as bandeiras do caso — para histórico RESOLVED do mesmo alvo. */
  historyFlags?: PrcAttendanceFlag[];
  onClose: () => void;
  onChanged: () => void | Promise<void>;
}) {
  const formId = useId();
  const [active, setActive] = useState<PrcAttendanceFlag | null>(flag);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const siblingResolved = useMemo(
    () =>
      historyFlags
        .filter(
          (f) =>
            f.status === "RESOLVED" &&
            sameTarget(f, target) &&
            (!active || f.id !== active.id),
        )
        .sort((a, b) =>
          String(b.resolvedAt || b.updatedAt || "").localeCompare(
            String(a.resolvedAt || a.updatedAt || ""),
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
    setConfirmDelete(false);
  }, [open, flag]);

  if (!open) return null;

  const isCreate = !active;
  const targetTitle =
    target.subject === "FIELD"
      ? target.fieldLabel ||
        PRC_FIELD_LABELS[target.targetPath || ""] ||
        target.targetPath ||
        "Campo"
      : target.subject === "SUPPLIER_LINK"
        ? `${PRC_SUPPLIER_LABELS[target.targetAttribute || "partNumber"] || target.targetAttribute} — ${target.supplierKey?.supplierCode || "?"} / ${target.supplierKey?.store || "?"}`
        : "Bandeira legada (sem campo)";

  const selectFlag = (next: PrcAttendanceFlag) => {
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
        await createPrcFlag(requestId, body, newIdempotencyKey("flag-create"));
      } else if (active) {
        await updatePrcFlag(
          requestId,
          active.id,
          { expectedVersion: active.version, title: t, description: d },
          newIdempotencyKey("flag-update"),
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
            {active?.status === "OPEN" ? (
              <EngineeringActionButton
                variant="ghost"
                disabled={busy}
                onClick={() =>
                  run(() =>
                    resolvePrcFlag(
                      requestId,
                      active.id,
                      { expectedVersion: active.version },
                      newIdempotencyKey("flag-resolve"),
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
            {active?.status === "RESOLVED" ? (
              <EngineeringActionButton
                variant="ghost"
                disabled={busy}
                onClick={() =>
                  run(() =>
                    reopenPrcFlag(
                      requestId,
                      active.id,
                      { expectedVersion: active.version },
                      newIdempotencyKey("flag-reopen"),
                    ),
                  )
                }
              >
                <ActionLabel
                  icon={<Flag size={14} color="#b42318" />}
                  text="Reabrir"
                  help={PRC_FLAG_ACTION_HELP.reopen}
                />
              </EngineeringActionButton>
            ) : null}
            {active ? (
              <EngineeringActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setConfirmDelete(true)}
              >
                <ActionLabel
                  icon={<Trash2 size={14} />}
                  text="Remover"
                  help={PRC_FLAG_ACTION_HELP.remove}
                />
              </EngineeringActionButton>
            ) : null}
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
                  isCreate ? PRC_FLAG_ACTION_HELP.add : PRC_FLAG_ACTION_HELP.save
                }
              />
            </EngineeringActionButton>
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

          {siblingResolved.length > 0 ? (
            <div>
              <p className="engineering-prc__muted">
                Histórico resolvido neste campo — selecione para consultar ou
                reabrir:
              </p>
              <ul className="engineering-prc__flag-history">
                {siblingResolved.map((h) => (
                  <li key={h.id}>
                    <EngineeringActionButton
                      variant="ghost"
                      disabled={busy}
                      onClick={() => selectFlag(h)}
                    >
                      <Flag size={12} color="#1a7f37" aria-hidden /> {h.title} ·{" "}
                      {formatWhen(h.resolvedAt || h.updatedAt)}
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
                <dd>{active.status === "OPEN" ? "Aberta" : "Resolvida"}</dd>
              </div>
              <div>
                <dt>Criada por</dt>
                <dd>
                  {actorLabel(active.createdBy)} ·{" "}
                  {formatWhen(active.createdAt)}
                </dd>
              </div>
              {active.resolvedAt ? (
                <div>
                  <dt>Resolvida</dt>
                  <dd>
                    {actorLabel(active.resolvedBy)} ·{" "}
                    {formatWhen(active.resolvedAt)}
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
            disabled={busy || active?.status === "RESOLVED"}
          />
          <EngineeringTextAreaField
            id={`${formId}-desc`}
            label="Descrição"
            hint={PRC_FLAG_ACTION_HELP.edit}
            value={description}
            onChange={setDescription}
            maxLength={1000}
            required
            disabled={busy || active?.status === "RESOLVED"}
            rows={5}
          />
          {active?.status === "OPEN" ? (
            <p className="engineering-prc__muted">
              <Pencil size={12} aria-hidden /> Edite título/descrição e salve,
              ou use Resolver para encerrar o acompanhamento.
            </p>
          ) : null}
        </div>
      </EngineeringHostDialog>
      <EngineeringConfirmDialog
        open={confirmDelete}
        title="Remover bandeira?"
        message="A exclusão é lógica e auditável. O histórico permanece."
        confirmLabel="Remover"
        cancelLabel="Cancelar"
        variant="danger"
        confirmBusy={busy}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => {
          if (!active) return;
          void run(() =>
            deletePrcFlag(
              requestId,
              active.id,
              active.version,
              newIdempotencyKey("flag-delete"),
            ),
          );
        }}
      />
    </>
  );
}
