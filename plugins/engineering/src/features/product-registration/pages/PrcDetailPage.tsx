/** Detalhe da solicitação PRC — ficha técnica editável (alteração
 * seletiva por path + CAS), ações de workflow guiadas por
 * allowedActions do backend e Verificar e concluir com resultado
 * campo-a-campo da verificação oficial TOTVS. Sem conclusão otimista. */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchPrcRequest,
  fetchPrcRevisions,
  fetchPrcTimeline,
  fetchPrcVerifications,
  prcAction,
  prcUpdateDraft,
  type PrcRequestDetail,
  type PrcRevision,
  type PrcTimelineEvent,
  type PrcVerification,
} from "../api/productRegistrationApi";

const STATUS_LABELS: Record<string, string> = {
  submitted: "Enviada",
  in_progress: "Em atendimento",
  needs_information: "Aguardando informações",
  under_review: "Em revisão",
  completed: "Concluída",
  rejected: "Rejeitada",
};

const FIELD_LABELS: Record<string, string> = {
  description: "Descrição",
  group: "Grupo",
  productKind: "Tipo",
  unit: "Unidade",
  defaultWarehouse: "Armazém padrão",
  thirdPartyProduct: "Produto de terceiros",
  accountingAccount: "Conta contábil",
  customerReference: "Referência do cliente",
  suppliers: "Fornecedores",
  officialProductCode: "Código oficial",
};

const ACTION_META: Record<
  string,
  { label: string; needsReason?: boolean; confirm?: string }
> = {
  start: { label: "Iniciar atendimento" },
  edit_draft: { label: "Editar ficha técnica" },
  request_information: {
    label: "Solicitar informações",
    needsReason: true,
  },
  resume: { label: "Retomar atendimento" },
  submit_review: { label: "Encaminhar para revisão" },
  reject: {
    label: "Rejeitar",
    needsReason: true,
    confirm: "Confirma a rejeição definitiva desta solicitação?",
  },
  verify_and_complete: {
    label: "Verificar e concluir",
    confirm:
      "A Engineering API consultará o cadastro oficial no TOTVS. A " +
      "solicitação só será concluída se todos os campos verificáveis " +
      "estiverem confirmados. Continuar?",
  },
};

function fieldLabel(path: string): string {
  return FIELD_LABELS[path] || path;
}

function fmt(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return `${value.length} fornecedor(es)`;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function PrcDetailPage({
  requestId,
  onBack,
}: {
  requestId: string;
  onBack: () => void;
}) {
  const [detail, setDetail] = useState<PrcRequestDetail | null>(null);
  const [timeline, setTimeline] = useState<PrcTimelineEvent[]>([]);
  const [verifications, setVerifications] = useState<PrcVerification[]>([]);
  const [revisions, setRevisions] = useState<PrcRevision[]>([]);
  const [state, setState] = useState<"loading" | "ok" | "error" | "forbidden">(
    "loading",
  );
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");
  const [officialCode, setOfficialCode] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [editReason, setEditReason] = useState("");
  const [verifyResult, setVerifyResult] = useState<Record<
    string,
    { result?: string; expected?: unknown; observed?: unknown; reason?: string }
  > | null>(null);

  const load = useCallback(async () => {
    setState("loading");
    try {
      const [d, t, v] = await Promise.all([
        fetchPrcRequest(requestId),
        fetchPrcTimeline(requestId),
        fetchPrcVerifications(requestId),
      ]);
      setDetail(d.data);
      setTimeline(t.data.items);
      setVerifications(v.data.items);
      setOfficialCode(d.data.officialCode || "");
      if (d.data.completedRecordId) {
        const rec = await fetchPrcRevisions(d.data.completedRecordId);
        setRevisions(rec.data.items);
      }
      setState("ok");
    } catch (e) {
      const err = e as { status?: number; message?: string };
      setError(err.message || "Falha ao carregar a solicitação.");
      setState(err.status === 403 ? "forbidden" : "error");
    }
  }, [requestId]);

  useEffect(() => {
    load();
  }, [load]);

  const runAction = useCallback(
    async (action: string, path: string, body: Record<string, unknown>) => {
      if (!detail) return;
      const meta = ACTION_META[action];
      if (meta?.confirm && !window.confirm(meta.confirm)) return;
      setBusy(true);
      setFeedback("");
      setVerifyResult(null);
      try {
        const res = await prcAction(
          requestId,
          path,
          { expectedVersion: detail.caseVersion, ...body },
          `prc-${action}-${requestId}-${detail.caseVersion}`,
        );
        setDetail(res.data);
        setFeedback("Operação aplicada com sucesso.");
        setReason("");
        await load();
      } catch (e) {
        const err = e as {
          status?: number;
          message?: string;
          fields?: Record<string, string>;
          data?: { fieldResults?: Record<string, unknown> };
        };
        const fr = (err as { fieldResults?: typeof verifyResult })
          .fieldResults;
        if (fr) setVerifyResult(fr as typeof verifyResult);
        setFeedback(
          err.status === 409
            ? `Conflito: ${err.message}. Recarregue e revise o estado atual.`
            : err.message || "Falha na operação.",
        );
      } finally {
        setBusy(false);
      }
    },
    [detail, requestId, load],
  );

  const saveDraftField = useCallback(
    async (path: string) => {
      if (!detail || !editReason.trim()) return;
      setBusy(true);
      try {
        const res = await prcUpdateDraft(requestId, {
          expectedVersion: detail.caseVersion,
          changes: [
            { path, proposedValue: editValue, reason: editReason.trim() },
          ],
        });
        setDetail(res.data);
        setEditing(null);
        setEditReason("");
        setFeedback("Campo da ficha atualizado.");
        await load();
      } catch (e) {
        const err = e as { status?: number; message?: string };
        setFeedback(
          err.status === 409
            ? `Conflito de versão — recarregue. ${err.message || ""}`
            : err.message || "Falha ao salvar o campo.",
        );
      } finally {
        setBusy(false);
      }
    },
    [detail, editValue, editReason, requestId, load],
  );

  const draft = detail?.technicalDraft || {};
  const changedPaths = useMemo(
    () => new Set((detail?.changedPaths || []).map((c) => c.path)),
    [detail],
  );

  if (state === "loading")
    return <p role="status">Carregando solicitação…</p>;
  if (state === "forbidden")
    return <p role="alert">Solicitação fora do seu escopo de acesso.</p>;
  if (state === "error" || !detail)
    return <p role="alert">{error || "Solicitação não encontrada."}</p>;

  const terminal =
    detail.status === "completed" || detail.status === "rejected";
  const canEdit = detail.allowedActions.includes("edit_draft");

  return (
    <section className="engineering-page">
      <button type="button" onClick={onBack} className="engineering-link">
        ← Voltar para a fila
      </button>

      <header>
        <h2>
          Solicitação {detail.id.slice(0, 8)} —{" "}
          {detail.requestType === "create" ? "Criação" : "Alteração"}
        </h2>
        <p>
          Status: <strong>{STATUS_LABELS[detail.status]}</strong> · versão{" "}
          {detail.caseVersion} · origem {detail.source}
        </p>
      </header>

      {feedback ? <p role="status">{feedback}</p> : null}

      <section aria-label="Identificação">
        <h3>Identificação</h3>
        <dl>
          <dt>Solicitante</dt>
          <dd>
            {detail.requester.displayName || detail.requester.subject}
          </dd>
          <dt>Responsável</dt>
          <dd>{detail.assignedTo || "—"}</dd>
          <dt>Código oficial TOTVS</dt>
          <dd>{detail.officialCode || "—"}</dd>
          <dt>Revisão base</dt>
          <dd>{detail.baseRevision ?? "—"}</dd>
          <dt>Abertura</dt>
          <dd>{new Date(detail.createdAt).toLocaleString("pt-BR")}</dd>
        </dl>
      </section>

      <section aria-label="Ficha técnica">
        <h3>Ficha técnica {canEdit ? "(edição autorizada)" : ""}</h3>
        <table className="engineering-table">
          <thead>
            <tr>
              <th>Campo</th>
              <th>Valor</th>
              {canEdit ? <th>Ação</th> : null}
            </tr>
          </thead>
          <tbody>
            {Object.entries(draft).map(([path, value]) => (
              <tr
                key={path}
                className={changedPaths.has(path) ? "prc-changed" : undefined}
              >
                <td>{fieldLabel(path)}</td>
                <td>
                  {editing === path ? (
                    <input
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      aria-label={`Editar ${fieldLabel(path)}`}
                    />
                  ) : Array.isArray(value) ? (
                    <ul>
                      {value.map((s, i) => (
                        <li key={i}>
                          {fmt(
                            (s as Record<string, unknown>).supplierCode,
                          )}
                          {" · loja "}
                          {fmt((s as Record<string, unknown>).store)}
                          {" · Part Number "}
                          {fmt(
                            (s as Record<string, unknown>).partNumber,
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    fmt(value)
                  )}
                </td>
                {canEdit ? (
                  <td>
                    {editing === path ? (
                      <>
                        <input
                          placeholder="Justificativa (obrigatória)"
                          value={editReason}
                          onChange={(e) => setEditReason(e.target.value)}
                          aria-label="Justificativa"
                        />
                        <button
                          type="button"
                          disabled={busy || !editReason.trim()}
                          onClick={() => saveDraftField(path)}
                        >
                          Salvar
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditing(null)}
                        >
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          setEditing(path);
                          setEditValue(fmt(value) === "—" ? "" : fmt(value));
                          setEditReason("");
                        }}
                      >
                        Editar
                      </button>
                    )}
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {detail.changedPaths.length > 0 ? (
        <section aria-label="Alterações propostas">
          <h3>Alterações propostas</h3>
          <ul>
            {detail.changedPaths.map((c) => (
              <li key={c.path}>
                {fieldLabel(c.path)} — {c.reason}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {detail.allowedActions.length > 0 ? (
        <section aria-label="Ações">
          <h3>Ações</h3>
          <div className="engineering-actions">
            {detail.allowedActions
              .filter((a) => a !== "edit_draft")
              .map((action) => {
                const meta = ACTION_META[action];
                if (!meta) return null;
                return (
                  <button
                    key={action}
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      if (meta.needsReason && !reason.trim()) {
                        setFeedback(
                          `Informe o motivo para "${meta.label}".`,
                        );
                        return;
                      }
                      const path =
                        action === "request_information"
                          ? "request-information"
                          : action === "submit_review"
                            ? "submit-review"
                            : action === "verify_and_complete"
                              ? "verify-and-complete"
                              : action;
                      runAction(action, path, {
                        reason: reason.trim() || undefined,
                        officialCode:
                          action === "verify_and_complete"
                            ? officialCode || undefined
                            : undefined,
                      });
                    }}
                  >
                    {meta.label}
                  </button>
                );
              })}
          </div>
          <input
            placeholder="Motivo (quando exigido)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            aria-label="Motivo da ação"
          />
          {detail.allowedActions.includes("verify_and_complete") ? (
            <label>
              Código oficial para verificação
              <input
                value={officialCode}
                onChange={(e) => setOfficialCode(e.target.value)}
                aria-label="Código oficial TOTVS"
              />
            </label>
          ) : null}
        </section>
      ) : null}

      {verifyResult ? (
        <section aria-label="Resultado da verificação">
          <h3>Resultado da verificação oficial</h3>
          <table className="engineering-table">
            <thead>
              <tr>
                <th>Campo</th>
                <th>Esperado</th>
                <th>Observado</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(verifyResult).map(([path, r]) => (
                <tr key={path}>
                  <td>{fieldLabel(path)}</td>
                  <td>{fmt(r.expected)}</td>
                  <td>{fmt(r.observed)}</td>
                  <td>{r.result || r.reason || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      {verifications.length > 0 ? (
        <section aria-label="Verificações TOTVS">
          <h3>Verificações oficiais</h3>
          <ul>
            {verifications.map((v) => (
              <li key={v.id}>
                {new Date(v.checked_at).toLocaleString("pt-BR")} —{" "}
                {v.result} ({v.official_product_code})
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {revisions.length > 0 ? (
        <section aria-label="Revisões">
          <h3>Revisões técnicas</h3>
          <table className="engineering-table">
            <thead>
              <tr>
                <th>Revisão</th>
                <th>Data</th>
                <th>Autor</th>
                <th>Campos alterados</th>
              </tr>
            </thead>
            <tbody>
              {revisions.map((rev) => (
                <tr key={rev.id}>
                  <td>{rev.revision_number}</td>
                  <td>{new Date(rev.approved_at).toLocaleString("pt-BR")}</td>
                  <td>{rev.approved_by_subject}</td>
                  <td>
                    {rev.changes.map((c) => fieldLabel(c.path)).join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <section aria-label="Histórico">
        <h3>Histórico de atendimento</h3>
        <ol>
          {timeline.map((ev) => (
            <li key={ev.id}>
              {new Date(ev.occurred_at).toLocaleString("pt-BR")} —{" "}
              {ev.event_type}
              {ev.previous_status && ev.next_status
                ? ` (${STATUS_LABELS[ev.previous_status] || ev.previous_status} → ${STATUS_LABELS[ev.next_status] || ev.next_status})`
                : ""}
              {ev.reason ? ` — ${ev.reason}` : ""} · {ev.actor_subject}
            </li>
          ))}
        </ol>
      </section>

      {terminal ? (
        <p>
          Solicitação encerrada —{" "}
          {STATUS_LABELS[detail.status].toLowerCase()}. Nenhuma ação
          disponível.
        </p>
      ) : null}
    </section>
  );
}
