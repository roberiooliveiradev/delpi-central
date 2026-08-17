import {
  DocumentFooter,
  DocumentPage,
  DocumentReader,
  DocumentReaderToolbar,
  DocumentSignatureBlock,
} from "@delpi/plugin-ui/index";

import type { PublicSignContext } from "./api";
import { isHtmlEmpty, mergeAtaContentHtml } from "./ataContent";
import logoTransformaMaisUrl from "./logoTransformaMaisDelpi.svg";

const MEETING_TYPE_LABELS: Record<string, string> = {
  ordinary: "Reunião ordinária",
  extraordinary: "Reunião extraordinária",
  workshop: "Workshop",
  follow_up: "Acompanhamento",
  kickoff: "Kickoff",
  other: "Outro",
};

const ROLE_LABELS: Record<string, string> = {
  chair: "Condução",
  secretary: "Secretário(a)",
  sponsor: "Patrocinador(a)",
  facilitator: "Facilitador(a)",
  participant: "Participante",
  guest: "Convidado(a)",
  other: "Outro",
};

const SIGNER_STATUS_LABELS: Record<string, string> = {
  pending: "Pendente",
  viewed: "Visualizada",
  signed: "Assinada",
  refused: "Recusada",
  invalidated: "Invalidada",
  cancelled: "Cancelada",
};

const MONTHS = [
  "",
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro",
];

function dateLong(value: unknown): string {
  const raw = String(value || "").slice(0, 10);
  const [year, month, day] = raw.split("-").map(Number);
  if (!year || !month || !day || !MONTHS[month]) return "data não informada";
  return `${day} de ${MONTHS[month]} de ${year}`;
}

function formatShortDate(value: unknown): string {
  const raw = String(value ?? "").trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(raw);
  if (!match) return raw || "—";
  const [, y, m, d] = match;
  return `${d}/${m}/${y}`;
}

function unitCity(unitCode: string): string {
  if (unitCode === "01") return "Jaraguá do Sul — SC";
  if (unitCode === "02") return "Unidade 02";
  return unitCode || "—";
}

type Props = {
  context: PublicSignContext;
};

export function PublicMeetingMinutePreview({ context }: Props) {
  const minute = context.minute;
  const version = context.version;
  const contentHtml = mergeAtaContentHtml(version);
  const meetingType =
    MEETING_TYPE_LABELS[String(minute.meeting_type ?? "")] ?? "Reunião";
  const unitCode = String(minute.unit_code ?? "");
  const participants = context.participants ?? [];
  const signers = context.signers ?? [];
  const status = String(minute.status ?? "");
  const showDraftWatermark = status === "draft" || status === "in_review";
  const showCancelledWatermark = status === "cancelled";

  return (
    <DocumentReader
      ariaLabel="Prévia da ata Transforma+"
      className="tm-sign-ata-reader"
      toolbar={
        <DocumentReaderToolbar
          printTitle={String(minute.title ?? minute.minute_number ?? "Ata Transforma+")}
        />
      }
    >
      <DocumentPage
        className="tm-sign-ata-paper"
        header={
          <div className="tm-sign-ata-brand">
            <img
              className="tm-sign-ata-logo"
              src={logoTransformaMaisUrl}
              alt="Transforma+ Delpi"
            />
          </div>
        }
        watermark={
          showDraftWatermark ? (
            <span className="tm-sign-ata-watermark">RASCUNHO</span>
          ) : showCancelledWatermark ? (
            <span className="tm-sign-ata-watermark tm-sign-ata-watermark--danger">
              CANCELADA
            </span>
          ) : null
        }
        footer={
          <div className="tm-sign-ata-footer">
            <DocumentFooter
              left={formatShortDate(minute.meeting_date)}
              center={
                <>
                  DELPI
                  <br />
                  {unitCity(unitCode)}
                </>
              }
              right={
                minute.minute_number ? `Ata ${String(minute.minute_number)}` : "Ata Transforma+"
              }
            />
            <div className="tm-sign-ata-brand-bar" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>
        }
      >
        <article className="tm-sign-ata-document">
          <header className="tm-sign-ata-document__header">
            <p className="tm-sign-ata-document__eyebrow">Ata oficial Transforma+</p>
            <h1 className="tm-sign-ata-document__title">
              {String(minute.title ?? "Ata")}
            </h1>
            <p className="tm-sign-ata-document__lede">
              {unitCity(unitCode)}, {dateLong(minute.meeting_date)}.
            </p>
            <dl className="tm-sign-ata-document__facts">
              <div>
                <dt>Tipo</dt>
                <dd>{meetingType}</dd>
              </div>
              <div>
                <dt>Unidade</dt>
                <dd>{unitCode || "—"}</dd>
              </div>
              <div>
                <dt>Local</dt>
                <dd>{String(minute.location ?? "Não informado")}</dd>
              </div>
              {minute.start_time || minute.end_time ? (
                <div>
                  <dt>Horário</dt>
                  <dd>
                    {String(minute.start_time ?? "—").slice(0, 5)}
                    {minute.end_time ? ` – ${String(minute.end_time).slice(0, 5)}` : ""}
                  </dd>
                </div>
              ) : null}
            </dl>
          </header>

          <section className="tm-sign-ata-document__body">
            {!isHtmlEmpty(contentHtml) ? (
              <div
                className="delpi-ui-document-rich-content"
                dangerouslySetInnerHTML={{ __html: contentHtml }}
              />
            ) : (
              <p className="tm-sign-ata-document__empty">Conteúdo ainda não preenchido.</p>
            )}
          </section>

          {participants.length > 0 ? (
            <section
              className="tm-sign-ata-document__participants"
              aria-label="Participantes"
            >
              <h2>Participantes</h2>
              <ul>
                {participants.map((item, index) => (
                  <li key={`${String(item.user_id ?? item.display_name)}-${index}`}>
                    <strong>{String(item.display_name ?? "—")}</strong>
                    <span>
                      {ROLE_LABELS[String(item.role_in_meeting ?? "")] ?? "Participante"}
                      {item.is_external ? " · externo" : ""}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="tm-sign-ata-document__signatures" aria-label="Assinaturas">
            <h2>Assinaturas</h2>
            {signers.length === 0 ? (
              <p className="tm-sign-ata-document__empty">Nenhum signatário definido.</p>
            ) : (
              <div className="tm-sign-ata-document__signature-grid">
                {signers.map((signer) => {
                  const participant = participants.find(
                    (item) =>
                      String(item.user_id ?? "") === String(signer.user_id ?? "") &&
                      Boolean(signer.user_id),
                  );
                  return (
                    <DocumentSignatureBlock
                      key={String(signer.id ?? signer.display_name)}
                      name={String(signer.display_name || "Signatário")}
                      role={
                        ROLE_LABELS[String(participant?.role_in_meeting ?? "")] ??
                        "Participante"
                      }
                      status={
                        SIGNER_STATUS_LABELS[String(signer.status ?? "pending")] ??
                        String(signer.status ?? "")
                      }
                    />
                  );
                })}
              </div>
            )}
          </section>
        </article>
      </DocumentPage>
    </DocumentReader>
  );
}
