import { useEffect, useState } from "react";
import { ActionButton, NativeTextControl, SignatureCapturePanel } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  fetchSignatureImageBlob,
  getSignatureProfile,
  updateSignatureProfile,
  uploadSignature,
} from "../../data/api/transformometroMeetingMinutesApi";

type Props = Pick<AppProps, "getAccessToken"> & { onNavigate?: (path: string) => void };

export function MySignaturePage({ getAccessToken, onNavigate }: Props) {
  const [name, setName] = useState("");
  const [png, setPng] = useState<Blob | null>(null);
  const [savedPreviewUrl, setSavedPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;
    void (async () => {
      try {
        const data = await getSignatureProfile(getAccessToken);
        if (cancelled) return;
        setName(data.display_name);
        if (data.has_signature) {
          const blob = await fetchSignatureImageBlob(getAccessToken);
          if (cancelled) return;
          objectUrl = URL.createObjectURL(blob);
          setSavedPreviewUrl(objectUrl);
        } else {
          setSavedPreviewUrl(null);
        }
      } catch (value) {
        if (!cancelled) {
          setError(value instanceof Error ? value.message : "Erro ao carregar assinatura.");
        }
      }
    })();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [getAccessToken]);

  async function saveName() {
    try {
      const data = await updateSignatureProfile({ display_name: name.trim() }, getAccessToken);
      setName(data.display_name);
      setSuccess("Nome para assinatura salvo.");
      setError(null);
    } catch (value) {
      setError(value instanceof Error ? value.message : "Erro ao salvar nome.");
    }
  }

  async function saveSignature() {
    if (!png) {
      setError("Capture a assinatura antes de salvar.");
      return;
    }
    try {
      await uploadSignature(png, getAccessToken);
      if (savedPreviewUrl) URL.revokeObjectURL(savedPreviewUrl);
      const nextUrl = URL.createObjectURL(png);
      setSavedPreviewUrl(nextUrl);
      setSuccess("Assinatura pessoal salva.");
      setPng(null);
      setError(null);
    } catch (value) {
      setError(value instanceof Error ? value.message : "Erro ao salvar assinatura.");
    }
  }

  return (
    <TransformometroShell>
      <section className="ds-card">
        <h1>Minha assinatura</h1>
        <p>Configure o nome e o traço reutilizados nas atas Transforma+.</p>
        {error ? <p role="alert">{error}</p> : null}
        {success ? <p role="status">{success}</p> : null}
        <label className="ds-field">
          <span>Nome exibido</span>
          <NativeTextControl value={name} onChange={setName} />
        </label>
        <ActionButton variant="primary" onClick={() => void saveName()}>
          Salvar nome
        </ActionButton>

        {savedPreviewUrl ? (
          <div className="ds-field">
            <span>Assinatura salva</span>
            <img
              src={savedPreviewUrl}
              alt="Assinatura pessoal salva"
              style={{ maxWidth: "100%", height: "auto", display: "block" }}
            />
          </div>
        ) : null}

        <h2>Nova assinatura</h2>
        <SignatureCapturePanel
          displayName={name}
          showPreview
          padProps={{ className: "delpi-ui-signature-pad--tall" }}
          onChange={setPng}
        />
        <ActionButton variant="primary" disabled={!png} onClick={() => void saveSignature()}>
          Salvar assinatura
        </ActionButton>
        {onNavigate ? (
          <ActionButton variant="link" onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.atas)}>
            Voltar às atas
          </ActionButton>
        ) : null}
      </section>
    </TransformometroShell>
  );
}
