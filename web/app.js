/* Standalone educational Lung-RADS v2022 subset; no network requests. */
(function (root) {
  "use strict";

  const info = {
    "1": ["Negative", "No nodules or suspicious findings.", "Continue annual LDCT screening."],
    "2": ["Benign appearance", "Low likelihood of clinically significant malignancy.", "Continue annual LDCT screening."],
    "3": ["Probably benign", "Short-interval assessment recommended.", "6-month LDCT follow-up."],
    "4A": ["Suspicious", "Further assessment is recommended.", "3-month LDCT follow-up; PET/CT may be considered if solid component is at least 8 mm."],
    "4B": ["Very suspicious", "Diagnostic evaluation is recommended.", "Chest CT with or without contrast, PET/CT and/or tissue sampling as clinically appropriate."],
    "4X": ["Additional suspicious features", "Category 3 or 4 finding with additional suspicious imaging features.", "Diagnostic workup based on clinical and imaging findings."]
  };
  const rank = { "1": 0, "2": 1, "3": 2, "4A": 3, "4B": 4, "4X": 5 };

  function optionalNumber(value, name) {
    if (value === "" || value === null || value === undefined) return null;
    const n = Number(value);
    if (!Number.isFinite(n)) throw new Error(name + " must be a finite number.");
    return n;
  }
  function categorize(n) {
    if (!["solid", "part-solid", "ground-glass"].includes(n.type)) throw new Error("Select a valid nodule type.");
    const d = optionalNumber(n.diameter, "Total diameter");
    if (d === null || d < 0 || d > 100) throw new Error("Total diameter must be between 0 and 100 mm.");
    const prior = optionalNumber(n.prior, "Prior diameter");
    const solid = optionalNumber(n.solid, "Solid component");
    const priorSolid = optionalNumber(n.priorSolid, "Prior solid component");
    const months = optionalNumber(n.months, "Comparison interval");
    if (prior !== null && (prior < 0 || prior > 100)) throw new Error("Prior diameter must be between 0 and 100 mm.");
    if (n.isNew && prior !== null) throw new Error("A new nodule cannot have a prior diameter.");
    if (months !== null && months <= 0) throw new Error("Comparison interval must be positive.");
    if (n.type !== "part-solid" && (solid !== null || priorSolid !== null)) throw new Error("Solid component is only valid for part-solid nodules.");
    if (solid !== null && (solid < 0 || solid > d)) throw new Error("Solid component must be between 0 and total diameter.");
    if (priorSolid !== null && (prior === null || solid === null || priorSolid < 0 || priorSolid > prior)) throw new Error("Prior solid component requires valid current and prior measurements.");
    const growth = prior !== null && (months === null || months <= 12) && d - prior > 1.5;
    let category;

    if (n.type === "solid") {
      if (n.isNew) category = d < 4 ? "2" : d < 6 ? "3" : d < 8 ? "4A" : "4B";
      else if (growth) category = d >= 8 ? "4B" : "4A";
      else category = d < 6 ? "2" : d < 8 ? "3" : d < 15 ? "4A" : "4B";
    } else if (n.type === "part-solid") {
      if (d < 6) category = n.isNew ? "3" : "2";
      else {
        if (solid === null) throw new Error("Part-solid nodules at least 6 mm require a measured solid component.");
        const increasingSolid = priorSolid !== null && (months === null || months <= 12) && solid - priorSolid > 1.5;
        const newlySolid = priorSolid === 0 && solid > 0;
        if (solid >= 8 || ((increasingSolid || newlySolid || n.isNew) && solid >= 4)) category = "4B";
        else if (solid >= 6 || ((increasingSolid || newlySolid || n.isNew) && solid > 0)) category = "4A";
        else category = "3";
      }
    } else category = d >= 30 && !(prior !== null && prior >= 30 && d - prior <= 1.5) ? "3" : "2";
    return { category, type: n.type, diameter_mm: d, solid_component_mm: solid,
             prior_diameter_mm: prior, prior_solid_component_mm: priorSolid, is_new: Boolean(n.isNew) };
  }
  function assess(nodules, options) {
    if (!Array.isArray(nodules)) throw new Error("Nodules must be an array.");
    options = options || {};
    const summaries = nodules.map(categorize);
    let category = summaries.reduce((best, x) => rank[x.category] > rank[best] ? x.category : best, "1");
    if (options.suspicious && ["3", "4A", "4B"].includes(category)) category = "4X";
    const notes = [];
    if (options.suspicious && category === "4X") notes.push("Additional suspicious imaging features triggered category 4X.");
    if (options.sModifier) notes.push("S modifier: separately evaluate the other significant finding.");
    if (!nodules.length) notes.push("No nodules entered.");
    return { category, category_label: info[category][0], description: info[category][1],
             management: info[category][2], s_modifier: Boolean(options.sModifier),
             nodule_summaries: summaries, notes, educational_only: true };
  }

  const api = { categorize, assess };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.LungRADS = api;

  if (typeof document === "undefined") return;
  document.addEventListener("DOMContentLoaded", () => {
    const rows = document.getElementById("rows");
    const output = document.getElementById("result");
    const status = document.getElementById("status");
    const exportButton = document.getElementById("export");
    let lastResult = null;
    let nextId = 1;

    function addRow() {
      const id = nextId++;
      const template = document.getElementById("nodule-template");
      const node = template.content.firstElementChild.cloneNode(true);
      node.dataset.id = String(id);
      node.querySelector(".row-number").textContent = "Nodule " + id;
      node.querySelector(".remove").addEventListener("click", () => node.remove());
      const typeSelect = node.querySelector('[data-name="type"]');
      const solidInputs = node.querySelectorAll('[data-name="solid"], [data-name="priorSolid"]');
      function setInputs() {
        const part = typeSelect.value === "part-solid";
        solidInputs.forEach(el => { el.disabled = !part; if (!part) el.value = ""; });
      }
      typeSelect.addEventListener("change", setInputs);
      setInputs();
      rows.appendChild(node);
      return node;
    }

    function val(row, key) { return row.querySelector('[data-name="' + key + '"]').value; }
    function buildRows() {
      return Array.from(rows.children).map(row => ({
        type: val(row, "type"), diameter: val(row, "diameter"),
        prior: val(row, "prior"), solid: val(row, "solid"),
        priorSolid: val(row, "priorSolid"), months: val(row, "months"),
        isNew: row.querySelector('[data-name="isNew"]').checked
      }));
    }

    document.getElementById("add").addEventListener("click", addRow);
    document.getElementById("assess").addEventListener("click", () => {
      lastResult = null;
      exportButton.disabled = true;
      try {
        const result = assess(buildRows(), {
          suspicious: document.getElementById("suspicious").checked,
          sModifier: document.getElementById("sModifier").checked
        });
        lastResult = result;
        output.textContent = JSON.stringify(result, null, 2);
        status.textContent = "Lung-RADS " + result.category + (result.s_modifier ? " + S" : "") +
          " — " + result.category_label + " | " + result.management;
        status.className = "outcome";
        exportButton.disabled = false;
      } catch (err) {
        status.textContent = "Assessment not completed: " + err.message;
        status.className = "outcome error";
        output.textContent = "";
      }
    });
    exportButton.addEventListener("click", () => {
      if (!lastResult) return;
      const file = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], { type: "application/json" });
      const url = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = url; link.download = "lung-rads-assessment.json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 0);
    });
    addRow();
    document.querySelector('[data-name="diameter"]').value = "7";
  });
})(typeof window !== "undefined" ? window : null);
