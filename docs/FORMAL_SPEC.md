# EURBT Formal Specification Draft

This document captures the protocol invariants that should be tested or proven before
EURBT is treated as more than a prototype.

## Types

### Atom

An atom is a signed-host-language integer constrained by EURBT validation rules.

```text
1 unit = 100_000_000 atoms
0 < transaction_amount_atoms <= 88_888_800_000_000
```

Floats are not part of the transaction grammar.

### Weight

A basket component weight is an integer in parts per million.

```text
0 <= component_weight_ppm <= 1_000_000
sum(component_weight_ppm) = 1_000_000
```

### Actor

An actor is authorised to transact if and only if it is one of:

- identified person;
- identified agent with an owner person;
- identified VoteBank DAO.

Only the VoteBank DAO may publish a signed basket spec.

## State

```text
Actors          = map(peer_id -> Actor)
Claims          = set(SignedKnowledgeClaim)
VBankSeries     = ordered set(VBankWeightPoint)
BasketSpec      = signed DAO-approved target spec
Orders          = set(SignedOrder)
Transfers       = set(SignedTransfer)
SettlementPlans = set(SettlementPlan)
```

## Basket Target

Given active signed knowledge claims and vBank time-series points:

1. validate each vBank point;
2. compute point influence from recency, participation, and confidence;
3. aggregate weighted component values;
4. normalise to exactly `1_000_000` ppm;
5. build components from active signed knowledge claims;
6. compute:

```text
target_atoms = round(sum(value_atoms_i * weight_ppm_i) / 1_000_000)
```

The implementation rounds half-up by adding `500_000` before integer division.

## Required Invariants

### I1: Integer Money

All balances, order quantities, prices, fills, transfers, and settlement legs use
integer atoms. A float cannot be accepted as transaction input.

### I2: Basket Completeness

Every valid EURBT basket spec includes:

- `eur_anchor`
- `fiat_trade`
- `crypto_trade`
- `commodity`

### I3: Exact Weight Sum

Every valid basket spec has component weights summing to exactly `1_000_000` ppm.

### I4: vBank-Derived Weights

Basket weights are derived from vBank time-series points. Fixed weights are allowed
only as test fixtures or explicit default seed points.

### I5: Active Claims Only

Expired or invalidly signed knowledge claims cannot form basket components.

### I6: DAO Policy Authority

Only the VoteBank DAO actor can sign basket specs.

### I7: Deterministic Replay

The same actor registry, knowledge claims, and vBank time series must produce the same
basket spec ID and target atoms on every conforming node.

### I8: Instant Is Not Final

`instant_accepted` means the transfer signature and actor registry checks passed. It
does not imply chain finality, custody, redemption, or dispute expiry.

## Proof Obligations

- Show that `normalise_weights` always sums to `1_000_000` for positive inputs.
- Show that integer quote rounding never underpays the seller by truncation.
- Show that stale vBank points retain bounded influence and cannot dominate fresh
  high-participation points.
- Show that no unsigned or non-DAO basket spec can pass verification.

