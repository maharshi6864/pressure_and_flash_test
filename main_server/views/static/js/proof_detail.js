let currentProof = null;
const proofId = window.PROOF_ID || parseInt(window.location.pathname.split('/').filter(Boolean).pop(), 10);
const token = localStorage.getItem("token");

function formatIsoForInput(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return '';
    const pad = n => n < 10 ? '0' + n : n;
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function loadProofDetails() {
    try {
        const res = await fetch(`/api/proofs/${proofId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Failed to fetch proof details");
        currentProof = await res.json();
        renderProofDetails(currentProof);
    } catch (error) {
        console.error(error);
        document.getElementById("lotDetailsContainer").innerHTML = '<div class="col-12 text-danger">Error loading proof details.</div>';
        document.getElementById("flashTestsTbody").innerHTML = '<tr><td colspan="5" class="text-danger text-center py-3">Error loading flash tests.</td></tr>';
        document.getElementById("pressureTestsTbody").innerHTML = '<tr><td colspan="6" class="text-danger text-center py-3">Error loading pressure tests.</td></tr>';
    }
}

function renderProofDetails(proof) {
    document.getElementById("proofLotNoTitle").innerText = proof.lot_no || `Proof #${proof.id}`;

    const detType = proof.detonator_type || "356_LZ";
    let badgeHtml = '';
    if (detType === "135_LZY") {
        badgeHtml = '<span class="badge det-badge-135 fs-6 px-3 py-1">Detonator 135 mg LZY</span>';
    } else if (detType === "RGM") {
        badgeHtml = '<span class="badge det-badge-rgm fs-6 px-3 py-1">Detonator RGM</span>';
    } else {
        badgeHtml = '<span class="badge det-badge-356 fs-6 px-3 py-1">Detonator 356 mg LZ</span>';
    }
    document.getElementById("detonatorTypeBadge").innerHTML = badgeHtml;

    // Render Parameters
    document.getElementById("lotDetailsContainer").innerHTML = `
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="text-muted small">Proof ID</div>
            <div class="fw-semibold">#${proof.id}</div>
        </div>
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="text-muted small">1. Lot No.</div>
            <div class="fw-bold text-primary">${proof.lot_no || '-'}</div>
        </div>
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="text-muted small">2. Sample Received on</div>
            <div class="fw-semibold">${proof.sample_received_on || proof.slip_date || '-'}</div>
        </div>
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="text-muted small">3. Sample Size</div>
            <div class="fw-semibold">${proof.sample_size != null ? proof.sample_size : '-'} Nos</div>
        </div>
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="text-muted small">4. Proof Results</div>
            <div class="fw-bold text-success">${proof.proof_results || proof.result_no || '-'}</div>
        </div>
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="text-muted small">Date of Proof</div>
            <div class="fw-semibold">${proof.date_of_proof || proof.date || '-'}</div>
        </div>
        ${detType === '356_LZ' ? `
        <div class="col-sm-12 col-md-6">
            <div class="text-muted small">Schedule / Test Programme Ref</div>
            <div class="fw-semibold">${proof.schedule_ref || proof.schedule_test_programme_ref || 'CQA/Proof Schedule/Det/1/11'}</div>
        </div>
        ` : ''}
    `;

    // Render Test Observations Table
    const obsTbody = document.getElementById("testObsTbody");
    let obsRowsHtml = '';

    // Dynamic Flash Observation text
    let dynamicFlashObs = proof.flash_test_obs || '';
    const flashTests = (proof.flash_tests || []).sort((a, b) => (a.test_number || 0) - (b.test_number || 0));
    if (!dynamicFlashObs && flashTests.length > 0) {
        const allOk = flashTests.every(t => t.flash_detected === true);
        const failedCount = flashTests.filter(t => t.flash_detected === false).length;
        dynamicFlashObs = allOk ? "All samples satisfactory." : (failedCount > 0 ? `${failedCount} sample(s) failed.` : "Tests recorded.");
    }

    if (detType === "356_LZ") {
        obsRowsHtml += `
            <tr>
                <td class="ps-3 fw-semibold">01. Drop Test</td>
                <td>${proof.drop_test_sample_size != null ? proof.drop_test_sample_size + ' Nos.' : '20 Nos.'}</td>
                <td>${proof.drop_test_date || '-'}</td>
                <td>${proof.drop_test_obs || 'All Samples Sustained.'}</td>
                <td class="pe-3">${proof.drop_test_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">02. Sensitivity Test</td>
                <td>${proof.sensitivity_test_sample_size != null ? proof.sensitivity_test_sample_size + ' Nos.' : '10 Nos.'}</td>
                <td>${proof.sensitivity_test_date || '-'}</td>
                <td>${proof.sensitivity_test_obs || 'All Samples Functioned.'}</td>
                <td class="pe-3">${proof.sensitivity_test_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">03. Flash Delivery Test</td>
                <td>${proof.flash_test_sample_size != null ? proof.flash_test_sample_size + ' Nos.' : `${proof.sample_size || 10} Nos.`}</td>
                <td>${proof.flash_test_date || proof.date_of_proof || '-'}</td>
                <td>${dynamicFlashObs || 'Satisfactory.'}</td>
                <td class="pe-3">${proof.flash_test_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">04. Pressure Bar Test</td>
                <td>${proof.pressure_test_sample_size != null ? proof.pressure_test_sample_size + ' Nos.' : `${proof.sample_size || 10} Nos.`}</td>
                <td>${proof.pressure_test_date || proof.date_of_proof || '-'}</td>
                <td>${proof.pressure_test_obs || '-'}</td>
                <td class="pe-3">${proof.pressure_test_remarks || '-'}</td>
            </tr>
        `;
    } else if (detType === "135_LZY") {
        obsRowsHtml += `
            <tr>
                <td class="ps-3 fw-semibold">01. Drop Test</td>
                <td>${proof.drop_test_sample_size != null ? proof.drop_test_sample_size + ' Nos.' : '20 Nos.'}</td>
                <td>${proof.drop_test_date || '-'}</td>
                <td>${proof.drop_test_obs || 'All Samples Sustained.'}</td>
                <td class="pe-3">${proof.drop_test_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">02. Sensitivity Test</td>
                <td>${proof.sensitivity_test_sample_size != null ? proof.sensitivity_test_sample_size + ' Nos.' : '13 Nos.'}</td>
                <td>${proof.sensitivity_test_date || '-'}</td>
                <td>${proof.sensitivity_test_obs || 'All Samples Functioned.'}</td>
                <td class="pe-3">${proof.sensitivity_test_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">03. Pressure Bar Test</td>
                <td>${proof.pressure_test_sample_size != null ? proof.pressure_test_sample_size + ' Nos.' : `${proof.sample_size || 13} Nos.`}</td>
                <td>${proof.pressure_test_date || proof.date_of_proof || '-'}</td>
                <td>${proof.pressure_test_obs || '-'}</td>
                <td class="pe-3">${proof.pressure_test_remarks || '-'}</td>
            </tr>
        `;
    } else if (detType === "RGM") {
        obsRowsHtml += `
            <tr>
                <td class="ps-3 fw-semibold">1. Sensitivity Test at upper limit</td>
                <td>${proof.sens_upper_sample_size != null ? proof.sens_upper_sample_size + ' Nos.' : '-'}</td>
                <td>${proof.sens_upper_date || '-'}</td>
                <td>${proof.sens_upper_obs || 'Satisfactory.'}</td>
                <td class="pe-3">${proof.sens_upper_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">2. Sensitivity Test at lower limit</td>
                <td>${proof.sens_lower_sample_size != null ? proof.sens_lower_sample_size + ' Nos.' : '-'}</td>
                <td>${proof.sens_lower_date || '-'}</td>
                <td>${proof.sens_lower_obs || 'Satisfactory.'}</td>
                <td class="pe-3">${proof.sens_lower_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">3. Drop Test</td>
                <td>${proof.drop_test_sample_size != null ? proof.drop_test_sample_size + ' Nos.' : '-'}</td>
                <td>${proof.drop_test_date || '-'}</td>
                <td>${proof.drop_test_obs || 'All Samples Sustained.'}</td>
                <td class="pe-3">${proof.drop_test_remarks || '-'}</td>
            </tr>
            <tr>
                <td class="ps-3 fw-semibold">4. Pressure Bar Test</td>
                <td>${proof.pressure_test_sample_size != null ? proof.pressure_test_sample_size + ' Nos.' : `${proof.sample_size || 10} Nos.`}</td>
                <td>${proof.pressure_test_date || proof.date_of_proof || '-'}</td>
                <td>${proof.pressure_test_obs || '-'}</td>
                <td class="pe-3">${proof.pressure_test_remarks || '-'}</td>
            </tr>
        `;
    }
    obsTbody.innerHTML = obsRowsHtml;

    // Visibility of Flash Tests column
    const flashCol = document.getElementById("flashTestsCol");
    const pressureCol = document.getElementById("pressureTestsCol");
    if (detType === "356_LZ" || flashTests.length > 0) {
        flashCol.classList.remove("d-none");
        pressureCol.className = "col-lg-6";
    } else {
        flashCol.classList.add("d-none");
        pressureCol.className = "col-lg-12";
    }

    // Render Flash Tests Table
    const flashTbody = document.getElementById("flashTestsTbody");
    document.getElementById("flashTestCountBadge").innerText = `${flashTests.length} Tests`;

    if (flashTests.length > 0) {
        flashTbody.innerHTML = flashTests.map((t, idx) => {
            const dtStr = t.date_time ? new Date(t.date_time).toLocaleString() : (t.flash_detected_time ? new Date(t.flash_detected_time).toLocaleString() : '-');
            const imgPath = t.flash_detected_image_path || t.flash_image_path || t.flash_detection_image_path;
            const resultBadge = t.flash_detected === true
                ? '<span class="badge bg-success d-inline-flex align-items-center gap-1"><span class="material-symbols-outlined" style="font-size: 14px;">check_circle</span> Flash Detected</span>'
                : (t.flash_detected === false
                    ? '<span class="badge bg-danger d-inline-flex align-items-center gap-1"><span class="material-symbols-outlined" style="font-size: 14px;">cancel</span> No Flash</span>'
                    : '<span class="badge bg-secondary">Pending</span>');

            return `
                <tr>
                    <td class="ps-3 fw-bold">${t.test_number || (idx + 1)}</td>
                    <td>${resultBadge}</td>
                    <td class="small text-muted text-nowrap">${dtStr}</td>
                    <td>
                        ${imgPath ? `
                            <button type="button" class="btn btn-sm btn-outline-info py-0 px-2 d-inline-flex align-items-center gap-1 preview-img-btn" 
                                data-src="${imgPath}" data-title="Flash Test #${t.test_number || (idx + 1)} Image" data-info="Captured at: ${dtStr}">
                                <span class="material-symbols-outlined" style="font-size: 16px;">image</span> View
                            </button>
                        ` : '<span class="text-muted small">No image</span>'}
                    </td>
                    <td class="text-end pe-3">
                        <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2 edit-flash-btn" 
                            data-id="${t.id}" data-num="${t.test_number || (idx + 1)}" data-detected="${t.flash_detected}" data-dt="${t.date_time || t.flash_detected_time || ''}">
                            <span class="material-symbols-outlined" style="font-size: 16px;">edit</span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } else {
        flashTbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center py-4">No flash tests recorded for this proof.</td></tr>';
    }

    // Render Pressure Tests Table
    const pressureTbody = document.getElementById("pressureTestsTbody");
    const pressureTests = (proof.pressure_tests || []).sort((a, b) => (a.test_number || 0) - (b.test_number || 0));
    document.getElementById("pressureTestCountBadge").innerText = `${pressureTests.length} Tests`;

    if (pressureTests.length > 0) {
        pressureTbody.innerHTML = pressureTests.map((t, idx) => {
            const dtStr = t.date_time ? new Date(t.date_time).toLocaleString() : (t.datetime ? new Date(t.datetime).toLocaleString() : '-');
            const mpaBadge = t.mpa != null
                ? `<span class="badge bg-primary fw-bold">${Number(t.mpa).toFixed(2)} MPA</span>`
                : '<span class="badge bg-secondary">-</span>';

            return `
                <tr>
                    <td class="ps-3 fw-bold">${t.test_number || (idx + 1)}</td>
                    <td class="fw-semibold">${t.inch != null && t.inch !== '' ? t.inch : '<span class="text-muted">-</span>'}</td>
                    <td>${mpaBadge}</td>
                    <td class="small text-muted text-nowrap">${dtStr}</td>
                    <td class="text-end pe-3">
                        <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-2 edit-pressure-btn" 
                            data-id="${t.id}" data-num="${t.test_number || (idx + 1)}" data-inch="${t.inch || ''}" 
                            data-mpa="${t.mpa != null ? t.mpa : ''}" 
                            data-mm="${t.mm != null ? t.mm : ''}" data-origin="${t.origin_value != null ? t.origin_value : ''}" 
                            data-dt="${t.date_time || t.datetime || ''}">
                            <span class="material-symbols-outlined" style="font-size: 16px;">edit</span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } else {
        pressureTbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center py-4">No pressure tests recorded for this proof.</td></tr>';
    }

    // Render Pressure Grid & Statistical Formulas
    renderPressureCalculations(pressureTests, detType, proof);

    // Attach event listeners
    attachEventListeners();
}

function renderPressureCalculations(pressureTests, detType, proof) {
    const cardEl = document.getElementById("pressureCalculationCard");
    if (detType === "RGM") {
        if (cardEl) cardEl.classList.add("d-none");
        return;
    } else {
        if (cardEl) cardEl.classList.remove("d-none");
    }

    const gridEl = document.getElementById("pressureGridDisplay");
    const summaryEl = document.getElementById("pressureCalculationsSummary");
    const constantVal = (detType === "135_LZY") ? 80.00 : 125.00;

    const totalBoxes = Math.max(
        pressureTests ? pressureTests.length : 0,
        (proof && proof.pressure_test_sample_size) || 0,
        10
    );

    let pressures = [];
    let gridHtml = '';
    for (let i = 0; i < totalBoxes; i++) {
        const t = pressureTests && pressureTests[i];
        const hasVal = t && t.mpa != null && !isNaN(parseFloat(t.mpa));
        const numVal = hasVal ? parseFloat(t.mpa) : null;
        if (numVal !== null) {
            pressures.push(numVal);
        }
        const displayVal = hasVal ? numVal.toFixed(3) : '-';
        gridHtml += `
            <div class="pressure-box-cell">
                <div class="text-muted" style="font-size: 10px;">#${i + 1}</div>
                <div class="fw-bold ${hasVal ? 'text-primary' : 'text-muted'}">${displayVal}</div>
            </div>
        `;
    }
    gridEl.innerHTML = gridHtml;

    if (pressures.length > 0) {
        let sum = pressures.reduce((a, b) => a + b, 0);
        let mean = sum / pressures.length;
        // Mean Deviation (Md): Average of absolute differences from the mean
        let md = pressures.reduce((a, b) => a + Math.abs(b - mean), 0) / pressures.length;

        let i_val = 3.5 * md + constantVal;
        let ii_val = 2.5 * md + constantVal;

        let allMoreCount = pressures.filter(p => p >= constantVal).length;
        let anyLessCount = pressures.filter(p => p < constantVal).length;

        const moreText = (allMoreCount === pressures.length && pressures.length > 0) ? 'All' : `${allMoreCount}`;
        const lessText = (anyLessCount === 0) ? 'No' : `${anyLessCount}`;

        const isEq1 = Math.abs(mean - i_val) < 0.001;
        const isMoreEq1 = mean > i_val;
        const isBetween = (mean <= i_val && mean >= ii_val && !isEq1);
        const isLessEq2 = mean < ii_val;

        summaryEl.innerHTML = `
            <div class="d-flex justify-content-between border-bottom pb-1 mb-2">
                <span>Mean Pressure: <strong class="text-primary fs-6">${mean.toFixed(3)} MPA</strong></span>
                <span>Mean Deviation (Md): <strong class="text-secondary">${md.toFixed(3)}</strong></span>
            </div>
            <div class="row g-2 mb-2">
                <div class="col-6 bg-light p-2 rounded">
                    <span class="text-muted d-block" style="font-size: 11px;">(I) 3.5 &times; Md + ${constantVal.toFixed(2)} =</span>
                    <strong class="text-dark">${i_val.toFixed(3)}</strong>
                </div>
                <div class="col-6 bg-light p-2 rounded">
                    <span class="text-muted d-block" style="font-size: 11px;">(II) 2.5 &times; Md + ${constantVal.toFixed(2)} =</span>
                    <strong class="text-dark">${ii_val.toFixed(3)}</strong>
                </div>
            </div>
            <div class="p-2 border rounded bg-white">
                <div class="fw-bold mb-1">Mean Pressure is:</div>
                <div class="${isEq1 ? 'fw-bold text-success' : 'text-muted'}">${isEq1 ? '&#10003;' : '&bull;'} Equal to the figure of (I)</div>
                <div class="${isMoreEq1 ? 'fw-bold text-success' : 'text-muted'}">${isMoreEq1 ? '&#10003;' : '&bull;'} More than the figure of (I)</div>
                <div class="${isBetween ? 'fw-bold text-success' : 'text-muted'}">${isBetween ? '&#10003;' : '&bull;'} Between the figure of (I) &amp; (II)</div>
                <div class="${isLessEq2 ? 'fw-bold text-danger' : 'text-muted'}">${isLessEq2 ? '&#10003;' : '&bull;'} Less than the figure of (II)</div>
            </div>
            <div class="mt-2 text-dark" style="font-size: 11.5px; line-height: 1.6;">
                <div>&bull; -- <strong>${moreText}</strong> -- Detonators shown Pressure more than the minimum specified pressure (${constantVal.toFixed(2)} MPA).</div>
                <div>&bull; -- <strong>${lessText}</strong> -- Detonators shown Pressure less than the minimum specified Pressure.</div>
            </div>
        `;
    } else {
        summaryEl.innerHTML = '<div class="text-muted">Awaiting pressure test recordings from machine...</div>';
    }
}

function attachEventListeners() {
    // Image Lightbox
    document.querySelectorAll('.preview-img-btn').forEach(btn => {
        btn.onclick = () => {
            const src = btn.getAttribute('data-src');
            const title = btn.getAttribute('data-title');
            const info = btn.getAttribute('data-info');
            document.getElementById('lightboxImg').src = src;
            document.getElementById('lightboxTitle').innerText = title || 'Flash Image';
            document.getElementById('lightboxInfo').innerText = info || '';
            document.getElementById('lightboxOpenNewTab').href = src;
            new bootstrap.Modal(document.getElementById('imageLightboxModal')).show();
        };
    });

    // Edit Flash Test
    document.querySelectorAll('.edit-flash-btn').forEach(btn => {
        btn.onclick = () => {
            document.getElementById('edit_flash_test_id').value = btn.getAttribute('data-id');
            const testNum = btn.getAttribute('data-num');
            document.getElementById('edit_flash_test_num').innerText = testNum;
            document.getElementById('edit_flash_test_number').value = testNum;
            document.getElementById('edit_flash_detected').value = btn.getAttribute('data-detected') === 'true' ? 'true' : 'false';
            document.getElementById('edit_flash_datetime').value = formatIsoForInput(btn.getAttribute('data-dt'));
            document.getElementById('editFlashTestError').classList.add('d-none');
            new bootstrap.Modal(document.getElementById('editFlashTestModal')).show();
        };
    });

    // Edit Pressure Test
    document.querySelectorAll('.edit-pressure-btn').forEach(btn => {
        btn.onclick = () => {
            document.getElementById('edit_pressure_test_id').value = btn.getAttribute('data-id');
            const testNum = btn.getAttribute('data-num');
            document.getElementById('edit_pressure_test_num').innerText = testNum;
            document.getElementById('edit_pressure_test_number').value = testNum;
            document.getElementById('edit_pressure_inch').value = btn.getAttribute('data-inch');
            document.getElementById('edit_pressure_mpa').value = btn.getAttribute('data-mpa');
            document.getElementById('edit_pressure_mm').value = btn.getAttribute('data-mm');
            document.getElementById('edit_pressure_origin').value = btn.getAttribute('data-origin');
            document.getElementById('edit_pressure_datetime').value = formatIsoForInput(btn.getAttribute('data-dt'));
            document.getElementById('editPressureTestError').classList.add('d-none');
            new bootstrap.Modal(document.getElementById('editPressureTestModal')).show();
        };
    });
}

function openEditProofModal() {
    if (!currentProof) return;
    const detType = currentProof.detonator_type || "356_LZ";
    document.getElementById('edit_detonator_type').value = detType;
    document.getElementById('edit_lot_no').value = currentProof.lot_no || '';
    document.getElementById('edit_sample_received_on').value = currentProof.sample_received_on || currentProof.slip_date || '';
    document.getElementById('edit_sample_size').value = currentProof.sample_size != null ? currentProof.sample_size : '';
    document.getElementById('edit_proof_results').value = currentProof.proof_results || currentProof.result_no || '';
    document.getElementById('edit_date_of_proof').value = currentProof.date_of_proof || currentProof.date || '';
    document.getElementById('edit_schedule_ref').value = currentProof.schedule_ref || currentProof.schedule_test_programme_ref || 'CQA/Proof Schedule/Det/1/11';

    document.getElementById('edit_drop_test_sample_size').value = currentProof.drop_test_sample_size != null ? currentProof.drop_test_sample_size : '';
    document.getElementById('edit_drop_test_date').value = currentProof.drop_test_date || '';
    document.getElementById('edit_drop_test_obs').value = currentProof.drop_test_obs || '';
    document.getElementById('edit_drop_test_remarks').value = currentProof.drop_test_remarks || '';

    document.getElementById('edit_sensitivity_test_sample_size').value = currentProof.sensitivity_test_sample_size != null ? currentProof.sensitivity_test_sample_size : '';
    document.getElementById('edit_sensitivity_test_date').value = currentProof.sensitivity_test_date || '';
    document.getElementById('edit_sensitivity_test_obs').value = currentProof.sensitivity_test_obs || '';
    document.getElementById('edit_sensitivity_test_remarks').value = currentProof.sensitivity_test_remarks || '';

    document.getElementById('edit_flash_test_sample_size').value = currentProof.flash_test_sample_size != null ? currentProof.flash_test_sample_size : '';
    document.getElementById('edit_flash_test_date').value = currentProof.flash_test_date || '';
    document.getElementById('edit_flash_test_obs').value = currentProof.flash_test_obs || '';
    document.getElementById('edit_flash_test_remarks').value = currentProof.flash_test_remarks || '';

    document.getElementById('edit_pressure_test_sample_size').value = currentProof.pressure_test_sample_size != null ? currentProof.pressure_test_sample_size : '';
    document.getElementById('edit_pressure_test_date').value = currentProof.pressure_test_date || '';
    document.getElementById('edit_pressure_test_obs').value = currentProof.pressure_test_obs || '';
    document.getElementById('edit_pressure_test_remarks').value = currentProof.pressure_test_remarks || '';

    document.getElementById('edit_sens_upper_sample_size').value = currentProof.sens_upper_sample_size != null ? currentProof.sens_upper_sample_size : '';
    document.getElementById('edit_sens_upper_date').value = currentProof.sens_upper_date || '';
    document.getElementById('edit_sens_upper_obs').value = currentProof.sens_upper_obs || '';
    document.getElementById('edit_sens_upper_remarks').value = currentProof.sens_upper_remarks || '';

    document.getElementById('edit_sens_lower_sample_size').value = currentProof.sens_lower_sample_size != null ? currentProof.sens_lower_sample_size : '';
    document.getElementById('edit_sens_lower_date').value = currentProof.sens_lower_date || '';
    document.getElementById('edit_sens_lower_obs').value = currentProof.sens_lower_obs || '';
    document.getElementById('edit_sens_lower_remarks').value = currentProof.sens_lower_remarks || '';

    document.getElementById('edit_drop_test_sample_size_rgm').value = currentProof.drop_test_sample_size != null ? currentProof.drop_test_sample_size : '';
    document.getElementById('edit_drop_test_date_rgm').value = currentProof.drop_test_date || '';
    document.getElementById('edit_drop_test_obs_rgm').value = currentProof.drop_test_obs || '';
    document.getElementById('edit_drop_test_remarks_rgm').value = currentProof.drop_test_remarks || '';

    document.getElementById('edit_pressure_test_sample_size_rgm').value = currentProof.pressure_test_sample_size != null ? currentProof.pressure_test_sample_size : '';
    document.getElementById('edit_pressure_test_date_rgm').value = currentProof.pressure_test_date || '';
    document.getElementById('edit_pressure_test_obs_rgm').value = currentProof.pressure_test_obs || '';
    document.getElementById('edit_pressure_test_remarks_rgm').value = currentProof.pressure_test_remarks || '';

    toggleEditDetonatorFields(detType);
    document.getElementById('editProofError').classList.add('d-none');
    new bootstrap.Modal(document.getElementById('editProofModal')).show();
}

function toggleEditDetonatorFields(type) {
    const schedContainer = document.getElementById("edit_schedule_ref_container");
    const flashRow = document.getElementById("edit_flash_row");
    const pressureLabel = document.getElementById("edit_pressure_label");
    const standardTests = document.getElementById("edit_standard_tests");
    const rgmTests = document.getElementById("edit_rgm_tests");

    if (type === "356_LZ") {
        if (schedContainer) schedContainer.classList.remove("d-none");
        if (flashRow) flashRow.classList.remove("d-none");
        if (pressureLabel) pressureLabel.innerText = "04. Pressure Bar Test";
        if (standardTests) standardTests.classList.remove("d-none");
        if (rgmTests) rgmTests.classList.add("d-none");
    } else if (type === "135_LZY") {
        if (schedContainer) schedContainer.classList.add("d-none");
        if (flashRow) flashRow.classList.add("d-none");
        if (pressureLabel) pressureLabel.innerText = "03. Pressure Bar Test";
        if (standardTests) standardTests.classList.remove("d-none");
        if (rgmTests) rgmTests.classList.add("d-none");
    } else if (type === "RGM") {
        if (schedContainer) schedContainer.classList.add("d-none");
        if (standardTests) standardTests.classList.add("d-none");
        if (rgmTests) rgmTests.classList.remove("d-none");
    }
}

// Pressure Lookup Table for auto-mapping Inch <-> MPA
const INCH_LOOKUP = {
    "3": {"inch": "3/32", "mpa": 10.316},
    "4": {"inch": "4/32", "mpa": 12.741},
    "5": {"inch": "5/32", "mpa": 15.135},
    "6": {"inch": "6/32", "mpa": 17.528},
    "7": {"inch": "7/32", "mpa": 19.922},
    "8": {"inch": "8/32", "mpa": 22.393},
    "9": {"inch": "9/32", "mpa": 24.787},
    "10": {"inch": "10/32", "mpa": 27.258},
    "11": {"inch": "11/32", "mpa": 29.652},
    "12": {"inch": "12/32", "mpa": 32.046},
    "13": {"inch": "13/32", "mpa": 34.44},
    "14": {"inch": "14/32", "mpa": 36.911},
    "15": {"inch": "15/32", "mpa": 39.227},
    "16": {"inch": "16/32", "mpa": 41.694},
    "17": {"inch": "17/32", "mpa": 44.092},
    "18": {"inch": "18/32", "mpa": 46.563},
    "19": {"inch": "19/32", "mpa": 48.88},
    "20": {"inch": "20/32", "mpa": 51.351},
    "21": {"inch": "21/32", "mpa": 53.745},
    "22": {"inch": "22/32", "mpa": 56.138},
    "23": {"inch": "23/32", "mpa": 58.532},
    "24": {"inch": "24/32", "mpa": 61.003},
    "25": {"inch": "25/32", "mpa": 63.397},
    "26": {"inch": "26/32", "mpa": 65.791},
    "27": {"inch": "27/32", "mpa": 68.185},
    "28": {"inch": "28/32", "mpa": 70.656},
    "29": {"inch": "29/32", "mpa": 73.05},
    "30": {"inch": "30/32", "mpa": 75.443},
    "31": {"inch": "31/32", "mpa": 77.837},
    "32": {"inch": "1", "mpa": 80.308},
    "33": {"inch": "1-1/32", "mpa": 82.703},
    "34": {"inch": "1-2/32", "mpa": 85.174},
    "35": {"inch": "1-3/32", "mpa": 87.567},
    "36": {"inch": "1-4/32", "mpa": 89.961},
    "37": {"inch": "1-5/32", "mpa": 92.355},
    "38": {"inch": "1-6/32", "mpa": 94.826},
    "39": {"inch": "1-7/32", "mpa": 97.22},
    "40": {"inch": "1-8/32", "mpa": 99.614},
    "41": {"inch": "1-9/32", "mpa": 102.008},
    "42": {"inch": "1-10/32", "mpa": 104.479},
    "43": {"inch": "1-11/32", "mpa": 106.872},
    "44": {"inch": "1-12/32", "mpa": 109.266},
    "45": {"inch": "1-13/32", "mpa": 111.66},
    "46": {"inch": "1-14/32", "mpa": 114.131},
    "47": {"inch": "1-15/32", "mpa": 116.525},
    "48": {"inch": "1-16/32", "mpa": 118.919},
    "49": {"inch": "1-17/32", "mpa": 121.313},
    "50": {"inch": "1-18/32", "mpa": 123.784},
    "51": {"inch": "1-19/32", "mpa": 126.177},
    "52": {"inch": "1-20/32", "mpa": 128.571},
    "53": {"inch": "1-21/32", "mpa": 131.042},
    "54": {"inch": "1-22/32", "mpa": 133.436},
    "55": {"inch": "1-23/32", "mpa": 135.83},
    "56": {"inch": "1-24/32", "mpa": 138.124},
    "57": {"inch": "1-25/32", "mpa": 140.618},
    "58": {"inch": "1-26/32", "mpa": 143.089},
    "59": {"inch": "1-27/32", "mpa": 145.482},
    "60": {"inch": "1-28/32", "mpa": 147.876},
    "61": {"inch": "1-29/32", "mpa": 150.27},
    "62": {"inch": "1-30/32", "mpa": 152.741},
    "63": {"inch": "1-31/32", "mpa": 155.135},
    "64": {"inch": "2", "mpa": 157.529},
    "65": {"inch": "2-1/32", "mpa": 159.923},
    "66": {"inch": "2-2/32", "mpa": 182.394},
    "67": {"inch": "2-3/32", "mpa": 164.787},
    "68": {"inch": "2-4/32", "mpa": 167.181},
    "69": {"inch": "2-5/32", "mpa": 169.575},
    "70": {"inch": "2-6/32", "mpa": 172.046},
    "71": {"inch": "2-7/32", "mpa": 174.44},
    "72": {"inch": "2-8/32", "mpa": 176.834},
    "73": {"inch": "2-9/32", "mpa": 179.228},
    "74": {"inch": "2-10/32", "mpa": 181.699},
    "75": {"inch": "2-11/32", "mpa": 184.093},
    "76": {"inch": "2-12/32", "mpa": 186.486},
    "77": {"inch": "2-13/32", "mpa": 188.957},
    "78": {"inch": "2-14/32", "mpa": 191.351},
    "79": {"inch": "2-15/32", "mpa": 193.745},
    "80": {"inch": "2-16/32", "mpa": 196.139},
    "81": {"inch": "2-17/32", "mpa": 198.533},
    "82": {"inch": "2-18/32", "mpa": 201.004},
    "83": {"inch": "2-19/32", "mpa": 203.397},
    "84": {"inch": "2-20/32", "mpa": 205.791},
    "85": {"inch": "2-21/32", "mpa": 208.262},
    "86": {"inch": "2-22/32", "mpa": 210.656},
    "87": {"inch": "2-23/32", "mpa": 213.05}
};

function normalizeInch(val) {
    if (!val) return '';
    return String(val).trim().toLowerCase().replace(/inch|in|"/g, '').trim().replace(/\s+/g, '-');
}

function findMpaFromInch(inchStr) {
    if (!inchStr) return null;
    const norm = normalizeInch(inchStr);
    if (INCH_LOOKUP[norm]) return INCH_LOOKUP[norm].mpa;
    for (const k in INCH_LOOKUP) {
        const item = INCH_LOOKUP[k];
        if (normalizeInch(item.inch) === norm || item.inch === norm) {
            return item.mpa;
        }
    }
    return null;
}

function findInchFromMpa(mpaNum) {
    if (mpaNum == null || isNaN(mpaNum)) return null;
    let closestInch = null;
    let minDiff = Infinity;
    for (const k in INCH_LOOKUP) {
        const diff = Math.abs(INCH_LOOKUP[k].mpa - mpaNum);
        if (diff < minDiff) {
            minDiff = diff;
            closestInch = INCH_LOOKUP[k].inch;
        }
    }
    return closestInch;
}

document.addEventListener("DOMContentLoaded", async () => {
    if (!token) {
        window.location.href = "/login";
        return;
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

    const userRole = localStorage.getItem("role");
    const detailDelBtn = document.getElementById("detailDeleteProofBtn");
    if (detailDelBtn && userRole === "admin") {
        detailDelBtn.classList.remove("d-none");
        detailDelBtn.addEventListener("click", () => {
            if (currentProof) {
                const detLabelMap = {
                    '356_LZ': 'Detonator 356 mg LZ',
                    '135_LZY': 'Detonator 135 mg LZY',
                    'RGM': 'Detonator RGM'
                };
                document.getElementById('detail_del_lot_display').innerText = currentProof.lot_no || 'Proof #' + proofId;
                document.getElementById('detail_del_type_display').innerText = detLabelMap[currentProof.detonator_type] || currentProof.detonator_type;
            }
            document.getElementById('detailDeleteProofError').classList.add('d-none');
            new bootstrap.Modal(document.getElementById('detailDeleteProofModal')).show();
        });
    }

    const confirmDetailDelBtn = document.getElementById("detailConfirmDeleteProofBtn");
    if (confirmDetailDelBtn) {
        confirmDetailDelBtn.addEventListener("click", async () => {
            const errDiv = document.getElementById("detailDeleteProofError");
            errDiv.classList.add("d-none");
            confirmDetailDelBtn.disabled = true;
            confirmDetailDelBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Deleting...';

            try {
                const res = await fetch(`/api/proofs/${proofId}`, {
                    method: "DELETE",
                    headers: {
                        "Authorization": `Bearer ${token}`
                    }
                });

                if (res.ok) {
                    window.location.href = "/manage-proofs";
                } else {
                    const errData = await res.json();
                    errDiv.innerText = errData.detail || "Failed to delete proof.";
                    errDiv.classList.remove("d-none");
                }
            } catch (err) {
                console.error("Delete error:", err);
                errDiv.innerText = "Network error occurred.";
                errDiv.classList.remove("d-none");
            } finally {
                confirmDetailDelBtn.disabled = false;
                confirmDetailDelBtn.innerHTML = '<span class="material-symbols-outlined fs-5">delete_forever</span> Delete Proof & All Tests';
            }
        });
    }

    const editDetSelect = document.getElementById("edit_detonator_type");
    if (editDetSelect) {
        editDetSelect.addEventListener("change", (e) => {
            toggleEditDetonatorFields(e.target.value);
        });
    }

    document.getElementById("quickEditProofBtn").addEventListener("click", openEditProofModal);

    // Edit Proof Form Submit
    document.getElementById("editProofForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const errDiv = document.getElementById("editProofError");
        errDiv.classList.add("d-none");

        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

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

        // Clean empty strings to null
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

        data.result_no = data.proof_results;
        data.date = data.date_of_proof;

        try {
            const res = await fetch(`/api/proofs/${proofId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById('editProofModal')).hide();
                await loadProofDetails();
            } else {
                const errData = await res.json();
                errDiv.innerText = errData.detail || "Failed to update proof.";
                errDiv.classList.remove("d-none");
            }
        } catch (err) {
            errDiv.innerText = "Network error occurred.";
            errDiv.classList.remove("d-none");
        }
    });

    // Edit Flash Test Submit
    document.getElementById("editFlashTestForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const errDiv = document.getElementById("editFlashTestError");
        errDiv.classList.add("d-none");
        const testId = document.getElementById("edit_flash_test_id").value;
        const dtVal = document.getElementById("edit_flash_datetime").value;

        const payload = {
            test_number: parseInt(document.getElementById("edit_flash_test_number").value, 10),
            flash_detected: document.getElementById("edit_flash_detected").value === 'true',
            date_time: dtVal ? new Date(dtVal).toISOString() : null
        };

        try {
            const res = await fetch(`/api/proofs/${proofId}/flash-tests/${testId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById('editFlashTestModal')).hide();
                await loadProofDetails();
            } else {
                const errData = await res.json();
                errDiv.innerText = errData.detail || "Failed to update flash test.";
                errDiv.classList.remove("d-none");
            }
        } catch (err) {
            errDiv.innerText = "Network error occurred.";
            errDiv.classList.remove("d-none");
        }
    });

    // Initialize Datalist for Inch suggestions
    const dl = document.getElementById("inchOptions");
    if (dl && dl.options.length === 0) {
        let opts = '';
        for (const k in INCH_LOOKUP) {
            opts += `<option value="${INCH_LOOKUP[k].inch}">${INCH_LOOKUP[k].inch} (${INCH_LOOKUP[k].mpa} MPA)</option>`;
        }
        dl.innerHTML = opts;
    }

    // Bi-directional live auto-mapping
    const inchInput = document.getElementById("edit_pressure_inch");
    const mpaInput = document.getElementById("edit_pressure_mpa");

    if (inchInput && mpaInput) {
        inchInput.addEventListener("input", () => {
            const matchedMpa = findMpaFromInch(inchInput.value);
            if (matchedMpa !== null) {
                mpaInput.value = matchedMpa.toFixed(3);
            }
        });

        mpaInput.addEventListener("input", () => {
            const num = parseFloat(mpaInput.value);
            if (!isNaN(num)) {
                const matchedInch = findInchFromMpa(num);
                if (matchedInch) {
                    inchInput.value = matchedInch;
                }
            }
        });
    }

    // Edit Pressure Test Submit
    document.getElementById("editPressureTestForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const errDiv = document.getElementById("editPressureTestError");
        errDiv.classList.add("d-none");
        const testId = document.getElementById("edit_pressure_test_id").value;
        const dtVal = document.getElementById("edit_pressure_datetime").value;
        const inchVal = document.getElementById("edit_pressure_inch").value;
        const mpaVal = document.getElementById("edit_pressure_mpa").value;
        const mmVal = document.getElementById("edit_pressure_mm").value;
        const originVal = document.getElementById("edit_pressure_origin").value;

        const payload = {
            test_number: parseInt(document.getElementById("edit_pressure_test_number").value, 10),
            inch: inchVal !== '' ? inchVal : null,
            mpa: mpaVal !== '' ? parseFloat(mpaVal) : null,
            mm: mmVal !== '' ? parseFloat(mmVal) : null,
            origin_value: originVal !== '' ? parseFloat(originVal) : null,
            date_time: dtVal ? new Date(dtVal).toISOString() : null
        };

        try {
            const res = await fetch(`/api/proofs/${proofId}/pressure-tests/${testId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById('editPressureTestModal')).hide();
                await loadProofDetails();
            } else {
                const errData = await res.json();
                errDiv.innerText = errData.detail || "Failed to update pressure test.";
                errDiv.classList.remove("d-none");
            }
        } catch (err) {
            errDiv.innerText = "Network error occurred.";
            errDiv.classList.remove("d-none");
        }
    });

    // Initial Load
    await loadProofDetails();
});
