# EURBT Architecture

EURBT separates the DEX into four layers:

1. **Signed market intent**: a maker signs an order that can be verified anywhere.
2. **Serverless distribution**: orders and attestations move as signed P2P envelopes.
3. **Deterministic matching**: every node can derive the same candidate trades from the
   same order set.
4. **Settlement adapters**: matched trades produce explicit settlement plans; chain or
   payment integrations execute those plans later.

## Why Not Just AMM

AMMs are highly serverless at the settlement layer, but they are not user-to-user P2P:
traders swap against a pool and inherit LP, MEV, oracle, routing, and slippage risks.
For a euro market, the trust problem is broader because fiat rails, stablecoin issuers,
and redemption promises must be explained to users.

EURBT therefore starts with signed maker/taker intent and trust attestations. Liquidity
can later be pooled, but the base primitive stays portable and peer-verifiable.

## Trust Model

Trust is not a binary "verified" badge. It is an explainable score composed from signed
attestations:

- reserve evidence;
- settlement history;
- dispute history;
- identity or business checks;
- uptime and responsiveness.

The software shows common-language explanations such as "this maker has strong reserve
evidence but only a short settlement history." The scoring engine never hides the input
signals.

## Serverless Target

The target architecture avoids privileged hosts:

- order propagation can happen over gossip, DHT, mailbox relays, or Knitweb/Pulse;
- matching is local and deterministic;
- settlement plans are signed artifacts that any adapter can inspect;
- relays may exist, but they are replaceable caches, not authorities.

## Non-Goals For This First Version

- No real EUR token issuance.
- No custody.
- No production chain transactions.
- No legal claim that a euro token is regulated, backed, or redeemable.

