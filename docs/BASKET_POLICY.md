# BT Basket Policy

BT is not a simple single-currency peg. The basket has an explicit anchor currency
and display numeraire, while the target value is calculated from trade, crypto, and
commodity signals. The first seed configuration uses EUR, but the protocol field is
`anchor_currency` so a future DAO-approved basket can target another national
currency or a broader market numeraire.

## Required Components

Every valid BT basket spec must include:

- `currency_anchor`: selected anchor-currency baseline;
- `fiat_trade`: trade-weighted fiat pressure;
- `crypto_trade`: crypto trade and liquidity demand;
- `commodity`: tradable commodity value.

Inflation/HICP style data can be added as an additional component, but it cannot
replace the four required components.

## Dynamic vBank Weights

Component weights are not hardcoded policy. They are derived from a vBank time series.
Each time-series point contains:

- observed timestamp;
- one weight per required component;
- participation ppm;
- confidence ppm;
- source, usually a vBank result, election, poll, or DAO record.

The BT engine applies recency, participation, and confidence influence, then
normalises the result to exactly `1_000_000` ppm. Fresh high-participation vBank
points therefore steer the basket more than older or weakly-supported points.

## Integer Rules

- Values use 8-decimal atoms.
- Weights use integer parts-per-million.
- Weights must sum to exactly `1_000_000`.
- The basket target is a deterministic integer weighted average.

Default seed time-series points currently derive approximately:

| Component | Weight |
| --- | ---: |
| EUR seed anchor | 391051 ppm |
| Fiat trade | 240000 ppm |
| Crypto trade | 168949 ppm |
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
