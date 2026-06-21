# EURBT Architecture

EURBT separates the DEX into four layers:

1. **Signed market intent**: a maker signs an order that can be verified anywhere.
2. **Integer transaction base**: balances, fills, transfers, and settlement amounts
   are stored as 8-decimal integer atoms.
3. **Authorised actors**: only identified people, agents with owner people, and the
   VoteBank DAO can submit transactions.
4. **Serverless distribution**: orders and attestations move as signed P2P envelopes.
5. **Deterministic matching**: every node can derive the same candidate trades from the
   same order set.
6. **Settlement adapters**: matched trades produce explicit settlement plans; chain or
   payment integrations execute those plans later.

The basket policy is implemented in `src/eurbt/basket.py`.

## Why Not Just AMM

AMMs are highly serverless at the settlement layer, but they are not user-to-user P2P:
traders swap against a pool and inherit LP, MEV, oracle, routing, and slippage risks.
For a euro market, the trust problem is broader because fiat rails, stablecoin issuers,
and redemption promises must be explained to users.

EURBT therefore starts with signed maker/taker intent and trust attestations. Liquidity
can later be pooled, but the base primitive stays portable and peer-verifiable.

## Integer Base

Money values use integer atoms, not floats:

- `1.00000000` equals `100_000_000` atoms.
- `0.00000001` is the minimum displayable atom.
- `888888.00000000` is the ordinary maximum transaction value.

The maximum is `88_888_800_000_000` atoms, well below signed 64-bit limits. vBank can
use floating values for governance weights or basket scoring where approximation is
acceptable, but transaction amounts must stay integer.

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

## Actor Rule

A transaction is valid only when the signer is one of:

- an identified person;
- an agent with an identified owner person;
- the VoteBank DAO.

The receiver can show `instant_accepted` once the signature and actor registry check
pass. That status is a receiver UX state, not a claim that every external settlement
rail has finalised.

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
