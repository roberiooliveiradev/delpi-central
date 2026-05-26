import { useCallback, useContext, useEffect, useRef, useState } from "react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import type { ConsentItem, PrivacyInfo } from "../data/coreApi";
import { FileText, ShieldCheck, ChevronRight } from "lucide-react";
import "./ConsentModal.css";

const REQUIRED_PURPOSE = "data_processing";

const PURPOSE_LABELS: Record<string, { label: string; description: string }> = {
  data_processing: {
    label: "Tratamento de dados pessoais",
    description:
      "Necessário para o funcionamento do sistema. Seus dados serão tratados conforme a política de privacidade acima.",
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
  const policyRef = useRef<HTMLDivElement>(null);

  const [step, setStep] = useState<"policy" | "consents">("policy");
  const [policyRead, setPolicyRead] = useState(false);
  const [privacy, setPrivacy] = useState<PrivacyInfo | null>(null);

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
        const [raw, privacyData] = await Promise.all([
          api.getConsentsRaw(),
          api.getPrivacyInfo(),
        ]);

        if (cancelled) return;

        setPrivacy(privacyData);
        setConsents(raw.items);
        setAvailablePurposes(
          raw.availablePurposes.length > 0
            ? raw.availablePurposes
            : Object.keys(PURPOSE_LABELS),
        );

        const alreadyGranted = new Set(
          raw.items.filter((c) => c.granted).map((c) => c.purpose),
        );
        alreadyGranted.add(REQUIRED_PURPOSE);
        setSelected(alreadyGranted);
      } catch {
        setError("Não foi possível carregar os dados.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => { cancelled = true; };
  }, [getApi]);

  const handlePolicyScroll = () => {
    const el = policyRef.current;
    if (!el || policyRead) return;
    const threshold = el.scrollHeight - el.clientHeight - 40;
    if (el.scrollTop >= threshold) {
      setPolicyRead(true);
    }
  };

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

  const dpoName = privacy?.dpo?.name || "Encarregado de Proteção de Dados";
  const dpoEmail = privacy?.dpo?.email || "dpo@empresa.com.br";
  const canAccept = selected.has(REQUIRED_PURPOSE);

  return (
    <div className="consent-overlay">
      <div className="consent-modal consent-modal--wide">

        {/* ====== STEP INDICATOR ====== */}
        <div className="consent-steps">
          <button
            type="button"
            className={`consent-step ${step === "policy" ? "consent-step--active" : "consent-step--done"}`}
            onClick={() => setStep("policy")}
          >
            <FileText size={16} />
            <span>1. Política de Privacidade</span>
          </button>
          <ChevronRight size={16} className="consent-steps__sep" />
          <button
            type="button"
            className={`consent-step ${step === "consents" ? "consent-step--active" : ""}`}
            onClick={() => policyRead && setStep("consents")}
            disabled={!policyRead}
          >
            <ShieldCheck size={16} />
            <span>2. Consentimentos</span>
          </button>
        </div>

        {/* ====== STEP 1: POLICY ====== */}
        {step === "policy" && (
          <>
            <div className="consent-header">
              <h2>Política de Privacidade</h2>
              <p>Leia atentamente antes de prosseguir. Role até o final para continuar.</p>
            </div>

            <div
              className="consent-policy"
              ref={policyRef}
              onScroll={handlePolicyScroll}
            >
              <section>
                <h3>1. Controlador dos Dados e Encarregado (DPO)</h3>
                <p>
                  O controlador dos dados pessoais tratados nesta plataforma é a{" "}
                  <strong>DELPI Energia &amp; Conectividade</strong>.
                </p>
                <p>
                  O Encarregado de Proteção de Dados (DPO), <strong>{dpoName}</strong>,
                  pode ser contatado pelo e-mail <strong>{dpoEmail}</strong> para
                  esclarecimentos sobre o tratamento de dados pessoais.
                </p>
              </section>

              <section>
                <h3>2. Dados Coletados e Finalidades</h3>
                <table className="consent-table">
                  <thead>
                    <tr><th>Categoria</th><th>Finalidade</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>Nome, e-mail corporativo</td><td>Identificação e autenticação</td></tr>
                    <tr><td>Cargo, departamento, filial</td><td>Controle de permissões (RBAC)</td></tr>
                    <tr><td>Data de nascimento</td><td>Notificações de aniversário</td></tr>
                    <tr><td>Logs de acesso</td><td>Auditoria de segurança</td></tr>
                    <tr><td>Preferências e consentimentos</td><td>Conformidade legal</td></tr>
                    <tr><td>Interações com IA</td><td>Melhoria do assistente</td></tr>
                  </tbody>
                </table>
              </section>

              <section>
                <h3>3. Base Legal (LGPD — Lei 13.709/2018)</h3>
                <ul>
                  <li><strong>Execução de contrato (Art. 7º, V)</strong> — autenticação e funcionalidades da plataforma.</li>
                  <li><strong>Legítimo interesse (Art. 7º, IX)</strong> — auditoria, prevenção a fraudes e melhoria dos serviços.</li>
                  <li><strong>Consentimento (Art. 7º, I)</strong> — funcionalidades opcionais, revogável a qualquer momento.</li>
                  <li><strong>Obrigação legal (Art. 7º, II)</strong> — retenção exigida por legislação.</li>
                </ul>
              </section>

              <section>
                <h3>4. Compartilhamento de Dados</h3>
                <p>Seus dados podem ser compartilhados com prestadores de infraestrutura (operadores sob contrato),
                  autoridades competentes (ordem judicial) e integrações internas autorizadas.
                  Não comercializamos dados pessoais.</p>
              </section>

              <section>
                <h3>5. Direitos do Titular (Art. 18)</h3>
                <ul>
                  <li>Confirmação e acesso aos dados tratados</li>
                  <li>Correção de dados incompletos ou inexatos</li>
                  <li>Anonimização, bloqueio ou eliminação de dados</li>
                  <li>Portabilidade (exportação em formato estruturado)</li>
                  <li>Revogação do consentimento a qualquer momento</li>
                </ul>
              </section>

              <section>
                <h3>6. Retenção de Dados</h3>
                <table className="consent-table">
                  <thead>
                    <tr><th>Tipo</th><th>Prazo</th></tr>
                  </thead>
                  <tbody>
                    <tr><td>Conta ativa</td><td>Enquanto ativa</td></tr>
                    <tr><td>Logs de auditoria</td><td>5 anos</td></tr>
                    <tr><td>Chat com IA</td><td>12 meses</td></tr>
                    <tr><td>Após desligamento</td><td>Anonimizado em 90 dias</td></tr>
                  </tbody>
                </table>
              </section>

              <section>
                <h3>7. Segurança</h3>
                <p>Utilizamos criptografia TLS/HTTPS, RBAC, autenticação SSO (OpenID Connect),
                  auditoria de acessos e política automatizada de retenção.</p>
              </section>

              <section>
                <h3>8. Contato</h3>
                <p>
                  <strong>DPO:</strong> {dpoName} — {dpoEmail}<br />
                  <strong>Controlador:</strong> DELPI Energia &amp; Conectividade
                </p>
                <p>Caso não obtenha resposta satisfatória, apresente reclamação à ANPD.</p>
              </section>
            </div>

            <div className="consent-footer">
              <span className="consent-hint">
                {policyRead
                  ? "Você leu a política. Prossiga para os consentimentos."
                  : "Role até o final do documento para continuar."}
              </span>
              <button
                className="btn-primary consent-btn"
                disabled={!policyRead}
                onClick={() => setStep("consents")}
              >
                Prosseguir
                <ChevronRight size={16} />
              </button>
            </div>
          </>
        )}

        {/* ====== STEP 2: CONSENTS ====== */}
        {step === "consents" && (
          <>
            <div className="consent-header">
              <h2>Consentimentos</h2>
              <p>
                Marque os consentimentos que deseja conceder.
                O tratamento de dados pessoais é obrigatório para utilizar a plataforma.
              </p>
            </div>

            <div className="consent-body">
              {availablePurposes.map((purpose) => {
                const info = PURPOSE_LABELS[purpose] ?? { label: purpose, description: "" };
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
              <span className="consent-hint">
                Você pode alterar suas preferências a qualquer momento em <strong>Privacidade de Dados</strong>.
              </span>
              <button
                className="btn-primary consent-btn"
                disabled={!canAccept || saving}
                onClick={() => void handleAccept()}
              >
                {saving ? "Salvando..." : "Aceitar e continuar"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
