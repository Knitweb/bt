# Integer Transaction Policy

BT stores all transaction values as integers. Floats are not valid transaction
data.

## Decision

- Canonical scale: `100_000_000` atoms per unit.
- Display precision: 8 decimals, for example `1.00000000`.
- Maximum ordinary transaction value: `888888.00000000`.
- Maximum atoms: `88_888_800_000_000`.

This fits comfortably in signed 64-bit integers, while leaving enough precision for
small crypto fills and fiat-like display values.

Eight decimals are more precise than one-millionth precision. A true one-millionth
scale would use 6 decimals; BT uses 8 because `0.00000001` is common in crypto
systems and still keeps `888888.00000000` far below signed 64-bit limits.

## Why Not Float

Binary floating point is fast for graphics and estimates, but it is not exact for
money. A transaction record must hash, sign, compare, and replay identically on every
node. Integer atoms make that deterministic.

Use Knitweb integer records for balances, transfers, fills, and settlement amounts.
Use vBank or floating values only for governance, basket weighting, scoring, charts,
or research values where fractional approximation is acceptable.

## Speed

Integer arithmetic is cheaper than decimal arithmetic and avoids string canonicalisation
problems during matching. The order book compares integer `price_atoms`, `quantity_atoms`,
and `min_quantity_atoms`. Quote amounts are calculated as:

```text
quote_atoms = ceil(price_atoms * quantity_atoms / 100_000_000)
```

The ceiling protects sellers from losing one atom on indivisible fills.

## Instant Receiver UX

A receiver can show a transfer as `instant_accepted` when:

1. the signature is valid;
2. the sender is an authorised actor;
3. the receiver is an authorised actor.

Authorised actors are:

- identified person;
- agent with an identified owner person;
- VoteBank DAO.

This is instant acceptance, not final settlement. Chain finality, escrow release,
reserve proof, and dispute windows remain separate statuses.
