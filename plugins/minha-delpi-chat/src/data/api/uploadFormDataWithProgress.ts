export type UploadProgressCallback = (percent: number) => void;

const UPLOAD_PHASE_MAX = 88;
const PROCESSING_START = 90;

function mapLoadedToPercent(loaded: number, total: number): number {
  if (total <= 0) {
    return 0;
  }

  return Math.max(0, Math.min(UPLOAD_PHASE_MAX, Math.round((loaded / total) * UPLOAD_PHASE_MAX)));
}

export async function uploadFormDataWithProgress<T>(
  url: string,
  formData: FormData,
  options: {
    method?: string;
    headers?: HeadersInit;
    onUploadProgress?: UploadProgressCallback;
    parseResponse: (response: Response) => Promise<T>;
  },
): Promise<T> {
  const method = options.method ?? "POST";

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url);

    const headers = options.headers;

    if (headers) {
      if (headers instanceof Headers) {
        headers.forEach((value, key) => {
          if (key.toLowerCase() !== "content-type") {
            xhr.setRequestHeader(key, value);
          }
        });
      } else if (Array.isArray(headers)) {
        for (const [key, value] of headers) {
          if (key.toLowerCase() !== "content-type") {
            xhr.setRequestHeader(key, value);
          }
        }
      } else {
        for (const [key, value] of Object.entries(headers)) {
          if (key.toLowerCase() !== "content-type" && value) {
            xhr.setRequestHeader(key, value);
          }
        }
      }
    }

    xhr.upload.onprogress = (event) => {
      if (!options.onUploadProgress || !event.lengthComputable) {
        return;
      }

      options.onUploadProgress(mapLoadedToPercent(event.loaded, event.total));
    };

    xhr.upload.onload = () => {
      options.onUploadProgress?.(PROCESSING_START);
    };

    xhr.onload = () => {
      const response = new Response(xhr.responseText, {
        status: xhr.status,
        statusText: xhr.statusText,
      });

      void options
        .parseResponse(response)
        .then((result) => {
          options.onUploadProgress?.(100);
          resolve(result);
        })
        .catch(reject);
    };

    xhr.onerror = () => {
      reject(new Error("Falha na conexão ao enviar o arquivo."));
    };

    xhr.onabort = () => {
      reject(new DOMException("The operation was aborted.", "AbortError"));
    };

    options.onUploadProgress?.(0);
    xhr.send(formData);
  });
}

export function composeBatchUploadProgress(
  fileIndex: number,
  fileCount: number,
  filePercent: number,
): number {
  if (fileCount <= 0) {
    return filePercent;
  }

  const slice = 100 / fileCount;
  const base = fileIndex * slice;

  return Math.max(0, Math.min(100, Math.round(base + (filePercent / 100) * slice)));
}

export function createBatchUploadProgressHandler(
  fileIndex: number,
  fileCount: number,
  onProgress?: UploadProgressCallback,
): UploadProgressCallback | undefined {
  if (!onProgress) {
    return undefined;
  }

  return (filePercent) => {
    onProgress(composeBatchUploadProgress(fileIndex, fileCount, filePercent));
  };
}
