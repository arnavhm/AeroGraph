// Pure module: no React, no DOM, no fetch. Consumed by the agent panel.
//
// Nothing in this module knows what the correct answer to any question is.
// divergenceState compares the two variants' results to each other and to
// nothing else — no reference value, no expected tail, no "correct" branch.
// Encoding the gate-verified answer here would put the oracle in the UI and
// destroy the panel's evidentiary value.

export const DIVERGENCE = Object.freeze({
  BOTH_EMPTY: 'both-empty',
  ONE_EMPTY: 'one-empty',
  DIFFER: 'differ',
  AGREE: 'agree',
});

export function resultFields(rows) {
  if (rows == null) return [];
  if (!Array.isArray(rows)) {
    throw new Error(`resultFields expects an array, null, or undefined; got ${typeof rows}`);
  }
  if (rows.length === 0) return [];
  return Object.entries(rows[0]).map(([key, value]) => ({
    key,
    value:
      typeof value === 'object' && value !== null ? JSON.stringify(value) : value,
  }));
}

function isEmpty(rows) {
  return rows == null || rows.length === 0;
}

function deepEqual(a, b) {
  if (Object.is(a, b)) return true;
  if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) {
    return false;
  }
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) {
    if (a.length !== b.length) return false;
    return a.every((v, i) => deepEqual(v, b[i]));
  }
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  return keysA.every((k) => Object.hasOwn(b, k) && deepEqual(a[k], b[k]));
}

export function divergenceState(leftRows, rightRows) {
  const leftEmpty = isEmpty(leftRows);
  const rightEmpty = isEmpty(rightRows);
  if (leftEmpty && rightEmpty) return DIVERGENCE.BOTH_EMPTY;
  if (leftEmpty !== rightEmpty) return DIVERGENCE.ONE_EMPTY;
  return deepEqual(leftRows[0], rightRows[0])
    ? DIVERGENCE.AGREE
    : DIVERGENCE.DIFFER;
}
