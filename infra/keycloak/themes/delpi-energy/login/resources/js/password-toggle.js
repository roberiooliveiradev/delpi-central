(function () {
  const toggles = document.querySelectorAll(".js-toggle-passwords");

  if (!toggles.length) return;

  toggles.forEach((toggle) => {
    const form = toggle.closest("form") || document;
    const passwordInputs = Array.from(
      form.querySelectorAll('input[data-password-toggle="true"]')
    );

    if (!passwordInputs.length) return;

    toggle.addEventListener("change", function () {
      const nextType = toggle.checked ? "text" : "password";

      passwordInputs.forEach((input) => {
        input.setAttribute("type", nextType);
      });
    });
  });
})();