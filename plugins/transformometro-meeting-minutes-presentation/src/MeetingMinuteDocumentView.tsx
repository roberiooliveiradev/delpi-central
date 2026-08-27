import { useEffect, useMemo, useState } from "react";
import {
  DocumentFooter,
  DocumentPage,
  DocumentReader,
  DocumentReaderToolbar,
  DocumentSignatureBlock,
  normalizeSignatureDisplayPngBlob,
} from "@delpi/plugin-ui/index";

import { AtaBrandBar, transformaMaisLogoSrc } from "./meetingMinuteBrand";
import { isHtmlEmpty, mergeAtaContentHtml } from "./meetingMinuteContent";
import {
  ATA_MEETING_TYPE_LABELS,
  ATA_PARTICIPANT_ROLE_LABELS,
} from "./meetingMinuteLabels";
import {
  ataSignatureStatusLabel,
  ataStatusLabel,
  formatAtaMeetingDate,
} from "./meetingMinuteStatusUi";
import type { MeetingMinuteDocumentViewProps } from "./types";

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

function unitCity(unitCode: string): string {
  if (unitCode === "01") return "Jaraguá do Sul — SC";
  if (unitCode === "02") return "Unidade 02";
  return unitCode || "—";
}

function signatureHasImage(signature: {
  image_path?: string | null;
  has_image?: boolean | null;
}): boolean {
  if (typeof signature.has_image === "boolean") return signature.has_image;
  return Boolean(String(signature.image_path ?? "").trim());
}

export function MeetingMinuteDocumentView({
  minute,
  version = {},
  participants = [],
  signers = [],
  signatures = [],
  getSignatureImage,
  ariaLabel = "Leitura da ata Transforma+",
  className = "tm-ata-reader",
}: MeetingMinuteDocumentViewProps) {
  const status = String(minute.status ?? "");
  const contentHtml = mergeAtaContentHtml(version);
  const meetingType =
    ATA_MEETING_TYPE_LABELS[String(minute.meeting_type ?? "")] ?? "Reunião";
  const [signatureUrls, setSignatureUrls] = useState<Record<string, string>>({});

  const signatureByUser = useMemo(
    () =>
      new Map(
        signatures
          .filter((item) => item.user_id)
          .map((item) => [String(item.user_id), item]),
      ),
    [signatures],
  );

  const signatureBySignerId = useMemo(
    () =>
      new Map(
        signatures
          .filter((item) => item.signer_id)
          .map((item) => [String(item.signer_id), item]),
      ),
    [signatures],
  );

  useEffect(() => {
    if (!getSignatureImage) {
      setSignatureUrls({});
      return;
    }
    const controller = new AbortController();
    const createdUrls: string[] = [];
    void Promise.all(
      signatures.map(async (signature) => {
        const signatureId = String(signature.id || "");
        if (!signatureId || !signatureHasImage(signature)) {
          return null;
        }
        try {
          const blob = await getSignatureImage(signatureId);
          if (controller.signal.aborted) return null;
          const normalized = await normalizeSignatureDisplayPngBlob(blob);
          if (controller.signal.aborted) return null;
          const url = URL.createObjectURL(normalized);
          createdUrls.push(url);
          return [signatureId, url] as const;
        } catch {
          return null;
        }
      }),
    ).then((entries) => {
      if (controller.signal.aborted) return;
      setSignatureUrls(
        Object.fromEntries(
          entries.filter((entry): entry is readonly [string, string] => Boolean(entry)),
        ),
      );
    });
    return () => {
      controller.abort();
      createdUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [getSignatureImage, signatures]);

  const showDraftWatermark = status === "draft" || status === "in_review";
  const showCancelledWatermark = status === "cancelled";

  return (
    <DocumentReader
      ariaLabel={ariaLabel}
      className={className}
      toolbar={
        <DocumentReaderToolbar
          printTitle={String(minute.title ?? minute.minute_number ?? "Ata Transforma+")}
        />
      }
    >
      <DocumentPage
        className="tm-ata-paper"
        header={
          <div className="tm-ata-document-brand">
            <img
              className="tm-ata-document__logo"
              src={transformaMaisLogoSrc()}
              alt="Transforma+ Delpi"
            />
          </div>
        }
        watermark={
          showDraftWatermark ? (
            <span className="tm-ata-watermark">RASCUNHO</span>
          ) : showCancelledWatermark ? (
            <span className="tm-ata-watermark tm-ata-watermark--danger">CANCELADA</span>
          ) : null
        }
        footer={
          <div className="tm-ata-document-footer">
            <DocumentFooter
              left={formatAtaMeetingDate(String(minute.meeting_date ?? ""))}
              center={
                <>
                  DELPI
                  <br />
                  {unitCity(String(minute.unit_code ?? ""))}
                </>
              }
              right={
                minute.minute_number
                  ? `Ata ${String(minute.minute_number)}`
                  : ataStatusLabel(status) || "Ata Transforma+"
              }
            />
            <AtaBrandBar />
          </div>
        }
      >
        <article className="tm-ata-document">
          <header className="tm-ata-document__header">
            <p className="tm-ata-document__eyebrow">Ata oficial Transforma+</p>
            <h1 className="tm-ata-document__title">{String(minute.title ?? "Ata")}</h1>
            <p className="tm-ata-document__lede">
              {unitCity(String(minute.unit_code ?? ""))}, {dateLong(minute.meeting_date)}.
            </p>
            <dl className="tm-ata-document__facts">
              <div>
                <dt>Tipo</dt>
                <dd>{meetingType}</dd>
              </div>
              <div>
                <dt>Unidade</dt>
                <dd>{String(minute.unit_code ?? "—")}</dd>
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

          <section className="tm-ata-document__body">
            {!isHtmlEmpty(contentHtml) ? (
              <div
                className="delpi-ui-document-rich-content"
                dangerouslySetInnerHTML={{ __html: contentHtml }}
              />
            ) : (
              <p className="tm-ata-document__empty">Conteúdo ainda não preenchido.</p>
            )}
          </section>

          {participants.length > 0 ? (
            <section className="tm-ata-document__participants" aria-label="Participantes">
              <h2>Participantes</h2>
              <ul>
                {participants.map((item, index) => (
                  <li key={`${String(item.user_id ?? item.display_name)}-${index}`}>
                    <strong>{String(item.display_name ?? "—")}</strong>
                    <span>
                      {ATA_PARTICIPANT_ROLE_LABELS[String(item.role_in_meeting ?? "")] ??
                        "Participante"}
                      {item.is_external ? " · externo" : ""}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="tm-ata-document__signatures" aria-label="Assinaturas">
            <h2>Assinaturas</h2>
            {signers.length === 0 ? (
              <p className="tm-ata-document__empty">Nenhum signatário definido.</p>
            ) : (
              <div className="tm-ata-document__signature-grid">
                {signers.map((signer) => {
                  const userId = String(signer.user_id ?? "");
                  const signerId = String(signer.id ?? "");
                  const participant = participants.find(
                    (item) => String(item.user_id ?? "") === userId && Boolean(userId),
                  );
                  const signature =
                    (userId ? signatureByUser.get(userId) : undefined) ??
                    (signerId ? signatureBySignerId.get(signerId) : undefined);
                  const signatureId = String(signature?.id ?? "");
                  const imageUrl = signatureUrls[signatureId];
                  return (
                    <DocumentSignatureBlock
                      key={String(signer.id ?? userId)}
                      name={String(
                        signature?.display_name_confirmed ||
                          signer.display_name ||
                          "Signatário",
                      )}
                      role={
                        ATA_PARTICIPANT_ROLE_LABELS[
                          String(participant?.role_in_meeting ?? "")
                        ] ?? "Participante"
                      }
                      status={ataSignatureStatusLabel(String(signer.status ?? "pending"))}
                      image={
                        imageUrl ? (
                          <img
                            src={imageUrl}
                            alt={`Assinatura de ${String(signer.display_name || "")}`}
                          />
                        ) : null
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
