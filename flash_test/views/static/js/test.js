document.addEventListener("DOMContentLoaded", () => {
  // --- Proof & Test Selection ---
  const proofSelect = document.getElementById("proofSelect");
  const testSelect = document.getElementById("testSelect");
  const refreshProofsBtn = document.getElementById("refreshProofsBtn");
  const saveBtn = document.getElementById("saveMeasurementBtn");
  const resetBtn = document.getElementById("resetBtn");
  const readyBtn = document.getElementById("readyBtn");
  let ready_status = null

  const endTestManuallyBtn = document.getElementById("endTestManuallyBtn");
  const msg = document.getElementById("measureMessage");
  const valCurrent = document.getElementById("val-current");

  let isSaving = false;

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
        testSelect.innerHTML = '<option value="">-- Select Test --</option>';
        testSelect.disabled = true;
        if (saveBtn) saveBtn.disabled = true;
      }
    } catch (e) {
      console.error("Failed to load proofs", e);
    }
  }

  async function loadTests(selectTestId = null) {
    const proofId = proofSelect ? proofSelect.value : null;
    if (!testSelect) return [];

    testSelect.innerHTML = '<option value="">-- Select Test --</option>';
    if (saveBtn) saveBtn.disabled = true;

    if (!proofId) {
      testSelect.disabled = true;
      return [];
    }

    testSelect.disabled = false;
    try {
      const res = await fetch(`/api/proofs/${proofId}/tests`);
      const tests = await res.json();

      tests.forEach((t) => {
        const opt = document.createElement("option");
        opt.value = t.id;

        let statusText = "(Empty)";
        if (t.flash_detected === true) {
          statusText = `(Yes)`;
          if (t.flash_detected_time) {
            const dt = new Date(t.flash_detected_time).toLocaleString();
            statusText += ` - ${dt}`;
          }
        } else if (t.flash_detected === false) {
          statusText = "(No)";
        }
        opt.textContent = `Test ${t.test_number} ${statusText}`;
        testSelect.appendChild(opt);
      });

      // If a specific testId is requested, select it
      if (selectTestId && Array.from(testSelect.options).some((o) => o.value == selectTestId)) {
        testSelect.value = selectTestId;
        testSelect.dispatchEvent(new Event("change"));
      }

      return tests;
    } catch (e) {
      console.error("Failed to load tests", e);
      return [];
    }
  }

  if (proofSelect) {
    proofSelect.addEventListener("change", async () => {
      const tests = await loadTests();
      // Auto-select first empty test, or first test if all are done
      const firstEmpty = tests.find((t) => t.flash_detected === null || t.flash_detected === undefined);
      if (firstEmpty) {
        testSelect.value = firstEmpty.id;
        testSelect.dispatchEvent(new Event("change"));
      } else if (tests.length > 0) {
        testSelect.value = tests[0].id;
        testSelect.dispatchEvent(new Event("change"));
      }
    });
  }

  if (testSelect) {
    testSelect.addEventListener("change", async () => {
      const testId = testSelect.value;
      if (saveBtn) saveBtn.disabled = !testId;

      if (testId) {
        try {
          const res = await fetch(`/api/test/setCurrentTestId?test_id=${testId}`);
          const result = await res.json();
          console.log("Current test set:", result);
        } catch (e) {
          console.error("Failed to set test id", e);
        }
      }
    });
  }

  async function handleSaveTest() {
    const testId = testSelect ? testSelect.value : null;
    if (!testId || isSaving) return;

    isSaving = true;
    if (saveBtn) saveBtn.disabled = true;

    try {
      // Find current test index before saving to determine the next test
      const currentOptions = Array.from(testSelect.options).filter((o) => o.value);
      const currentIndex = currentOptions.findIndex((o) => o.value == testId);
      const nextTestId =
        currentIndex >= 0 && currentIndex < currentOptions.length - 1
          ? currentOptions[currentIndex + 1].value
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
          handleReadyTest()
        } else if (result.flash_detected === false) {
          savedText = "Saved No Flash Result";
        }
        if (msg) {
          msg.textContent = nextTestId ? `${savedText} - Switching to next test...` : `${savedText} (All tests completed!)`;
          msg.className = "mt-3 text-center small fw-bold text-success";
        }

        // Reload tests and automatically select the next test
        await loadTests(nextTestId);
      } else {
        if (msg) {
          msg.textContent = result.message || "Failed to save.";
          msg.className = "mt-3 text-center small fw-bold text-danger";
        }
        if (saveBtn) saveBtn.disabled = false;
      }
    } catch (e) {
      if (msg) {
        msg.textContent = "Network error saving measurement.";
        msg.className = "mt-3 text-center small fw-bold text-danger";
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


  async function check_ready_status() {
    try {
      const res = await fetch("/api/test/get_ready_status");
      const result = await res.json();
      console.log(result);
      ready_status = result['ready_status']
      if (ready_status) {
        readyBtn.innerHTML = "<span class='material-symbols-outlined'>thumb_down</span> Not Ready"
        readyBtn.classList.remove("btn-success")
        readyBtn.classList.add("btn-danger")
      } else {
        readyBtn.innerHTML = "<span class='material-symbols-outlined'>thumb_up</span> Ready"
        readyBtn.classList.remove("btn-danger")
        readyBtn.classList.add("btn-success")
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
          msg.textContent = result.message || "Failed to save.";
          msg.className = "mt-3 text-center small fw-bold text-danger";
        }
        if (saveBtn) saveBtn.disabled = false;
      }
    } catch (e) {
      if (msg) {
        msg.textContent = "Network error saving measurement.";
        msg.className = "mt-3 text-center small fw-bold text-danger";
      }
      if (saveBtn) saveBtn.disabled = false;
    } finally {
      isSaving = false;
    }

    setTimeout(() => {
      if (msg) msg.textContent = "";
    }, 3000);
  }

  if (readyBtn) {
    readyBtn.addEventListener("click", handleReadyTest);
  }

  if (endTestManuallyBtn) {
    endTestManuallyBtn.addEventListener("click", async () => {
      const testId = testSelect ? testSelect.value : null;
      if (!testId || isSaving) return;

      const currentOptions = Array.from(testSelect.options).filter((o) => o.value);
      const currentIndex = currentOptions.findIndex((o) => o.value == testId);
      const nextTestId =
        currentIndex >= 0 && currentIndex < currentOptions.length - 1
          ? currentOptions[currentIndex + 1].value
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
              ? "Test ended manually with no flash detected! Switching to next test..."
              : "Test ended manually with no flash detected! (All tests completed!)";
            msg.className = "mt-3 text-center small fw-bold text-warning";
          }

          // Reload tests and select next test
          await loadTests(nextTestId);
        } else {
          if (msg) {
            msg.textContent = result.message || "Failed to end test manually.";
            msg.className = "mt-3 text-center small fw-bold text-danger";
          }
          endTestManuallyBtn.disabled = false;
        }
      } catch (e) {
        if (msg) {
          msg.textContent = "Network error ending test manually.";
          msg.className = "mt-3 text-center small fw-bold text-danger";
        }
        endTestManuallyBtn.disabled = false;
      }
      setTimeout(() => {
        if (msg) msg.textContent = "";
      }, 3000);
    });
  }

  if (refreshProofsBtn) {
    refreshProofsBtn.addEventListener("click", async () => {
      const refreshIcon = refreshProofsBtn.querySelector(".material-symbols-outlined");
      if (refreshIcon) refreshIcon.classList.add("spin");
      refreshProofsBtn.disabled = true;

      try {
        const currentSelectedProof = proofSelect ? proofSelect.value : null;
        const currentSelectedTest = testSelect ? testSelect.value : null;

        await loadProofs(true);

        if (currentSelectedProof && proofSelect && proofSelect.value == currentSelectedProof) {
          await loadTests(currentSelectedTest);
        }

        if (msg) {
          msg.textContent = "Proofs refreshed!";
          msg.className = "mt-3 text-center small fw-bold text-success";
          setTimeout(() => {
            if (msg.textContent === "Proofs refreshed!") msg.textContent = "";
          }, 2000);
        }
      } catch (err) {
        console.error("Failed refreshing proofs", err);
        if (msg) {
          msg.textContent = "Failed to refresh proofs.";
          msg.className = "mt-3 text-center small fw-bold text-danger";
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

  loadProofs();
  check_ready_status();

  // --- Websocket for measurements & timing ---
  const wsUrl = `ws://${window.location.host}/ws/test_info`;

  function connectMeasurementWS() {
    if (!valCurrent) return; // Not on test page
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.flash_detected) {
        valCurrent.textContent = "Yes";
        if (saveBtn && !saveBtn.disabled && !isSaving && testSelect && testSelect.value) {
          handleSaveTest();
        }
      } else {
        valCurrent.textContent = "No";
      }
    };

    ws.onclose = () => {
      setTimeout(connectMeasurementWS, 2000);
    };
  }

  connectMeasurementWS();
});
