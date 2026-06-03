type AlertHandler = (message: string, title?: string) => void;

let alertHandler: AlertHandler = (message, title) => {
  const prefix = title ? `${title}\n\n` : "";
  window.alert(`${prefix}${message}`);
};

export function setChatAlertHandler(handler: AlertHandler): void {
  alertHandler = handler;
}

export function chatAlert(message: string, title = "Aviso"): void {
  alertHandler(message, title);
}
