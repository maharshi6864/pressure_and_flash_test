document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const proofSelect = document.getElementById('proofSelect');
    const testCardsContainer = document.getElementById('testCardsContainer');
    const testsSummaryBadge = document.getElementById('testsSummaryBadge');
    const refreshProofsBtn = document.getElementById('refreshProofsBtn');
    const saveBtn = document.getElementById('saveMeasurementBtn');
    const setOriginBtn = document.getElementById('setOriginBtn');
    const resetBtn = document.getElementById('resetBtn');
    const msg = document.getElementById('measureMessage');

    // Live display elements
    const valCurrentInch = document.getElementById('val-current-inch');
    const valCurrentPress = document.getElementById('val-current-press');
    const recValMaxPosInch = document.getElementById('rec-val-max-pos-inch');
    const recValMaxPosPress = document.getElementById('rec-val-max-pos-press');

    // --- State Variables ---
    let currentRelativeX = 0.0;
    let isSaving = false;
    let currentSelectedTestId = null;
    let currentTests = [];

    // --- Render Test Cards Grid ---
    function renderCards() {
        if (!testCardsContainer) return;
        testCardsContainer.innerHTML = '';

        if (!proofSelect || !proofSelect.value) {
            testCardsContainer.innerHTML = `
                <div class="col-12 w-100 text-center text-muted py-4">
                    <span class="material-symbols-outlined fs-2 text-secondary opacity-50 mb-1">inventory_2</span>
                    <p class="small mb-0">Select a proof to display test cards</p>
                </div>`;
            if (testsSummaryBadge) {
                testsSummaryBadge.textContent = '0 / 0 Completed';
                testsSummaryBadge.className = 'badge bg-secondary-subtle text-secondary small';
            }
            return;
        }

        if (currentTests.length === 0) {
            testCardsContainer.innerHTML = `
                <div class="col-12 w-100 text-center text-muted py-4">
                    <span class="material-symbols-outlined fs-2 text-secondary opacity-50 mb-1">info</span>
                    <p class="small mb-0">No tests available for this proof</p>
                </div>`;
            if (testsSummaryBadge) {
                testsSummaryBadge.textContent = '0 / 0 Completed';
                testsSummaryBadge.className = 'badge bg-secondary-subtle text-secondary small';
            }
            return;
        }

        // Summary badge update
        const completedCount = currentTests.filter(t => t.measurement_value !== null && t.measurement_value !== undefined).length;
        const totalCount = currentTests.length;
        if (testsSummaryBadge) {
            testsSummaryBadge.textContent = `${completedCount} / ${totalCount} Completed`;
            if (completedCount === totalCount && totalCount > 0) {
                testsSummaryBadge.className = 'badge bg-success-subtle text-success border border-success-subtle small';
            } else {
                testsSummaryBadge.className = 'badge bg-primary-subtle text-primary border border-primary-subtle small';
            }
        }

        currentTests.forEach(t => {
            const col = document.createElement('div');
            col.className = 'col';

            const isActive = t.id === currentSelectedTestId;
            const isCompleted = t.measurement_value !== null && t.measurement_value !== undefined;

            let statusIcon = '';
            let statusBadge = '';
            let statusClass = 'pending';
            let valueDetail = '';
            let timeStr = '';

            if (isCompleted) {
                statusClass = 'passed';
                statusIcon = '<span class="material-symbols-outlined text-success fs-5">check_circle</span>';
                statusBadge = '<span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1 small fw-semibold" style="font-size: 0.75rem;">Done</span>';
                const valMpa = (t.max_mpa !== null && t.max_mpa !== undefined) ? t.max_mpa : (t.mpa !== null && t.mpa !== undefined ? t.mpa : 0);
                valueDetail = `<div class="fw-bold text-dark small mt-1" style="font-size: 0.75rem;">${valMpa.toFixed(3)} MPA</div>`;

                if (t.datetime) {
                    const dt = new Date(t.datetime);
                    timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                }
            } else {
                statusClass = 'pending';
                statusIcon = '<span class="material-symbols-outlined text-secondary fs-5" style="opacity: 0.4;">radio_button_unchecked</span>';
                statusBadge = '<span class="badge bg-light text-secondary border px-2 py-1 small" style="font-size: 0.75rem;">Pending</span>';
                valueDetail = '<div class="text-muted small mt-1" style="font-size: 0.75rem;">-- MPA</div>';
            }

            col.innerHTML = `
                <div class="card h-100 test-card p-2 text-center position-relative ${statusClass} ${isActive ? 'active' : ''}" data-test-id="${t.id}">
                    ${isActive ? '<span class="badge bg-primary position-absolute top-0 start-50 translate-middle px-2 py-0 shadow-sm" style="font-size: 0.6rem; letter-spacing: 0.5px; border-radius: 999px;">CURRENT</span>' : ''}
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-bold small text-dark">#${t.test_number} Test</span>
                        ${statusIcon}
                    </div>
                    <div class="d-flex flex-column align-items-center justify-content-center py-1">
                        ${statusBadge}
                        ${valueDetail}
                        ${timeStr ? `<small class="text-secondary text-truncate w-100 mt-1" style="font-size: 0.68rem;" title="${timeStr}">${timeStr}</small>` : `<small class="text-secondary text-truncate w-100 mt-1" style="font-size: 0.68rem;">--:--:--</small>`}
                    </div>
                </div>`;

            const cardEl = col.querySelector('.test-card');
            cardEl.addEventListener('click', () => {
                selectTest(t.id, true);
            });

            testCardsContainer.appendChild(col);
        });
    }

    // --- Select a Specific Test ---
    async function selectTest(testId, informBackend = true) {
        currentSelectedTestId = testId;
        if (saveBtn) saveBtn.disabled = !testId;

        renderCards();

        if (testId && informBackend) {
            const proofId = proofSelect ? proofSelect.value : null;
            if (proofId) {
                try {
                    const res = await fetch(`/api/proofs/${proofId}/tests/${testId}`);
                    const result = await res.json();
                    console.log('Current test selected on backend:', result);
                } catch (e) {
                    console.error('Failed to set current test id on backend', e);
                }
            }
        }
    }

    // --- Load Tests for Selected Proof ---
    async function loadTests(selectTestId = null) {
        const proofId = proofSelect ? proofSelect.value : null;
        if (!proofId) {
            currentSelectedTestId = null;
            currentTests = [];
            renderCards();
            if (saveBtn) saveBtn.disabled = true;
            return [];
        }

        try {
            const res = await fetch(`/api/proofs/${proofId}/tests`);
            const tests = await res.json();
            currentTests = tests || [];

            // Determine which test to auto-select
            let targetTestId = null;
            if (selectTestId && currentTests.some(t => t.id === selectTestId)) {
                targetTestId = selectTestId;
            } else if (currentSelectedTestId && currentTests.some(t => t.id === currentSelectedTestId)) {
                targetTestId = currentSelectedTestId;
            } else {
                // Auto-select first empty/pending test, or first test if all are done
                const firstEmpty = currentTests.find(t => t.measurement_value === null || t.measurement_value === undefined);
                if (firstEmpty) {
                    targetTestId = firstEmpty.id;
                } else if (currentTests.length > 0) {
                    targetTestId = currentTests[0].id;
                }
            }

            await selectTest(targetTestId, true);
            return currentTests;
        } catch (e) {
            console.error('Failed to load tests', e);
            currentTests = [];
            renderCards();
            return [];
        }
    }

    // --- Load Proofs ---
    async function loadProofs(preserveSelection = false) {
        if (!proofSelect) return;
        const currentSelectedProof = preserveSelection ? proofSelect.value : null;
        try {
            const res = await fetch('/api/proofs');
            const proofs = await res.json();
            proofSelect.innerHTML = '<option value="">-- Select Proof --</option>';
            proofs.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = `Lot no : ${p.lot_no}`;
                proofSelect.appendChild(opt);
            });

            if (currentSelectedProof && proofs.some(p => String(p.id) === String(currentSelectedProof))) {
                proofSelect.value = currentSelectedProof;
            } else if (currentSelectedProof) {
                proofSelect.value = '';
                currentSelectedTestId = null;
                currentTests = [];
                renderCards();
                if (saveBtn) saveBtn.disabled = true;
            }
        } catch (e) {
            console.error('Failed to load proofs', e);
            throw e;
        }
    }

    // --- Save Test Measurement with Auto-Increment ---
    async function handleSaveTest() {
        const testId = currentSelectedTestId;
        if (!testId || isSaving) return;

        isSaving = true;
        if (saveBtn) saveBtn.disabled = true;

        try {
            // Find current test index before saving to determine the next test
            const currentIndex = currentTests.findIndex(t => t.id === testId);
            const nextTestId = currentIndex >= 0 && currentIndex < currentTests.length - 1
                ? currentTests[currentIndex + 1].id
                : null;

            const res = await fetch(`/api/tests/${testId}/measurement`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value: currentRelativeX })
            });
            const result = await res.json();

            if (result.status === 'success') {
                // Reset recorded values on backend
                await fetch('/api/test/reset', { method: 'GET' });

                if (msg) {
                    const nextNum = nextTestId ? currentTests[currentIndex + 1].test_number : null;
                    msg.textContent = nextTestId
                        ? `Saved measurement ${result.measurement_value.toFixed(3)}! Switching to Test #${nextNum}...`
                        : `Saved measurement ${result.measurement_value.toFixed(3)}! (All tests completed!)`;
                    msg.className = 'mt-2 text-center small fw-bold text-success';
                }

                // Reload tests and automatically select the next test
                await loadTests(nextTestId);
            } else {
                if (msg) {
                    msg.textContent = result.message || 'Failed to save.';
                    msg.className = 'mt-2 text-center small fw-bold text-danger';
                }
                if (saveBtn) saveBtn.disabled = false;
            }
        } catch (e) {
            if (msg) {
                msg.textContent = 'Network error saving measurement.';
                msg.className = 'mt-2 text-center small fw-bold text-danger';
            }
            if (saveBtn) saveBtn.disabled = false;
        } finally {
            isSaving = false;
        }

        setTimeout(() => {
            if (msg) msg.textContent = '';
        }, 3000);
    }

    // --- Event Listeners ---

    if (proofSelect) {
        proofSelect.addEventListener('change', async () => {
            currentSelectedTestId = null;
            await loadTests();
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', handleSaveTest);
    }

    if (setOriginBtn) {
        setOriginBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/test/set_origin', { method: 'POST' });
                const result = await response.json();
                if (result.status === 'success') {
                    if (msg) {
                        msg.textContent = 'Origin set successfully!';
                        msg.className = 'mt-2 text-center small fw-bold text-success';
                    }
                } else {
                    if (msg) {
                        msg.textContent = result.message || 'Failed to set origin.';
                        msg.className = 'mt-2 text-center small fw-bold text-danger';
                    }
                }
            } catch (e) {
                if (msg) {
                    msg.textContent = 'Error setting origin.';
                    msg.className = 'mt-2 text-center small fw-bold text-danger';
                }
            }
            setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/test/reset', { method: 'GET' });
                const result = await response.json();
                if (result.status === 'success') {
                    if (msg) {
                        msg.textContent = 'Recorded values reset successfully!';
                        msg.className = 'mt-2 text-center small fw-bold text-success';
                    }
                } else {
                    if (msg) {
                        msg.textContent = result.message || 'Failed to reset values.';
                        msg.className = 'mt-2 text-center small fw-bold text-danger';
                    }
                }
            } catch (e) {
                if (msg) {
                    msg.textContent = 'Error resetting values.';
                    msg.className = 'mt-2 text-center small fw-bold text-danger';
                }
            }
            setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
        });
    }

    if (refreshProofsBtn) {
        refreshProofsBtn.addEventListener('click', async () => {
            const refreshIcon = refreshProofsBtn.querySelector('.material-symbols-outlined');
            if (refreshIcon) refreshIcon.classList.add('spin');
            refreshProofsBtn.disabled = true;

            try {
                const currentSelectedProof = proofSelect ? proofSelect.value : null;
                const currentTargetTest = currentSelectedTestId;

                await loadProofs(true);

                if (currentSelectedProof && proofSelect && proofSelect.value === currentSelectedProof) {
                    await loadTests(currentTargetTest);
                } else {
                    await loadTests();
                }

                if (msg) {
                    msg.textContent = 'Proofs refreshed successfully!';
                    msg.className = 'mt-2 text-center small fw-bold text-success';
                }
            } catch (e) {
                if (msg) {
                    msg.textContent = 'Failed to refresh proofs.';
                    msg.className = 'mt-2 text-center small fw-bold text-danger';
                }
            } finally {
                if (refreshIcon) refreshIcon.classList.remove('spin');
                refreshProofsBtn.disabled = false;
                setTimeout(() => {
                    if (msg) msg.textContent = '';
                }, 3000);
            }
        });
    }

    // --- WebSocket for live measurements ---
    const wsUrl = `ws://${window.location.host}/ws/measurements`;

    function formatLookup(lookup, isNegative) {
        if (!lookup) return "";
        let sign = isNegative ? "-" : "";
        if (lookup.inch === "0 inch") sign = "";
        return sign + lookup.inch;
    }

    function connectMeasurementWS() {
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Store current relative X globally for the save button
                currentRelativeX = data.relative_x;

                const current_mm = (data.relative_x * 1000);

                if (recValMaxPosInch) {
                    recValMaxPosInch.textContent = data.rec_pos_lookup ? (data.rec_pos_lookup.inch || '0 inch') : '0 inch';
                }
                if (recValMaxPosPress) {
                    const mpaVal = data.rec_pos_lookup && data.rec_pos_lookup.mpa ? data.rec_pos_lookup.mpa : 0;
                    recValMaxPosPress.textContent = `MPA: ${mpaVal.toFixed(3)}`;
                }

                if (valCurrentInch) {
                    valCurrentInch.textContent = formatLookup(data.current_lookup, current_mm < 0);
                }
                if (valCurrentPress) {
                    const currentMpa = data.current_lookup && data.current_lookup.mpa ? data.current_lookup.mpa : 0;
                    valCurrentPress.textContent = `MPA: ${currentMpa.toFixed(3)}`;
                }
            } catch (e) {
                console.error('Error parsing measurement websocket data', e);
            }
        };

        ws.onclose = () => {
            setTimeout(connectMeasurementWS, 2000);
        };
    }

    // --- Initial Initialization ---
    loadProofs();
    connectMeasurementWS();
});
