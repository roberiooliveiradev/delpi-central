/** Modal CRUD contextual de bandeira — kit oficial plugin-ui. */

import { useEffect, useId, useState } from "react";
import { Flag } from "lucide-react";

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
import { PRC_FIELD_LABELS, PRC_SUPPLIER_LABELS } from "../prcCopy";

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

export type FlagTargetContext = {
  subject: "FIELD" | "SUPPLIER_LINK" | "GENERAL";
  targetPath?: string | null;
  targetAttribute?: PrcFlagTargetAttribute | null;
  supplierKey?: { supplierCode: string; store: string } | null;
  currentValue?: string | null;
  fieldLabel?: string;
};

export function PrcFlagModal({
  open,
  requestId,
  flag,
  target,
  onClose,
  onChanged,
}: {
  open: boolean;
  requestId: string;
  flag: PrcAttendanceFlag | null;
  target: FlagTargetContext;
  onClose: () => void;
  onChanged: () => void | Promise<void>;
}) {
  const formId = useId();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!open) return;
    setTitle(flag?.title || "");
    setDescription(flag?.description || "");
    setError("");
    setConfirmDelete(false);
  }, [open, flag]);

  if (!open) return null;

  const isCreate = !flag;
  const targetTitle =
    target.subject === "FIELD"
      ? target.fieldLabel ||
        PRC_FIELD_LABELS[target.targetPath || ""] ||
        target.targetPath ||
        "Campo"
      : target.subject === "SUPPLIER_LINK"
        ? `${PRC_SUPPLIER_LABELS[target.targetAttribute || "partNumber"] || target.targetAttribute} — ${target.supplierKey?.supplierCode || "?"} / ${target.supplierKey?.store || "?"}`
        : "Bandeira legada (sem campo)";

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
      // Aguarda reload do provider antes de fechar — evita CAS com
      // versão obsoleta na próxima abertura do modal.
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
      } else if (flag) {
        await updatePrcFlag(
          requestId,
          flag.id,
          { expectedVersion: flag.version, title: t, description: d },
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
              Fechar
            </EngineeringActionButton>
            {flag?.status === "OPEN" ? (
              <EngineeringActionButton
                variant="secondary"
                disabled={busy}
                onClick={() =>
                  run(() =>
                    resolvePrcFlag(
                      requestId,
                      flag.id,
                      { expectedVersion: flag.version },
                      newIdempotencyKey("flag-resolve"),
                    ),
                  )
                }
              >
                Resolver
              </EngineeringActionButton>
            ) : null}
            {flag?.status === "RESOLVED" ? (
              <EngineeringActionButton
                variant="secondary"
                disabled={busy}
                onClick={() =>
                  run(() =>
                    reopenPrcFlag(
                      requestId,
                      flag.id,
                      { expectedVersion: flag.version },
                      newIdempotencyKey("flag-reopen"),
                    ),
                  )
                }
              >
                Reabrir
              </EngineeringActionButton>
            ) : null}
            {flag ? (
              <EngineeringActionButton
                variant="danger"
                disabled={busy}
                onClick={() => setConfirmDelete(true)}
              >
                Remover
              </EngineeringActionButton>
            ) : null}
            <EngineeringActionButton
              variant="primary"
              disabled={busy}
              onClick={() => void save()}
            >
              {isCreate ? "Criar" : "Salvar"}
            </EngineeringActionButton>
          </EngineeringFormActions>
        }
      >
        <div className="engineering-prc__flag-modal" id={formId}>
          <p className="engineering-prc__flag-modal-target">
            <Flag size={14} aria-hidden />
            <strong>{targetTitle}</strong>
          </p>
          {target.currentValue != null && target.currentValue !== "" ? (
            <p className="engineering-prc__muted">
              Valor atual (somente contexto): {target.currentValue}
            </p>
          ) : null}
          {flag ? (
            <dl className="engineering-prc__flag-meta">
              <div>
                <dt>Estado</dt>
                <dd>{flag.status === "OPEN" ? "Aberta" : "Resolvida"}</dd>
              </div>
              <div>
                <dt>Criada por</dt>
                <dd>
                  {actorLabel(flag.createdBy)} · {formatWhen(flag.createdAt)}
                </dd>
              </div>
              {flag.resolvedAt ? (
                <div>
                  <dt>Resolvida</dt>
                  <dd>
                    {actorLabel(flag.resolvedBy)} ·{" "}
                    {formatWhen(flag.resolvedAt)}
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
            value={title}
            onChange={setTitle}
            maxLength={120}
            required
            disabled={busy}
          />
          <EngineeringTextAreaField
            id={`${formId}-desc`}
            label="Descrição"
            value={description}
            onChange={setDescription}
            maxLength={1000}
            required
            disabled={busy}
            rows={5}
          />
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
          if (!flag) return;
          void run(() =>
            deletePrcFlag(
              requestId,
              flag.id,
              flag.version,
              newIdempotencyKey("flag-delete"),
            ),
          );
        }}
      />
    </>
  );
}
