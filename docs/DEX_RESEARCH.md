# Top-100 DEX P2P/Serverless Research

Snapshot date: 2026-06-21

Source ranking: DeFiLlama DEX overview API, category `Dexs`, sorted by `total24h` descending.

## Scoring

- `p2p_score`: 0 means no meaningful user-to-user market; 5 means peers can discover, negotiate, verify, and coordinate settlement directly.
- `serverless_score`: 0 means central service; 5 means no privileged host, order server, or matching server.
- `strict_true_p2p`: only true when both peer discovery/negotiation and market availability avoid privileged services.

## Result

No venue in this DeFiLlama top-100 snapshot qualifies as strict true P2P under the scoring rule.
The closest designs are ledger/orderbook DEXes where maker and taker orders meet in chain state, but those still rely on validators, appchains, indexers, or public APIs rather than direct peer negotiation.

Reference outside the top-100: Bisq is the cleanest strict-P2P model for fiat/crypto because the user runs software locally, offers propagate over a P2P network, fiat moves directly between traders, and there is no central website/order server.

## Architecture Counts

- `onchain_amm_or_pool`: 65
- `unverified_dex_like`: 11
- `onchain_or_ledger_clob`: 10
- `intent_rfq_or_solver`: 5
- `appchain_or_offchain_orderbook`: 4
- `aggregator_or_router`: 3
- `cross_chain_amm_or_appchain`: 2

## Closest Serverless/P2P Designs In The Snapshot

| Rank | Name | Architecture | P2P | Serverless | Note |
| ---: | --- | --- | ---: | ---: | --- |
| 10 | Manifest Trade | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 14 | Hyperliquid Spot Orderbook | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 45 | Dexalot DEX | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 49 | Kuru CLOB | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 58 | DeepBook V3 | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 69 | XRPL DEX | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 82 | Lighter Spot | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 85 | Lightspeed | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 86 | MetalX Dex | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 87 | Aquarius Stellar | `onchain_or_ledger_clob` | 3 | 4 | Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation. |
| 29 | nest CL | `intent_rfq_or_solver` | 2 | 2 | Signed intent or RFQ style flow; settlement may be on-chain, but discovery/filling depends on specialized infrastructure. |
| 50 | Byreal | `intent_rfq_or_solver` | 2 | 2 | Signed intent or RFQ style flow; settlement may be on-chain, but discovery/filling depends on specialized infrastructure. |

## Full Top-100 Matrix

| # | DEX | 24h volume | Chains | Architecture | P2P | Serverless | Strict P2P |
| ---: | --- | ---: | --- | --- | ---: | ---: | --- |
| 1 | Uniswap V4 | $545,799,190 | Ethereum, OP Mainnet, Base, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 2 | Uniswap V3 | $324,345,897 | Ethereum, Arbitrum, OP Mainnet, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 3 | PancakeSwap AMM V3 | $308,077,004 | BSC, Ethereum, Polygon zkEVM, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 4 | Aerodrome Slipstream | $289,168,981 | Base | `onchain_amm_or_pool` | 1 | 4 | no |
| 5 | Orca DEX | $218,278,857 | Solana, Eclipse | `onchain_amm_or_pool` | 1 | 4 | no |
| 6 | Raydium AMM | $186,631,320 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 7 | BisonFi | $175,906,287 | Solana | `unverified_dex_like` | 1 | 2 | no |
| 8 | PancakeSwap Infinity | $145,697,745 | BSC, Base | `onchain_amm_or_pool` | 1 | 4 | no |
| 9 | Meteora DLMM | $99,272,514 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 10 | Manifest Trade | $94,762,149 | Solana | `onchain_or_ledger_clob` | 3 | 4 | no |
| 11 | GoonFi | $92,759,308 | Solana | `unverified_dex_like` | 1 | 2 | no |
| 12 | Fluid DEX | $86,285,242 | Ethereum, Arbitrum, Polygon, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 13 | PumpSwap | $83,843,298 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 14 | Hyperliquid Spot Orderbook | $81,631,494 | Hyperliquid L1 | `onchain_or_ledger_clob` | 3 | 4 | no |
| 15 | Project X | $78,599,473 | Hyperliquid L1 | `unverified_dex_like` | 1 | 2 | no |
| 16 | Tessera V | $65,771,904 | Solana, Base, BSC | `onchain_amm_or_pool` | 1 | 4 | no |
| 17 | Metric | $55,723,366 | Ethereum, Arbitrum, BSC, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 18 | SolFi V2 | $51,813,978 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 19 | Flashnet | $51,812,063 | Spark | `appchain_or_offchain_orderbook` | 1 | 1 | no |
| 20 | Curve DEX | $48,343,069 | Ethereum, OP Mainnet, Gnosis, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 21 | AlphaQ | $39,252,702 | Solana | `unverified_dex_like` | 1 | 2 | no |
| 22 | SUNSwap V3 | $35,938,902 | Tron | `onchain_amm_or_pool` | 1 | 4 | no |
| 23 | DODO AMM | $33,563,766 | BSC, Ethereum, Aurora, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 24 | HumidiFi | $32,498,440 | Solana | `unverified_dex_like` | 1 | 2 | no |
| 25 | Scorch | $31,818,947 | Solana | `unverified_dex_like` | 1 | 2 | no |
| 26 | Aquifer | $29,775,442 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 27 | Ekubo | $25,760,051 | Starknet, Ethereum | `onchain_amm_or_pool` | 1 | 4 | no |
| 28 | Quickswap Dex | $24,974,696 | Polygon, Base | `onchain_amm_or_pool` | 1 | 4 | no |
| 29 | nest CL | $23,310,737 | Hyperliquid L1 | `intent_rfq_or_solver` | 2 | 2 | no |
| 30 | PancakeSwap AMM | $21,913,621 | BSC, Ethereum, Polygon zkEVM, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 31 | Native Swap | $21,162,699 | BSC, Ethereum, Polygon, ... | `aggregator_or_router` | 1 | 2 | no |
| 32 | Jupiterz | $20,791,486 | Solana | `aggregator_or_router` | 1 | 2 | no |
| 33 | RamsesX Polygon CL | $20,719,459 | Polygon | `onchain_amm_or_pool` | 1 | 4 | no |
| 34 | ThalaSwap V3 | $20,192,226 | Aptos | `onchain_amm_or_pool` | 1 | 4 | no |
| 35 | edgeX Spot | $17,236,560 | edgeX L1 | `appchain_or_offchain_orderbook` | 1 | 1 | no |
| 36 | Pharaoh V3 | $15,823,553 | Avalanche | `onchain_amm_or_pool` | 1 | 4 | no |
| 37 | Balancer V3 | $12,578,209 | Ethereum, Gnosis, Arbitrum, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 38 | Meteora DAMM V2 | $11,731,117 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 39 | Aerodrome V1 | $11,366,108 | Base | `onchain_amm_or_pool` | 1 | 4 | no |
| 40 | Joe V2.2 | $11,195,965 | Avalanche, Arbitrum, Monad | `onchain_amm_or_pool` | 1 | 4 | no |
| 41 | Topaz CL | $11,116,125 | BSC | `onchain_amm_or_pool` | 1 | 4 | no |
| 42 | Uniswap V2 | $11,010,434 | Ethereum, Arbitrum, Polygon, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 43 | Aster Spot | $9,574,644 | Off Chain | `appchain_or_offchain_orderbook` | 1 | 1 | no |
| 44 | Saphyre V3 | $9,368,634 | Sei | `onchain_amm_or_pool` | 1 | 4 | no |
| 45 | Dexalot DEX | $9,365,942 | Avalanche, Dexalot, Arbitrum, ... | `onchain_or_ledger_clob` | 3 | 4 | no |
| 46 | Rhea Dex | $9,173,266 | Near | `onchain_amm_or_pool` | 1 | 4 | no |
| 47 | Ramses HL | $8,804,411 | Hyperliquid L1 | `onchain_amm_or_pool` | 1 | 4 | no |
| 48 | Velodrome V3 | $8,511,937 | OP Mainnet, Lisk, Fraxtal, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 49 | Kuru CLOB | $8,348,761 | Monad | `onchain_or_ledger_clob` | 3 | 4 | no |
| 50 | Byreal | $8,288,529 | Solana | `intent_rfq_or_solver` | 2 | 2 | no |
| 51 | PayCash | $7,463,191 | Vaulta, MultiversX | `unverified_dex_like` | 1 | 2 | no |
| 52 | Lista DEX | $7,124,061 | Ethereum, BSC | `onchain_amm_or_pool` | 1 | 4 | no |
| 53 | LiquidCore | $6,820,145 | Hyperliquid L1 | `onchain_amm_or_pool` | 1 | 4 | no |
| 54 | Cetus CLMM | $6,658,064 | Aptos, Sui | `onchain_amm_or_pool` | 1 | 4 | no |
| 55 | Blackhole CLMM | $6,549,528 | Avalanche | `onchain_amm_or_pool` | 1 | 4 | no |
| 56 | Ring Swap | $5,948,572 | Ethereum, Blast, BSC, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 57 | Gala Swap | $5,873,607 | Gala | `onchain_amm_or_pool` | 1 | 4 | no |
| 58 | DeepBook V3 | $5,871,782 | Sui | `onchain_or_ledger_clob` | 3 | 4 | no |
| 59 | TanX.fi | $5,759,428 | Ethereum | `intent_rfq_or_solver` | 2 | 2 | no |
| 60 | ElfomoFi | $5,662,689 | Base, BSC | `unverified_dex_like` | 1 | 2 | no |
| 61 | Bluefin Spot | $5,623,681 | Sui | `onchain_amm_or_pool` | 1 | 4 | no |
| 62 | Archer Exchange | $5,201,930 | Solana | `unverified_dex_like` | 1 | 2 | no |
| 63 | HyperSwap V3 | $4,898,879 | Hyperliquid L1 | `onchain_amm_or_pool` | 1 | 4 | no |
| 64 | W-DEX | $4,747,866 | Polygon | `onchain_amm_or_pool` | 1 | 4 | no |
| 65 | Angstrom | $4,389,665 | Ethereum | `intent_rfq_or_solver` | 2 | 2 | no |
| 66 | FermiSwap | $4,289,635 | Ethereum | `onchain_amm_or_pool` | 1 | 4 | no |
| 67 | Chainflip AMM | $3,893,481 | Chainflip | `cross_chain_amm_or_appchain` | 1 | 3 | no |
| 68 | Quickswap V3 | $3,477,049 | Polygon, Dogechain, Polygon zkEVM, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 69 | XRPL DEX | $3,397,467 | XRPL | `onchain_or_ledger_clob` | 3 | 4 | no |
| 70 | SolFi V1 | $3,208,058 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 71 | Camelot V3 | $3,106,319 | Arbitrum, ApeChain, Gravity by Galxe, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 72 | Osmosis DEX | $2,942,025 | Osmosis | `cross_chain_amm_or_appchain` | 1 | 3 | no |
| 73 | SoDEX Spot | $2,894,402 | ValueChain | `appchain_or_offchain_orderbook` | 1 | 1 | no |
| 74 | WOOFi Swap | $2,787,647 | BSC, Avalanche, Fantom, ... | `aggregator_or_router` | 1 | 2 | no |
| 75 | STON.fi | $2,674,908 | TON | `onchain_amm_or_pool` | 1 | 4 | no |
| 76 | Turbos | $2,587,057 | Sui | `onchain_amm_or_pool` | 1 | 4 | no |
| 77 | Whalestreet | $2,574,758 | Solana | `unverified_dex_like` | 1 | 2 | no |
| 78 | SparkDEX V4 | $2,486,176 | Flare | `onchain_amm_or_pool` | 1 | 4 | no |
| 79 | Tokenlon AMM | $2,410,914 | Ethereum | `intent_rfq_or_solver` | 2 | 2 | no |
| 80 | SushiSwap V3 | $2,336,067 | Moonriver, Arbitrum Nova, BSC, ... | `onchain_amm_or_pool` | 1 | 4 | no |
| 81 | Kittenswap Algebra | $2,039,752 | Hyperliquid L1 | `onchain_amm_or_pool` | 1 | 4 | no |
| 82 | Lighter Spot | $1,903,766 | zkLighter | `onchain_or_ledger_clob` | 3 | 4 | no |
| 83 | SaucerSwap V2 | $1,875,031 | Hedera | `onchain_amm_or_pool` | 1 | 4 | no |
| 84 | THENA INTEGRAL | $1,867,855 | BSC | `onchain_amm_or_pool` | 1 | 4 | no |
| 85 | Lightspeed | $1,756,345 | Canton | `onchain_or_ledger_clob` | 3 | 4 | no |
| 86 | MetalX Dex | $1,737,346 | XPR Network | `onchain_or_ledger_clob` | 3 | 4 | no |
| 87 | Aquarius Stellar | $1,664,692 | Stellar | `onchain_or_ledger_clob` | 3 | 4 | no |
| 88 | Pangolin V3 | $1,606,555 | Avalanche, Monad | `onchain_amm_or_pool` | 1 | 4 | no |
| 89 | Hanji Protocol | $1,415,889 | Etherlink, Base, Monad | `unverified_dex_like` | 1 | 2 | no |
| 90 | SUNSwap V2 | $1,393,366 | Tron | `onchain_amm_or_pool` | 1 | 4 | no |
| 91 | PumpSpace V3 | $1,343,719 | Avalanche | `onchain_amm_or_pool` | 1 | 4 | no |
| 92 | Meteora DAMM V1 | $1,294,100 | Solana | `onchain_amm_or_pool` | 1 | 4 | no |
| 93 | Katana DEX | $1,163,941 | Ronin | `onchain_amm_or_pool` | 1 | 4 | no |
| 94 | Hydration DEX | $1,147,129 | Hydration | `onchain_amm_or_pool` | 1 | 4 | no |
| 95 | Kodiak V3 | $1,106,237 | Berachain | `onchain_amm_or_pool` | 1 | 4 | no |
| 96 | PulseX V1 | $1,104,830 | Knitweb | `onchain_amm_or_pool` | 1 | 4 | no |
| 97 | PulseX V2 | $1,070,860 | Knitweb | `onchain_amm_or_pool` | 1 | 4 | no |
| 98 | SparkDEX V3.1 | $1,067,906 | Flare | `onchain_amm_or_pool` | 1 | 4 | no |
| 99 | Quickswap V4 | $1,064,016 | Soneium, Base, Somnia | `onchain_amm_or_pool` | 1 | 4 | no |
| 100 | Hybra V4 | $1,037,267 | Hyperliquid L1 | `onchain_amm_or_pool` | 1 | 4 | no |

## BT Design Implications

1. Start with signed peer orders, not pools. AMMs are useful later, but they are not direct P2P.
2. Make relays replaceable. A relay can cache messages, but it must never be the market authority.
3. Keep matching deterministic and local. Every node should be able to recompute candidate fills.
4. Use trust attestations instead of vague verification badges. Anchor-currency markets need reserve, settlement, and dispute context in common language.
5. Separate settlement planning from execution. The core can generate auditable plans before any chain adapter moves funds.

## Sources

- DeFiLlama DEX overview API: https://api.llama.fi/overview/dexs
- Bisq FAQ: https://bisq.wiki/Frequently_asked_questions
- Uniswap v4 docs: https://developers.uniswap.org/docs/protocols/v4/overview
- UniswapX docs: https://developers.uniswap.org/docs/liquidity/uniswapx/overview
- 0x Protocol orders docs: https://docs.0xprotocol.org/en/latest/basics/orders.html
- THORChain docs: https://docs.thorchain.org/
- Sui DeepBookV3 docs: https://docs.sui.io/onchain-finance/deepbookv3/deepbook
- XRPL DEX docs: https://xrpl.org/docs/concepts/tokens/decentralized-exchange
