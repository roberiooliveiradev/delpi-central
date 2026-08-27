import { useEffect, useMemo, useState } from "react";
import {
  DocumentFooter,
  DocumentHeader,
  DocumentPage,
  DocumentReader,
  DocumentReaderToolbar,
  DocumentSignatureBlock,
} from "@delpi/plugin-ui/index";

import logoCipa from "./assets/logo-cipa.png";
import {
  collapseNbspRuns,
  formatDateBr,
  formatMeetingDateLong,
  unitCityLabel,
} from "./cipaMinuteContent";
import {
  CIPA_PARTICIPANT_ROLE_LABELS,
  CIPA_STATUS_LABELS,
  cipaSignatureStatusLabel,
} from "./cipaMinuteLabels";
import type { CipaMeetingMinuteDocumentViewProps } from "./types";

function signatureHasImage(signature: {
  image_path?: string | null;
  has_image?: boolean | null;
}): boolean {
  if (typeof signature.has_image === "boolean") return signature.has_image;
  return Boolean(String(signature.image_path ?? "").trim());
}

/** Espelho de leitura do documento oficial; o PDF autoritativo continua no cipa-api. */
export function CipaMeetingMinuteDocumentView({
  minute,
  version = {},
  participants = [],
  signers = [],
  signatures = [],
  getSignatureImage,
  ariaLabel = "Modo de leitura da ata",
  className = "cipa-ata-reader",
}: CipaMeetingMinuteDocumentViewProps) {
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
        if (!signatureId || !signatureHasImage(signature)) return null;
        try {
          const blob = await getSignatureImage(signatureId);
          if (controller.signal.aborted) return null;
          const url = URL.createObjectURL(blob);
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

  const participantByUser = useMemo(
    () =>
      new Map(
        participants
          .filter((item) => item.user_id)
          .map((item) => [String(item.user_id), item]),
      ),
    [participants],
  );

  const meetingDate = minute.meeting_date || version?.meeting_date;
  const city = unitCityLabel(String(minute.unit_code || ""));

  return (
    <DocumentReader
      ariaLabel={ariaLabel}
      className={className}
      toolbar={
        <DocumentReaderToolbar
          printTitle={String(minute.title ?? minute.minute_number ?? "Ata CIPA")}
        />
      }
    >
      <DocumentPage
        className="cipa-ata-paper"
        header={
          <DocumentHeader
            logo={<img className="cipa-ata-document__logo" src={logoCipa} alt="CIPA Segurança" />}
            title="Comissão Interna de Prevenção de Acidentes"
            subtitle="Segurança: responsabilidade de cada um, tarefa de todos"
          />
        }
        watermark={<img src={logoCipa} alt="" />}
        footer={
          <DocumentFooter
            left={formatDateBr(String(meetingDate || ""))}
            center={
              <>
                DELPI
                <br />
                {city}
              </>
            }
            right={`Ata ${String(minute.minute_number || "—")}`}
          />
        }
      >
        <div className="cipa-minute-document">
          <h1>Ata de reunião da CIPA</h1>
          <p className="cipa-minute-document__date">
            {city}, {formatMeetingDateLong(meetingDate)}.
          </p>

          {["agenda_html", "body_html", "decisions_html", "pending_html", "observations_html"].map(
            (field) => {
              const html = String(version?.[field as keyof typeof version] || "");
              if (!html) return null;
              return (
                <div
                  key={field}
                  className="cipa-minute-document__content delpi-ui-document-rich-content"
                  dangerouslySetInnerHTML={{ __html: collapseNbspRuns(html) }}
                />
              );
            },
          )}

          <h2>Assinaturas:</h2>
          <div className="cipa-minute-document__signatures">
            {signers.map((signer) => {
              const userId = String(signer.user_id || "");
              const signerId = String(signer.id || "");
              const participant = participantByUser.get(userId);
              const signature =
                (userId ? signatureByUser.get(userId) : undefined) ??
                (signerId ? signatureBySignerId.get(signerId) : undefined);
              const signatureId = String(signature?.id || "");
              const imageUrl = signatureUrls[signatureId];
              return (
                <DocumentSignatureBlock
                  key={String(signer.id || userId)}
                  name={String(
                    signature?.display_name_confirmed || signer.display_name || "—",
                  )}
                  role={
                    CIPA_PARTICIPANT_ROLE_LABELS[String(participant?.role_in_meeting || "other")] ||
                    "Participante"
                  }
                  status={cipaSignatureStatusLabel(signer.status)}
                  image={
                    imageUrl ? (
                      <img src={imageUrl} alt={`Assinatura de ${String(signer.display_name || "")}`} />
                    ) : null
                  }
                />
              );
            })}
          </div>

          <div className="cipa-minute-document__validation">
            <span>
              Status: {CIPA_STATUS_LABELS[String(minute.status || "")] || String(minute.status || "—")}
            </span>
            <span>Código de validação: {String(minute.validation_code || "RASCUNHO")}</span>
            <span>Hash: {String(version?.content_hash || "—")}</span>
          </div>
        </div>
      </DocumentPage>
    </DocumentReader>
  );
}
