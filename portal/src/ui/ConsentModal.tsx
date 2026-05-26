import { useCallback, useContext, useEffect, useRef, useState } from "react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import type { ConsentItem } from "../data/coreApi";
import "./ConsentModal.css";

const REQUIRED_PURPOSE = "data_processing";

const PURPOSE_LABELS: Record<string, { label: string; description: string; required?: boolean }> = {
  data_processing: {
    label: "Tratamento de dados pessoais",
    description:
      "Necessário para o funcionamento do sistema. Seus dados serão tratados conforme nossa política de privacidade.",
    required: true,
  },
  analytics: {
    label: "Métricas de uso",
    description: "Coleta de dados anônimos sobre a utilização do sistema para melhoria contínua do produto.",
  },
  ai_context: {
    label: "Contexto para IA",
    description: "Permite que o assistente de IA utilize informações do seu perfil para respostas mais relevantes.",
  },
  usage_tracking: {
    label: "Rastreamento de uso",
    description: "Registra quais módulos e funcionalidades você acessa para personalizar sua experiência.",
  },
  birthday_notifications: {
    label: "Notificações de aniversário",
    description: "Permite que o sistema envie notificações de aniversário para seus colegas.",
  },
};

type ConsentModalProps = {
  onAccepted: () => void;
};

export function ConsentModal({ onAccepted }: ConsentModalProps) {
  const { getAccessToken } = useContext(AuthContext);

  const apiRef = useRef<CoreApi | null>(null);
  const [consents, setConsents] = useState<ConsentItem[]>([]);
  const [availablePurposes, setAvailablePurposes] = useState<string[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set([REQUIRED_PURPOSE]));
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getApi = useCallback(() => {
    if (!apiRef.current) {
      const client = new ApiClient("", getAccessToken);
      apiRef.current = new CoreApi(client);
    }
    return apiRef.current;
  }, [getAccessToken]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const api = getApi();
        const data = await api.client.get<{
          items?: ConsentItem[];
          availablePurposes?: string[];
        }>("/core-api/me/consents");

        if (cancelled) return;

        const items: ConsentItem[] = Array.isArray(data?.items) ? data.items : [];
        const purposes: string[] = Array.isArray(data?.availablePurposes)
          ? data.availablePurposes
          : Object.keys(PURPOSE_LABELS);

        setConsents(items);
        setAvailablePurposes(purposes);

        const alreadyGranted = new Set(
          items.filter((c) => c.granted).map((c) => c.purpose),
        );
        alreadyGranted.add(REQUIRED_PURPOSE);
        setSelected(alreadyGranted);
      } catch {
        setError("Não foi possível carregar os consentimentos.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => { cancelled = true; };
  }, [getApi]);

  const toggle = (purpose: string) => {
    if (purpose === REQUIRED_PURPOSE) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(purpose)) next.delete(purpose);
      else next.add(purpose);
      return next;
    });
  };

  const handleAccept = async () => {
    setSaving(true);
    setError(null);

    try {
      const api = getApi();

      for (const purpose of selected) {
        const existing = consents.find((c) => c.purpose === purpose);
        if (!existing?.granted) {
          await api.grantConsent(purpose);
        }
      }

      for (const c of consents) {
        if (c.granted && !selected.has(c.purpose)) {
          await api.revokeConsent(c.purpose);
        }
      }

      onAccepted();
    } catch {
      setError("Erro ao salvar os consentimentos. Tente novamente.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="consent-overlay">
        <div className="consent-modal">
          <div className="consent-loading">Carregando...</div>
        </div>
      </div>
    );
  }

  const canAccept = selected.has(REQUIRED_PURPOSE);

  return (
    <div className="consent-overlay">
      <div className="consent-modal">
        <div className="consent-header">
          <h2>Política de Privacidade e Consentimentos</h2>
          <p>
            Para utilizar a plataforma, é necessário aceitar o tratamento de dados pessoais
            conforme a <a href="/privacy-policy" target="_blank" rel="noopener">Política de Privacidade</a> (LGPD — Lei 13.709/2018).
          </p>
        </div>

        <div className="consent-body">
          {availablePurposes.map((purpose) => {
            const info = PURPOSE_LABELS[purpose] ?? {
              label: purpose,
              description: "",
            };
            const isRequired = purpose === REQUIRED_PURPOSE;
            const checked = selected.has(purpose);

            return (
              <label key={purpose} className={`consent-item ${isRequired ? "consent-item--required" : ""}`}>
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={isRequired}
                  onChange={() => toggle(purpose)}
                />
                <div className="consent-item__text">
                  <strong>
                    {info.label}
                    {isRequired && <span className="consent-badge">Obrigatório</span>}
                  </strong>
                  <span>{info.description}</span>
                </div>
              </label>
            );
          })}
        </div>

        {error && <div className="consent-error">{error}</div>}

        <div className="consent-footer">
          <button
            className="btn-primary consent-btn"
            disabled={!canAccept || saving}
            onClick={() => void handleAccept()}
          >
            {saving ? "Salvando..." : "Aceitar e continuar"}
          </button>
        </div>
      </div>
    </div>
  );
}
