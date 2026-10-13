"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { categorize, assess } = require("../web/app.js");

const n = (type, diameter, more = {}) => ({ type, diameter, ...more });

test("solid v2022 boundaries", () => {
  assert.equal(categorize(n("solid", 5.9)).category, "2");
  assert.equal(categorize(n("solid", 6)).category, "3");
  assert.equal(categorize(n("solid", 8)).category, "4A");
  assert.equal(categorize(n("solid", 15)).category, "4B");
  assert.equal(categorize(n("solid", 5, { isNew: true })).category, "3");
  assert.equal(categorize(n("solid", 8, { isNew: true })).category, "4B");
});

test("growth strictly exceeds 1.5 mm within 12 months", () => {
  assert.equal(categorize(n("solid", 5.5, { prior: 4 })).category, "2");
  assert.equal(categorize(n("solid", 5.6, { prior: 4 })).category, "4A");
  assert.equal(categorize(n("solid", 5.6, { prior: 4, months: 18 })).category, "2");
  assert.equal(categorize(n("solid", 8, { prior: 6 })).category, "4B");
});

test("part-solid needs solid size", () => {
  assert.throws(() => categorize(n("part-solid", 10)), /solid component/i);
  assert.equal(categorize(n("part-solid", 10, { solid: 3 })).category, "3");
  assert.equal(categorize(n("part-solid", 10, { solid: 6 })).category, "4A");
  assert.equal(categorize(n("part-solid", 10, { solid: 8 })).category, "4B");
  assert.equal(categorize(n("part-solid", 4, { isNew: true })).category, "3");
  assert.equal(categorize(n("part-solid", 10, { solid: 5, prior: 9, priorSolid: 1 })).category, "4B");
});

test("pure ground glass follows 30mm threshold", () => {
  assert.equal(categorize(n("ground-glass", 10)).category, "2");
  assert.equal(categorize(n("ground-glass", 10, { prior: 7 })).category, "2");
  assert.equal(categorize(n("ground-glass", 29, { isNew: true })).category, "2");
  assert.equal(categorize(n("ground-glass", 30)).category, "3");
  assert.equal(categorize(n("ground-glass", 32, { prior: 31 })).category, "2");
});

test("S modifier independent of numeric category", () => {
  const result = assess([n("solid", 7)], { sModifier: true });
  assert.equal(result.category, "3");
  assert.equal(result.s_modifier, true);
  assert.equal(assess([], { sModifier: true }).category, "1");
});

test("suspicious features upgrade categories 3 and 4", () => {
  assert.equal(assess([n("solid", 7)], { suspicious: true }).category, "4X");
  assert.equal(assess([n("solid", 3)], { suspicious: true }).category, "2");
});

test("invalid data rejected rather than silently classified", () => {
  assert.throws(() => categorize(n("solid", "NaN")), /finite/);
  assert.throws(() => categorize(n("solid", -1)), /total diameter/i);
  assert.throws(() => categorize(n("part-solid", 9, { solid: 10 })), /component/i);
  assert.throws(() => categorize(n("solid", 7, { prior: 5, isNew: true })), /new nodule/i);
});
