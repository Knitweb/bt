# EURBT Basket Policy

EURBT is not a simple euro peg. The euro is the anchor and display numeraire, while
the target value is calculated from a trade-weighted basket.

## Required Components

Every valid EURBT basket spec must include:

- `eur_anchor`: euro baseline;
- `fiat_trade`: trade-weighted fiat pressure;
- `crypto_trade`: crypto trade and liquidity demand;
- `commodity`: tradable commodity value.

Inflation/HICP style data can be added as an additional component, but it cannot
replace the four required components.

## Integer Rules

- Values use 8-decimal atoms.
- Weights use integer parts-per-million.
- Weights must sum to exactly `1_000_000`.
- The basket target is a deterministic integer weighted average.

Example genesis weights:

| Component | Weight |
| --- | ---: |
| EUR anchor | 380000 ppm |
| Fiat trade | 240000 ppm |
| Crypto trade | 180000 ppm |
| Commodities | 200000 ppm |

## Knowledge Claims

Each component must reference at least one signed knowledge claim. A claim records:

- issuer peer;
- component type;
- integer value;
- confidence in ppm;
- observation and expiry times;
- source and note.

Expired or invalidly signed claims cannot be used to build basket components.

## VoteBank DAO Control

Basket specs can only be signed by the VoteBank DAO actor. Identified people and
owned agents may transact, but they cannot update the monetary basket policy.

