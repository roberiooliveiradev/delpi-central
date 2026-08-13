import { useCallback, useEffect, useMemo, useState } from "react";
import { ActionButton, StatusBadge, triggerFileDownload } from "@delpi/plugin-ui/index";
import {
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  Circle,
  Download,
  MapPin,
  Pencil,
  Send,
  Signature,
} from "lucide-react";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { buildAtaEditPath, buildAtaSignPath, TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  fetchAtaPdfBlob,
  finalizeAta,
  getAta,
  sendAta,
  type AtaDetail,
} from "../../data/api/transformometroMeetingMinutesApi";
import { MeetingMinuteDocumentView } from "../meeting-minutes/MeetingMinuteDocumentView";
import { ATA_MEETING_TYPE_LABELS, ATA_PARTICIPANT_ROLE_LABELS } from "../meeting-minutes/meetingMinuteLabels";
import {
  ataSignatureProgress,
  ataStatusLabel,
  ataStatusVariant,
  formatAtaMeetingDate,
  tmAtaStatusBadgeClassNames,
} from "../meeting-minutes/meetingMinuteStatusUi";

type Props = Pick<AppProps, "getAccessToken"> & {
  ataId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
};

function signerIsDone(status: string): boolean {
  return status === "signed";
}

export function MeetingMinuteDetailPage({ getAccessToken, ataId, pathname, onNavigate }: Props) {
  const [detail, setDetail] = useState<AtaDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setDetail(await getAta(ataId, getAccessToken));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Erro ao carregar ata.");
    } finally {
      setLoading(false);
    }
  }, [ataId, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    try {
      await action();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível concluir a ação.");
    } finally {
      setBusy(false);
    }
  }

  const minute = detail?.minute;
  const status = String(minute?.status ?? "");
  const editable = status === "draft" || status === "in_review";
  const canSend = editable;
  const canFinalize = status === "signed";
  const canSign = Boolean(detail?.viewer?.can_sign_now);
  const title = String(minute?.title ?? (loading ? "Carregando…" : "Ata"));
  const meetingType =
    ATA_MEETING_TYPE_LABELS[String(minute?.meeting_type ?? "")] ?? "Reunião";

  const signatureRows = useMemo(() => {
    if (!detail) return [];
    return detail.signers.map((signer) => {
      const userId = String(signer.user_id ?? "");
      const participant = detail.participants.find(
        (item) => String(item.user_id ?? "") === userId,
      );
      const sigStatus = String(signer.status ?? "pending");
      return {
        id: String(signer.id ?? userId),
        name: String(signer.display_name ?? "Signatário"),
        role:
          ATA_PARTICIPANT_ROLE_LABELS[String(participant?.role_in_meeting ?? "")] ??
          "Participante",
        status: sigStatus,
        done: signerIsDone(sigStatus),
      };
    });
  }, [detail]);

  const progress = useMemo(() => {
    const done = signatureRows.filter((row) => row.done).length;
    const total = signatureRows.length;
    return {
      done,
      total,
      pct: total > 0 ? Math.round((done / total) * 100) : 0,
      label: ataSignatureProgress({
        signatures_done: done,
        signatures_pending: Math.max(total - done, 0),
      }).label,
    };
  }, [signatureRows]);

  return (
    <TransformometroShell>
      <PageHeader
        title={title}
        subtitle="Visualização da ata Transforma+"
        currentPath={pathname}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={loading || busy}
        actions={
          <>
            {editable ? (
              <ActionButton onClick={() => onNavigate(buildAtaEditPath(ataId))}>
                <Pencil size={16} aria-hidden />
                Editar
              </ActionButton>
            ) : null}
            {canSend ? (
              <ActionButton
                variant="primary"
                onClick={() => void run(() => sendAta(ataId, getAccessToken))}
                disabled={busy}
              >
                <Send size={16} aria-hidden />
                Enviar para assinatura
              </ActionButton>
            ) : null}
            {canFinalize ? (
              <ActionButton
                onClick={() => void run(() => finalizeAta(ataId, getAccessToken))}
                disabled={busy}
              >
                <CheckCircle2 size={16} aria-hidden />
                Finalizar
              </ActionButton>
            ) : null}
            {canSign ? (
              <ActionButton
                variant="primary"
                onClick={() => onNavigate(buildAtaSignPath(ataId))}
              >
                <Signature size={16} aria-hidden />
                Assinar
              </ActionButton>
            ) : null}
            <ActionButton
              disabled={busy}
              onClick={() => {
                void (async () => {
                  setBusy(true);
                  setError(null);
                  try {
                    const { blob, filename } = await fetchAtaPdfBlob(ataId, getAccessToken);
                    triggerFileDownload(blob, filename);
                  } catch (err) {
                    setError(
                      err instanceof Error ? err.message : "Não foi possível baixar o PDF da ata.",
                    );
                  } finally {
                    setBusy(false);
                  }
                })();
              }}
            >
              <Download size={16} aria-hidden />
              PDF
            </ActionButton>
          </>
        }
      />

      {error ? (
        <p className="tm-atas-alert" role="alert">
          {error}
        </p>
      ) : null}

      {loading && !detail ? (
        <div className="tm-atas-view-loading ds-card" role="status">
          <div className="tm-atas-view-loading__pulse" />
          <p className="ds-muted">Carregando documento e assinaturas…</p>
        </div>
      ) : null}

      {detail ? (
        <div className="tm-atas-view">
          <aside className="tm-atas-view__aside" aria-label="Resumo e acompanhamento">
            <section className="tm-atas-view__panel ds-card">
              <div className="tm-atas-view__status-row">
                <StatusBadge
                  label={ataStatusLabel(status)}
                  variant={ataStatusVariant(status)}
                  classNames={tmAtaStatusBadgeClassNames}
                />
                {minute?.minute_number ? (
                  <span className="tm-atas-view__number">Nº {String(minute.minute_number)}</span>
                ) : null}
              </div>

              <h2 className="tm-atas-view__aside-title">{title}</h2>
              <p className="tm-atas-view__aside-lede ds-muted">{meetingType}</p>

              <ul className="tm-atas-view__facts">
                <li>
                  <Calendar size={16} aria-hidden />
                  <span>
                    <strong>Data</strong>
                    <small>{formatAtaMeetingDate(String(minute?.meeting_date ?? ""))}</small>
                  </span>
                </li>
                <li>
                  <Building2 size={16} aria-hidden />
                  <span>
                    <strong>Unidade</strong>
                    <small>{String(minute?.unit_code ?? "—")}</small>
                  </span>
                </li>
                <li>
                  <MapPin size={16} aria-hidden />
                  <span>
                    <strong>Local</strong>
                    <small>{String(minute?.location ?? "Não informado")}</small>
                  </span>
                </li>
              </ul>

              {editable ? (
                <p className="tm-atas-view__hint ds-muted">
                  Rascunho editável. Revise o conteúdo e envie para assinatura quando estiver pronto.
                  No envio, signatários Delpi recebem notificação no portal e todos com e-mail recebem
                  o link público de assinatura.
                </p>
              ) : null}

              <div className="tm-atas-view__aside-actions">
                {editable ? (
                  <ActionButton onClick={() => onNavigate(buildAtaEditPath(ataId))}>
                    <Pencil size={16} aria-hidden />
                    Continuar editando
                  </ActionButton>
                ) : null}
                {canSign ? (
                  <ActionButton
                    variant="primary"
                    onClick={() => onNavigate(buildAtaSignPath(ataId))}
                  >
                    <Signature size={16} aria-hidden />
                    Assinar agora
                  </ActionButton>
                ) : null}
              </div>
            </section>

            <section className="tm-atas-view__panel ds-card" aria-label="Progresso das assinaturas">
              <header className="tm-atas-view__panel-head">
                <h3>Assinaturas</h3>
                <span className="tm-atas-view__progress-label">
                  {progress.done}/{progress.total || "—"}
                </span>
              </header>
              <div
                className="tm-atas-view__progress-bar"
                role="progressbar"
                aria-valuenow={progress.pct}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={progress.label}
              >
                <span style={{ width: `${progress.pct}%` }} />
              </div>
              <p className="tm-atas-view__progress-caption ds-muted">{progress.label}</p>

              {signatureRows.length === 0 ? (
                <p className="ds-muted tm-atas-view__empty">Nenhum signatário definido.</p>
              ) : (
                <ul className="tm-atas-view__signers">
                  {signatureRows.map((row) => (
                    <li
                      key={row.id}
                      className={`tm-atas-view__signer${row.done ? " is-done" : ""}`}
                    >
                      {row.done ? (
                        <CheckCircle2 size={16} aria-hidden />
                      ) : (
                        <Circle size={16} aria-hidden />
                      )}
                      <span>
                        <strong>{row.name}</strong>
                        <small>{row.role}</small>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </aside>

          <section className="tm-atas-view__document" aria-label="Documento da ata">
            <MeetingMinuteDocumentView
              detail={detail}
              getAccessToken={getAccessToken}
              onError={setError}
            />
          </section>
        </div>
      ) : null}

      <div className="tm-atas-detail-footer">
        <ActionButton variant="link" onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.atas)}>
          <ArrowLeft size={16} aria-hidden />
          Voltar às atas
        </ActionButton>
      </div>
    </TransformometroShell>
  );
}
