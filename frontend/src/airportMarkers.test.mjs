import { test } from 'node:test';
import assert from 'node:assert';
import { deriveAirportMarkers } from './airportMarkers.js';

test('well-formed Airport node produces one marker with finite lat, lon, and altitude', () => {
    const nodes = [
        { id: 'a1', label: 'Airport', props: { icao: 'EGLL', expected_wx_delay_min_per_arrival: 1.5 } }
    ];
    const markers = deriveAirportMarkers(nodes);
    assert.strictEqual(markers.length, 1);
    const m = markers[0];
    assert.ok(Number.isFinite(m.lat));
    assert.ok(Number.isFinite(m.lon));
    assert.ok(Number.isFinite(m.altitude));
});

test('unknown ICAO produces zero markers', () => {
    const nodes = [
        { id: 'a1', label: 'Airport', props: { icao: 'ZZZZ', expected_wx_delay_min_per_arrival: 1.5 } }
    ];
    const markers = deriveAirportMarkers(nodes);
    assert.strictEqual(markers.length, 0);
});

test('node missing delay property produces zero markers', () => {
    const nodes = [
        { id: 'a1', label: 'Airport', props: { icao: 'EGLL' } }
    ];
    const markers = deriveAirportMarkers(nodes);
    assert.strictEqual(markers.length, 0);
});

test('t clamps: delay above 2.5 produces same colour and altitude as 2.5', () => {
    const node25 = { id: 'a1', label: 'Airport', props: { icao: 'EGLL', expected_wx_delay_min_per_arrival: 2.5 } };
    const node30 = { id: 'a2', label: 'Airport', props: { icao: 'EDDL', expected_wx_delay_min_per_arrival: 3.0 } };
    
    const markers = deriveAirportMarkers([node25, node30]);
    assert.strictEqual(markers.length, 2);
    
    assert.strictEqual(markers[0].color, markers[1].color);
    assert.strictEqual(markers[0].altitude, markers[1].altitude);
});

test('altitude is strictly increasing with delay', () => {
    const nodeLow = { id: 'a1', label: 'Airport', props: { icao: 'EGLL', expected_wx_delay_min_per_arrival: 1.0 } };
    const nodeHigh = { id: 'a2', label: 'Airport', props: { icao: 'EDDL', expected_wx_delay_min_per_arrival: 2.0 } };
    
    const markers = deriveAirportMarkers([nodeLow, nodeHigh]);
    assert.strictEqual(markers.length, 2);
    
    assert.ok(markers[1].altitude > markers[0].altitude, 'Higher delay should yield strictly greater altitude');
});

test('floor holds: delay of 0 yields altitude 0.02, not 0', () => {
    const nodes = [
        { id: 'a1', label: 'Airport', props: { icao: 'EGLL', expected_wx_delay_min_per_arrival: 0.0 } }
    ];
    const markers = deriveAirportMarkers(nodes);
    assert.strictEqual(markers.length, 1);
    assert.strictEqual(markers[0].altitude, 0.02);
});

test('input array is unchanged after the call', () => {
    const nodes = [
        { id: 'a1', label: 'Airport', props: { icao: 'EGLL', expected_wx_delay_min_per_arrival: 1.5 } }
    ];
    const nodesCopy = JSON.parse(JSON.stringify(nodes));
    
    deriveAirportMarkers(nodes);
    
    assert.deepStrictEqual(nodes, nodesCopy);
});
