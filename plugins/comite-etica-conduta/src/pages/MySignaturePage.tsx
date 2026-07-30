import { useEffect, useState } from "react";
import {
  ActionButton,
  BackLink,
  FieldLabel,
  NativeTextControl,
  SignaturePad,
} from "@delpi/plugin-ui/index";
import { PenLine, Save } from "lucide-react";

import {
  fetchMySignatureImageBlob,
  getMySignatureProfile,
  updateMySignatureProfile,
  uploadMySignatureImage,
} from "../api/cecApi";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCec } from "../hooks/useCecRouterPath";
import {
  ComiteEticaFormActions,
  ComiteEticaLoadingState,
  ComiteEticaPageHeader,
  ComiteEticaPageNotices,
  ComiteEticaSectionCard,
  ComiteEticaStateBanner,
} from "../ui/cecUi";

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
        if (err instanceof DOMException && err.name === "AbortError") return;
        const message = err instanceof Error ? err.message : "Erro ao carregar assinatura.";
        if (/404|not found/i.test(message)) {
          setError(
            "API Comitê de Ética sem a rota de assinatura pessoal (404). Reinicie/rebuild o serviço comite-etica-conduta-api e confira a migration V003.",
          );
          return;
        }
        setError(message);
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
    return <ComiteEticaLoadingState message="Carregando sua assinatura…" />;
  }

  return (
    <div className="cec-page-stack">
      <ComiteEticaPageHeader
        nav={
          <BackLink variant="prominent" onClick={() => navigateCec("/apps/comite-etica-conduta")}>
            Voltar ao início
          </BackLink>
        }
        title="Minha assinatura"
        subtitle="Configure o nome e o traço que serão reutilizados ao assinar atas. Cada usuário acessa apenas o próprio perfil."
      />

      <ComiteEticaPageNotices
        error={error}
        success={success}
        onDismissError={() => setError(null)}
        onDismissSuccess={() => setSuccess(null)}
      />

      <ComiteEticaSectionCard title="Nome para assinatura">
        <div className="cec-field">
          <FieldLabel label="Nome exibido" htmlFor="comite-etica-conduta-my-signature-name" />
          <NativeTextControl
            id="comite-etica-conduta-my-signature-name"
            value={displayName}
            onChange={setDisplayName}
            placeholder="Seu nome completo"
          />
        </div>
        <ComiteEticaFormActions>
          <ActionButton
            variant="primary"
            disabled={savingProfile}
            onClick={() => void handleSaveProfile()}
          >
            <Save size={16} /> Salvar nome
          </ActionButton>
        </ComiteEticaFormActions>
      </ComiteEticaSectionCard>

      <ComiteEticaSectionCard title="Assinatura manuscrita" hint={helpTooltips.signaturePad}>
        {hasSignature && previewUrl ? (
          <div className="cec-signature-preview">
            <ComiteEticaStateBanner>Assinatura cadastrada</ComiteEticaStateBanner>
            <img src={previewUrl} alt="Assinatura cadastrada" className="cec-signature-img" />
          </div>
        ) : (
          <ComiteEticaStateBanner>Nenhuma assinatura cadastrada ainda.</ComiteEticaStateBanner>
        )}
        <p>Desenhe abaixo para criar ou substituir a assinatura salva.</p>
        <SignaturePad key={padKey} className="delpi-ui-signature-pad--tall" onChange={setPng} />
        <ComiteEticaFormActions>
          <ActionButton
            variant="primary"
            disabled={savingImage || !png}
            onClick={() => void handleSaveImage()}
          >
            <PenLine size={16} /> Salvar assinatura
          </ActionButton>
        </ComiteEticaFormActions>
      </ComiteEticaSectionCard>
    </div>
  );
}
