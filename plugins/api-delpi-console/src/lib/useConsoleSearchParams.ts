import { useCallback, useEffect, useState } from "react";

function readSearchParams(): URLSearchParams {
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.search);
}

export function useConsoleSearchParams() {
  const [params, setParams] = useState(readSearchParams);

  const refresh = useCallback(() => {
    setParams(readSearchParams());
  }, []);

  useEffect(() => {
    const onPopState = () => refresh();
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, [refresh]);

  return params;
}
