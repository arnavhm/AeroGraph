/**
 * 2.5 is a display bound chosen to contain the current observed maximum, not a performance threshold.
 * EUROCONTROL publishes no per-airport ATFM delay bands; performance is assessed against per-state local targets under the RP3 National Performance Plans.
 */
import { getAirport } from './airports.js';

export function deriveAirportMarkers(nodes) {
    const markers = [];
    
    for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        if (node.label !== 'Airport') {
            continue;
        }

        const icao = node.props.icao;
        const delay = node.props.expected_wx_delay_min_per_arrival;

        if (delay === undefined || delay === null) {
            continue;
        }

        const airportData = getAirport(icao);
        if (!airportData) {
            continue;
        }

        let t = delay / 2.5;
        if (t < 0) t = 0;
        if (t > 1) t = 1;

        const s = 15 + t * (100 - 15);
        const l = 45 + t * (65 - 45);
        
        const color = `hsl(359, ${s}%, ${l}%)`;
        
        const altitude = 0.02 + t * (0.35 - 0.02);

        markers.push({
            icao: icao,
            name: airportData.name,
            lat: airportData.lat,
            lon: airportData.lon,
            delay: delay,
            color: color,
            altitude: altitude
        });
    }

    return markers;
}
