const recoveryMessage = document.getElementById("form-message");
const forgotForm = document.getElementById("forgot-password-form");
const resetForm = document.getElementById("reset-password-form");

async function submitPublicRequest(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error ||
      (body.errors && Object.values(body.errors).join(" ")) ||
      "Unable to complete the request.");
  }
  return body;
}

if (forgotForm) {
  const requestPanel = document.getElementById("recovery-request");
  const nextSteps = document.getElementById("recovery-next-steps");
  const emailSummary = document.getElementById("recovery-email-summary");
  const tryAnotherEmail = document.getElementById("try-another-email");

  forgotForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = forgotForm.querySelector('button[type="submit"]');
    const email = forgotForm.email.value.trim();
    button.disabled = true;
    button.textContent = "Sending…";
    try {
      await submitPublicRequest("/api/v1/security/forgot-password", {
        email
      });
      recoveryMessage.textContent = "";
      forgotForm.reset();
      requestPanel.hidden = true;
      emailSummary.textContent =
        `If an account matches ${email}, a reset link has been sent.`;
      nextSteps.hidden = false;
    } catch (error) {
      recoveryMessage.textContent = error.message;
      recoveryMessage.classList.remove("success");
    } finally {
      button.disabled = false;
      button.textContent = "Send reset link";
    }
  });

  tryAnotherEmail.addEventListener("click", () => {
    nextSteps.hidden = true;
    requestPanel.hidden = false;
    recoveryMessage.textContent = "";
    forgotForm.email.focus();
  });
}

if (resetForm) {
  const token = new URLSearchParams(window.location.search).get("token") || "";
  resetForm.token.value = token;
  if (!token) recoveryMessage.textContent = "This reset link is missing its token.";

  resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (resetForm.password.value !== resetForm.confirm_password.value) {
      recoveryMessage.textContent = "The passwords do not match.";
      return;
    }
    const button = resetForm.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await submitPublicRequest("/api/v1/security/reset-password", {
        token: resetForm.token.value,
        password: resetForm.password.value
      });
      recoveryMessage.textContent = "Password updated. Redirecting to sign in…";
      recoveryMessage.classList.add("success");
      window.setTimeout(() => window.location.replace("/login"), 1200);
    } catch (error) {
      recoveryMessage.textContent = error.message;
      recoveryMessage.classList.remove("success");
      button.disabled = false;
    }
  });
}
