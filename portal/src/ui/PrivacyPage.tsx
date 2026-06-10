import { useContext, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  Download,
  Eye,
  ToggleLeft,
  ToggleRight,
  Mail,
  FileText,
  CheckCircle,
  Loader2,
  AlertTriangle,
} from "lucide-react";

import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import {
  CoreApi,
  type ConsentItem,
  type PrivacyInfo,
} from "../data/coreApi";

import "./PrivacyPage.css";

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.22, delay: 0.04 * i },
  }),
};

export const PrivacyPage = () => {
  const { getAccessToken } = useContext(AuthContext);

  const apiRef = useRef<CoreApi | null>(null);
  if (!apiRef.current) {
    apiRef.current = new CoreApi(new ApiClient("", getAccessToken));
  }

  const [privacy, setPrivacy] = useState<PrivacyInfo | null>(null);
  const [consents, setConsents] = useState<ConsentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportDone, setExportDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const api = apiRef.current!;

    const load = async () => {
      const errors: string[] = [];

      try {
        const privacyData = await api.getPrivacyInfo();
        if (!cancelled) setPrivacy(privacyData);
      } catch {
        errors.push("informações de privacidade");
      }

      try {
        const consentData = await api.getConsents();
        if (!cancelled) setConsents(consentData);
      } catch {
        errors.push("consentimentos");
      }

      if (!cancelled) {
        if (errors.length > 0) {
          setError(`Erro ao carregar: ${errors.join(", ")}. Verifique se o servidor foi atualizado.`);
        }
        setLoading(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, []);

  const handleToggle = async (purpose: string, currentlyGranted: boolean) => {
    const api = apiRef.current!;
    setToggling(purpose);
    try {
      if (currentlyGranted) {
        await api.revokeConsent(purpose);
      } else {
        await api.grantConsent(purpose);
      }
      const updated = await api.getConsents();
      setConsents(updated);
    } catch {
      setError("Erro ao atualizar consentimento.");
    } finally {
      setToggling(null);
    }
  };

  const handleExport = async () => {
    const api = apiRef.current!;
    setExporting(true);
    setExportDone(false);
    try {
      const data = await api.getDataExport();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `meus-dados-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExportDone(true);
    } catch {
      setError("Erro ao exportar dados.");
    } finally {
      setExporting(false);
    }
  };

  const getConsentForPurpose = (key: string) =>
    consents.find((c) => c.purpose === key);

  if (loading) {
    return (
      <div className="privacy-page privacy-page--loading">
        <Loader2 className="spin" size={28} />
        <span>Carregando...</span>
      </div>
    );
  }

  return (
    <div className="privacy-page" data-tour="privacy-page">
      <motion.div
        className="privacy-page__header"
        initial="hidden"
        animate="show"
        variants={fadeUp}
      >
        <Shield size={28} />
        <div>
          <h1>Privacidade e Dados</h1>
          <p>Gerencie seus consentimentos, exporte seus dados e conheça seus direitos.</p>
        </div>
      </motion.div>

      {error && (
        <motion.div
          className="privacy-page__alert privacy-page__alert--error"
          initial="hidden"
          animate="show"
          variants={fadeUp}
        >
          <AlertTriangle size={16} />
          <span>{error}</span>
          <button onClick={() => setError(null)}>&times;</button>
        </motion.div>
      )}

      <div className="privacy-page__grid">
        {/* CONSENTS */}
        <motion.section
          className="privacy-page__card"
          data-tour="privacy-consent"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={1}
        >
          <div className="privacy-page__card-header">
            <Eye size={20} />
            <h2>Consentimentos</h2>
          </div>
          <p className="privacy-page__card-desc">
            Controle para quais finalidades seus dados podem ser utilizados.
          </p>

          <div className="privacy-page__consent-list">
            {privacy?.consent_purposes.map(({ key, label }) => {
              const consent = getConsentForPurpose(key);
              const granted = consent?.granted ?? false;
              const isToggling = toggling === key;

              return (
                <div key={key} className="privacy-page__consent-item">
                  <div className="privacy-page__consent-info">
                    <span className="privacy-page__consent-label">{label}</span>
                    <span className="privacy-page__consent-status">
                      {granted ? "Ativo" : "Inativo"}
                    </span>
                  </div>
                  <button
                    className={`privacy-page__toggle ${granted ? "privacy-page__toggle--on" : ""}`}
                    onClick={() => handleToggle(key, granted)}
                    disabled={isToggling}
                    aria-label={`${granted ? "Revogar" : "Conceder"} ${label}`}
                  >
                    {isToggling ? (
                      <Loader2 className="spin" size={18} />
                    ) : granted ? (
                      <ToggleRight size={28} />
                    ) : (
                      <ToggleLeft size={28} />
                    )}
                  </button>
                </div>
              );
            })}

            {(!privacy?.consent_purposes || privacy.consent_purposes.length === 0) && (
              <p className="privacy-page__empty">Nenhuma finalidade de consentimento configurada.</p>
            )}
          </div>
        </motion.section>

        {/* DATA EXPORT */}
        <motion.section
          className="privacy-page__card"
          data-tour="privacy-export"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={2}
        >
          <div className="privacy-page__card-header">
            <Download size={20} />
            <h2>Exportar meus dados</h2>
          </div>
          <p className="privacy-page__card-desc">
            Baixe uma cópia de todos os seus dados pessoais armazenados no sistema,
            conforme seu direito de portabilidade (LGPD Art. 18, V).
          </p>

          <button
            className="privacy-page__btn privacy-page__btn--primary"
            onClick={handleExport}
            disabled={exporting}
          >
            {exporting ? (
              <>
                <Loader2 className="spin" size={16} />
                Exportando...
              </>
            ) : exportDone ? (
              <>
                <CheckCircle size={16} />
                Download concluído
              </>
            ) : (
              <>
                <Download size={16} />
                Baixar meus dados (JSON)
              </>
            )}
          </button>
        </motion.section>

        {/* DPO & POLICY */}
        <motion.section
          className="privacy-page__card"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={3}
        >
          <div className="privacy-page__card-header">
            <Mail size={20} />
            <h2>Encarregado de Dados (DPO)</h2>
          </div>
          <p className="privacy-page__card-desc">
            Para exercer seus direitos ou esclarecer dúvidas sobre o tratamento
            dos seus dados, entre em contato com o Encarregado de Proteção de Dados.
          </p>

          {privacy?.dpo && (
            <div className="privacy-page__dpo">
              <div className="privacy-page__dpo-item">
                <span className="privacy-page__dpo-label">Nome</span>
                <span>{privacy.dpo.name}</span>
              </div>
              <div className="privacy-page__dpo-item">
                <span className="privacy-page__dpo-label">Email</span>
                <a href={`mailto:${privacy.dpo.email}`}>{privacy.dpo.email}</a>
              </div>
            </div>
          )}

          {privacy?.privacy_policy_url && (
            <a
              href={privacy.privacy_policy_url}
              target="_blank"
              rel="noopener noreferrer"
              className="privacy-page__btn privacy-page__btn--outline"
            >
              <FileText size={16} />
              Política de Privacidade
            </a>
          )}
        </motion.section>

        {/* RIGHTS */}
        <motion.section
          className="privacy-page__card"
          initial="hidden"
          animate="show"
          variants={fadeUp}
          custom={4}
        >
          <div className="privacy-page__card-header">
            <Shield size={20} />
            <h2>Seus direitos (LGPD Art. 18)</h2>
          </div>
          <ul className="privacy-page__rights">
            {privacy?.data_subject_rights.map((right, i) => (
              <li key={i}>
                <CheckCircle size={14} />
                <span>{right}</span>
              </li>
            ))}
          </ul>
        </motion.section>

        {/* RETENTION */}
        {privacy?.retention_periods && Object.keys(privacy.retention_periods).length > 0 && (
          <motion.section
            className="privacy-page__card privacy-page__card--wide"
            initial="hidden"
            animate="show"
            variants={fadeUp}
            custom={5}
          >
            <div className="privacy-page__card-header">
              <FileText size={20} />
              <h2>Prazos de retenção</h2>
            </div>
            <div className="privacy-page__retention">
              {Object.entries(privacy.retention_periods).map(([key, value]) => (
                <div key={key} className="privacy-page__retention-item">
                  <span className="privacy-page__retention-label">{key}</span>
                  <span className="privacy-page__retention-value">{value}</span>
                </div>
              ))}
            </div>
          </motion.section>
        )}
      </div>
    </div>
  );
};
