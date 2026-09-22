document.addEventListener("DOMContentLoaded", () => {
  // --- Proof & Test Selection ---
  const proofSelect = document.getElementById("proofSelect");
  const testSelect = document.getElementById("testSelect");
  const saveBtn = document.getElementById("saveMeasurementBtn");
  const resetBtn = document.getElementById("resetBtn");
  const endTestManuallyBtn = document.getElementById("endTestManuallyBtn");
  const msg = document.getElementById("measureMessage");

  const valCurrent = document.getElementById("val-current");
  async function loadProofs() {
    if (!proofSelect) return;
    try {
      const res = await fetch("/api/proofs");
      const proofs = await res.json();
      proofSelect.innerHTML = '<option value="">-- Select Proof --</option>';
      proofs.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.lot_no} - ${p.type_of_proof}`;
        proofSelect.appendChild(opt);
      });
    } catch (e) {
      console.error("Failed to load proofs", e);
    }
  }

  if (proofSelect) {
    proofSelect.addEventListener("change", async () => {
      const proofId = proofSelect.value;
      testSelect.innerHTML = '<option value="">-- Select Test --</option>';
      saveBtn.disabled = true;

      if (proofId) {
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
            } else if (t.flash_detected === false) {
              statusText = "(No)";
            }
            opt.textContent = `Test ${t.test_number} ${statusText}`;
            testSelect.appendChild(opt);
          });
        } catch (e) {
          console.error("Failed to load tests", e);
        }
      } else {
        testSelect.disabled = true;
      }
    });
  }

  if (testSelect) {
    testSelect.addEventListener("change", async () => {
      saveBtn.disabled = !testSelect.value;
      const testId = testSelect.value;

      try {
        const res = await fetch(`/api/test/setCurrentTestId?test_id=${testId}`);
        const result = await res.json();
        console.log(result);
      } catch (e) {
        console.error("Failed to set test id", e);
      }
    });
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const testId = testSelect.value;
      if (!testId) return;

      try {
        const res = await fetch(`/api/tests/${testId}/save`, {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const result = await res.json();

        if (result.status === "success") {
          let savedText = "Saved test successfully!";
          if (result.flash_detected) {
            savedText = `Saved Flash Result`;
          } else if (result.flash_detected === false) {
            savedText = "Saved No Flash Result";
          }
          msg.textContent = savedText;
          msg.className = "mt-3 text-center small fw-bold text-success";
          // Trigger proof change to reload test labels
          proofSelect.dispatchEvent(new Event("change"));
        } else {
          msg.textContent = result.message || "Failed to save.";
          msg.className = "mt-3 text-center small fw-bold text-danger";
        }
      } catch (e) {
        msg.textContent = "Network error saving measurement.";
        msg.className = "mt-3 text-center small fw-bold text-danger";
      }
      setTimeout(() => {
        msg.textContent = "";
      }, 3000);
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/test/reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const result = await res.json();
        console.log(result)
        if (result.status === "success") {
          // Reset frontend state
          valCurrent.textContent = "No";

          msg.textContent = "Timer and backend state reset!";
          msg.className = "mt-3 text-center small fw-bold text-warning";

          if (proofSelect && proofSelect.value) {
            proofSelect.dispatchEvent(new Event("change"));
          }
        } else {
          msg.textContent = result.message || "Failed to reset.";
          msg.className = "mt-3 text-center small fw-bold text-danger";
        }
      } catch (e) {
        msg.textContent = "Network error resetting state.";
        msg.className = "mt-3 text-center small fw-bold text-danger";
      }
      setTimeout(() => {
        msg.textContent = "";
      }, 3000);
    });
  }

  if (endTestManuallyBtn) {
    endTestManuallyBtn.addEventListener("click", async () => {
      endTestManuallyBtn.disabled = true;
      try {
        const res = await fetch("/api/test/end_manually", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const result = await res.json();
        if (result.status === "success") {
          // Stop running timer animations and freeze
          serverStartTime = null;
          serverEndTime = null;
          if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
          }
          valCurrent.textContent = "No";

          msg.textContent = "Test ended manually with no flash detected!";
          msg.className = "mt-3 text-center small fw-bold text-warning";

          // Reload proofs dropdown list of tests
          if (proofSelect && proofSelect.value) {
            proofSelect.dispatchEvent(new Event("change"));
          }
        } else {
          msg.textContent = result.message || "Failed to end test manually.";
          msg.className = "mt-3 text-center small fw-bold text-danger";
          endTestManuallyBtn.disabled = false;
        }
      } catch (e) {
        msg.textContent = "Network error ending test manually.";
        msg.className = "mt-3 text-center small fw-bold text-danger";
        endTestManuallyBtn.disabled = false;
      }
      setTimeout(() => {
        msg.textContent = "";
      }, 3000);
    });
  }

  loadProofs();

  // --- Websocket for measurements & timing ---
  const wsUrl = `ws://${window.location.host}/ws/test_info`;

  function connectMeasurementWS() {
    if (!valCurrent) return; // Not on test page
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(data)
      if (data.flash_detected) {
        valCurrent.textContent = "Yes"
      } else {
        valCurrent.textContent = "No"
      }
    };

    ws.onclose = () => {
      setTimeout(connectMeasurementWS, 2000);
    };
  }

  connectMeasurementWS();
});
