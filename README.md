# BT

BT is a Python-first research/prototype codebase for the Knitweb basket-trust
monetary protocol and P2P DEX.
The goal is a market that is as decentralized as possible while still giving users
plain-language trust signals before they trade.

This repository starts from a current DEX architecture review instead of copying
today's default AMM pattern. The short finding is that most high-volume "DEX" venues
are not true peer-to-peer networks. They are usually peer-to-pool smart contracts,
chain-level order books, appchain order books, or intent/RFQ systems with solver
infrastructure. BT therefore uses:

- signed, portable orders;
- integer transaction amounts with 8-decimal fixed-point atoms;
- deterministic local matching;
- P2P message envelopes that can be gossiped without a central API;
- authorised actors: identified people, agents with owner persons, and the VoteBank DAO;
- human-readable trust explanations;
- settlement plans that separate non-custodial crypto locks from anchor-currency
  payment proofs.

The code does not move real funds yet. It is the protocol core and test harness for
building toward a serverless, dynamically anchored DEX. The first seed basket uses
EUR as its display numeraire, but the repository and package identity are BT.

## Research

- `docs/DEX_RESEARCH.md` explains the top-100 DEX snapshot and classification.
- `docs/INTEGER_TRANSACTIONS.md` explains the integer base and actor transaction policy.
- `docs/BASKET_POLICY.md` explains the anchor-currency plus trade, crypto, and commodity basket.
- `docs/FORMAL_SPEC.md` defines the current protocol invariants.
- `docs/ACADEMIC_ROADMAP.md` lists the research work needed before production claims.
- `docs/PULSE_READINESS.md` explains what is still blocking real PULSE trading.
- `docs/DECENTRALIZED_MARKET_CORRECTNESS.md` defines the next correctness and UX targets.
- `docs/SOVEREIGN_DISTRIBUTION.md` explains how BT survives loss of GitHub as a platform.
- `data/dex_top100_2026-06-21.json` stores the generated top-100 matrix.

## Website

GitHub Pages serves the browser DEX from `docs/`.

Expected public URL after Pages deployment:

```text
https://knitweb.github.io/bt/
```

Data source: DeFiLlama DEX overview snapshot from `https://api.llama.fi/overview/dexs`.

## Development

```bash
python -m pip install -e .
python -m pytest -q
bt demo
bt pulse-demo
python scripts/make_source_bundle.py
git bundle verify dist/bt-<commit>.bundle
```

## Design Position

Strictly true P2P means that peers can discover, negotiate, verify, and settle without
a privileged website, matching server, solver API, or custodial operator. A blockchain
or validator network can still be part of settlement, but the user-facing market should
not depend on one host.

BT starts with signed order gossip plus deterministic local state. Future settlement
adapters can settle matched trades through Knitweb records, Bitcoin-style HTLCs, or
other verified networks without changing the order format.

The project should also be distributed as signed Git commits, source bundles, and
non-GitHub mirrors. A GitHub URL is a public convenience route, not the canonical
identity of a BT release.
