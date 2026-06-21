# BT Decentralized Market Correctness

BT should feel different from a normal exchange because users can see why a market
action is valid before they trust it. The user experience should expose the proof in
plain language, while the protocol keeps a strict formal core.

## Correctness Goals

### Safety

No conforming node may accept:

- unsigned orders;
- orders from unauthorised actors;
- float money values;
- expired orders;
- duplicate fills;
- real-funds orders without readiness evidence;
- settlement finality claims without a verified receipt.

### Liveness

The market must continue when one server disappears. Orders and receipts should be
portable signed events that can move through:

- local peer gossip;
- multiple relays;
- direct peer-to-peer transfer;
- Git or file-based event archives;
- web hosts that are treated only as convenience relays.

### Determinism

Given the same signed event log, every conforming node must compute the same:

- valid actor registry;
- open order book;
- fills;
- cancelled orders;
- settlement state;
- basket target.

### Fairness

The current prototype uses deterministic local price-time matching. That is simple
and replayable, but it is not enough for high-value production markets because
whoever controls ordering can gain power.

Production BT should add one or more fairness modes:

- frequent batch auctions for pairs with enough liquidity;
- commit-reveal order submission for sensitive periods;
- deterministic tie-breakers based on signed order IDs;
- bounded clock rules so one host cannot define market time alone;
- public replay reports that show why each fill won priority.

### Data Availability

Market state must be reconstructable from public signed events. A display server may
cache the state, but it must not be the only place where state exists.

Required data objects:

- actor registration events;
- trust evidence events;
- order events;
- cancel events;
- match events;
- settlement plan events;
- settlement receipt events;
- vBank basket time-series events.

### Governance Correctness

The VoteBank DAO may update basket policy, but every policy change must be a signed
event with replayable inputs. vBank time-series records should determine dynamic
weights; fixed values are only seed fixtures until the signed series is available.

## Plain-Language User Experience

The DEX should avoid vague claims like "safe" or "decentralized" unless the screen
shows the evidence. A user should see:

- who signed the order;
- what actor type signed it;
- what trust threshold is required;
- whether the pair is dry-run or real-funds eligible;
- which fairness mode matched the trade;
- which settlement adapter will be used;
- why instant acceptance is not the same as final settlement;
- how to replay the market state locally;
- where the source code can be recovered without GitHub.

## Unique Product Features

### Proof Passport

Every order and trade should have a proof passport:

- actor identity proof;
- signature verification result;
- integer amount proof;
- trust evidence summary;
- readiness blockers;
- settlement route;
- replay hash.

The passport should use normal language first, with raw hashes available for
operators and auditors.

### Replay Button

The website should offer a "replay market" action that downloads the signed event log
and recomputes the book in the browser or Python CLI. If replay produces a different
result, the UI must show that the market view is not trustworthy.

### Sovereign Code Panel

The website should show whether the current release can survive GitHub loss:

- commit hash;
- signed tag status;
- bundle SHA-256;
- non-GitHub mirrors;
- P2P repository IDs;
- archive identifiers.

### Settlement Timeline

A trade should move through explicit states:

```text
signed -> instant_accepted -> settlement_planned -> lock_seen -> receipt_verified -> final
```

The receiver can get an instant signed acceptance, but finality must wait for the
settlement adapter evidence.

### Fairness Mode Selector

The market should expose the current matching mode:

- `price_time`: fastest prototype path;
- `batch_auction`: better fairness for liquid pairs;
- `commit_reveal`: better censorship and front-running resistance;
- `manual_otc`: direct negotiated trade with signed settlement plan.

## Implementation Roadmap

### R1: Signed Event Log

Add a canonical event type for actors, trust, orders, cancels, matches, settlement
plans, receipts, and vBank updates.

Exit condition: a node can rebuild the market state from events only.

### R2: Event Replay CLI

Add:

```bash
bt replay events.jsonl
```

Exit condition: replay output matches website output for the same event file.

### R3: Batch Auction Matcher

Add deterministic batch matching with an explicit clearing rule and tie-breaker.

Exit condition: tests prove that all conforming nodes produce the same fills.

### R4: Settlement Receipt Verifier

Add Knitweb/PULSE receipt validation before any real-funds finality label.

Exit condition: `submit_real_funds_order` cannot reach `final` without a verified
receipt.

### R5: Sovereign Release Metadata

Generate release metadata from the repository:

- commit;
- tag;
- bundle hash;
- mirror list;
- P2P identifiers;
- archive identifiers.

Exit condition: the website can display release resilience without hard-coding
GitHub as the only source.

## New Proof Obligations

- Prove that event replay is deterministic for every accepted event sequence.
- Prove that duplicate fill events cannot reduce remaining order quantity below zero.
- Prove that every final settlement state references a valid receipt.
- Prove that every real-funds order passed readiness gates at submission time.
- Prove that each batch auction has one deterministic clearing price for the same
  event set.
- Prove that source recovery does not depend on one forge URL.
