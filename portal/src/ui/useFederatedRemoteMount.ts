import { useEffect, useRef, useState } from "react";

import {
  createFederatedMountSession,
  type FederatedHostProps,
} from "./federatedRemoteHost";

export function useFederatedRemoteMount(options: {
  enabled: boolean;
  entryUrl?: string;
  exposedModule?: string;
  props: FederatedHostProps;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const sessionRef = useRef(createFederatedMountSession());
  const propsRef = useRef(options.props);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  propsRef.current = options.props;

  useEffect(() => {
    const session = sessionRef.current;
    const hostEl = hostRef.current;
    let cancelled = false;

    if (!options.enabled || !options.entryUrl || !hostEl) {
      session.unmount();
      setReady(false);
      setError(null);
      return () => {
        session.unmount();
      };
    }

    setError(null);
    setReady(false);

    void session
      .mount(hostEl, options.entryUrl, propsRef.current, options.exposedModule)
      .then(() => {
        if (!cancelled) setReady(true);
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setReady(true);
        setError(cause instanceof Error ? cause.message : String(cause));
      });

    return () => {
      cancelled = true;
      session.unmount();
    };
  }, [options.enabled, options.entryUrl, options.exposedModule, options.props.getAccessToken]);

  useEffect(() => {
    if (!options.enabled) return;
    if (!sessionRef.current.isMounted()) return;
    sessionRef.current.updateRoute(options.props);
  }, [
    options.enabled,
    options.props.pathname,
    options.props.search,
    options.props.basePath,
    options.props.alternateEntry,
    options.props.appRoutes,
    options.props.routeLabel,
    options.props.permissions,
    options.props.isSuperadmin,
    options.props.getAccessToken,
  ]);

  return { hostRef, error, ready };
}
