/**
 * Source URL: https://davidmegginson.github.io/ourairports-data/airports.csv
 * Generator command: node /tmp/gen_airports.mjs
 * Reproduced by: node /tmp/gen_airports.mjs on 2026-08-18
 */

export const AIRPORTS = {
  "EDDL": { lat: 51.289501, lon: 6.76678, name: "Düsseldorf Airport" },
  "EGLL": { lat: 51.470748, lon: -0.459909, name: "London Heathrow Airport" },
  "EHAM": { lat: 52.308601, lon: 4.76389, name: "Amsterdam Airport Schiphol" },
  "ESSA": { lat: 59.64849, lon: 17.928829, name: "Stockholm-Arlanda Airport" },
  "LEBL": { lat: 41.2971, lon: 2.07846, name: "Josep Tarradellas Barcelona-El Prat Airport" },
  "LFPO": { lat: 48.729499, lon: 2.358963, name: "Paris-Orly Airport" }
};

export function getAirport(icao) {
  return AIRPORTS[icao];
}
