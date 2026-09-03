# @quant-trade/agent-tools-pi

pi extension for the 9 read-only `quant_trade` market analysis and decision-support tools.

```bash
pi install npm:@quant-trade/agent-tools-pi
```

The Python package `quant-trade-agent-tools` and reachable `quant_trade` HTTP services are required. See the repository root `README.md` for environment variables, safety boundaries and development commands.

The shared schema supports `9984.T` and `6981.T` for quote, kline, signals, trending, backtest and
benchmark. News and aggregate sentiment remain global upstream feeds. The extension only serializes
arguments to the canonical CLI; it contains no strategy defaults or backtest implementation.

Compatibility and runtime:

- tested host API: `@earendil-works/pi-coding-agent` 0.84.x;
- runtime: Node.js >= 22.19 plus `uvx` on `PATH`;
- Bun is used to test/build this repository, but the published extension does not require a global Bun runtime;
- no sibling `../quant_trade` checkout or Python import is used; all market access is HTTP.
