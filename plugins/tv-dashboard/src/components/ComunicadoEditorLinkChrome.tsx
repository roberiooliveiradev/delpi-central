import { Link2 } from "lucide-react";

import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  blockId: string;
  href?: string;
  hint?: string;
};

export function ComunicadoEditorLinkChrome({ blockId, href, hint }: Props) {
  const { updateBlockLink } = useComunicadoEditor();

  return (
    <div className="td-composer__text-inline-chrome" onPointerDown={(event) => event.stopPropagation()}>
      {hint ? <span className="td-composer__text-inline-hint">{hint}</span> : null}
      <label className="td-composer__text-link-field">
        <Link2 size={12} aria-hidden="true" />
        <input
          type="url"
          placeholder="Link (URL)"
          value={href ?? ""}
          onChange={(event) => updateBlockLink(blockId, event.target.value)}
        />
      </label>
    </div>
  );
}
