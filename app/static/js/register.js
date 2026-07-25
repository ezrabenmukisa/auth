const registerForm = document.getElementById("register-form");
const registerMessage = document.getElementById("form-message");

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  registerMessage.textContent = "";
  if (registerForm.password.value !== registerForm.confirm_password.value) {
    registerMessage.textContent = "Passwords do not match.";
    registerForm.confirm_password.focus();
    return;
  }
  const button = registerForm.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = "Creating account…";
  const payload = {
    username: registerForm.username.value.trim(),
    email: registerForm.email.value.trim(),
    password: registerForm.password.value,
    full_name: registerForm.full_name.value.trim() || null
  };

  try {
    const registration = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const registrationBody = await registration.json();
    if (!registration.ok) throw new Error(registrationBody.error ||
      (registrationBody.errors &&
        Object.values(registrationBody.errors).join(" ")) ||
      "Unable to create your account.");

    const login = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier: payload.username,
        password: payload.password
      })
    });
    const tokens = await login.json();
    if (!login.ok) throw new Error("Account created. Please sign in.");
    AuthSession.store(tokens);
    window.location.replace("/dashboard");
  } catch (error) {
    registerMessage.textContent = error.message;
    button.disabled = false;
    button.textContent = "Create account";
  }
});
