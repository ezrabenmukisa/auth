const loginForm = document.getElementById("login-form");
const loginMessage = document.getElementById("form-message");

if (AuthSession.hasSession()) window.location.replace("/dashboard");

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginMessage.textContent = "";
  const button = loginForm.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = "Signing in…";

  try {
    const response = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier: loginForm.identifier.value.trim(),
        password: loginForm.password.value
      })
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error ||
      (body.errors && Object.values(body.errors).join(" ")) ||
      "Unable to sign in.");
    AuthSession.store(body);
    window.location.replace("/dashboard");
  } catch (error) {
    loginMessage.textContent = error.message;
    button.disabled = false;
    button.textContent = "Sign in";
  }
});
