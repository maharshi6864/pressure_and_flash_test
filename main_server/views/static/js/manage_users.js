let allUsers = [];

function generateRandomPassword(elementId) {
    const chars = "abcdefghjkmnpqrstuvwxyz23456789";
    let res = "";
    for (let i = 0; i < 8; i++) {
        res += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    document.getElementById(elementId).value = res;
}

document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");

    if (!token) {
        window.location.href = "/login";
        return;
    }

    if (role !== "admin") {
        window.location.href = "/manage-proofs";
        return;
    }

    const headers = {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };

    async function loadUsers() {
        try {
            const res = await fetch("/api/users", { headers });
            if (!res.ok) {
                if (res.status === 401) {
                    window.location.href = "/login";
                    return;
                }
                throw new Error(`Failed to load users (HTTP ${res.status})`);
            }
            allUsers = await res.json();
            renderUsers(allUsers);
        } catch (err) {
            console.error(err);
            document.getElementById("usersTbody").innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-danger">
                        <span class="material-symbols-outlined fs-2">error</span>
                        <div class="mt-1">${err.message}</div>
                    </td>
                </tr>
            `;
        }
    }

    function renderUsers(users) {
        const tbody = document.getElementById("usersTbody");
        document.getElementById("userCountBadge").innerText = `${users.length} Users`;

        if (users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-5 text-muted">
                        <span class="material-symbols-outlined fs-1 text-secondary opacity-50">group_off</span>
                        <div class="mt-2">No users found.</div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = users.map((u, idx) => {
            const initial = (u.name ? u.name.charAt(0) : (u.username ? u.username.charAt(0) : 'U')).toUpperCase();
            const roleBadge = u.role === 'admin' 
                ? '<span class="badge bg-primary px-2 py-1"><span class="material-symbols-outlined fs-6 align-middle">shield</span> Admin</span>' 
                : '<span class="badge bg-secondary px-2 py-1">User</span>';
            
            const createdStr = u.created_at ? new Date(u.created_at).toLocaleDateString() : '-';

            return `
                <tr>
                    <td class="ps-4 fw-bold text-muted">${idx + 1}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <div class="rounded-circle bg-light border text-primary d-flex align-items-center justify-content-center fw-bold" style="width: 34px; height: 34px; font-size: 13px;">
                                ${initial}
                            </div>
                            <div class="fw-semibold text-dark">${u.name || '<span class="text-muted italic">Not set</span>'}</div>
                        </div>
                    </td>
                    <td>
                        <span class="font-monospace text-secondary fw-semibold">@${u.username}</span>
                    </td>
                    <td>
                        <span class="badge bg-light text-dark border font-monospace px-2 py-1" style="font-size: 13px;">${u.password || '-'}</span>
                    </td>
                    <td>${roleBadge}</td>
                    <td class="small text-muted">${createdStr}</td>
                    <td class="text-end pe-4">
                        <div class="btn-group btn-group-sm">
                            <button type="button" class="btn btn-outline-secondary edit-user-btn" 
                                data-id="${u.id}" data-name="${u.name || ''}" data-username="${u.username}" 
                                data-password="${u.password || ''}" data-role="${u.role}">
                                <span class="material-symbols-outlined fs-6">edit</span>
                            </button>
                            <button type="button" class="btn btn-outline-danger delete-user-btn" 
                                data-id="${u.id}" data-username="${u.username}">
                                <span class="material-symbols-outlined fs-6">delete</span>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        attachTableListeners();
    }

    function attachTableListeners() {
        // Edit User button
        document.querySelectorAll(".edit-user-btn").forEach(btn => {
            btn.onclick = () => {
                const id = btn.getAttribute("data-id");
                const name = btn.getAttribute("data-name");
                const username = btn.getAttribute("data-username");
                const password = btn.getAttribute("data-password");
                const role = btn.getAttribute("data-role");

                document.getElementById("edit_user_id").value = id;
                document.getElementById("edit_name").value = name;
                document.getElementById("edit_username").value = username;
                document.getElementById("edit_password").value = password;
                document.getElementById("edit_role").value = role || "user";
                document.getElementById("editUserError").classList.add("d-none");

                new bootstrap.Modal(document.getElementById("editUserModal")).show();
            };
        });

        // Delete User button
        document.querySelectorAll(".delete-user-btn").forEach(btn => {
            btn.onclick = () => {
                const id = btn.getAttribute("data-id");
                const username = btn.getAttribute("data-username");

                document.getElementById("delete_user_id").value = id;
                document.getElementById("delete_username_text").innerText = `@${username}`;
                document.getElementById("deleteUserError").classList.add("d-none");

                new bootstrap.Modal(document.getElementById("deleteUserModal")).show();
            };
        });
    }

    // Search Filter
    document.getElementById("userSearchInput").addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            renderUsers(allUsers);
            return;
        }
        const filtered = allUsers.filter(u => 
            (u.name && u.name.toLowerCase().includes(query)) ||
            (u.username && u.username.toLowerCase().includes(query)) ||
            (u.role && u.role.toLowerCase().includes(query))
        );
        renderUsers(filtered);
    });

    // Refresh Button
    document.getElementById("refreshUsersBtn").onclick = loadUsers;

    // Add User Form Submit
    document.getElementById("addUserForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const errDiv = document.getElementById("addUserError");
        errDiv.classList.add("d-none");

        const payload = {
            name: document.getElementById("add_name").value.trim() || null,
            username: document.getElementById("add_username").value.trim(),
            password: document.getElementById("add_password").value,
            role: document.getElementById("add_role").value
        };

        try {
            const res = await fetch("/api/users", {
                method: "POST",
                headers,
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById("addUserModal")).hide();
                document.getElementById("addUserForm").reset();
                await loadUsers();
            } else {
                const data = await res.json();
                errDiv.innerText = data.detail || "Failed to create user.";
                errDiv.classList.remove("d-none");
            }
        } catch (err) {
            errDiv.innerText = "Network error occurred.";
            errDiv.classList.remove("d-none");
        }
    });

    // Edit User Form Submit
    document.getElementById("editUserForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const errDiv = document.getElementById("editUserError");
        errDiv.classList.add("d-none");
        const userId = document.getElementById("edit_user_id").value;

        const payload = {
            name: document.getElementById("edit_name").value.trim() || null,
            username: document.getElementById("edit_username").value.trim(),
            password: document.getElementById("edit_password").value,
            role: document.getElementById("edit_role").value
        };

        try {
            const res = await fetch(`/api/users/${userId}`, {
                method: "PUT",
                headers,
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById("editUserModal")).hide();
                await loadUsers();
            } else {
                const data = await res.json();
                errDiv.innerText = data.detail || "Failed to update user.";
                errDiv.classList.remove("d-none");
            }
        } catch (err) {
            errDiv.innerText = "Network error occurred.";
            errDiv.classList.remove("d-none");
        }
    });

    // Confirm Delete User
    document.getElementById("confirmDeleteUserBtn").onclick = async () => {
        const errDiv = document.getElementById("deleteUserError");
        errDiv.classList.add("d-none");
        const userId = document.getElementById("delete_user_id").value;

        try {
            const res = await fetch(`/api/users/${userId}`, {
                method: "DELETE",
                headers
            });

            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById("deleteUserModal")).hide();
                await loadUsers();
            } else {
                const data = await res.json();
                errDiv.innerText = data.detail || "Failed to delete user.";
                errDiv.classList.remove("d-none");
            }
        } catch (err) {
            errDiv.innerText = "Network error occurred.";
            errDiv.classList.remove("d-none");
        }
    };

    // Initial Load
    await loadUsers();
});
