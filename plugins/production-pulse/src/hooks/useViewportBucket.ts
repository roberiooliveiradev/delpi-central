import { useEffect, useState } from "react";

import { resolveViewportBucket, type ViewportBucket } from "../utils/deviceDisplay";

export function useViewportBucket(): ViewportBucket {
  const [bucket, setBucket] = useState<ViewportBucket>(() =>
    typeof window !== "undefined" ? resolveViewportBucket(window.innerWidth) : "desktop",
  );

  useEffect(() => {
    const onResize = () => setBucket(resolveViewportBucket(window.innerWidth));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return bucket;
}
