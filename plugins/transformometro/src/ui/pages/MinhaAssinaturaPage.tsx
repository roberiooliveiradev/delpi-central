import { useEffect, useState } from "react";
import { ActionButton, NativeTextControl, SignaturePad } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  getSignatureProfile,
  updateSignatureProfile,
  uploadSignature,
} from "../../data/api/transformometroAtaApi";

type Props = Pick<AppProps, "getAccessToken"> & { onNavigate?: (path: string) => void };

export function MinhaAssinaturaPage({ getAccessToken, onNavigate }: Props) {
  const [name, setName] = useState("");
  const [png, setPng] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    void getSignatureProfile(getAccessToken)
      .then((data) => setName(data.display_name))
      .catch((value) =>
        setError(value instanceof Error ? value.message : "Erro ao carregar assinatura."),
      );
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
      setError("Desenhe a assinatura antes de salvar.");
      return;
    }
    try {
      await uploadSignature(png, getAccessToken);
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
        <h2>Assinatura manuscrita</h2>
        <SignaturePad className="delpi-ui-signature-pad--tall" onChange={setPng} />
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
