# BT Academic Realisation Roadmap

BT should be treated as a research protocol until its monetary, governance,
market, legal, and operational claims are tested. The goal is not to claim that a
stable coin is already safe, but to make every stabilisation claim auditable and
falsifiable.

## Research Question

Can a dynamically anchored, knowledge-weighted basket token provide a more
transparent settlement unit for P2P crypto markets than a single-asset stablecoin,
while avoiding hidden float arithmetic, opaque governance, and central matching
infrastructure?

## Current Hypothesis

BT can be made academically credible if:

1. all monetary amounts are integer atoms;
2. basket weights are derived from signed vBank time-series records;
3. each component value is backed by signed knowledge claims with expiry;
4. only the VoteBank DAO can publish basket-policy updates;
5. users can independently recompute the target index from public records;
6. receiver "instant accepted" status is explicitly separated from settlement finality.

## Falsification Criteria

The design should be considered invalid or incomplete if any of these hold:

- two conforming nodes compute different basket targets from the same records;
- a float value is required to validate a transaction amount or settlement leg;
- a non-DAO actor can publish a valid basket spec;
- an expired knowledge claim can influence the current basket;
- vBank weights can be changed without a traceable time-series record;
- the UI implies legal redemption, custody, or final settlement before the adapter proves it;
- the system cannot reproduce historical basket targets from archived records.

## Work Packages

### WP1: Formal Model

Deliverables:

- canonical state-transition definitions;
- integer money model;
- basket normalisation proof sketch;
- actor-authorisation state machine;
- settlement-state distinction between `instant_accepted`, `pending_settlement`, and finality.

Exit criteria:

- every invariant in `docs/FORMAL_SPEC.md` has a test or a clear proof obligation.

### WP2: vBank Data Provenance

Deliverables:

- signed `vbank-weight-point` records from vBank poll/election outputs;
- provenance mapping from poll CIDs to component weights;
- replay tool that rebuilds BT basket weights over time;
- conflict-resolution rule for competing vBank series.

Exit criteria:

- a third party can recompute the current BT basket from archived vBank records.

### WP3: Knowledge Claim Quality

Deliverables:

- source taxonomy for ECB, BIS, World Bank, crypto volume, commodity, and market-depth data;
- expiry rules per source type;
- confidence scoring methodology;
- stale-data and outlier rejection tests.

Exit criteria:

- every basket component links to active signed claims and exposes source freshness.

### WP4: Market Microstructure

Deliverables:

- deterministic matching benchmark;
- latency measurement for local match, signed P2P propagation, and settlement adapter planning;
- adversarial tests for spam orders, stale envelopes, and duplicate fills;
- comparison with AMM, CLOB, and intent/RFQ designs.

Exit criteria:

- performance claims are measured, not asserted.

### WP5: Legal And Regulatory Mapping

Deliverables:

- MiCA mapping for asset-referenced-token and e-money-token questions;
- FSB global stablecoin arrangement checklist;
- disclosure text for no custody, no redemption claim, and no production settlement;
- environmental and operational risk disclosure.

Exit criteria:

- the repository can generate a draft disclosure appendix without changing code semantics.

### WP6: Reproducibility Package

Deliverables:

- deterministic fixtures for basket histories;
- command that rebuilds every published target index;
- archived source snapshots or immutable references;
- CI job for replay tests.

Exit criteria:

- a clean checkout can reproduce the documented BT target values.

## Primary External References

- EUR-Lex, Regulation (EU) 2023/1114 on markets in crypto-assets.
- Financial Stability Board, High-level Recommendations for Global Stablecoin Arrangements.
- Bank for International Settlements, Annual Economic Report 2025.
- European Central Bank, effective exchange rate statistics.
- World Bank, Commodity Markets data.
