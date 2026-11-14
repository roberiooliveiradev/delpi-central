import { RichTextEditor } from "@delpi/plugin-ui/index";
import { useMemo } from "react";

import { CommercialSegmentToggle } from "../../app/commercialUi";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import { buildInviteHtml, buildMessengerText } from "./inviteMessage";

export type InvitePreviewMode = "email" | "messenger";

type InvitePreviewProps = {
  idPrefix: string;
  mode: InvitePreviewMode;
  onModeChange: (mode: InvitePreviewMode) => void;
  subject: string;
  body: string;
  /** false para URLs fictícias (prévia de configuração): nunca vira link clicável. */
  linkify?: boolean;
};

const noop = () => undefined;

/**
 * Prévia somente leitura em dois modos (Correio eletrônico | Mensageiro).
 * O HTML do modo e-mail é sempre gerado por `buildInviteHtml` (escape total) —
 * `RichTextEditor mode="preview"` não sanitiza o `value`.
 */
export function InvitePreview({
  idPrefix,
  mode,
  onModeChange,
  subject,
  body,
  linkify = true,
}: InvitePreviewProps) {
  const copy = SATISFACTION_CONTENT.message;
  const html = useMemo(() => buildInviteHtml(body, { linkify }), [body, linkify]);
  const messenger = useMemo(() => buildMessengerText(body), [body]);

  return (
    <div className="cm-satisfaction-stack">
      <CommercialSegmentToggle
        ariaLabel={copy.previewAriaLabel}
        idPrefix={`${idPrefix}-preview-mode`}
        value={mode}
        widthMode="content"
        onChange={(value) => {
          if (value === "email" || value === "messenger") onModeChange(value);
        }}
        options={[
          { value: "email", label: copy.previewEmail },
          { value: "messenger", label: copy.previewMessenger },
        ]}
      />
      {mode === "email" ? (
        <div role="group" aria-label={copy.previewEmailAriaLabel}>
          <p>
            <strong>{copy.previewSubjectLabel}:</strong> {subject}
          </p>
          <RichTextEditor
            value={html}
            onChange={noop}
            mode="preview"
            ariaLabel={copy.previewEmailAriaLabel}
            portalScopeClassName="dashboard-commercial"
            minHeight={120}
          />
        </div>
      ) : (
        <div role="group" aria-label={copy.previewMessengerAriaLabel}>
          <pre className="cm-satisfaction-messenger-preview">
            {messenger}
          </pre>
        </div>
      )}
    </div>
  );
}
