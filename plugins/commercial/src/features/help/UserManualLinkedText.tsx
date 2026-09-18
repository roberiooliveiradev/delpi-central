import type { ReactNode } from "react";

import { CommercialUserManual } from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { splitManualTextWithToolLinks } from "../../content/userManualToolLinks";

type UserManualLinkedTextProps = {
  text: string;
  basePath: string;
  className?: string;
};

/** Renderiza texto do manual com links internos para telas citadas. */
export function UserManualLinkedText({
  text,
  basePath,
  className,
}: UserManualLinkedTextProps): ReactNode {
  const parts = splitManualTextWithToolLinks(text);
  if (parts.length === 1 && parts[0]?.kind === "text") {
    return className ? <span className={className}>{text}</span> : text;
  }

  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (part.kind === "text") {
          return <span key={`t-${index}`}>{part.value}</span>;
        }
        const href = buildPluginPath(part.viewId, basePath, part.search);
        return (
          <a
            key={`l-${index}-${part.value}`}
            className={CommercialUserManual.classNames.toolLink}
            href={href}
            onClick={(event) => {
              event.preventDefault();
              navigatePluginView(part.viewId, {
                basePath,
                search: part.search,
              });
            }}
          >
            {part.value}
          </a>
        );
      })}
    </span>
  );
}
