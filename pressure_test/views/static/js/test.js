const proofSelect = document.getElementById('proofSelect');
const testSelect = document.getElementById('testSelect');
const saveBtn = document.getElementById('saveMeasurementBtn');
const msg = document.getElementById('measureMessage');
const updateSizeBtn = document.getElementById('updateSizeBtn');
const setOriginBtn = document.getElementById('setOriginBtn');
let currentRelativeX = 0.0;


async function getTest(preserveTestSelection = false) {
    const proofId = proofSelect.value;
    const currentTestVal = preserveTestSelection && testSelect ? testSelect.value : null;
    testSelect.innerHTML = '<option value="">-- Select Test --</option>';
    saveBtn.disabled = true;

    if (proofId) {
        testSelect.disabled = false;
        try {
            const res = await fetch(`/api/proofs/${proofId}/tests`);
            const tests = await res.json();
            tests.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.id;
                let text = `Test ${t.test_number}`;
                if (t.measurement_value !== null) {
                    text += ` (MPA: ${t.max_mpa})`;
                    if (t.datetime) {
                        const dt = new Date(t.datetime).toLocaleString();
                        text += ` - ${dt}`;
                    }
                } else {
                    text += ' (Empty)';
                }
                opt.textContent = text;
                testSelect.appendChild(opt);
            });

            if (currentTestVal && tests.some(t => String(t.id) === String(currentTestVal))) {
                testSelect.value = currentTestVal;
                saveBtn.disabled = false;
            }

            return tests;
        } catch (e) {
            console.error("Failed to load tests", e);
        }
    } else {
        testSelect.disabled = true;
    }
    return [];
}

async function saveTestResult(testSelect, proofSelect, msg, currentRelativeX) {
    const testId = testSelect.value;
    if (!testId) return;

    try {
        const res = await fetch(`/api/tests/${testId}/measurement`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: currentRelativeX })
        });
        const result = await res.json();

        if (result.status === 'success') {
            msg.textContent = `Saved measurement ${result.measurement_value.toFixed(3)} to Test!`;
            msg.className = 'mt-3 text-center small fw-bold text-success';
            await moveToNextTest(testId);
        } else {
            msg.textContent = result.message || 'Failed to save.';
            msg.className = 'mt-3 text-center small fw-bold text-danger';
        }
    } catch (e) {
        msg.textContent = 'Network error saving measurement.';
        msg.className = 'mt-3 text-center small fw-bold text-danger';
    }
    setTimeout(() => { msg.textContent = ''; }, 3000);
}

async function moveToNextTest(currentTestId) {
    // 1. Reset recorded max/current values on backend
    await fetch('/api/test/reset', { method: 'GET' });

    // 2. Reload tests dropdown with the newly saved values
    const tests = await getTest();

    // 3. Locate the test that was just completed
    const currentIndex = tests.findIndex(t => String(t.id) === String(currentTestId));

    // 4. Select the next test if available
    if (currentIndex !== -1 && currentIndex + 1 < tests.length) {
        const nextTest = tests[currentIndex + 1];
        testSelect.value = nextTest.id;
        testSelect.dispatchEvent(new Event('change'));
    } else {
        testSelect.value = '';
        saveBtn.disabled = true;
    }
}

document.addEventListener('DOMContentLoaded', () => {

    // --- Size and Origin Update ---

    if (setOriginBtn) {
        setOriginBtn.addEventListener('click', async () => {
            const response = await fetch('/api/test/set_origin', { method: 'POST' });
            const result = await response.json();
            const msg = document.getElementById('measureMessage');
            if (result.status === 'success') {
                msg.textContent = 'Origin set successfully!';
                msg.className = 'mt-3 text-center small fw-bold text-success';
            } else {
                msg.textContent = result.message || 'Failed to set origin.';
                msg.className = 'mt-3 text-center small fw-bold text-danger';
            }
            setTimeout(() => { msg.textContent = ''; }, 3000);
        });
    }

    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            const response = await fetch('/api/test/reset', { method: 'GET' });
            const result = await response.json();
            const msg = document.getElementById('measureMessage');
            if (result.status === 'success') {
                msg.textContent = 'Recorded values reset successfully!';
                msg.className = 'mt-3 text-center small fw-bold text-success';
            } else {
                msg.textContent = result.message || 'Failed to reset values.';
                msg.className = 'mt-3 text-center small fw-bold text-danger';
            }
            setTimeout(() => { msg.textContent = ''; }, 3000);
        });
    }

    // --- Proof & Test Selection ---


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
                if (testSelect) {
                    testSelect.innerHTML = '<option value="">-- Select Test --</option>';
                    testSelect.disabled = true;
                }
                if (saveBtn) saveBtn.disabled = true;
            }
        } catch (e) {
            console.error("Failed to load proofs", e);
            throw e;
        }
    }

    const refreshProofsBtn = document.getElementById('refreshProofsBtn');
    if (refreshProofsBtn) {
        refreshProofsBtn.addEventListener('click', async () => {
            const refreshIcon = refreshProofsBtn.querySelector('.material-symbols-outlined');
            if (refreshIcon) refreshIcon.classList.add('spin');
            refreshProofsBtn.disabled = true;

            try {
                const currentSelectedProof = proofSelect ? proofSelect.value : null;
                await loadProofs(true);
                if (currentSelectedProof && proofSelect && proofSelect.value === currentSelectedProof) {
                    await getTest(true);
                }
                if (msg) {
                    msg.textContent = 'Proofs refreshed successfully!';
                    msg.className = 'mt-3 text-center small fw-bold text-success';
                }
            } catch (e) {
                if (msg) {
                    msg.textContent = 'Failed to refresh proofs.';
                    msg.className = 'mt-3 text-center small fw-bold text-danger';
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

    if (proofSelect) {
        proofSelect.addEventListener('change', async () => {
            await getTest();
        });
    }

    if (testSelect) {
        testSelect.addEventListener('change', async () => {
            saveBtn.disabled = !testSelect.value;
            const proofId = proofSelect.value;
            const testId = testSelect.value;
            if (proofId && testId) {
                try {
                    const res = await fetch(`/api/proofs/${proofId}/tests/${testId}`);
                    const test = await res.json();
                    console.log(test);
                } catch (e) {
                    console.error("Failed to fetch test details", e);
                }
            }
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            await saveTestResult(testSelect, proofSelect, msg, currentRelativeX);
        });
    }

    loadProofs();

    // --- Websocket for measurements ---
    const wsUrl = `ws://${window.location.host}/ws/measurements`;
    const valCurrent = document.getElementById('val-current');
    const valMaxPos = document.getElementById('val-max-pos');
    const valCurrentInch = document.getElementById('val-current-inch');
    const valMaxPosInch = document.getElementById('val-max-pos-inch');
    const valCurrentPress = document.getElementById('val-current-press');
    const valMaxPosPress = document.getElementById('val-max-pos-press');
    const recValMaxPos = document.getElementById('rec-val-max-pos');
    const recValMaxPosInch = document.getElementById('rec-val-max-pos-inch');
    const recValMaxPosPress = document.getElementById('rec-val-max-pos-press');

    function formatLookup(lookup, isNegative) {
        if (!lookup) return "";
        let sign = isNegative ? "-" : "";
        if (lookup.inch === "0 inch") sign = "";
        return sign + lookup.inch;
    }

    function connectMeasurementWS() {
        if (!valCurrent) return; // Not on test page
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // Store current relative X globally for the save button
            currentRelativeX = data.relative_x;

            const current_mm = (data.relative_x * 1000);
            const max_pos_mm = (data.max_positive_x * 1000);
            const rec_pos_mm = (data.rec_positive_x * 1000);

            valCurrent.textContent = `${current_mm > 0 ? '+' : ''}${current_mm.toFixed(1)} mm`;
            valMaxPos.textContent = `+${max_pos_mm.toFixed(1)} mm`;

            recValMaxPos.textContent = `+${(rec_pos_mm).toFixed(1)} mm`;

            recValMaxPosInch.textContent = data.rec_pos_lookup.inch || '0 inch';
            recValMaxPosPress.textContent = `PSI: ${(data.rec_pos_lookup.psi || 0).toFixed(3)} | MPA: ${(data.rec_pos_lookup.mpa || 0).toFixed(3)}`;

            valCurrentInch.textContent = formatLookup(data.current_lookup, current_mm < 0);
            valMaxPosInch.textContent = formatLookup(data.max_pos_lookup, false);

            valCurrentPress.textContent = `PSI: ${data.current_lookup.psi.toFixed(3)} | MPA: ${data.current_lookup.mpa.toFixed(3)}`;
            valMaxPosPress.textContent = `PSI: ${data.max_pos_lookup.psi.toFixed(3)} | MPA: ${data.max_pos_lookup.mpa.toFixed(3)}`;
        };

        ws.onclose = () => {
            setTimeout(connectMeasurementWS, 2000);
        };
    }
    connectMeasurementWS();
});
