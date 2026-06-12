import { useEffect, useState } from "react";

import { fetchWorkspaceFileIngestPolicy } from "../../data/api/chatApi";
import type { WorkspaceFileIngestPolicyFamily } from "../../data/api/chatTypes";
import type { WorkspaceFileDropzoneContentVariant } from "../../content/workspaceFileIngestContent";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

const CONTENT_VARIANT_TO_FAMILY: Record<
  WorkspaceFileDropzoneContentVariant,
  WorkspaceFileIngestPolicyFamily
> = {
  session: "session_attachment",
  workspace: "global_knowledge",
  agent: "agent_source",
  project: "project_source",
  context: "context_paste",
};

export function workspaceFileIngestFamilyForContentVariant(
  variant: WorkspaceFileDropzoneContentVariant,
): WorkspaceFileIngestPolicyFamily {
  return CONTENT_VARIANT_TO_FAMILY[variant];
}

export function useWorkspaceFileIngestPolicy(
  family: WorkspaceFileIngestPolicyFamily | undefined,
  options: { getAccessToken?: TokenProvider } = {},
) {
  const [accept, setAccept] = useState<string | undefined>();
  const [maxSizeBytes, setMaxSizeBytes] = useState<number | undefined>();
  const [extensions, setExtensions] = useState<string[] | undefined>();

  useEffect(() => {
    if (!family) {
      return;
    }

    let active = true;

    void fetchWorkspaceFileIngestPolicy(family, { getAccessToken: options.getAccessToken })
      .then((policy) => {
        if (!active) {
          return;
        }

        setAccept(policy.accept);
        setMaxSizeBytes(policy.maxSizeBytes);
        setExtensions(policy.extensions);
      })
      .catch(() => {
        if (!active) {
          return;
        }

        setAccept(undefined);
        setMaxSizeBytes(undefined);
        setExtensions(undefined);
      });

    return () => {
      active = false;
    };
  }, [family, options.getAccessToken]);

  return { accept, maxSizeBytes, extensions };
}
