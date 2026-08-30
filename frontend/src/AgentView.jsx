import React from 'react';
import { resultFields, divergenceState, DIVERGENCE } from './agentModel.js';
import ActionResult from './ActionResult.jsx';

// Props contract (fetching lives in App.jsx, not here):
//   question        string
//   onQuestionChange(nextValue)
//   onSubmit()
//   onRerun()       identical to submit but uncached
//   inFlight        boolean — both controls disabled while true
//   v1Result / v2Result  null (not yet run, or cleared while a round is in flight) | /ask payload object | Error
const isError = (result) => result instanceof Error;
const isPayload = (result) => result !== null && !isError(result);
// A payload whose top-level error is non-null is not a comparable result: the
// provider failed and no query ran, so its rows say nothing about the variant.
const isComparable = (result) => isPayload(result) && result.error == null;

const MARKER_TEXT = {
  [DIVERGENCE.BOTH_EMPTY]: 'Neither variant returned rows',
  [DIVERGENCE.ONE_EMPTY]: 'One variant returned rows; the other returned none',
  [DIVERGENCE.DIFFER]: "The two variants' first returned rows differ",
  [DIVERGENCE.AGREE]: "The two variants' first returned rows are deep-equal",
};
const MARKER_SCOPE = ' — comparison covers the first returned row of each result only';

const sectionLabelStyle = {
  color: 'var(--ag-text-dim)',
  fontSize: '12px',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  margin: '14px 0 4px',
};

const controlStyle = (inFlight) => ({
  padding: '5px 12px',
  backgroundColor: 'var(--ag-panel)',
  color: inFlight ? 'var(--ag-text-dim)' : 'var(--ag-accent)',
  border: `1px solid ${inFlight ? 'var(--ag-border)' : 'var(--ag-accent)'}`,
  cursor: inFlight ? 'default' : 'pointer',
});

function ResultColumn({ variantLabel, result, inFlight }) {
  return (
    <div style={{
      flex: 1,
      minWidth: 0,
      backgroundColor: 'var(--ag-panel)',
      border: '1px solid var(--ag-border)',
      padding: '12px 16px',
      overflow: 'hidden',
    }}>
      <div style={{ color: 'var(--ag-accent)', fontSize: '13px', letterSpacing: '0.08em' }}>
        {variantLabel}
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

      {isPayload(result) && (
        <div>
          <div style={sectionLabelStyle}>Answer</div>
          <div style={{ color: 'var(--ag-text)', fontSize: '19px', lineHeight: '1.4' }}>
            {result.answer}
          </div>

          {result.error !== null && result.error !== undefined && (
            <div>
              <div style={sectionLabelStyle}>Payload error</div>
              <div style={{ color: 'var(--ag-text)', overflowWrap: 'break-word' }}>
                {String(result.error)}
              </div>
            </div>
          )}

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

          <div style={sectionLabelStyle}>Attempts</div>
          {result.attempts.map((attempt, i) => (
            <div key={i} style={{ marginBottom: '10px' }}>
              <div style={{ color: 'var(--ag-text-dim)', fontSize: '13px' }}>
                Attempt {i + 1}
              </div>
              <div style={{ color: 'var(--ag-text-dim)', fontFamily: 'var(--ag-mono)', fontSize: '11px' }}>
                scrolls — drag or shift-scroll
              </div>
              <pre style={{
                color: 'var(--ag-text-dim)',
                fontFamily: 'var(--ag-mono)',
                fontSize: '12px',
                backgroundColor: 'var(--ag-bg)',
                border: '1px solid var(--ag-border)',
                padding: '8px',
                margin: '4px 0',
                maxHeight: '220px',
                overflow: 'auto',
                whiteSpace: 'pre',
              }}>{attempt.cypher}</pre>
              <div style={{ color: 'var(--ag-text-dim)', fontFamily: 'var(--ag-mono)', fontSize: '12px' }}>
                row_count: {String(attempt.row_count)} · rejected_by: {String(attempt.rejected_by)} · error: {String(attempt.error)}
              </div>
            </div>
          ))}

          <div style={sectionLabelStyle}>Provenance</div>
          <div style={{ color: 'var(--ag-text-dim)', fontFamily: 'var(--ag-mono)', fontSize: '12px' }}>
            model: {String(result.model)} · cached: {String(result.cached)} · api_calls: {String(result.api_calls)}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AgentView({
  question,
  onQuestionChange,
  onSubmit,
  onRerun,
  inFlight,
  v1Result,
  v2Result,
  actionResult,
  actionInFlight,
  onRunAction,
}) {
  const bothComparable = isComparable(v1Result) && isComparable(v2Result);
  const marker = bothComparable
    ? divergenceState(v1Result.rows, v2Result.rows)
    : null;

  return (
    <div style={{
      width: '100%',
      height: '100%',
      boxSizing: 'border-box',
      padding: '16px',
      overflow: 'auto',
    }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          style={{
            flex: 1,
            padding: '6px 10px',
            backgroundColor: 'var(--ag-panel)',
            color: 'var(--ag-text)',
            border: '1px solid var(--ag-border)',
            fontSize: '14px',
          }}
        />
        <button disabled={inFlight} onClick={onSubmit} style={controlStyle(inFlight)}>
          Run
        </button>
        <button disabled={inFlight} onClick={onRerun} style={controlStyle(inFlight)}>
          Re-run without cache
        </button>
      </div>

      {marker !== null && (
        <div style={{
          color: 'var(--ag-accent)',
          border: '1px solid var(--ag-accent)',
          padding: '6px 12px',
          margin: '12px 0 0',
          fontSize: '13px',
        }}>
          {MARKER_TEXT[marker]}{MARKER_SCOPE}
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px', marginTop: '12px', alignItems: 'flex-start' }}>
        <ResultColumn variantLabel="V1" result={v1Result} inFlight={inFlight} />
        <ResultColumn variantLabel="V2" result={v2Result} inFlight={inFlight} />
      </div>

      <div style={{ marginTop: '16px' }}>
        <div style={{ color: 'var(--ag-text-dim)', fontSize: '12px', margin: '0 0 6px' }}>
          Pre-approved action — fixed join, parameters only. Does not read the question box.
        </div>
        <button disabled={actionInFlight} onClick={onRunAction} style={controlStyle(actionInFlight)}>
          Run action: worst_exposure_swap
        </button>
        <ActionResult result={actionResult} inFlight={actionInFlight} />
      </div>
    </div>
  );
}
