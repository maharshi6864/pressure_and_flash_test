document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    const username = localStorage.getItem("username");
    if (username) {
        const userProfile = document.getElementById("userProfile");
        if (userProfile) userProfile.classList.remove("d-none");
        const userDisplay = document.getElementById("usernameDisplay");
        if (userDisplay) userDisplay.innerText = username;
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            localStorage.removeItem("token");
            localStorage.removeItem("username");
            localStorage.removeItem("role");
            window.location.href = "/login";
        });
    }

    const refreshBtn = document.getElementById("refreshDashboardBtn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            loadDashboardData();
        });
    }

    const syncBtn = document.getElementById("triggerSyncBtn");
    if (syncBtn) {
        syncBtn.addEventListener("click", async () => {
            syncBtn.disabled = true;
            syncBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Syncing...';
            try {
                const res = await fetch("/api/proofs/sync/trigger", {
                    method: "POST",
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    await loadDashboardData();
                }
            } catch (e) {
                console.error("Sync error:", e);
            } finally {
                syncBtn.disabled = false;
                syncBtn.innerHTML = '<span class="material-symbols-outlined fs-5">sync</span> Sync Nodes Now';
            }
        });
    }

    async function loadDashboardData() {
        try {
            const res = await fetch("/api/proofs/dashboard/stats", {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to fetch dashboard stats");
            const data = await res.json();

            // Update Stats
            const totalProofs = document.getElementById("totalProofsStat");
            if (totalProofs) totalProofs.innerText = data.total_proofs || 0;

            const flashTests = document.getElementById("flashTestsStat");
            if (flashTests) flashTests.innerText = data.total_flash_tests || 0;

            const flashDet = document.getElementById("flashDetectedCount");
            if (flashDet) flashDet.innerText = data.flash_detected_count || 0;

            const pressureTests = document.getElementById("pressureTestsStat");
            if (pressureTests) pressureTests.innerText = data.total_pressure_tests || 0;

            const avgMpa = document.getElementById("avgMpaStat");
            if (avgMpa) avgMpa.innerText = data.avg_pressure_mpa ? data.avg_pressure_mpa.toFixed(2) : '0.00';

            const syncedProof = document.getElementById("syncedProofCount");
            if (syncedProof) syncedProof.innerText = `${data.synced_flash_count || 0} / ${data.total_proofs || 0}`;

            // Render Recent Proofs
            const tbody = document.getElementById("recentProofsTbody");
            if (tbody) {
                if (data.recent_proofs && data.recent_proofs.length > 0) {
                    tbody.innerHTML = data.recent_proofs.map(p => `
                        <tr>
                            <td class="ps-3">
                                <a href="/proof/${p.id}" class="fw-bold text-decoration-none text-primary">
                                    ${p.lot_no || `Proof #${p.id}`}
                                </a>
                            </td>
                            <td class="small text-muted">${p.date || '-'}</td>
                            <td class="small">${p.store || '-'}</td>
                            <td>
                                <span class="badge ${p.synced_with_flash ? 'bg-success' : 'bg-secondary'} bg-opacity-75">
                                    ${p.synced_with_flash ? 'Synced' : 'Pending'}
                                </span>
                            </td>
                            <td>
                                <span class="badge ${p.synced_with_pressure ? 'bg-info' : 'bg-secondary'} bg-opacity-75">
                                    ${p.synced_with_pressure ? 'Synced' : 'Pending'}
                                </span>
                            </td>
                            <td class="text-end pe-3">
                                <a href="/proof/${p.id}" class="btn btn-sm btn-outline-primary py-0 px-2 d-inline-flex align-items-center gap-1">
                                    <span class="material-symbols-outlined" style="font-size: 16px;">visibility</span> View
                                </a>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No proof slips registered yet.</td></tr>';
                }
            }

        } catch (err) {
            console.error("Dashboard error:", err);
        }
    }

    loadDashboardData();
});
