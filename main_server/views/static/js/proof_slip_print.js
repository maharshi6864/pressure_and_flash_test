function getGeneratorName() {
    let name = localStorage.getItem("name") || localStorage.getItem("username");
    if (!name) {
        const token = localStorage.getItem("token");
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                name = payload.name || payload.sub;
            } catch (e) {}
        }
    }
    return name || "Authorized User";
}

function getFormattedToday() {
    const d = new Date();
    const pad = n => n < 10 ? '0' + n : n;
    return `${pad(d.getDate())}-${pad(d.getMonth() + 1)}-${d.getFullYear()}`;
}

document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    const proofId = window.PROOF_ID || parseInt(window.location.pathname.split('/')[2], 10);
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

    // Setup Generator Name on UI & document
    let generatorName = getGeneratorName();
    const generatorInput = document.getElementById("generatorNameInput");
    if (generatorInput) {
        generatorInput.value = generatorName;
        generatorInput.addEventListener("input", (e) => {
            const val = e.target.value.trim() || "Authorized Person";
            document.querySelectorAll(".doc-generator-name").forEach(el => el.textContent = val);
            document.querySelectorAll(".doc-generator-signature").forEach(el => el.textContent = `(${val})`);
        });
    }

    try {
        const res = await fetch(`/api/proofs/${proofId}`, { headers });
        if (!res.ok) throw new Error(`Failed to load proof data (HTTP ${res.status})`);
        const proof = await res.json();

        renderLogSheet(proof);
    } catch (err) {
        console.error("Render Error:", err);
        document.getElementById('printableArea').innerHTML = `
            <div style="padding: 30px; text-align: center; color: #b91c1c; font-family: 'Inter', sans-serif;">
                <h2>Error Loading Log Sheet</h2>
                <p style="margin-top: 10px;">${err.message}</p>
            </div>
        `;
    }
});

function formatDate(dStr) {
    if (!dStr) return '';
    const parts = dStr.split('-');
    if (parts.length === 3) {
        return `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    return dStr;
}

function calculatePressureMetrics(pressureTests, detType, sampleSize) {
    if (detType === 'RGM') {
        return null;
    }

    const constantVal = (detType === '135_LZY') ? 80.00 : 125.00;
    let readings = [];
    let validReadings = [];

    if (pressureTests && pressureTests.length > 0) {
        pressureTests.forEach(pt => {
            if (pt && pt.mpa != null && !isNaN(parseFloat(pt.mpa))) {
                const val = parseFloat(pt.mpa);
                readings.push(val);
                validReadings.push(val);
            }
        });
    }

    // Target box count: at least 10, or total pressure tests / sampleSize
    const targetLength = Math.max(readings.length, sampleSize || 0, 10);
    while (readings.length < targetLength) {
        readings.push(null);
    }

    let mean = null;
    let md = null;
    let eq1 = null;
    let eq2 = null;

    if (validReadings.length > 0) {
        const sum = validReadings.reduce((a, b) => a + b, 0);
        mean = sum / validReadings.length;
        // Mean Deviation (Md): Average of absolute differences from the mean
        md = validReadings.reduce((a, b) => a + Math.abs(b - mean), 0) / validReadings.length;

        eq1 = (3.5 * md) + constantVal;
        eq2 = (2.5 * md) + constantVal;
    }

    return { readings, validReadings, mean, md, eq1, eq2, constantVal };
}

function renderPressureObservationContent(metrics, userObs) {
    if (!metrics) {
        return userObs ? `<span>${userObs}</span>` : '';
    }

    const r = metrics.readings;
    const validCount = metrics.validReadings.length;

    // Build dynamic 5-column grid for readings
    let gridRows = '';
    const numRows = Math.ceil(r.length / 5);
    for (let row = 0; row < numRows; row++) {
        let rowCells = '';
        for (let col = 0; col < 5; col++) {
            const idx = row * 5 + col;
            const val = idx < r.length && r[idx] !== null ? r[idx].toFixed(3) : '&nbsp;';
            rowCells += `<td style="border: 1px solid #000; text-align: center; padding: 3px 2px; font-weight: bold; width: 20%; font-size: 11.5px; height: 23px;">${val}</td>`;
        }
        gridRows += `<tr>${rowCells}</tr>`;
    }

    const gridHtml = `
        <div style="margin-bottom: 5px;">
            <div style="font-weight: bold; font-size: 12px; margin-bottom: 3px;">Pressure (in Mpa):</div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 4px;">
                <tbody>${gridRows}</tbody>
            </table>
        </div>
    `;

    if (validCount === 0) {
        return `
            ${gridHtml}
            ${userObs ? `<div style="margin-top: 4px;">${userObs}</div>` : ''}
        `;
    }

    const mean = metrics.mean;
    const md = metrics.md;
    const eq1 = metrics.eq1;
    const eq2 = metrics.eq2;
    const constantVal = metrics.constantVal;

    const isEq1 = Math.abs(mean - eq1) < 0.001;
    const isMoreEq1 = mean > eq1;
    const isBetween = (mean <= eq1 && mean >= eq2 && !isEq1);
    const isLessEq2 = mean < eq2;

    const allMoreCount = metrics.validReadings.filter(p => p >= constantVal).length;
    const anyLessCount = metrics.validReadings.filter(p => p < constantVal).length;

    const moreText = (allMoreCount === validCount && validCount > 0) ? 'All' : `${allMoreCount}`;
    const lessText = (anyLessCount === 0) ? 'No' : `${anyLessCount}`;

    return `
        ${gridHtml}
        <div style="font-size: 11.5px; line-height: 1.4; color: #000;">
            <table style="border: none; border-collapse: collapse; width: 100%; max-width: 260px; margin-bottom: 3px;">
                <tr>
                    <td style="border: none; padding: 1px 0; font-weight: bold;">Mean Pressure:</td>
                    <td style="border: none; padding: 1px 0; text-align: right; font-weight: bold; font-size: 12px;">${mean.toFixed(3)}</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 1px 0; font-weight: bold;">Md:</td>
                    <td style="border: none; padding: 1px 0; text-align: right; font-weight: bold; font-size: 12px;">${md.toFixed(3)}</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 1px 0;">(I) 3.5XMd + ${constantVal.toFixed(2)} =</td>
                    <td style="border: none; padding: 1px 0; text-align: right; font-weight: bold; font-size: 12px;">${eq1.toFixed(3)}</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 1px 0;">(II) 2.5XMd + ${constantVal.toFixed(2)} =</td>
                    <td style="border: none; padding: 1px 0; text-align: right; font-weight: bold; font-size: 12px;">${eq2.toFixed(3)}</td>
                </tr>
            </table>

            <div style="font-weight: bold; margin-top: 3px; margin-bottom: 1px;">Mean Pressure is</div>
            <div style="padding-left: 4px; font-size: 11px;">
                <div style="${isEq1 ? 'font-weight: bold;' : ''}">${isEq1 ? '<span style="font-size: 12.5px; font-weight: 900;">&#10003;</span>' : '&bull;'} Equal to the figure of (I)</div>
                <div style="${isMoreEq1 ? 'font-weight: bold;' : ''}">${isMoreEq1 ? '<span style="font-size: 12.5px; font-weight: 900;">&#10003;</span>' : '&bull;'} More than the figure of (I)</div>
                <div style="${isBetween ? 'font-weight: bold;' : ''}">${isBetween ? '<span style="font-size: 12.5px; font-weight: 900;">&#10003;</span>' : '&bull;'} Between the figure of (I) &amp; (II)</div>
                <div style="${isLessEq2 ? 'font-weight: bold;' : ''}">${isLessEq2 ? '<span style="font-size: 12.5px; font-weight: 900;">&#10003;</span>' : '&bull;'} Less than the figure of (II)</div>
            </div>

            <div style="padding-left: 4px; margin-top: 3px; font-size: 11px;">
                <div>&bull; -- <strong>${moreText}</strong> -- Detonators shown Pressure equal/more than the minimum specified pressure.</div>
                <div>&bull; -- <strong>${lessText}</strong> -- Detonators shown Pressure less than the minimum specified Pressure.</div>
            </div>

            ${userObs ? `<div style="margin-top: 3px; font-style: italic;">${userObs}</div>` : ''}
        </div>
    `;
}

function renderLogSheet(proof) {
    const detType = proof.detonator_type || '356_LZ';
    const lotNo = proof.lot_no || '';
    const sampleReceivedOn = formatDate(proof.sample_received_on);
    const sampleSize = proof.sample_size ? `${proof.sample_size} Nos.` : '';
    const proofResults = proof.proof_results || '';
    const scheduleRef = proof.schedule_ref || 'CQA/Proof Schedule/Det/1/11';
    const sampleSizeNum = proof.pressure_test_sample_size || proof.sample_size || 10;
    const pressureMetrics = calculatePressureMetrics(proof.pressure_tests || [], detType, sampleSizeNum);

    // Generator info
    const generatorInput = document.getElementById("generatorNameInput");
    const generatorName = (generatorInput && generatorInput.value.trim()) ? generatorInput.value.trim() : getGeneratorName();
    const currentDateStr = getFormattedToday();

    // Auto-compute flash observation if empty and tests are recorded
    let flashObs = proof.flash_test_obs || '';
    if (!flashObs && proof.flash_tests && proof.flash_tests.length > 0) {
        const allSat = proof.flash_tests.every(t => t.flash_detected === true);
        const anyFail = proof.flash_tests.some(t => t.flash_detected === false);
        if (allSat) flashObs = 'All 10 samples satisfactory (Flash detected)';
        else if (anyFail) {
            const failCount = proof.flash_tests.filter(t => t.flash_detected === false).length;
            flashObs = `${failCount} sample(s) failed`;
        }
    }

    // Update top bar text
    const barLotEl = document.getElementById('barLotNo');
    if (barLotEl) barLotEl.innerText = `| Lot No: ${lotNo}`;
    let html = '';

    if (detType === '356_LZ') {
        const docTitleEl = document.getElementById('barDocTitle');
        if (docTitleEl) docTitleEl.innerText = 'Log Sheet for Detonator 356 mg LZ';
        html = `
            <div class="header-title-1">ORDNANCE FACTORY BADMAL</div>
            <div class="header-title-2">SECTION: QC(PROOF RANGE)</div>
            <div class="header-title-3">Log Sheet for Detonator 356 mg LZ</div>
            <div class="header-title-ref"><u>(Proof Schedule/Test Programme Ref: ${scheduleRef})</u></div>
            <div class="format-badge"><u>FORMAT</u></div>

            <div class="meta-list">
                <div class="meta-row">
                    <span class="meta-num">1.</span>
                    <span class="meta-label">Lot No</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${lotNo}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">2.</span>
                    <span class="meta-label">Sample Received on</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${sampleReceivedOn}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">3.</span>
                    <span class="meta-label">Sample Size</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${sampleSize}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">4.</span>
                    <span class="meta-label">Proof Results</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${proofResults}</span>
                </div>
            </div>

            <div class="results-heading">RESULTS</div>

            <table class="proof-table">
                <thead>
                    <tr>
                        <th style="width: 6%;">Sl.No.</th>
                        <th style="width: 22%;">Type of proof</th>
                        <th style="width: 13%;">Sample size</th>
                        <th style="width: 13%;">Date of proof</th>
                        <th style="width: 34%;">Observation</th>
                        <th style="width: 12%;">Remarks</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>01.</td>
                        <td>Drop Test</td>
                        <td>: ${proof.drop_test_sample_size != null ? proof.drop_test_sample_size + ' Nos.' : '20 Nos.'}</td>
                        <td>${formatDate(proof.drop_test_date)}</td>
                        <td>${proof.drop_test_obs || 'All Samples Sustained.'}</td>
                        <td>${proof.drop_test_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>02.</td>
                        <td>Sensitivity Test</td>
                        <td>: ${proof.sensitivity_test_sample_size != null ? proof.sensitivity_test_sample_size + ' Nos.' : '10 Nos.'}</td>
                        <td>${formatDate(proof.sensitivity_test_date)}</td>
                        <td>${proof.sensitivity_test_obs || 'All Samples Functioned.'}</td>
                        <td>${proof.sensitivity_test_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>03.</td>
                        <td>Flash Delivery Test</td>
                        <td>: ${proof.flash_test_sample_size != null ? proof.flash_test_sample_size + ' Nos.' : '10 Nos.'}</td>
                        <td>${formatDate(proof.flash_test_date)}</td>
                        <td>${proof.flash_test_obs || flashObs || 'Satisfactory.'}</td>
                        <td>${proof.flash_test_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>04.</td>
                        <td>
                            Pressure Bar Test
                            <div style="font-size: 10.5px; font-weight: normal; margin-top: 2px;">(Minimum specified pressure for individual Detonator is 125.00 Mpa)</div>
                        </td>
                        <td>: ${proof.pressure_test_sample_size != null ? proof.pressure_test_sample_size + ' Nos.' : '10 Nos.'}</td>
                        <td>${formatDate(proof.pressure_test_date)}</td>
                        <td>${renderPressureObservationContent(pressureMetrics, proof.pressure_test_obs)}</td>
                        <td>${proof.pressure_test_remarks || ''}</td>
                    </tr>
                </tbody>
            </table>

            <div class="footer-block">
                <div class="generated-info">
                    <div><strong>Generated by:</strong> <span class="doc-generator-name">${generatorName}</span></div>
                    <div style="font-size: 11px; color: #444; margin-top: 2px;">Date: ${currentDateStr}</div>
                </div>
                <div class="signature-block">
                    <div style="height: 25px;"></div>
                    <div class="doc-generator-signature" style="font-weight: 600; font-size: 12px; margin-bottom: 2px;">(${generatorName})</div>
                    <div class="signature-text">I/C Proof</div>
                </div>
            </div>
        `;
    } else if (detType === '135_LZY') {
        const docTitleEl = document.getElementById('barDocTitle');
        if (docTitleEl) docTitleEl.innerText = 'Log Sheet for Detonator 135 mg LZY';
        const serialNumber = proof.id ? (2715000 + proof.id) : '2715785';
        html = `
            <div class="header-title-1">ORDNANCE FACTORY BADMAL</div>
            <div class="header-title-2">SECTION: QC(PROOF RANGE)</div>
            <div class="header-title-3">Log Sheet for Detonator 135 mg LZY</div>
            <div class="format-badge"><u>FORMAT</u></div>

            <div class="meta-list">
                <div class="meta-row">
                    <span class="meta-num">1.</span>
                    <span class="meta-label">Lot No.</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${lotNo}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">2.</span>
                    <span class="meta-label">Sample Received on</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${sampleReceivedOn}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">3.</span>
                    <span class="meta-label">Sample Size</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${sampleSize}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">4.</span>
                    <span class="meta-label">Proof Results</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${proofResults}</span>
                </div>
            </div>

            <div class="results-heading">RESULTS</div>

            <table class="proof-table">
                <thead>
                    <tr>
                        <th style="width: 6%;">Sl.No.</th>
                        <th style="width: 22%;">Type of proof</th>
                        <th style="width: 13%;">Sample size</th>
                        <th style="width: 13%;">Date of proof</th>
                        <th style="width: 34%;">Observation</th>
                        <th style="width: 12%;">Remarks</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>01.</td>
                        <td>Drop Test</td>
                        <td>: ${proof.drop_test_sample_size != null ? proof.drop_test_sample_size + ' Nos.' : '20 Nos.'}</td>
                        <td>${formatDate(proof.drop_test_date)}</td>
                        <td>${proof.drop_test_obs || 'All Samples Sustained.'}</td>
                        <td>${proof.drop_test_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>02.</td>
                        <td>Sensitivity Test</td>
                        <td>: ${proof.sensitivity_test_sample_size != null ? proof.sensitivity_test_sample_size + ' Nos.' : '13 Nos.'}</td>
                        <td>${formatDate(proof.sensitivity_test_date)}</td>
                        <td>${proof.sensitivity_test_obs || 'All Samples Functioned.'}</td>
                        <td>${proof.sensitivity_test_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>03.</td>
                        <td>
                            Pressure Bar Test
                            <div style="font-size: 10.5px; font-weight: normal; margin-top: 2px;">(Minimum specified pressure for individual Detonator is 80.00 Mpa)</div>
                        </td>
                        <td>: ${proof.pressure_test_sample_size != null ? proof.pressure_test_sample_size + ' Nos.' : '13 Nos.'}</td>
                        <td>${formatDate(proof.pressure_test_date)}</td>
                        <td>${renderPressureObservationContent(pressureMetrics, proof.pressure_test_obs)}</td>
                        <td>${proof.pressure_test_remarks || ''}</td>
                    </tr>
                </tbody>
            </table>

            <div class="footer-block">
                <div>
                    <div class="serial-no">${serialNumber}</div>
                    <div class="generated-info" style="margin-top: 6px;">
                        <div><strong>Generated by:</strong> <span class="doc-generator-name">${generatorName}</span></div>
                        <div style="font-size: 11px; color: #444; margin-top: 2px;">Date: ${currentDateStr}</div>
                    </div>
                </div>
                <div class="signature-block">
                    <div style="height: 25px;"></div>
                    <div class="doc-generator-signature" style="font-weight: 600; font-size: 12px; margin-bottom: 2px;">(${generatorName})</div>
                    <div class="signature-text">I/C Proof</div>
                </div>
            </div>
        `;
    } else if (detType === 'RGM') {
        const docTitleEl = document.getElementById('barDocTitle');
        if (docTitleEl) docTitleEl.innerText = 'Log Sheet for Detonator RGM';
        html = `
            <div class="header-title-1">ORDNANCE FACTORY BADMAL</div>
            <div class="header-title-2">SECTION: QC(PROOF RANGE)</div>
            <div class="header-title-3">Log Sheet for Detonator RGM</div>
            <div class="format-badge"><u>FORMAT</u></div>

            <div class="meta-list">
                <div class="meta-row">
                    <span class="meta-num">1.</span>
                    <span class="meta-label">Lot No.</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${lotNo}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">2.</span>
                    <span class="meta-label">Sample Received on</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${sampleReceivedOn}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">3.</span>
                    <span class="meta-label">Sample Size</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${sampleSize}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-num">4.</span>
                    <span class="meta-label">Proof Results</span>
                    <span class="meta-colon">:</span>
                    <span class="meta-val">${proofResults}</span>
                </div>
            </div>

            <div class="results-heading">RESULTS</div>

            <table class="proof-table">
                <thead>
                    <tr>
                        <th style="width: 32%;">Type of proof</th>
                        <th style="width: 16%;">Date of proof</th>
                        <th style="width: 15%;">Sample size</th>
                        <th style="width: 22%;">Observation</th>
                        <th style="width: 15%;">Remarks</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1. Sensitivity Test at upper limit :</td>
                        <td>${formatDate(proof.sens_upper_date)}</td>
                        <td>: ${proof.sens_upper_sample_size != null ? proof.sens_upper_sample_size + ' Nos.' : ''}</td>
                        <td>${proof.sens_upper_obs || 'Satisfactory.'}</td>
                        <td>${proof.sens_upper_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>2. Sensitivity Test at lower limit :</td>
                        <td>${formatDate(proof.sens_lower_date)}</td>
                        <td>: ${proof.sens_lower_sample_size != null ? proof.sens_lower_sample_size + ' Nos.' : ''}</td>
                        <td>${proof.sens_lower_obs || 'Satisfactory.'}</td>
                        <td>${proof.sens_lower_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>3. Drop Test :</td>
                        <td>${formatDate(proof.drop_test_date)}</td>
                        <td>: ${proof.drop_test_sample_size != null ? proof.drop_test_sample_size + ' Nos.' : ''}</td>
                        <td>${proof.drop_test_obs || 'All Samples Sustained.'}</td>
                        <td>${proof.drop_test_remarks || ''}</td>
                    </tr>
                    <tr>
                        <td>4. Pressure Bar Test :</td>
                        <td>${formatDate(proof.pressure_test_date)}</td>
                        <td>: ${proof.pressure_test_sample_size != null ? proof.pressure_test_sample_size + ' Nos.' : ''}</td>
                        <td>${proof.pressure_test_obs || ''}</td>
                        <td>${proof.pressure_test_remarks || ''}</td>
                    </tr>
                </tbody>
            </table>

            <div class="footer-block">
                <div class="generated-info">
                    <div><strong>Generated by:</strong> <span class="doc-generator-name">${generatorName}</span></div>
                    <div style="font-size: 11px; color: #444; margin-top: 2px;">Date: ${currentDateStr}</div>
                </div>
                <div class="signature-block">
                    <div style="height: 25px;"></div>
                    <div class="doc-generator-signature" style="font-weight: 600; font-size: 12px; margin-bottom: 2px;">(${generatorName})</div>
                    <div class="signature-text">I/C Proof</div>
                </div>
            </div>
        `;
    }

    document.getElementById('printableArea').innerHTML = html;
}
