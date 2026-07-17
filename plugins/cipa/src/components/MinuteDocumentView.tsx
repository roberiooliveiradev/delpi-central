import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  DocumentFooter,
  DocumentHeader,
  DocumentPage,
  DocumentReader,
  DocumentSignatureBlock,
} from "@delpi/plugin-ui/index";

import { getSignatureImage, type MinuteDetail } from "../api/cipaApi";
import {
  PARTICIPANT_ROLE_LABELS,
  STATUS_LABELS,
  UNIT_LABELS,
} from "../constants/labels";
import logoCipa from "../assets/logo-cipa.png";
import { collapseNbspRuns, formatDateBr } from "../utils/htmlContent";

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
  return unitCode === "01" ? "Jaraguá do Sul - SC" : UNIT_LABELS[unitCode] || unitCode;
}

function signatureStatus(value: unknown): string {
  const status = String(value || "");
  const labels: Record<string, string> = {
    pending: "Pendente",
    viewed: "Visualizada",
    signed: "Assinada",
    refused: "Recusada",
    invalidated: "Invalidada",
  };
  return labels[status] || status;
}

export type MinuteDocumentViewProps = {
  detail: MinuteDetail;
  toolbar?: ReactNode;
  className?: string;
};

/** Espelho de leitura do documento oficial; o PDF autoritativo continua no cipa-api. */
export function MinuteDocumentView({
  detail,
  toolbar,
  className,
}: MinuteDocumentViewProps) {
  const minute = detail.minute;
  const version = detail.version || {};
  const minuteId = String(minute.id || "");
  const [signatureUrls, setSignatureUrls] = useState<Record<string, string>>({});

  useEffect(() => {
    const controller = new AbortController();
    const createdUrls: string[] = [];
    const signatures = detail.signatures || [];
    void Promise.all(
      signatures.map(async (signature) => {
        const signatureId = String(signature.id || "");
        if (!minuteId || !signatureId) return null;
        try {
          const blob = await getSignatureImage(minuteId, signatureId, controller.signal);
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
        Object.fromEntries(entries.filter((entry): entry is readonly [string, string] => Boolean(entry))),
      );
    });
    return () => {
      controller.abort();
      createdUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [detail.signatures, minuteId]);

  const participantByUser = useMemo(
    () =>
      new Map(
        (detail.participants || [])
          .filter((item) => item.user_id)
          .map((item) => [String(item.user_id), item]),
      ),
    [detail.participants],
  );
  const signatureByUser = useMemo(
    () =>
      new Map(
        (detail.signatures || [])
          .filter((item) => item.user_id)
          .map((item) => [String(item.user_id), item]),
      ),
    [detail.signatures],
  );

  const meetingDate = minute.meeting_date || version.meeting_date;
  const city = unitCity(String(minute.unit_code || ""));

  return (
    <DocumentReader toolbar={toolbar} className={className} ariaLabel="Modo de leitura da ata">
      <DocumentPage
        header={
          <DocumentHeader
            logo={<img src={logoCipa} alt="CIPA Segurança" />}
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
            {city}, {dateLong(meetingDate)}.
          </p>

          {["agenda_html", "body_html", "decisions_html", "pending_html", "observations_html"].map(
            (field) => {
              const html = String(version[field] || "");
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
            {(detail.signers || []).map((signer) => {
              const userId = String(signer.user_id || "");
              const participant = participantByUser.get(userId);
              const signature = signatureByUser.get(userId);
              const signatureId = String(signature?.id || "");
              const imageUrl = signatureUrls[signatureId];
              return (
                <DocumentSignatureBlock
                  key={String(signer.id || userId)}
                  name={String(
                    signature?.display_name_confirmed || signer.display_name || "—",
                  )}
                  role={
                    PARTICIPANT_ROLE_LABELS[String(participant?.role_in_meeting || "other")] ||
                    "Participante"
                  }
                  status={signatureStatus(signer.status)}
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
              Status: {STATUS_LABELS[String(minute.status || "")] || String(minute.status || "—")}
            </span>
            <span>Código de validação: {String(minute.validation_code || "RASCUNHO")}</span>
            <span>Hash: {String(version.content_hash || "—")}</span>
          </div>
        </div>
      </DocumentPage>
    </DocumentReader>
  );
}
