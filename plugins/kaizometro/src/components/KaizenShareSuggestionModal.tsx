import { useEffect, useMemo, useState } from "react";
import { Check, Copy, Download, QrCode } from "lucide-react";

import { Modal, SelectField } from "./ui";
import {
  downloadKaizenSuggestionQrPng,
  kaizenSuggestionQrImageUrl,
  resolveKaizenPublicSuggestionUrl,
} from "../utils/kaizenPublicSuggestionLink";
import { unitLabel } from "../utils/labels";
import { isMultiUnitAccount, type BranchOption } from "../utils/kaizenBranchPermissions";

type Props = {
  open: boolean;
  onClose: () => void;
  /** Unidades permitidas ao usuário. */
  branchOptions: BranchOption[];
  /** Pré-seleção (ex.: filtro da listagem). */
  initialBranchCode?: string;
};

export function KaizenShareSuggestionModal({
  open,
  onClose,
  branchOptions,
  initialBranchCode,
}: Props) {
  const [branchCode, setBranchCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const preferred =
      initialBranchCode && branchOptions.some((o) => o.value === initialBranchCode)
        ? initialBranchCode
        : branchOptions.length === 1
          ? branchOptions[0].value
          : "";
    setBranchCode(preferred);
    setCopied(false);
    setExportError(null);
  }, [open, initialBranchCode, branchOptions]);

  const url = useMemo(
    () => (branchCode ? resolveKaizenPublicSuggestionUrl({ branchCode }) : ""),
    [branchCode],
  );
  const qrSrc = useMemo(
    () => (url ? kaizenSuggestionQrImageUrl(url) : ""),
    [url],
  );
  const canShare = Boolean(branchCode && url);
  const multiUnit = isMultiUnitAccount(branchOptions);

  async function copyLink() {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  async function exportPng() {
    if (!url) return;
    setExportError(null);
    setExporting(true);
    try {
      const label = unitLabel(branchCode).replace(/\s+/g, "-").toLowerCase();
      await downloadKaizenSuggestionQrPng(
        url,
        `kaizen-sugestao-${branchCode}-${label}.png`,
      );
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Falha ao exportar PNG.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <Modal open={open} title="Compartilhar formulário de sugestão" onClose={onClose}>
      <div className="kz-share-modal">
        <p className="kz-share-modal__hint">
          Qualquer pessoa com o link pode enviar uma sugestão. O registro entra
          {branchCode ? (
            <>
              {" "}
              em <strong>{unitLabel(branchCode)}</strong>
            </>
          ) : (
            " na unidade escolhida"
          )}{" "}
          com status <strong>Recebido</strong> e notifica quem tiver a permissão de alertas.
        </p>

        {multiUnit ? (
          <SelectField
            id="kz-share-branch"
            label="Unidade *"
            required
            value={branchCode}
            onChange={setBranchCode}
            options={branchOptions}
            placeholderOption="Selecione a unidade"
          />
        ) : null}

        {!branchOptions.length ? (
          <p className="kz-share-modal__error" role="alert">
            Você não tem permissão de unidade (kaizometro.branch-01 / branch-02).
          </p>
        ) : null}

        {multiUnit && branchCode ? (
          <p className="kz-share-modal__hint">
            Sugestões deste link entram em <strong>{unitLabel(branchCode)}</strong>.
          </p>
        ) : null}

        <div className="kz-share-modal__qr-panel">
          <div className="kz-share-modal__qr-badge">
            <QrCode size={14} aria-hidden="true" />
            QR code
          </div>
          <div className="kz-share-modal__qr">
            {canShare ? (
              <img
                src={qrSrc}
                alt={`QR code do formulário de sugestão — ${unitLabel(branchCode)}`}
                width={240}
                height={240}
              />
            ) : (
              <p className="kz-share-modal__hint">Selecione a unidade para gerar o QR.</p>
            )}
          </div>
          <button
            type="button"
            className="kz-primary-btn kz-share-modal__export"
            onClick={() => void exportPng()}
            disabled={!canShare || exporting}
          >
            <Download size={16} aria-hidden="true" />
            {exporting ? "Gerando PNG…" : "Exportar PNG"}
          </button>
          {exportError ? (
            <p className="kz-share-modal__error" role="alert">
              {exportError}
            </p>
          ) : null}
        </div>

        <div className="kz-share-modal__link-block">
          <label className="kz-share-modal__link-label" htmlFor="kz-share-url">
            Link de acesso
          </label>
          <div className="kz-share-modal__link-row">
            <input
              id="kz-share-url"
              readOnly
              value={url}
              placeholder="Selecione a unidade"
              onFocus={(e) => e.currentTarget.select()}
            />
            <button
              type="button"
              className="kz-ghost-btn kz-share-modal__copy"
              onClick={() => void copyLink()}
              disabled={!canShare}
            >
              {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
              {copied ? "Copiado" : "Copiar"}
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
