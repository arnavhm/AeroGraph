import React from 'react';
import { resultFields } from './agentModel.js';

// Renders the result of POST /action — the Option D pre-approved catalog path.
// Response shape (agent/action_tool.py): { ok, rows, row_count, truncated,
// error, rejected_by }. No answer, no attempts, no model — this is not an
// /ask payload, which is why this is a sibling of ResultColumn rather than a
// generalisation of it. The action result enters no comparison with V1/V2.
//
// Props contract (fetching lives in App.jsx, not here):
//   result    null (not yet run, or cleared while in flight) | /action payload object | Error
//   inFlight  boolean
const isError = (result) => result instanceof Error;

const sectionLabelStyle = {
  color: 'var(--ag-text-dim)',
  fontSize: '12px',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  margin: '14px 0 4px',
};

export default function ActionResult({ result, inFlight }) {
  return (
    <div style={{
      backgroundColor: 'var(--ag-panel)',
      border: '1px solid var(--ag-border)',
      padding: '12px 16px',
      marginTop: '8px',
      overflow: 'hidden',
    }}>
      <div style={{ color: 'var(--ag-accent)', fontSize: '13px', letterSpacing: '0.08em' }}>
        ACTION
      </div>

      {result === null && (
        <div style={{ color: 'var(--ag-text-dim)', marginTop: '14px' }}>
          {inFlight ? 'Request in flight' : 'Not run yet'}
        </div>
      )}

      {isError(result) && (
        <div style={{ marginTop: '14px' }}>
          <div style={sectionLabelStyle}>Request failed</div>
          <div style={{ color: 'var(--ag-text)', whiteSpace: 'pre-wrap', overflowWrap: 'break-word' }}>
            {result.message}
          </div>
        </div>
      )}

      {result !== null && !isError(result) && (
        <div>
          {result.ok ? (
            <div>
              <div style={sectionLabelStyle}>Result fields</div>
              {resultFields(result.rows).length === 0 ? (
                <div style={{ color: 'var(--ag-text-dim)' }}>no rows returned</div>
              ) : (
                <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                  <tbody>
                    {resultFields(result.rows).map(({ key, value }) => (
                      <tr key={key}>
                        <td style={{
                          color: 'var(--ag-text-dim)',
                          fontFamily: 'var(--ag-mono)',
                          fontSize: '13px',
                          padding: '2px 12px 2px 0',
                          verticalAlign: 'top',
                          whiteSpace: 'nowrap',
                        }}>{key}</td>
                        <td style={{
                          color: 'var(--ag-text)',
                          fontFamily: 'var(--ag-mono)',
                          fontSize: '13px',
                          padding: '2px 0',
                          overflowWrap: 'anywhere',
                        }}>{String(value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ) : (
            <div>
              <div style={sectionLabelStyle}>Action rejected</div>
              <div style={{ color: 'var(--ag-text)', overflowWrap: 'break-word' }}>
                {String(result.error)}
              </div>
            </div>
          )}

          <div style={sectionLabelStyle}>Status</div>
          <div style={{ color: 'var(--ag-text-dim)', fontFamily: 'var(--ag-mono)', fontSize: '12px' }}>
            ok: {String(result.ok)} · row_count: {String(result.row_count)} · truncated: {String(result.truncated)} · rejected_by: {String(result.rejected_by)} · error: {String(result.error)}
          </div>
        </div>
      )}
    </div>
  );
}
