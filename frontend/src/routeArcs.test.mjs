import { test } from 'node:test';
import assert from 'node:assert';
import { deriveRouteArcs } from './routeArcs.js';

test('well-formed route produces one arc with finite coordinates', () => {
    const nodes = [
        { id: 'r1', label: 'FlightRoute', props: { origin_icao: 'EGLL', destination_icao: 'EDDL' } }
    ];
    const links = [
        { source: 'r1', target: 'a1', type: 'DEPARTS_FROM' },
        { source: 'r1', target: 'a2', type: 'ARRIVES_AT' }
    ];
    const arcs = deriveRouteArcs(nodes, links);
    assert.strictEqual(arcs.length, 1);
    const arc = arcs[0];
    assert.strictEqual(arc.route_id, 'r1');
    assert.strictEqual(arc.origin_icao, 'EGLL');
    assert.strictEqual(arc.destination_icao, 'EDDL');
    assert.ok(Number.isFinite(arc.origin_lat));
    assert.ok(Number.isFinite(arc.origin_lon));
    assert.ok(Number.isFinite(arc.destination_lat));
    assert.ok(Number.isFinite(arc.destination_lon));
});

test('unknown ICAO produces zero arcs', () => {
    const nodes = [
        { id: 'r1', label: 'FlightRoute', props: { origin_icao: 'EGLL', destination_icao: 'ZZZZ' } }
    ];
    const links = [
        { source: 'r1', target: 'a1', type: 'DEPARTS_FROM' },
        { source: 'r1', target: 'a2', type: 'ARRIVES_AT' }
    ];
    const arcs = deriveRouteArcs(nodes, links);
    assert.strictEqual(arcs.length, 0);
});

test('missing arrival edge produces zero arcs', () => {
    const nodes = [
        { id: 'r1', label: 'FlightRoute', props: { origin_icao: 'EGLL', destination_icao: 'EDDL' } }
    ];
    const links = [
        { source: 'r1', target: 'a1', type: 'DEPARTS_FROM' }
    ];
    const arcs = deriveRouteArcs(nodes, links);
    assert.strictEqual(arcs.length, 0);
});

test('input arrays are unchanged', () => {
    const nodes = [
        { id: 'r1', label: 'FlightRoute', props: { origin_icao: 'EGLL', destination_icao: 'EDDL' } }
    ];
    const links = [
        { source: 'r1', target: 'a1', type: 'DEPARTS_FROM' },
        { source: 'r1', target: 'a2', type: 'ARRIVES_AT' }
    ];
    const nodesCopy = JSON.parse(JSON.stringify(nodes));
    const linksCopy = JSON.parse(JSON.stringify(links));
    
    deriveRouteArcs(nodes, links);
    
    assert.deepStrictEqual(nodes, nodesCopy);
    assert.deepStrictEqual(links, linksCopy);
});

test('endpoints as objects produce same result as id strings', () => {
    const nodes = [
        { id: 'r1', label: 'FlightRoute', props: { origin_icao: 'EGLL', destination_icao: 'EDDL' } }
    ];
    const linksStr = [
        { source: 'r1', target: 'a1', type: 'DEPARTS_FROM' },
        { source: 'r1', target: 'a2', type: 'ARRIVES_AT' }
    ];
    const linksObj = [
        { source: { id: 'r1' }, target: { id: 'a1' }, type: 'DEPARTS_FROM' },
        { source: { id: 'r1' }, target: { id: 'a2' }, type: 'ARRIVES_AT' }
    ];
    
    const arcsStr = deriveRouteArcs(nodes, linksStr);
    const arcsObj = deriveRouteArcs(nodes, linksObj);
    
    assert.deepStrictEqual(arcsStr, arcsObj);
    assert.strictEqual(arcsObj.length, 1);
});
