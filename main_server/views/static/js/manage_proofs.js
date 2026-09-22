function selectDetonator(type) {
    document.getElementById("selectedDetonatorType").value = type;

    document.querySelectorAll(".detonator-card").forEach(c => {
        const isMatch = c.getAttribute("data-det-type") === type;
        c.classList.toggle("selected", isMatch);
        const icon = c.querySelector(".check-icon");
        if (icon) {
            if (isMatch) icon.classList.remove("d-none");
            else icon.classList.add("d-none");
        }
    });

    const titleMap = {
        "356_LZ": "LOG SHEET PARAMETERS - DETONATOR 356 mg LZ",
        "135_LZY": "LOG SHEET PARAMETERS - DETONATOR 135 mg LZY",
        "RGM": "LOG SHEET PARAMETERS - DETONATOR RGM"
    };
    document.getElementById("logSheetHeaderTitle").innerText = titleMap[type] || "LOG SHEET PARAMETERS";

    const schedField = document.getElementById("scheduleRefFieldContainer");
    const flashRow = document.getElementById("flashDeliveryRow");
    const pressureBarLabel = document.getElementById("pressureBarLabel");
    const standardRows = document.getElementById("standardProofRows");
    const rgmRows = document.getElementById("rgmProofRows");

    if (type === "356_LZ") {
        if (schedField) schedField.classList.remove("d-none");
        if (flashRow) flashRow.classList.remove("d-none");
        if (pressureBarLabel) pressureBarLabel.innerText = "04. Pressure Bar Test";
        if (standardRows) standardRows.classList.remove("d-none");
        if (rgmRows) rgmRows.classList.add("d-none");
        document.getElementById("schedule_ref_input").value = "CQA/Proof Schedule/Det/1/11";
    } else if (type === "135_LZY") {
        if (schedField) schedField.classList.add("d-none");
        if (flashRow) flashRow.classList.add("d-none");
        if (pressureBarLabel) pressureBarLabel.innerText = "03. Pressure Bar Test";
        if (standardRows) standardRows.classList.remove("d-none");
        if (rgmRows) rgmRows.classList.add("d-none");
    } else if (type === "RGM") {
        if (schedField) schedField.classList.add("d-none");
        if (standardRows) standardRows.classList.add("d-none");
        if (rgmRows) rgmRows.classList.remove("d-none");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Set default dates
    const todayStr = new Date().toISOString().split('T')[0];
    if (document.getElementById("add_sample_received_on")) {
        document.getElementById("add_sample_received_on").value = todayStr;
    }
    if (document.getElementById("add_date_of_proof")) {
        document.getElementById("add_date_of_proof").value = todayStr;
    }
    document.querySelectorAll(".test-date-input").forEach(input => {
        input.value = todayStr;
    });

    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "/login";
    }

    const userRole = localStorage.getItem("role");

    const table = $('#proofsTable').DataTable({
        autoWidth: false,
        ajax: {
            url: '/api/proofs',
            dataSrc: ''
        },
        columns: [
            {
                data: 'id',
                width: '5%',
                className: 'ps-3 fw-bold text-secondary'
            },
            {
                data: 'detonator_type',
                width: '18%',
                render: function(data) {
                    if (data === '135_LZY') {
                        return '<span class="badge det-badge-135 px-2 py-1 fs-7">Detonator 135 mg LZY</span>';
                    } else if (data === 'RGM') {
                        return '<span class="badge det-badge-rgm px-2 py-1 fs-7">Detonator RGM</span>';
                    } else {
                        return '<span class="badge det-badge-356 px-2 py-1 fs-7">Detonator 356 mg LZ</span>';
                    }
                }
            },
            {
                data: 'lot_no',
                width: '18%',
                className: 'fw-bold text-primary',
                render: function (data, type, row) {
                    return `<a href="/proof/${row.id}" class="text-decoration-none text-primary fw-bold">${data || 'Proof #' + row.id}</a>`;
                }
            },
            {
                data: 'sample_received_on',
                width: '14%',
                className: 'text-muted',
                render: function (data, type, row) {
                    return data || row.slip_date || row.date_of_proof || row.date || '-';
                }
            },
            {
                data: 'sample_size',
                width: '12%',
                render: function (data) {
                    return data != null ? `<span>${data} Nos</span>` : '<span class="text-muted">-</span>';
                }
            },
            {
                data: 'proof_results',
                width: '13%',
                render: function (data, type, row) {
                    const res = data || row.result_no;
                    return res ? `<span class="fw-semibold text-success">${res}</span>` : '<span class="text-muted">-</span>';
                }
            },
            {
                data: null,
                width: '20%',
                orderable: false,
                className: 'pe-3',
                render: function (data, type, row) {
                    let deleteBtnHtml = '';
                    if (userRole === 'admin') {
                        deleteBtnHtml = `<button type="button" class="btn btn-sm btn-outline-danger d-inline-flex align-items-center gap-1 text-nowrap delete-proof-btn" 
                            data-proof-id="${row.id}" 
                            data-lot-no="${(row.lot_no || 'Proof #' + row.id).replace(/"/g, '&quot;')}"
                            data-det-type="${row.detonator_type || '356_LZ'}"
                            title="Delete Proof and associated tests">
                            <span class="material-symbols-outlined fs-6">delete</span> DELETE
                        </button>`;
                    }
                    return `<div class="d-flex align-items-center gap-1">
                        <a href="/proof/${row.id}" class="btn btn-sm btn-outline-primary d-inline-flex align-items-center gap-1 text-nowrap" title="View Results">
                            <span class="material-symbols-outlined fs-6">visibility</span> Results
                        </a>
                        <a href="/proof/${row.id}/print" target="_blank" class="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1 text-nowrap" title="Print PDF">
                            <span class="material-symbols-outlined fs-6">print</span> PDF
                        </a>
                        ${deleteBtnHtml}
                    </div>`;
                }
            }
        ],
        order: [[0, 'desc']],
        responsive: true
    });

    // Delegate Delete Button Click
    $('#proofsTable tbody').on('click', '.delete-proof-btn', function () {
        const proofId = $(this).data('proof-id');
        const lotNo = $(this).data('lot-no');
        const detType = $(this).data('det-type') || '356_LZ';

        const detLabelMap = {
            '356_LZ': 'Detonator 356 mg LZ',
            '135_LZY': 'Detonator 135 mg LZY',
            'RGM': 'Detonator RGM'
        };

        document.getElementById('delete_proof_id').value = proofId;
        document.getElementById('delete_proof_id_display').innerText = '#' + proofId;
        document.getElementById('delete_lot_no_display').innerText = lotNo;
        document.getElementById('delete_det_type_display').innerText = detLabelMap[detType] || detType;
        document.getElementById('deleteProofError').classList.add('d-none');

        const delModal = new bootstrap.Modal(document.getElementById('deleteProofModal'));
        delModal.show();
    });

    // Handle Confirm Delete Proof
    const confirmDelBtn = document.getElementById('confirmDeleteProofBtn');
    if (confirmDelBtn) {
        confirmDelBtn.addEventListener('click', async () => {
            const proofId = document.getElementById('delete_proof_id').value;
            const errDiv = document.getElementById('deleteProofError');
            errDiv.classList.add('d-none');

            confirmDelBtn.disabled = true;
            confirmDelBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Deleting...';

            try {
                const res = await fetch(`/api/proofs/${proofId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (res.ok) {
                    const modalEl = document.getElementById('deleteProofModal');
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) modalInstance.hide();
                    table.ajax.reload();
                } else {
                    const errData = await res.json();
                    errDiv.innerText = errData.detail || 'Failed to delete proof.';
                    errDiv.classList.remove('d-none');
                }
            } catch (err) {
                console.error('Delete error:', err);
                errDiv.innerText = 'Network error occurred.';
                errDiv.classList.remove('d-none');
            } finally {
                confirmDelBtn.disabled = false;
                confirmDelBtn.innerHTML = '<span class="material-symbols-outlined fs-5">delete_forever</span> Delete Proof & All Tests';
            }
        });
    }

    const username = localStorage.getItem("username");
    if (username) {
        const up = document.getElementById("userProfile");
        if (up) up.classList.remove("d-none");
        const ud = document.getElementById("usernameDisplay");
        if (ud) ud.innerText = username;
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
                    table.ajax.reload();
                }
            } catch (e) {
                console.error("Sync error:", e);
            } finally {
                syncBtn.disabled = false;
                syncBtn.innerHTML = '<span class="material-symbols-outlined fs-5">sync</span> Sync Nodes Now';
            }
        });
    }

    // Add Proof Form Submit
    const form = document.getElementById("addProofForm");
    const formError = document.getElementById("formError");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            formError.classList.add("d-none");

            const formData = new FormData(form);
            const data = Object.fromEntries(formData);

            const detType = data.detonator_type || "356_LZ";
            if (detType === "RGM") {
                if (data.drop_test_sample_size_rgm) data.drop_test_sample_size = data.drop_test_sample_size_rgm;
                if (data.drop_test_date_rgm) data.drop_test_date = data.drop_test_date_rgm;
                if (data.drop_test_obs_rgm) data.drop_test_obs = data.drop_test_obs_rgm;
                if (data.drop_test_remarks_rgm) data.drop_test_remarks = data.drop_test_remarks_rgm;

                if (data.pressure_test_sample_size_rgm) data.pressure_test_sample_size = data.pressure_test_sample_size_rgm;
                if (data.pressure_test_date_rgm) data.pressure_test_date = data.pressure_test_date_rgm;
                if (data.pressure_test_obs_rgm) data.pressure_test_obs = data.pressure_test_obs_rgm;
                if (data.pressure_test_remarks_rgm) data.pressure_test_remarks = data.pressure_test_remarks_rgm;
                data.flash_test_sample_size = null;
                data.flash_test_date = null;
            } else if (detType === "135_LZY") {
                data.flash_test_sample_size = null;
                data.flash_test_date = null;
            }

            // Clean empty string values to null
            for (let key in data) {
                if (data[key] === "") {
                    data[key] = null;
                }
            }

            // Parse integer fields
            const intFields = [
                'sample_size',
                'drop_test_sample_size',
                'sensitivity_test_sample_size',
                'sens_upper_sample_size',
                'sens_lower_sample_size',
                'flash_test_sample_size',
                'pressure_test_sample_size'
            ];
            intFields.forEach(field => {
                if (data[field] !== null && data[field] !== undefined) {
                    const parsed = parseInt(data[field], 10);
                    data[field] = isNaN(parsed) ? null : parsed;
                }
            });

            // Also set legacy field mappings for full compatibility
            data.result_no = data.proof_results;
            data.date = data.date_of_proof;

            try {
                const res = await fetch("/api/proofs", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(data)
                });

                if (res.ok) {
                    form.reset();
                    selectDetonator("356_LZ");
                    $('#addProofModal').modal('hide');
                    table.ajax.reload();
                } else {
                    const errorData = await res.json();
                    formError.innerText = errorData.detail || "Failed to add proof.";
                    formError.classList.remove("d-none");
                }
            } catch (err) {
                formError.innerText = "Network error occurred.";
                formError.classList.remove("d-none");
            }
        });
    }
});
