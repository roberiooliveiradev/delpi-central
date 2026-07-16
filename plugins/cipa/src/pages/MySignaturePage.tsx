import { useEffect, useState } from "react";
import {
  FieldLabel,
  HelpTooltip,
  NativeTextControl,
  SignaturePad,
} from "@delpi/plugin-ui/index";
import { PenLine, Save } from "lucide-react";

import {
  fetchMySignatureImageBlob,
  getMySignatureProfile,
  updateMySignatureProfile,
  uploadMySignatureImage,
} from "../api/cipaApi";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCipa } from "../hooks/useCipaRouterPath";

export function MySignaturePage() {
  const [displayName, setDisplayName] = useState("");
  const [hasSignature, setHasSignature] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [png, setPng] = useState<Blob | null>(null);
  const [padKey, setPadKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingImage, setSavingImage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getMySignatureProfile(controller.signal)
      .then(async (data) => {
        setDisplayName(data.display_name || "");
        setHasSignature(Boolean(data.has_signature));
        setError(null);
        if (data.has_signature) {
          await loadPreview(controller.signal);
        }
      })
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro ao carregar assinatura.");
        }
      })
      .finally(() => setLoading(false));
    return () => {
      controller.abort();
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    };
  }, []);

  async function loadPreview(signal?: AbortSignal) {
    try {
      const blob = await fetchMySignatureImageBlob(signal);
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
      setHasSignature(true);
    } catch {
      setHasSignature(false);
    }
  }

  async function handleSaveProfile() {
    if (!displayName.trim()) {
      setError("Informe o nome para assinatura.");
      return;
    }
    setSavingProfile(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await updateMySignatureProfile({ display_name: displayName.trim() });
      setDisplayName(data.display_name);
      setSuccess("Nome para assinatura salvo.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar o nome.");
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleSaveImage() {
    if (!png) {
      setError("Desenhe a assinatura antes de salvar.");
      return;
    }
    setSavingImage(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await uploadMySignatureImage(png);
      setHasSignature(Boolean(data.has_signature));
      setSuccess("Assinatura pessoal salva.");
      await loadPreview();
      setPng(null);
      setPadKey((value) => value + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar a assinatura.");
    } finally {
      setSavingImage(false);
    }
  }

  if (loading) {
    return <p className="cipa-state">Carregando sua assinatura…</p>;
  }

  return (
    <div className="cipa-page-stack">
      <header className="cipa-header">
        <div>
          <button type="button" className="cipa-link" onClick={() => navigateCipa("/apps/cipa")}>
            ← Voltar ao início
          </button>
          <h1>Minha assinatura</h1>
          <p>
            Configure o nome e o traço que serão reutilizados ao assinar atas. Cada usuário
            acessa apenas o próprio perfil.
          </p>
        </div>
      </header>

      {error && <p className="cipa-error">{error}</p>}
      {success && <p className="cipa-state">{success}</p>}

      <section className="cipa-card">
        <h2>Nome para assinatura</h2>
        <div className="cipa-field">
          <FieldLabel
            label="Nome exibido"
            htmlFor="cipa-my-signature-name"
            className="cipa-field__label"
          />
          <NativeTextControl
            id="cipa-my-signature-name"
            value={displayName}
            onChange={setDisplayName}
            placeholder="Seu nome completo"
          />
        </div>
        <div className="cipa-footer-actions">
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            disabled={savingProfile}
            onClick={() => void handleSaveProfile()}
          >
            <Save size={16} /> Salvar nome
          </button>
        </div>
      </section>

      <section className="cipa-card">
        <h2>
          Assinatura manuscrita <HelpTooltip content={helpTooltips.signaturePad} />
        </h2>
        {hasSignature && previewUrl ? (
          <div className="cipa-signature-preview">
            <p className="cipa-state">Assinatura cadastrada</p>
            <img src={previewUrl} alt="Assinatura cadastrada" className="cipa-signature-img" />
          </div>
        ) : (
          <p className="cipa-state">Nenhuma assinatura cadastrada ainda.</p>
        )}
        <p>Desenhe abaixo para criar ou substituir a assinatura salva.</p>
        <SignaturePad key={padKey} onChange={setPng} />
        <div className="cipa-footer-actions">
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            disabled={savingImage || !png}
            onClick={() => void handleSaveImage()}
          >
            <PenLine size={16} /> Salvar assinatura
          </button>
        </div>
      </section>
    </div>
  );
}
