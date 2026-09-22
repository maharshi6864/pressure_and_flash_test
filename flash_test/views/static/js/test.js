document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const proofSelect = document.getElementById("proofSelect");
  const testCardsContainer = document.getElementById("testCardsContainer");
  const testsSummaryBadge = document.getElementById("testsSummaryBadge");
  const refreshProofsBtn = document.getElementById("refreshProofsBtn");
  const saveBtn = document.getElementById("saveMeasurementBtn");
  const readyBtn = document.getElementById("readyBtn");
  const endTestManuallyBtn = document.getElementById("endTestManuallyBtn");
  const msg = document.getElementById("measureMessage");
  const valCurrent = document.getElementById("val-current");

  // Modal Elements
  const flashImageModalEl = document.getElementById("flashImageModal");
  const flashModalImg = document.getElementById("flashModalImg");
  const flashModalTitle = document.getElementById("flashModalTitle");
  const flashModalCaption = document.getElementById("flashModalCaption");
  const flashModalTime = document.getElementById("flashModalTime");
  const flashModalDownloadBtn = document.getElementById("flashModalDownloadBtn");

  const viewActiveFlashImageBtn = document.getElementById("viewActiveFlashImageBtn");

  // --- State Variables ---
  let ready_status = null;
  let isSaving = false;
  let currentSelectedTestId = null;
  let currentTests = [];

  // --- Open Flash Image Modal ---
  function openFlashImageModal(imagePath, testNumber, detectionTime) {
    if (!imagePath) return;
    const formattedUrl = imagePath.startsWith("/") ? imagePath : `/${imagePath}`;
    if (flashModalImg) flashModalImg.src = formattedUrl;
    if (flashModalTitle) flashModalTitle.textContent = `Flash Detection Image (Test #${testNumber || ""})`;
    if (flashModalCaption) flashModalCaption.textContent = `File: ${imagePath.split("/").pop()}`;
    if (flashModalTime) {
      if (detectionTime) {
        const dt = new Date(detectionTime);
        flashModalTime.textContent = `Detected at: ${dt.toLocaleString()}`;
      } else {
        flashModalTime.textContent = "";
      }
    }
    if (flashModalDownloadBtn) {
      flashModalDownloadBtn.href = formattedUrl;
      flashModalDownloadBtn.download = `flash_test_${testNumber || "image"}.jpg`;
    }
    if (flashImageModalEl && window.bootstrap) {
      const modal = bootstrap.Modal.getOrCreateInstance(flashImageModalEl);
      modal.show();
    }
  }

  // --- Active Test Image Button Click ---
  if (viewActiveFlashImageBtn) {
    viewActiveFlashImageBtn.addEventListener("click", () => {
      const activeTest = currentTests.find((t) => t.id === currentSelectedTestId);
      if (activeTest && activeTest.flash_detected_image_path) {
        openFlashImageModal(activeTest.flash_detected_image_path, activeTest.test_number, activeTest.flash_detected_time);
      }
    });
  }

  // --- Load Proofs ---
  async function loadProofs(preserveSelection = false) {
    if (!proofSelect) return;
    const previousProofId = preserveSelection ? proofSelect.value : null;
    try {
      const res = await fetch("/api/proofs");
      const proofs = await res.json();
      proofSelect.innerHTML = '<option value="">-- Select Proof --</option>';
      proofs.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `Lot No : ${p.lot_no}`;
        proofSelect.appendChild(opt);
      });

      if (previousProofId && Array.from(proofSelect.options).some((o) => o.value == previousProofId)) {
        proofSelect.value = previousProofId;
      } else if (preserveSelection && previousProofId) {
        currentSelectedTestId = null;
        currentTests = [];
        renderCards();
        if (saveBtn) saveBtn.disabled = true;
      }
    } catch (e) {
      console.error("Failed to load proofs", e);
    }
  }

  // --- Render Test Cards Grid ---
  function renderCards() {
    if (!testCardsContainer) return;
    testCardsContainer.innerHTML = "";

    if (!proofSelect || !proofSelect.value) {
      testCardsContainer.innerHTML = `
        <div class="col-12 w-100 text-center text-muted py-4">
          <span class="material-symbols-outlined fs-2 text-secondary opacity-50 mb-1">inventory_2</span>
          <p class="small mb-0">Select a proof to display test cards</p>
        </div>`;
      if (testsSummaryBadge) {
        testsSummaryBadge.textContent = "0 / 0 Completed";
        testsSummaryBadge.className = "badge bg-secondary-subtle text-secondary small";
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
        testsSummaryBadge.textContent = "0 / 0 Completed";
        testsSummaryBadge.className = "badge bg-secondary-subtle text-secondary small";
      }
      return;
    }

    // Update summary badge
    const completedCount = currentTests.filter((t) => t.flash_detected !== null && t.flash_detected !== undefined).length;
    const passedCount = currentTests.filter((t) => t.flash_detected === true).length;
    const totalCount = currentTests.length;
    if (testsSummaryBadge) {
      testsSummaryBadge.textContent = `${completedCount} / ${totalCount} Done (${passedCount} Flash)`;
      if (completedCount === totalCount && totalCount > 0) {
        testsSummaryBadge.className = "badge bg-success-subtle text-success border border-success-subtle small";
      } else {
        testsSummaryBadge.className = "badge bg-primary-subtle text-primary border border-primary-subtle small";
      }
    }

    currentTests.forEach((t) => {
      const col = document.createElement("div");
      col.className = "col";

      const isActive = t.id === currentSelectedTestId;

      let statusIcon = "";
      let statusBadge = "";
      let statusClass = "pending";
      let timeStr = "";
      let imageButtonHtml = "";

      if (t.flash_detected === true) {
        statusClass = "passed";
        statusIcon = `<span class="material-symbols-outlined text-success fs-5">check_circle</span>`;
        statusBadge = `<span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1 small fw-semibold" style="font-size: 0.75rem;">Flash</span>`;
        if (t.flash_detected_time) {
          const dt = new Date(t.flash_detected_time);
          timeStr = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
        }
        if (t.flash_detected_image_path) {
          imageButtonHtml = `
            <button type="button" class="btn btn-xs btn-outline-success view-flash-btn d-inline-flex align-items-center justify-content-center gap-1 mt-1 py-0 px-2 rounded-pill shadow-none" style="font-size: 0.65rem;" title="View Saved Flash Image">
              <span class="material-symbols-outlined" style="font-size: 0.85rem;">image</span>
              <span>View Image</span>
            </button>`;
        }
      } else if (t.flash_detected === false) {
        statusClass = "failed";
        if (t.flash_detected_time) {
          const dt = new Date(t.flash_detected_time);
          timeStr = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
        }
        statusIcon = `<span class="material-symbols-outlined text-danger fs-5">cancel</span>`;
        statusBadge = `<span class="badge bg-danger-subtle text-danger border border-danger-subtle px-2 py-1 small fw-semibold" style="font-size: 0.75rem;">No Flash</span>`;
        if (t.flash_detected_image_path) {
          imageButtonHtml = `
            <button type="button" class="btn btn-xs btn-outline-danger view-flash-btn d-inline-flex align-items-center justify-content-center gap-1 mt-1 py-0 px-2 rounded-pill shadow-none" style="font-size: 0.65rem;" title="View Saved Frame">
              <span class="material-symbols-outlined" style="font-size: 0.85rem;">image</span>
              <span>View Image</span>
            </button>`;
        }
      } else {

        statusClass = "pending";
        statusIcon = `<span class="material-symbols-outlined text-secondary fs-5" style="opacity: 0.4;">radio_button_unchecked</span>`;
        statusBadge = `<span class="badge bg-light text-secondary border px-2 py-1 small" style="font-size: 0.75rem;">Pending</span>`;
      }

      col.innerHTML = `
        <div class="card h-100 test-card p-2 text-center position-relative ${statusClass} ${isActive ? "active" : ""}" data-test-id="${t.id}">
          ${isActive ? '<span class="badge bg-primary position-absolute top-0 start-50 translate-middle px-2 py-0 shadow-sm" style="font-size: 0.6rem; letter-spacing: 0.5px; border-radius: 999px;">CURRENT</span>' : ""}
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="fw-bold small text-dark">#${t.test_number} Test</span>
            ${statusIcon}
          </div>
          <div class="d-flex flex-column align-items-center justify-content-center py-1">
            ${statusBadge}
            ${timeStr ? `<small class="text-secondary text-truncate w-100 mt-1" style="font-size: 0.68rem;" title="${timeStr}">${timeStr}</small>` : `<small class="text-secondary text-truncate w-100 mt-1" style="font-size: 0.68rem;">--:--:--</small>`}
            ${imageButtonHtml}
          </div>
        </div>`;

      const cardEl = col.querySelector(".test-card");
      cardEl.addEventListener("click", () => {
        selectTest(t.id, true);
      });

      const viewBtn = col.querySelector(".view-flash-btn");
      if (viewBtn) {
        viewBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          openFlashImageModal(t.flash_detected_image_path, t.test_number, t.flash_detected_time);
        });
      }

      testCardsContainer.appendChild(col);
    });
  }

  // --- Select a Specific Test ---
  async function selectTest(testId, informBackend = true) {
    currentSelectedTestId = testId;
    if (saveBtn) saveBtn.disabled = !testId;

    // Toggle active image preview button in left column
    const activeTest = currentTests.find((t) => t.id === testId);
  

    renderCards();

    if (testId && informBackend) {
      try {
        const res = await fetch(`/api/test/setCurrentTestId?test_id=${testId}`);
        const result = await res.json();
        console.log("Current test set:", result);
      } catch (e) {
        console.error("Failed to set current test id", e);
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
      if (selectTestId && currentTests.some((t) => t.id === selectTestId)) {
        targetTestId = selectTestId;
      } else if (currentSelectedTestId && currentTests.some((t) => t.id === currentSelectedTestId)) {
        targetTestId = currentSelectedTestId;
      } else {
        // Auto-select first empty/pending test, or first test if all are done
        const firstEmpty = currentTests.find((t) => t.flash_detected === null || t.flash_detected === undefined);
        if (firstEmpty) {
          targetTestId = firstEmpty.id;
        } else if (currentTests.length > 0) {
          targetTestId = currentTests[0].id;
        }
      }

      await selectTest(targetTestId, true);
      return currentTests;
    } catch (e) {
      console.error("Failed to load tests", e);
      currentTests = [];
      renderCards();
      return [];
    }
  }

  // --- Proof Select Event Listener ---
  if (proofSelect) {
    proofSelect.addEventListener("change", async () => {
      currentSelectedTestId = null;
      await loadTests();
    });
  }

  // --- Save Test (with Auto-Increment) ---
  async function handleSaveTest() {
    const testId = currentSelectedTestId;
    if (!testId || isSaving) return;

    isSaving = true;
    if (saveBtn) saveBtn.disabled = true;

    try {
      // Find current test index before saving to determine next test
      const currentIndex = currentTests.findIndex((t) => t.id === testId);
      const nextTestId =
        currentIndex >= 0 && currentIndex < currentTests.length - 1
          ? currentTests[currentIndex + 1].id
          : null;

      const res = await fetch(`/api/tests/${testId}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const result = await res.json();

      if (result.status === "success") {
        let savedText = "Saved test successfully!";
        if (result.flash_detected) {
          savedText = "Saved Flash Result";
          handleReadyTest();
        } else if (result.flash_detected === false) {
          savedText = "Saved No Flash Result";
        }
        if (msg) {
          msg.textContent = nextTestId
            ? `${savedText} - Switching to Test #${currentTests[currentIndex + 1].test_number}...`
            : `${savedText} (All tests completed!)`;
          msg.className = "mt-2 text-center small fw-bold text-success";
        }

        // Reload tests and automatically select the next test
        await loadTests(nextTestId);
      } else {
        if (msg) {
          msg.textContent = result.message || "Failed to save.";
          msg.className = "mt-2 text-center small fw-bold text-danger";
        }
        if (saveBtn) saveBtn.disabled = false;
      }
    } catch (e) {
      if (msg) {
        msg.textContent = "Network error saving measurement.";
        msg.className = "mt-2 text-center small fw-bold text-danger";
      }
      if (saveBtn) saveBtn.disabled = false;
    } finally {
      isSaving = false;
    }

    setTimeout(() => {
      if (msg) msg.textContent = "";
    }, 3000);
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", handleSaveTest);
  }

  // --- Ready Status Handling ---
  async function check_ready_status() {
    try {
      const res = await fetch("/api/test/get_ready_status");
      const result = await res.json();
      ready_status = result["ready_status"];
      if (readyBtn) {
        if (ready_status) {
          readyBtn.innerHTML = "<span class='material-symbols-outlined'>thumb_down</span> Not Ready";
          readyBtn.classList.remove("btn-success");
          readyBtn.classList.add("btn-danger");
        } else {
          readyBtn.innerHTML = "<span class='material-symbols-outlined'>thumb_up</span> Ready";
          readyBtn.classList.remove("btn-danger");
          readyBtn.classList.add("btn-success");
        }
      }
    } catch (e) {
      console.error("Failed to get ready status", e);
    }
  }

  async function handleReadyTest() {
    try {
      const res = await fetch(`/api/test/set_ready_status?ready=${!ready_status}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });
      const result = await res.json();

      if (result.status === "success") {
        check_ready_status();
      } else {
        if (msg) {
          msg.textContent = result.message || "Failed to toggle ready status.";
          msg.className = "mt-2 text-center small fw-bold text-danger";
        }
      }
    } catch (e) {
      if (msg) {
        msg.textContent = "Network error toggling ready status.";
        msg.className = "mt-2 text-center small fw-bold text-danger";
      }
    }

    setTimeout(() => {
      if (msg) msg.textContent = "";
    }, 3000);
  }

  if (readyBtn) {
    readyBtn.addEventListener("click", handleReadyTest);
  }

  // --- End Test Manually ---
  if (endTestManuallyBtn) {
    endTestManuallyBtn.addEventListener("click", async () => {
      const testId = currentSelectedTestId;
      if (!testId || isSaving) return;

      const currentIndex = currentTests.findIndex((t) => t.id === testId);
      const nextTestId =
        currentIndex >= 0 && currentIndex < currentTests.length - 1
          ? currentTests[currentIndex + 1].id
          : null;

      endTestManuallyBtn.disabled = true;
      try {
        const res = await fetch("/api/test/end_manually", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const result = await res.json();
        if (result.status === "success") {
          if (valCurrent) valCurrent.textContent = "No";

          if (msg) {
            msg.textContent = nextTestId
              ? `Test ended manually! Switching to Test #${currentTests[currentIndex + 1].test_number}...`
              : "Test ended manually! (All tests completed!)";
            msg.className = "mt-2 text-center small fw-bold text-warning";
          }

          // Reload tests and select next test
          await loadTests(nextTestId);
        } else {
          if (msg) {
            msg.textContent = result.message || "Failed to end test manually.";
            msg.className = "mt-2 text-center small fw-bold text-danger";
          }
          endTestManuallyBtn.disabled = false;
        }
      } catch (e) {
        if (msg) {
          msg.textContent = "Network error ending test manually.";
          msg.className = "mt-2 text-center small fw-bold text-danger";
        }
        endTestManuallyBtn.disabled = false;
      }
      setTimeout(() => {
        if (msg) msg.textContent = "";
      }, 3000);
    });
  }

  // --- Refresh Proofs Button ---
  if (refreshProofsBtn) {
    refreshProofsBtn.addEventListener("click", async () => {
      const refreshIcon = refreshProofsBtn.querySelector(".material-symbols-outlined");
      if (refreshIcon) refreshIcon.classList.add("spin");
      refreshProofsBtn.disabled = true;

      try {
        const currentSelectedProof = proofSelect ? proofSelect.value : null;
        const currentTargetTest = currentSelectedTestId;

        await loadProofs(true);

        if (currentSelectedProof && proofSelect && proofSelect.value == currentSelectedProof) {
          await loadTests(currentTargetTest);
        } else {
          await loadTests();
        }

        if (msg) {
          msg.textContent = "Proofs refreshed!";
          msg.className = "mt-2 text-center small fw-bold text-success";
          setTimeout(() => {
            if (msg.textContent === "Proofs refreshed!") msg.textContent = "";
          }, 2000);
        }
      } catch (err) {
        console.error("Failed refreshing proofs", err);
        if (msg) {
          msg.textContent = "Failed to refresh proofs.";
          msg.className = "mt-2 text-center small fw-bold text-danger";
          setTimeout(() => {
            if (msg.textContent === "Failed to refresh proofs.") msg.textContent = "";
          }, 2000);
        }
      } finally {
        if (refreshIcon) refreshIcon.classList.remove("spin");
        refreshProofsBtn.disabled = false;
      }
    });
  }

  // Initial Load
  loadProofs();
  check_ready_status();

  // --- WebSocket for live measurements & flash trigger ---
  const wsUrl = `ws://${window.location.host}/ws/test_info`;

  function connectMeasurementWS() {
    if (!valCurrent) return; // Not on test page
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.flash_detected) {
          valCurrent.textContent = "Yes";
          if (saveBtn && !saveBtn.disabled && !isSaving && currentSelectedTestId) {
            handleSaveTest();
          }
        } else {
          valCurrent.textContent = "No";
        }
      } catch (e) {
        console.error("Error parsing websocket message", e);
      }
    };

    ws.onclose = () => {
      setTimeout(connectMeasurementWS, 2000);
    };
  }

  connectMeasurementWS();
});
