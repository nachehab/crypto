import { CoinbaseClient } from "./client";
import { MarketAnalyzer } from "./analysis";

const API_KEY = process.env.COINBASE_API_KEY || "";
const API_SECRET = process.env.COINBASE_API_SECRET || "";

if (!API_KEY || !API_SECRET) {
  console.error("ERROR: COINBASE_API_KEY and COINBASE_API_SECRET must be set");
  process.exit(1);
}

const client = new CoinbaseClient({
  apiKey: API_KEY,
  apiSecret: API_SECRET
});

const analyzer = new MarketAnalyzer(client);

export async function handleCommand(command: string, args: any) {
  switch (command) {
    case "coinbase_doctor":
      return analyzer.coinbasDoctor();
    case "list_markets":
      return analyzer.listMarkets(args);
    case "top_movers":
      return analyzer.topMovers(args);
    case "volatility_rank":
      return analyzer.volatilityRank(args);
    case "liquidity_snapshot":
      return analyzer.liquiditySnapshot(args);
    case "trend_signal":
      return analyzer.trendSignal(args);
    case "multi_timeframe_summary":
      return analyzer.multiTimeframeSummary(args);
    case "analyze_markets":
      return analyzer.analyzeMarkets(args);
    default:
      throw new Error(`Unknown command: ${command}`);
  }
}

if (require.main === module) {
  const command = process.argv[2];
  const argsRaw = process.argv.slice(3);
  const args: any = {};

  for (let i = 0; i < argsRaw.length; i += 2) {
    const key = argsRaw[i].replace(/^--/, "");
    const value = argsRaw[i + 1];
    args[key] = isNaN(Number(value)) ? value : Number(value);
  }

  handleCommand(command, args)
    .then(result => {
      console.log(JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch(error => {
      console.error("ERROR:", error.message);
      process.exit(1);
    });
}

export { CoinbaseClient, MarketAnalyzer };