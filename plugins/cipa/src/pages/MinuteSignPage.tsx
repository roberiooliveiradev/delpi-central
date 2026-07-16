import { useEffect, useState } from "react";
import { HelpTooltip, SignaturePad } from "@delpi/plugin-ui/index";

import { getSignContext, refuseMinute, signMinute } from "../api/cipaApi";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCipa } from "../hooks/useCipaRouterPath";

type Props = {
  unitCode: "01" | "02";
  minuteId: string;
};

export function MinuteSignPage({ unitCode, minuteId }: Props) {
  const [context, setContext] = useState<Record<string, unknown> | null>(null);
  const [name, setName] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [png, setPng] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [refuseReason, setRefuseReason] = useState("");

  useEffect(() => {
    getSignContext(minuteId)
      .then((data) => {
        setContext(data);
        const signer = data.signer as { display_name?: string } | undefined;
        setName(signer?.display_name || "");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erro"));
  }, [minuteId]);

  async function confirmSign() {
    if (!png || !accepted || !name.trim()) {
      setError("Preencha nome, aceite o termo e desenhe a assinatura.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("signature", png, "signature.png");
      form.append("display_name_confirmed", name.trim());
      form.append("terms_accepted", "true");
      form.append("session_id", crypto.randomUUID());
      await signMinute(minuteId, form, crypto.randomUUID());
      navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao assinar");
    } finally {
      setBusy(false);
    }
  }

  async function confirmRefuse() {
    if (!refuseReason.trim()) {
      setError("Informe a justificativa da recusa.");
      return;
    }
    setBusy(true);
    try {
      await refuseMinute(minuteId, refuseReason.trim());
      navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao recusar");
    } finally {
      setBusy(false);
    }
  }

  const minute = (context?.minute || {}) as Record<string, unknown>;
  const version = (context?.version || {}) as Record<string, unknown>;
  const terms = String(context?.terms || "");

  return (
    <div className="cipa-page-stack cipa-sign-page">
      <header className="cipa-header">
        <div>
          <h1>Assinatura da ata</h1>
          <p>
            {String(minute.minute_number || "")} — {String(minute.title || "")}
          </p>
        </div>
      </header>

      {error && <p className="cipa-error">{error}</p>}

      <section className="cipa-card">
        <h2>Resumo</h2>
        <div
          className="cipa-prose"
          dangerouslySetInnerHTML={{
            __html: String(version.body_html || "<p>Sem conteúdo.</p>"),
          }}
        />
      </section>

      <section className="cipa-card">
        <label>
          Nome do signatário
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label className="cipa-check">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
          />
          {terms}
        </label>
        <p>
          Assinatura <HelpTooltip content={helpTooltips.signaturePad} />
        </p>
        <SignaturePad onChange={setPng} />
        <div className="cipa-footer-actions">
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            disabled={busy}
            onClick={() => void confirmSign()}
          >
            Confirmar assinatura
          </button>
        </div>
      </section>

      <section className="cipa-card">
        <h2>Recusar assinatura</h2>
        <textarea
          value={refuseReason}
          onChange={(e) => setRefuseReason(e.target.value)}
          rows={3}
          placeholder="Justificativa obrigatória"
        />
        <button
          type="button"
          className="cipa-btn"
          disabled={busy}
          onClick={() => void confirmRefuse()}
        >
          Recusar
        </button>
      </section>
    </div>
  );
}
