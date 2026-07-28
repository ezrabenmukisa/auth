const app = document.getElementById("dashboard-app");
const message = document.getElementById("dashboard-message");
let currentUser = null;
let rolesCache = [];
let permissionsCache = [];
let peoplePage = 1;
let peopleTotalPages = 1;
let peopleSearch = "";
let auditPage = 1;
let auditTotalPages = 1;

const rolePaths = {
  Admin: "/admin",
  Manager: "/manager",
  Accountant: "/accountant",
  Employee: "/employee"
};

const roleCopy = {
  Admin: "Manage people, roles and permissions across the organization.",
  Manager: "Review your organization’s role and permission structure.",
  Accountant: "Review the permission information available to your role.",
  Employee: "View your account and continue with your assigned employee access."
};

function showMessage(text, kind = "") {
  message.textContent = text;
  message.className = `dashboard-message ${kind}`;
}

function showView(name) {
  document.querySelectorAll(".view").forEach((view) =>
    view.classList.toggle("active", view.id === `${name}-view`));
  document.querySelectorAll(".nav-item").forEach((item) =>
    item.classList.toggle("active", item.dataset.view === name));
  document.getElementById("page-title").textContent =
    name === "profile" ? "My profile" : name.charAt(0).toUpperCase() + name.slice(1);
}

function applyRole(role) {
  document.body.dataset.role = role.toLowerCase();
  document.querySelectorAll(".nav-item").forEach((item) => {
    const unrestricted =
      !["roles", "permissions", "people", "audit"].includes(item.dataset.view);
    const allowed = unrestricted || item.classList.contains(role.toLowerCase());
    item.hidden = !allowed;
  });
}

function escapeHtml(value) {
  const element = document.createElement("span");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function actionButton(label, action, id, kind = "secondary") {
  return `<button class="button ${kind}" type="button" data-action="${action}"
    data-id="${id}">${escapeHtml(label)}</button>`;
}

function roleCard(role) {
  const actions = currentUser.role === "Admin"
    ? `<div class="card-actions">
        ${actionButton("Edit", "edit-role", role.id)}
        ${actionButton("Permissions", "manage-role-permissions", role.id)}
        ${actionButton("Delete", "delete-role", role.id, "danger")}
      </div>`
    : "";
  return `<article class="data-card">
    <span>Role ${role.id}</span>
    <h3>${escapeHtml(role.name)}</h3>
    <p>${escapeHtml(role.description || "No description provided.")}</p>
    ${actions}
  </article>`;
}

function permissionCard(permission) {
  const actions = currentUser.role === "Admin"
    ? `<div class="card-actions">
        ${actionButton("Edit", "edit-permission", permission.id)}
        ${actionButton("Delete", "delete-permission", permission.id, "danger")}
      </div>`
    : "";
  return `<article class="data-card">
    <span>Permission ${permission.id}</span>
    <h3>${escapeHtml(permission.name)}</h3>
    <p>${escapeHtml(permission.description || "No description provided.")}</p>
    ${actions}
  </article>`;
}

async function loadRoles() {
  rolesCache = await AuthSession.request("/api/v1/authorization/roles");
  document.getElementById("roles-list").innerHTML =
    rolesCache.map(roleCard).join("") || "<p class=\"muted\">No roles found.</p>";
  return rolesCache;
}

async function loadPermissions() {
  permissionsCache = await AuthSession.request("/api/v1/authorization/permissions");
  document.getElementById("permissions-list").innerHTML =
    permissionsCache.map(permissionCard).join("") ||
    "<p class=\"muted\">No permissions found.</p>";
  return permissionsCache;
}

async function loadPeople() {
  if (!rolesCache.length) await loadRoles();
  const params = new URLSearchParams({
    page: peoplePage,
    per_page: 8
  });
  if (peopleSearch) params.set("search", peopleSearch);
  const response = await AuthSession.request(`/api/v1/users/?${params}`);
  peopleTotalPages = Math.max(response.total_pages, 1);

  const rows = await Promise.all(response.users.map(async (user) => {
    const role = await AuthSession.request(
      `/api/v1/authorization/users/${user.id}/role`);
    return { ...user, role };
  }));

  document.getElementById("people-list").innerHTML = rows.map((user) => `
    <article class="person-row">
      <div class="avatar small">${escapeHtml(
        (user.full_name || user.username)[0].toUpperCase())}</div>
      <div class="person-copy">
        <strong>${escapeHtml(user.full_name || user.username)}</strong>
        <span>@${escapeHtml(user.username)} · ${escapeHtml(user.email)} ·
          ${user.is_suspended ? "Suspended" : "Active"}</span>
      </div>
      ${user.id === currentUser.id
        ? `<span class="self-role-label">${escapeHtml(
          user.role ? user.role.name : "No role")} · Your account</span>`
        : `<div class="person-actions">
            <select data-user-id="${user.id}" aria-label="Role for ${escapeHtml(
              user.username)}">
              ${rolesCache.map((role) => `<option value="${role.id}"
                ${user.role && role.id === user.role.id ? "selected" : ""}>
                ${escapeHtml(role.name)}</option>`).join("")}
            </select>
            <button class="button ${user.is_suspended ? "secondary" : "danger"}"
              type="button" data-account-action="${user.is_suspended
                ? "activate" : "suspend"}" data-user-id="${user.id}">
              ${user.is_suspended ? "Reactivate" : "Suspend"}
            </button>
          </div>`}
    </article>`).join("") || "<p class=\"muted\">No people matched your search.</p>";

  document.getElementById("people-page").textContent =
    `Page ${peoplePage} of ${peopleTotalPages} · ${response.total} people`;
  document.getElementById("people-previous").disabled = peoplePage <= 1;
  document.getElementById("people-next").disabled = peoplePage >= peopleTotalPages;

  document.querySelectorAll("[data-user-id]").forEach((select) => {
    if (select.tagName !== "SELECT") return;
    select.addEventListener("change", async () => {
      try {
        await AuthSession.request(
          `/api/v1/authorization/users/${select.dataset.userId}/role`,
          { method: "PUT", body: JSON.stringify({ role_id: Number(select.value) }) }
        );
        showMessage("Role updated successfully.", "success");
      } catch (error) {
        showMessage(error.message, "error");
        await loadPeople();
      }
    });
  });

  document.querySelectorAll("[data-account-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.accountAction;
      if (action === "suspend" &&
          !window.confirm("Suspend this account and block future access?")) return;
      try {
        await AuthSession.request(
          `/api/v1/security/users/${button.dataset.userId}/${action}`,
          { method: "POST" }
        );
        showMessage(
          action === "suspend" ? "Account suspended." : "Account reactivated.",
          "success"
        );
        await loadPeople();
      } catch (error) {
        showMessage(error.message, "error");
      }
    });
  });
}

async function loadAuditLogs() {
  const response = await AuthSession.request(
    `/api/v1/security/audit-logs?page=${auditPage}&per_page=15`);
  auditTotalPages = Math.max(response.total_pages, 1);
  document.getElementById("audit-list").innerHTML = response.events.map((event) => `
    <article class="audit-row">
      <div><strong>${escapeHtml(event.action.replaceAll("_", " "))}</strong>
        <span>${escapeHtml(event.status)}</span></div>
      <div><span>User</span><strong>${escapeHtml(event.user_id || "Unknown")}</strong></div>
      <div><span>IP address</span><strong>${escapeHtml(event.ip_address || "Unavailable")}</strong></div>
      <time>${escapeHtml(new Date(event.created_at).toLocaleString())}</time>
    </article>`).join("") || "<p class=\"muted\">No security events recorded.</p>";
  document.getElementById("audit-page").textContent =
    `Page ${auditPage} of ${auditTotalPages} · ${response.total} events`;
  document.getElementById("audit-previous").disabled = auditPage <= 1;
  document.getElementById("audit-next").disabled = auditPage >= auditTotalPages;
}

function populateProfile(user) {
  const displayName = user.full_name || user.username;
  document.getElementById("profile-avatar").textContent = displayName[0].toUpperCase();
  document.getElementById("profile-display-name").textContent = displayName;
  document.getElementById("profile-username").textContent = `@${user.username}`;
  document.getElementById("profile-email").textContent = user.email;
  document.getElementById("profile-role").textContent = user.role || "Not assigned";
  document.getElementById("profile-status").textContent =
    user.is_active ? "Active" : "Inactive";
  document.getElementById("profile-full-name").value = user.full_name || "";
}

async function openRolePermissions(roleId) {
  if (!permissionsCache.length) await loadPermissions();
  const role = await AuthSession.request(`/api/v1/authorization/roles/${roleId}`);
  const assigned = await AuthSession.request(
    `/api/v1/authorization/roles/${roleId}/permissions`);
  const assignedIds = new Set(assigned.map((permission) => permission.id));
  const panel = document.getElementById("role-permissions-panel");
  document.getElementById("role-permissions-title").textContent =
    `${role.name} permissions`;
  document.getElementById("role-permissions-list").innerHTML =
    permissionsCache.map((permission) => `
      <label class="permission-option">
        <input type="checkbox" data-role-id="${role.id}"
          data-permission-id="${permission.id}"
          ${assignedIds.has(permission.id) ? "checked" : ""}>
        <span><strong>${escapeHtml(permission.name)}</strong>
          <small>${escapeHtml(permission.description || "No description")}</small>
        </span>
      </label>`).join("");
  panel.hidden = false;
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function editRole(roleId) {
  const role = await AuthSession.request(`/api/v1/authorization/roles/${roleId}`);
  const name = window.prompt("Role name", role.name);
  if (name === null) return;
  const description = window.prompt("Role description", role.description || "");
  if (description === null) return;
  await AuthSession.request(`/api/v1/authorization/roles/${roleId}`, {
    method: "PUT",
    body: JSON.stringify({ name: name.trim(), description: description.trim() || null })
  });
  await loadRoles();
  showMessage("Role updated.", "success");
}

async function editPermission(permissionId) {
  const permission = await AuthSession.request(
    `/api/v1/authorization/permissions/${permissionId}`);
  const name = window.prompt("Permission name", permission.name);
  if (name === null) return;
  const description = window.prompt(
    "Permission description", permission.description || "");
  if (description === null) return;
  await AuthSession.request(`/api/v1/authorization/permissions/${permissionId}`, {
    method: "PUT",
    body: JSON.stringify({ name: name.trim(), description: description.trim() || null })
  });
  await loadPermissions();
  showMessage("Permission updated.", "success");
}

async function initialize() {
  if (!AuthSession.hasSession()) {
    window.location.replace("/login");
    return;
  }
  try {
    currentUser = await AuthSession.request("/api/v1/auth/me");
    const correctPath = rolePaths[currentUser.role] || "/employee";
    if (window.location.pathname === "/dashboard" ||
        (app.dataset.expectedRole && app.dataset.expectedRole !== currentUser.role)) {
      window.location.replace(correctPath);
      return;
    }

    applyRole(currentUser.role);
    populateProfile(currentUser);
    const displayName = currentUser.full_name || currentUser.username;
    document.getElementById("identity-name").textContent = displayName;
    document.getElementById("identity-role").textContent = currentUser.role;
    document.getElementById("avatar").textContent = displayName[0].toUpperCase();
    document.getElementById("role-badge").textContent = currentUser.role;
    document.getElementById("welcome-title").textContent =
      `Welcome, ${displayName.split(" ")[0]}`;
    document.getElementById("welcome-copy").textContent =
      roleCopy[currentUser.role] || roleCopy.Employee;

    const metrics = [{ label: "Account", value: currentUser.username }];
    if (["Admin", "Manager"].includes(currentUser.role)) {
      metrics.push({ label: "Roles", value: (await loadRoles()).length });
    }
    if (["Admin", "Manager", "Accountant"].includes(currentUser.role)) {
      metrics.push({ label: "Permissions", value: (await loadPermissions()).length });
    }
    document.getElementById("overview-metrics").innerHTML = metrics
      .map((metric) => `<article class="metric-card"><span>${metric.label}</span>
        <strong>${escapeHtml(metric.value)}</strong></article>`).join("");
  } catch (error) {
    AuthSession.clear();
    window.location.replace("/login");
  }
}

document.querySelectorAll(".nav-item").forEach((item) =>
  item.addEventListener("click", async () => {
    showView(item.dataset.view);
    try {
      if (item.dataset.view === "roles") await loadRoles();
      if (item.dataset.view === "permissions") await loadPermissions();
      if (item.dataset.view === "people") await loadPeople();
      if (item.dataset.view === "audit") await loadAuditLogs();
      if (item.dataset.view === "profile") populateProfile(currentUser);
    } catch (error) {
      showMessage(error.message, "error");
    }
  }));

document.getElementById("account-button").addEventListener("click", () => {
  showView("profile");
  populateProfile(currentUser);
});
document.getElementById("logout-button").addEventListener("click", AuthSession.logout);
document.getElementById("refresh-roles").addEventListener("click", () =>
  loadRoles().catch((error) => showMessage(error.message, "error")));
document.getElementById("refresh-permissions").addEventListener("click", () =>
  loadPermissions().catch((error) => showMessage(error.message, "error")));
document.getElementById("refresh-people").addEventListener("click", () =>
  loadPeople().catch((error) => showMessage(error.message, "error")));
document.getElementById("refresh-audit").addEventListener("click", () =>
  loadAuditLogs().catch((error) => showMessage(error.message, "error")));

document.getElementById("create-role-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await AuthSession.request("/api/v1/authorization/roles", {
      method: "POST",
      body: JSON.stringify({
        name: form.name.value.trim(),
        description: form.description.value.trim() || null
      })
    });
    form.reset();
    await loadRoles();
    showMessage("Role created.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

document.getElementById("create-permission-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await AuthSession.request("/api/v1/authorization/permissions", {
        method: "POST",
        body: JSON.stringify({
          name: form.name.value.trim(),
          description: form.description.value.trim() || null
        })
      });
      form.reset();
      await loadPermissions();
      showMessage("Permission created.", "success");
    } catch (error) {
      showMessage(error.message, "error");
    }
  });

document.getElementById("roles-list").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  try {
    if (button.dataset.action === "edit-role") await editRole(button.dataset.id);
    if (button.dataset.action === "manage-role-permissions") {
      await openRolePermissions(button.dataset.id);
    }
    if (button.dataset.action === "delete-role" &&
        window.confirm("Delete this role? This only works when no users use it.")) {
      await AuthSession.request(`/api/v1/authorization/roles/${button.dataset.id}`, {
        method: "DELETE"
      });
      await loadRoles();
      showMessage("Role deleted.", "success");
    }
  } catch (error) {
    showMessage(error.message, "error");
  }
});

document.getElementById("permissions-list")
  .addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    try {
      if (button.dataset.action === "edit-permission") {
        await editPermission(button.dataset.id);
      }
      if (button.dataset.action === "delete-permission" &&
          window.confirm("Delete this permission?")) {
        await AuthSession.request(
          `/api/v1/authorization/permissions/${button.dataset.id}`,
          { method: "DELETE" });
        await loadPermissions();
        showMessage("Permission deleted.", "success");
      }
    } catch (error) {
      showMessage(error.message, "error");
    }
  });

document.getElementById("role-permissions-list")
  .addEventListener("change", async (event) => {
    const checkbox = event.target.closest("[data-permission-id]");
    if (!checkbox) return;
    const path = `/api/v1/authorization/roles/${checkbox.dataset.roleId}` +
      `/permissions/${checkbox.dataset.permissionId}`;
    try {
      await AuthSession.request(path, {
        method: checkbox.checked ? "POST" : "DELETE"
      });
      showMessage("Role permissions updated.", "success");
    } catch (error) {
      checkbox.checked = !checkbox.checked;
      showMessage(error.message, "error");
    }
  });

document.getElementById("close-role-permissions").addEventListener("click", () => {
  document.getElementById("role-permissions-panel").hidden = true;
});

document.getElementById("people-search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  peopleSearch = document.getElementById("people-search").value.trim();
  peoplePage = 1;
  await loadPeople().catch((error) => showMessage(error.message, "error"));
});
document.getElementById("clear-people-search").addEventListener("click", async () => {
  document.getElementById("people-search").value = "";
  peopleSearch = "";
  peoplePage = 1;
  await loadPeople().catch((error) => showMessage(error.message, "error"));
});
document.getElementById("people-previous").addEventListener("click", async () => {
  if (peoplePage > 1) peoplePage -= 1;
  await loadPeople().catch((error) => showMessage(error.message, "error"));
});
document.getElementById("people-next").addEventListener("click", async () => {
  if (peoplePage < peopleTotalPages) peoplePage += 1;
  await loadPeople().catch((error) => showMessage(error.message, "error"));
});
document.getElementById("audit-previous").addEventListener("click", async () => {
  if (auditPage > 1) auditPage -= 1;
  await loadAuditLogs().catch((error) => showMessage(error.message, "error"));
});
document.getElementById("audit-next").addEventListener("click", async () => {
  if (auditPage < auditTotalPages) auditPage += 1;
  await loadAuditLogs().catch((error) => showMessage(error.message, "error"));
});

document.getElementById("profile-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const updated = await AuthSession.request(`/api/v1/users/${currentUser.id}`, {
      method: "PATCH",
      body: JSON.stringify({
        full_name: document.getElementById("profile-full-name").value.trim() || null
      })
    });
    currentUser = { ...currentUser, ...updated };
    populateProfile(currentUser);
    document.getElementById("identity-name").textContent =
      currentUser.full_name || currentUser.username;
    showMessage("Profile updated.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

document.getElementById("verify-session").addEventListener("click", async () => {
  try {
    await AuthSession.request("/api/v1/auth/protected");
    showMessage("Your secure session is active.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

initialize();
