import { test } from 'node:test';
import assert from 'node:assert';
import { AIRPORTS, getAirport } from './airports.js';

test('AIRPORTS has exactly 6 keys', () => {
    const keys = Object.keys(AIRPORTS);
    assert.strictEqual(keys.length, 6);
    const expected = ["EDDL", "EGLL", "EHAM", "ESSA", "LEBL", "LFPO"];
    for (const code of expected) {
        assert.ok(keys.includes(code), `Missing key ${code}`);
    }
});

test('AIRPORTS entries have valid lat, lon, and name', () => {
    for (const code in AIRPORTS) {
        const entry = AIRPORTS[code];
        assert.ok(Number.isFinite(entry.lat) && entry.lat >= -90 && entry.lat <= 90, `Invalid lat for ${code}`);
        assert.ok(Number.isFinite(entry.lon) && entry.lon >= -180 && entry.lon <= 180, `Invalid lon for ${code}`);
        assert.strictEqual(typeof entry.name, 'string');
        assert.ok(entry.name.length > 0, `Empty name for ${code}`);
    }
});

test('getAirport returns undefined for unknown code', () => {
    assert.strictEqual(getAirport('ZZZZ'), undefined);
});

test('given the exact six-code list, every code resolves to an entry with both coordinates defined', () => {
    const expected = ["EGLL", "EDDL", "LEBL", "EHAM", "ESSA", "LFPO"];
    for (const code of expected) {
        const entry = getAirport(code);
        assert.notStrictEqual(entry, undefined, `Expected entry for ${code}`);
        assert.notStrictEqual(entry.lat, undefined, `Expected lat for ${code}`);
        assert.notStrictEqual(entry.lon, undefined, `Expected lon for ${code}`);
    }
});
