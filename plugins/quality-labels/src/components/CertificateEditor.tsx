import { useEffect, useState } from "react";
import { FileText, Loader2, Save } from "lucide-react";

import {
  fetchCertificatePdfBlob,
  getCertificate,
  saveCertificate,
} from "../api/qualityLabelsApi";
import type { Certificate, CertificateFormState, QualityLabel } from "../types/qualityLabels";
import {
  certificateToForm,
  formToSavePayload,
} from "../utils/certificateFormUtils";
import { CertificateFormFields } from "./CertificateFormFields";

type Props = {
  label: QualityLabel;
  onSaved?: (message: string) => void;
  onError?: (message: string) => void;
};

export function CertificateEditor({ label, onSaved, onError }: Props) {
  const [certificate, setCertificate] = useState<Certificate | null>(null);
  const [form, setForm] = useState<CertificateFormState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<null | "draft" | "issue">(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getCertificate(label.id, controller.signal)
      .then((cert) => {
        setCertificate(cert);
        setForm(certificateToForm(cert));
      })
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          const message =
            err instanceof Error ? err.message : "Erro ao carregar o certificado.";
          setError(message);
          onError?.(message);
        }
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [label.id, onError]);

  async function handleSave(issue: boolean) {
    if (!form) return;
    setSaving(issue ? "issue" : "draft");
    setError(null);
    try {
      const cert = await saveCertificate(label.id, formToSavePayload(form, issue));
      setCertificate(cert);
      setForm(certificateToForm(cert));
      if (issue) {
        await openPdf();
        onSaved?.("Certificado emitido com sucesso. Evento registrado na auditoria.");
      } else {
        onSaved?.("Certificado salvo como rascunho. Evento registrado na auditoria.");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao salvar o certificado.";
      setError(message);
      onError?.(message);
    } finally {
      setSaving(null);
    }
  }

  async function openPdf() {
    try {
      const blob = await fetchCertificatePdfBlob(label.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao abrir o PDF.";
      setError(message);
      onError?.(message);
    }
  }

  if (loading || !form) {
    return (
      <div className="ql-cert-panel ql-state">
        <p>
          <Loader2 className="ql-icon ql-spin" /> Carregando certificado...
        </p>
      </div>
    );
  }

  return (
    <div className="ql-cert-panel">
      <div className="ql-cert-panel__head">
        <div>
          <h3 className="ql-cert-panel__title">Certificado de Qualidade</h3>
          <p className="ql-cert-panel__meta">
            OP {label.productionOrder} · {label.productCode}
            {certificate?.docRef ? ` · ${certificate.docRef}` : ""}
          </p>
        </div>
        {certificate?.status === "issued" ? (
          <span className="ql-badge ql-badge--on">Emitido</span>
        ) : (
          <span className="ql-badge">Rascunho</span>
        )}
      </div>

      <p className="ql-info-note ql-info-note--compact">
        Alterações no certificado são registradas na aba Auditoria.
      </p>

      {error && (
        <div className="ql-state ql-state--error">
          <p>{error}</p>
        </div>
      )}

      <CertificateFormFields
        form={form}
        onChange={(partial) => setForm((prev) => (prev ? { ...prev, ...partial } : prev))}
        productionOrder={label.productionOrder}
        productCode={label.productCode}
        docRef={certificate?.docRef ?? undefined}
        disabled={saving !== null}
      />

      <div className="ql-cert-panel__actions">
        {certificate?.hasPdf && (
          <button
            type="button"
            className="ql-btn ql-btn--ghost"
            onClick={() => void openPdf()}
            disabled={saving !== null}
          >
            <FileText className="ql-icon" /> Ver PDF
          </button>
        )}
        <button
          type="button"
          className="ql-btn ql-btn--ghost"
          onClick={() => void handleSave(false)}
          disabled={saving !== null}
        >
          {saving === "draft" ? (
            <Loader2 className="ql-icon ql-spin" />
          ) : (
            <Save className="ql-icon" />
          )}
          Salvar rascunho
        </button>
        <button
          type="button"
          className="ql-btn ql-btn--primary"
          onClick={() => void handleSave(true)}
          disabled={saving !== null}
        >
          {saving === "issue" ? (
            <Loader2 className="ql-icon ql-spin" />
          ) : (
            <FileText className="ql-icon" />
          )}
          Emitir e gerar PDF
        </button>
      </div>
    </div>
  );
}
