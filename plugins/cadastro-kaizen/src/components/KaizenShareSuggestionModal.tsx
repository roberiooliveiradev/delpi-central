import { useMemo, useState } from "react";
import { Check, Copy } from "lucide-react";

import { Modal } from "./ui";
import {
  kaizenSuggestionQrImageUrl,
  resolveKaizenPublicSuggestionUrl,
} from "../utils/kaizenPublicSuggestionLink";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function KaizenShareSuggestionModal({ open, onClose }: Props) {
  const url = useMemo(() => resolveKaizenPublicSuggestionUrl(), []);
  const qrSrc = useMemo(() => kaizenSuggestionQrImageUrl(url), [url]);
  const [copied, setCopied] = useState(false);

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Modal open={open} title="Compartilhar formulário de sugestão" onClose={onClose}>
      <div className="kz-share-modal">
        <p className="kz-share-modal__hint">
          Qualquer pessoa com o link pode enviar uma sugestão. O registro entra com status{" "}
          <strong>Recebido</strong> e notifica quem tiver a permissão de alertas.
        </p>
        <div className="kz-share-modal__qr">
          <img src={qrSrc} alt="QR code do formulário de sugestão Kaizen" width={240} height={240} />
        </div>
        <label className="kz-share-modal__link-label" htmlFor="kz-share-url">
          Link de acesso
        </label>
        <div className="kz-share-modal__link-row">
          <input id="kz-share-url" readOnly value={url} onFocus={(e) => e.currentTarget.select()} />
          <button
            type="button"
            className="kz-ghost-btn kz-share-modal__copy"
            onClick={() => void copyLink()}
          >
            {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
            {copied ? "Copiado" : "Copiar"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
