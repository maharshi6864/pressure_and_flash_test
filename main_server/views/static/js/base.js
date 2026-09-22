// Global Auth & Navigation Guard
(function() {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    const username = localStorage.getItem("username");
    const name = localStorage.getItem("name");

    if (!token && window.location.pathname !== "/login") {
        window.location.href = "/login";
        return;
    }

    // Show Manage Users menu only for admin
    const navUsers = document.getElementById("navManageUsers");
    if (navUsers && role === "admin") {
        navUsers.classList.remove("d-none");
    }

    // Populate profile badge
    const up = document.getElementById("userProfile");
    if (up && token) {
        up.classList.remove("d-none");
        const und = document.getElementById("userNameDisplay");
        if (und) und.innerText = name || username || "User";
        const ud = document.getElementById("usernameDisplay");
        if (ud) ud.innerText = username ? `@${username}` : '';
        const rb = document.getElementById("userRoleBadge");
        if (rb) {
            rb.innerText = role || "user";
            if (role === "admin") {
                rb.className = "badge bg-primary";
            } else {
                rb.className = "badge bg-secondary";
            }
        }
    }

    // Global Logout
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.onclick = function(e) {
            e.preventDefault();
            localStorage.removeItem("token");
            localStorage.removeItem("role");
            localStorage.removeItem("username");
            localStorage.removeItem("name");
            window.location.href = "/login";
        };
    }
})();
