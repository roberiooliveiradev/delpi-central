import { useEffect, useState } from "react";
import {
  ActionButton,
  NativeCheckboxControl,
  NativeTextAreaControl,
  NativeTextControl,
  SignatureCapturePanel,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { TransformometroShell } from "../../components/TransformometroShell";
import { buildAtaPath, TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  fetchSignatureImageBlob,
  getAtaSignContext,
  getSignatureProfile,
  refuseAta,
  signAta,
  type AtaDetail,
} from "../../data/api/transformometroMeetingMinutesApi";
import { MeetingMinuteDocumentView } from "../meeting-minutes/MeetingMinuteDocumentView";

type Props = Pick<AppProps, "getAccessToken"> & {
  ataId: string;
  onNavigate: (path: string) => void;
};

export function MeetingMinuteSignPage({ getAccessToken, ataId, onNavigate }: Props) {
  const [context, setContext] = useState<Record<string, unknown> | null>(null);
  const [name, setName] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [png, setPng] = useState<Blob | null>(null);
  const [hasSavedSignature, setHasSavedSignature] = useState(false);
  const [showPad, setShowPad] = useState(false);
  const [reason, setReason] = useState("");
  const [showRefuse, setShowRefuse] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void Promise.all([
      getAtaSignContext(ataId, getAccessToken),
      getSignatureProfile(getAccessToken).catch(() => null),
    ])
      .then(async ([data, profile]) => {
        setContext(data);
        setName(
          String(
            (data.signer as Record<string, unknown> | undefined)?.display_name ??
              profile?.display_name ??
              "",
          ),
        );
        const saved = Boolean(profile?.has_signature);
        setHasSavedSignature(saved);
        setShowPad(!saved);
      })
      .catch((value) =>
        setError(value instanceof Error ? value.message : "Erro ao carregar assinatura."),
      );
  }, [ataId, getAccessToken]);

  async function submit(signatureBlob: Blob) {
    if (!accepted || !name.trim()) {
      setError("Confirme o nome e aceite o termo para assinar.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("signature", signatureBlob, "signature.png");
      form.append("display_name_confirmed", name.trim());
      form.append("terms_accepted", "true");
      form.append("session_id", crypto.randomUUID());
      await signAta(ataId, form, getAccessToken);
      onNavigate(buildAtaPath(ataId));
    } catch (value) {
      setError(value instanceof Error ? value.message : "Erro ao assinar.");
    } finally {
      setBusy(false);
    }
  }

  async function signDrawn() {
    if (!png) {
      setError("Capture a assinatura antes de confirmar.");
      return;
    }
    await submit(png);
  }

  async function signSaved() {
    try {
      const blob = await fetchSignatureImageBlob(getAccessToken);
      await submit(blob);
    } catch (value) {
      setError(value instanceof Error ? value.message : "Erro ao usar assinatura cadastrada.");
      setShowPad(true);
    }
  }

  async function refuse() {
    if (!reason.trim()) {
      setError("Informe a justificativa da recusa.");
      return;
    }
    setBusy(true);
    try {
      await refuseAta(ataId, reason.trim(), getAccessToken);
      onNavigate(buildAtaPath(ataId));
    } catch (value) {
      setError(value instanceof Error ? value.message : "Erro ao recusar.");
    } finally {
      setBusy(false);
    }
  }

  const detail: AtaDetail | null = context
    ? {
        minute: (context.minute ?? {}) as Record<string, unknown>,
        version: (context.version ?? null) as Record<string, unknown> | null,
        participants: (context.participants ?? []) as Record<string, unknown>[],
        signers: (context.signers ?? []) as Record<string, unknown>[],
        signatures: (context.signatures ?? []) as Record<string, unknown>[],
      }
    : null;

  return (
    <TransformometroShell>
      <section className="ds-card">
        <h1>Assinar ata</h1>
        <p className="ds-muted">Leia o documento, confirme seu nome e assine.</p>
        {error ? <p role="alert">{error}</p> : null}
        {detail ? <MeetingMinuteDocumentView detail={detail} /> : null}

        <label className="ds-field">
          <span>Seu nome na ata</span>
          <NativeTextControl value={name} onChange={setName} />
        </label>
        <NativeCheckboxControl
          checked={accepted}
          onChange={setAccepted}
          label={String(
            context?.terms ??
              "Li o conteúdo e confirmo minha assinatura eletrônica nesta ata.",
          )}
        />

        <div className="ds-cadastro-form__actions">
          {hasSavedSignature ? (
            <ActionButton variant="primary" disabled={busy} onClick={() => void signSaved()}>
              Assinar com minha assinatura salva
            </ActionButton>
          ) : null}
          {!showPad ? (
            <ActionButton variant="link" onClick={() => setShowPad(true)}>
              Usar outra assinatura
            </ActionButton>
          ) : null}
        </div>

        {showPad ? (
          <>
            <SignatureCapturePanel
              displayName={name}
              showPreview
              padProps={{ className: "delpi-ui-signature-pad--tall" }}
              onChange={setPng}
            />
            <ActionButton variant="primary" disabled={busy || !png} onClick={() => void signDrawn()}>
              Confirmar assinatura
            </ActionButton>
          </>
        ) : null}

        {!showRefuse ? (
          <ActionButton variant="link" onClick={() => setShowRefuse(true)}>
            Recusar assinatura…
          </ActionButton>
        ) : (
          <>
            <h2>Recusar</h2>
            <NativeTextAreaControl
              value={reason}
              onChange={setReason}
              rows={3}
              placeholder="Justificativa obrigatória"
            />
            <ActionButton disabled={busy} onClick={() => void refuse()}>
              Confirmar recusa
            </ActionButton>
          </>
        )}

        <ActionButton variant="link" onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.atas)}>
          Voltar
        </ActionButton>
      </section>
    </TransformometroShell>
  );
}
