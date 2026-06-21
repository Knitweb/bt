# PLS Trading Readiness

BT now has a PulseChain-focused signed-order path for PLS markets, but it is not
production-ready for real funds yet.

## Working In Code

- Native `PLS` is registered as a PulseChain asset with 18-decimal integer atoms.
- `PLS/BT` orders can be signed, verified, submitted, matched, and replayed without
  floats.
- Actor checks still apply: identified people, owned agents, or the VoteBank DAO.
- Trust minimums block matches when the counterparty score is too low.
- Settlement plans use a PulseChain escrow route for same-chain PLS markets.
- `bt pls-demo` produces a dry-run readiness report, matched trade, and settlement
  plan.

## Real-Funds Blockers

The code intentionally blocks `submit_real_funds_order` unless all real-funds checks
pass. Current blockers are:

- no deployed production PulseChain escrow or HTLC adapter is configured;
- no independent audit or formal verification reference is attached;
- `BT` is still a protocol/demo unit, not a registered production PulseChain token;
- arbitrary PulseChain tokens need verified contract addresses, decimals, and risk
  profiles before they can be accepted.

## Required Before Offering Real PLS

1. Deploy a minimal non-custodial PulseChain escrow adapter.
2. Add the adapter contract address to deployment configuration.
3. Add independent audit or formal verification evidence.
4. Register every tradable PulseChain token with symbol, address, decimals, and source.
5. Add chain receipt verification and confirmation tracking.
6. Add cancellation and timeout recovery paths.
7. Run adversarial tests for duplicate fills, replayed orders, stale envelopes, and
   partial fills.

Until those are complete, BT should be used for signed dry-runs and protocol testing,
not for locking real PLS.
