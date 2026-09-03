# @quant-trade/agent-tools-dsh

Experimental DeepSeek Harness/Cordis adapter for 12 `quant_trade` market, analysis and product-owned conversation tools.

This package is not considered stable until it passes installation, discovery and real tool-call E2E against a pinned dsh release. See the repository root `README.md` and `docs/agent-tools-publish.md` for the compatibility gate.

The shared schema supports `9984.T` and `6981.T` for quote, kline, signals, trending, backtest and
benchmark. News and aggregate sentiment remain global upstream feeds. This adapter contains no strategy
defaults, backtest implementation or trading mutation; dsh remains experimental.

The package follows the current native plugin shape:

- `dsh.bundle.patch` installs `cordis.patch.yml` into a profile;
- the module exports `name`, `inject = ["tools"]`, and `apply(ctx)`;
- twelve `quant_*` tools register through `ctx.tools.register()`;
- tool cancellation is forwarded to the owned Python CLI subprocess.

```bash
dsh plugin --profile <profile> add @quant-trade/agent-tools-dsh@experimental
```

The current type-check target is Cordis 4.0.x with `@deepseek-ai/dsh-tools` 0.1.1-rc.2. Node.js >= 22.19, `uvx`, the Python `quant-trade-agent-tools` package, and reachable `quant_trade` HTTP services are required. Bun is a repository development/build tool, not a published adapter runtime requirement.
