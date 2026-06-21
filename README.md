# EURBT

EURBT is a Python-first research/prototype codebase for the first working Knitweb
euro crypto market DEX.
The goal is a market that is as decentralized as possible while still giving users
plain-language trust signals before they trade.

This repository starts from a current DEX architecture review instead of copying
today's default AMM pattern. The short finding is that most high-volume "DEX" venues
are not true peer-to-peer networks. They are usually peer-to-pool smart contracts,
chain-level order books, appchain order books, or intent/RFQ systems with solver
infrastructure. EURBT therefore uses:

- signed, portable orders;
- integer transaction amounts with 8-decimal fixed-point atoms;
- deterministic local matching;
- P2P message envelopes that can be gossiped without a central API;
- authorised actors: identified people, agents with owner persons, and the VoteBank DAO;
- human-readable trust explanations;
- settlement plans that separate non-custodial crypto locks from fiat/euro rails.

The code does not move real funds yet. It is the protocol core and test harness for
building toward a serverless euro DEX.

## Research

- `docs/DEX_RESEARCH.md` explains the top-100 DEX snapshot and classification.
- `docs/INTEGER_TRANSACTIONS.md` explains the integer base and actor transaction policy.
- `data/dex_top100_2026-06-21.json` stores the generated top-100 matrix.

## Website

GitHub Pages serves the browser DEX from `docs/`.

Expected public URL after Pages deployment:

```text
https://knitweb.github.io/eurbt/
```

Data source: DeFiLlama DEX overview snapshot from `https://api.llama.fi/overview/dexs`.

## Development

```bash
python -m pip install -e .
python -m pytest -q
eurbt demo
```

## Design Position

Strictly true P2P means that peers can discover, negotiate, verify, and settle without
a privileged website, matching server, solver API, or custodial operator. A blockchain
or validator network can still be part of settlement, but the user-facing market should
not depend on one host.

EURBT starts with signed order gossip plus deterministic local state. A future chain
adapter can settle matched trades on EVM, XRPL, Sui, Bitcoin-style HTLCs, or Pulse/Knitweb
records without changing the order format.
