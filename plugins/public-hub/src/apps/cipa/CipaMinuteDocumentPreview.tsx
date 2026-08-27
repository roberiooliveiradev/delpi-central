import { useEffect, useState } from "react";

import type { PublicSignContext } from "./signApi";
import { fetchPublicSignatureImageBlob } from "./signApi";
import "./sign.css";

type Props = {
  context: PublicSignContext;
  token: string;
};

function HtmlBlock({ title, html }: { title: string; html?: string | null }) {
  const content = (html || "").trim();
  if (!content) return null;
  return (
    <section className="cipa-sign-doc__section">
      <h2>{title}</h2>
      <div className="cipa-sign-doc__html" dangerouslySetInnerHTML={{ __html: content }} />
    </section>
  );
}

export function CipaMinuteDocumentPreview({ context, token }: Props) {
  const [signatureUrls, setSignatureUrls] = useState<Record<string, string>>({});

  useEffect(() => {
    const controller = new AbortController();
    const signatures = context.signatures || [];
    void (async () => {
      const entries = await Promise.all(
        signatures.map(async (signature) => {
          const signatureId = String(signature.id || "");
          if (!signatureId || !signature.has_image) return null;
          try {
            const blob = await fetchPublicSignatureImageBlob(token, signatureId);
            return [signatureId, URL.createObjectURL(blob)] as const;
          } catch {
            return null;
          }
        }),
      );
      if (controller.signal.aborted) return;
      const next: Record<string, string> = {};
      for (const entry of entries) {
        if (entry) next[entry[0]] = entry[1];
      }
      setSignatureUrls(next);
    })();
    return () => {
      controller.abort();
      Object.values(signatureUrls).forEach((url) => URL.revokeObjectURL(url));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- revoke on unmount only
  }, [context.signatures, token]);

  const minute = context.minute;
  const version = context.version;

  return (
    <article className="cipa-sign-doc" aria-label="Prévia da ata CIPA">
      <header className="cipa-sign-doc__header">
        <p className="cipa-sign-doc__number">{minute.minute_number || "—"}</p>
        <h2>{minute.title || "Ata CIPA"}</h2>
        <p className="cipa-sign-doc__meta">
          {[minute.meeting_date, minute.location].filter(Boolean).join(" · ")}
        </p>
      </header>

      <HtmlBlock title="Pauta" html={version.agenda_html} />
      <HtmlBlock title="Conteúdo" html={version.body_html} />
      <HtmlBlock title="Deliberações" html={version.decisions_html} />
      <HtmlBlock title="Pendências" html={version.pending_html} />
      <HtmlBlock title="Observações" html={version.observations_html} />

      {(context.signers || []).length > 0 ? (
        <section className="cipa-sign-doc__section">
          <h2>Assinaturas</h2>
          <ul className="cipa-sign-doc__signers">
            {(context.signers || []).map((signer) => {
              const signerId = String(signer.id || "");
              const signature = (context.signatures || []).find(
                (item) => String(item.signer_id || "") === signerId,
              );
              const imageUrl = signature?.id ? signatureUrls[String(signature.id)] : undefined;
              return (
                <li key={signerId}>
                  <strong>{String(signer.display_name || "—")}</strong>
                  <span>{String(signer.status || "pending")}</span>
                  {imageUrl ? (
                    <img src={imageUrl} alt={`Assinatura de ${String(signer.display_name || "")}`} />
                  ) : null}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </article>
  );
}
