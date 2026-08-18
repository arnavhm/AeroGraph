import { getAirport } from './airports.js';
import { normalizeEndpoint } from './graphModel.js';

export function deriveRouteArcs(nodes, links) {
    const flightRoutes = [];
    
    for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].label === 'FlightRoute') {
            flightRoutes.push(nodes[i]);
        }
    }

    const departsFrom = new Set();
    const arrivesAt = new Set();

    for (let i = 0; i < links.length; i++) {
        const link = links[i];
        if (link.type === 'DEPARTS_FROM') {
            departsFrom.add(normalizeEndpoint(link.source));
        } else if (link.type === 'ARRIVES_AT') {
            arrivesAt.add(normalizeEndpoint(link.source));
        }
    }

    const arcs = [];

    for (let i = 0; i < flightRoutes.length; i++) {
        const route = flightRoutes[i];
        const routeId = route.id;

        if (!departsFrom.has(routeId) || !arrivesAt.has(routeId)) {
            continue;
        }

        const originIcao = route.props.origin_icao;
        const destIcao = route.props.destination_icao;

        const originData = getAirport(originIcao);
        const destData = getAirport(destIcao);

        if (!originData || !destData) {
            continue;
        }

        arcs.push({
            route_id: routeId,
            origin_icao: originIcao,
            destination_icao: destIcao,
            origin_lat: originData.lat,
            origin_lon: originData.lon,
            destination_lat: destData.lat,
            destination_lon: destData.lon
        });
    }

    return arcs;
}
