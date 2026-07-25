window.AuthSession = (() => {
  const accessKey = "access_hub_access";
  const refreshKey = "access_hub_refresh";

  function store(tokens) {
    sessionStorage.setItem(accessKey, tokens.access_token);
    sessionStorage.setItem(refreshKey, tokens.refresh_token);
  }

  function clear() {
    sessionStorage.removeItem(accessKey);
    sessionStorage.removeItem(refreshKey);
  }

  async function parse(response) {
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = body.error ||
        (body.errors && Object.values(body.errors).join(" ")) ||
        "Something went wrong.";
      throw new Error(message);
    }
    return body;
  }

  async function refreshAccess() {
    const refreshToken = sessionStorage.getItem(refreshKey);
    if (!refreshToken) return false;
    const response = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      headers: { Authorization: `Bearer ${refreshToken}` }
    });
    if (!response.ok) {
      clear();
      return false;
    }
    const body = await response.json();
    sessionStorage.setItem(accessKey, body.access_token);
    return true;
  }

  async function request(path, options = {}, retry = true) {
    const headers = new Headers(options.headers || {});
    headers.set("Content-Type", "application/json");
    const accessToken = sessionStorage.getItem(accessKey);
    if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
    const response = await fetch(path, { ...options, headers });
    if (response.status === 401 && retry && await refreshAccess()) {
      return request(path, options, false);
    }
    return parse(response);
  }

  async function logout() {
    await request("/api/v1/auth/logout", { method: "POST" }).catch(async () => {
      const refreshToken = sessionStorage.getItem(refreshKey);
      if (!refreshToken) return;
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${refreshToken}` }
      }).catch(() => {});
    });
    clear();
    window.location.replace("/login");
  }

  function hasSession() {
    return Boolean(sessionStorage.getItem(accessKey));
  }

  return { store, clear, request, logout, hasSession };
})();

document.querySelectorAll("[data-password-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.passwordToggle);
    const shouldShow = input.type === "password";
    input.type = shouldShow ? "text" : "password";
    button.setAttribute("aria-label", shouldShow ? "Hide password" : "Show password");
    button.setAttribute("aria-pressed", String(shouldShow));
  });
});
