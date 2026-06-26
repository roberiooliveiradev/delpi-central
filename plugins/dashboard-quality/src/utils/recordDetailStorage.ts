const PPM_DETAIL_KEY = "delpi.dashboard-quality.ppm-detail";
const NC_DETAIL_KEY = "delpi.dashboard-quality.nc-detail";

export function savePpmDetailRecord<T>(record: T): void {
  try {
    sessionStorage.setItem(PPM_DETAIL_KEY, JSON.stringify(record));
  } catch {
    // ignora
  }
}

export function readPpmDetailRecord<T>(): T | null {
  try {
    const raw = sessionStorage.getItem(PPM_DETAIL_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function saveNonconformityDetailRecord<T>(record: T): void {
  try {
    sessionStorage.setItem(NC_DETAIL_KEY, JSON.stringify(record));
  } catch {
    // ignora
  }
}

export function readNonconformityDetailRecord<T>(): T | null {
  try {
    const raw = sessionStorage.getItem(NC_DETAIL_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}
