import { CoinbaseClient } from "./client";
import {
  Product,
  MarketAnalysisRow,
  AnalysisResult,
  TrendSignal,
  MultiTimeframeResult,
  DiagnosticResult
} from "./types";
import {
  calculateRSI,
  calculateEMA,
  calculateATR,
  calculateVolatility,
  determineTrend
} from "./indicators";

export class MarketAnalyzer {
  constructor(private client: CoinbaseClient) {}

  async listMarkets(options: {
    quote_currency?: string;
    status?: string;
    limit?: number;
  } = {}): Promise<Product[]> {
    let products = await this.client.getProducts();

    if (options.quote_currency) {
      products = products.filter(p => p.quote_currency === options.quote_currency);
    }

    if (options.status) {
      products = products.filter(p => p.status === options.status);
    }

    if (options.limit) {
      products = products.slice(0, options.limit);
    }

    return products;
  }

  async topMovers(options: {
    window: "1h" | "4h" | "24h";
    quote_currency: string;
    limit: number;
    min_volume?: number;
  }): Promise<MarketAnalysisRow[]> {
    const products = await this.listMarkets({ quote_currency: options.quote_currency });
    const movers: MarketAnalysisRow[] = [];

    for (const product of products) {
      try {
        const stats = await this.client.get24HourStats(product.id);
        const price = parseFloat(stats.last || "0");
        const open = parseFloat(stats.open);
        const volume = parseFloat(stats.volume);

        if (options.min_volume && volume < options.min_volume) continue;

        const change_pct = ((price - open) / open) * 100;

        movers.push({
          product_id: product.id,
          base: product.base_currency,
          quote: product.quote_currency,
          price,
          change_pct,
          volume,
          volatility: null,
          spread: null,
          trend_label: null,
          notes: [],
          reasons: [`${change_pct > 0 ? "+" : ""}${change_pct.toFixed(2)}% in 24h`]
        });
      } catch (error) {
        continue;
      }
    }

    movers.sort((a, b) => Math.abs(b.change_pct || 0) - Math.abs(a.change_pct || 0));
    return movers.slice(0, options.limit);
  }

  async volatilityRank(options: {
    window: "1h" | "4h" | "24h";
    quote_currency: string;
    limit: number;
    min_candles?: number;
  }): Promise<MarketAnalysisRow[]> {
    const products = await this.listMarkets({ quote_currency: options.quote_currency });
    const ranked: MarketAnalysisRow[] = [];
    const granularity = options.window === "1h" ? 3600 : options.window === "4h" ? 14400 : 86400;

    for (const product of products) {
      try {
        const rawCandles = await this.client.getCandles(product.id, granularity);
        if (rawCandles.length < (options.min_candles || 20)) continue;

        const closes = rawCandles.map(c => c[4]);
        const volatility = calculateVolatility(closes);
        const ticker = await this.client.getTicker(product.id);
        const price = parseFloat(ticker.price);

        ranked.push({
          product_id: product.id,
          base: product.base_currency,
          quote: product.quote_currency,
          price,
          change_pct: null,
          volume: parseFloat(ticker.volume || "0"),
          volatility,
          spread: null,
          trend_label: null,
          notes: [`Volatility: ${(volatility! * 100).toFixed(2)}%`],
          reasons: []
        });
      } catch (error) {
        continue;
      }
    }

    ranked.sort((a, b) => (b.volatility || 0) - (a.volatility || 0));
    return ranked.slice(0, options.limit);
  }

  async liquiditySnapshot(options: {
    quote_currency: string;
    limit: number;
  }): Promise<MarketAnalysisRow[]> {
    const products = await this.listMarkets({ quote_currency: options.quote_currency });
    const snapshots: MarketAnalysisRow[] = [];

    for (const product of products) {
      try {
        const book = await this.client.getOrderBook(product.id, 2);
        if (!book.bids.length || !book.asks.length) continue;

        const bestBid = parseFloat(book.bids[0][0]);
        const bestAsk = parseFloat(book.asks[0][0]);
        const spread = ((bestAsk - bestBid) / bestBid) * 100;
        const price = (bestBid + bestAsk) / 2;

        snapshots.push({
          product_id: product.id,
          base: product.base_currency,
          quote: product.quote_currency,
          price,
          change_pct: null,
          volume: null,
          volatility: null,
          spread,
          trend_label: null,
          notes: [`Spread: ${spread.toFixed(4)}%`],
          reasons: []
        });
      } catch (error) {
        continue;
      }
    }

    snapshots.sort((a, b) => (a.spread || Infinity) - (b.spread || Infinity));
    return snapshots.slice(0, options.limit);
  }

  async trendSignal(options: {
    product_id: string;
    timeframe: "1h" | "4h" | "1d";
  }): Promise<TrendSignal> {
    const granularity = options.timeframe === "1h" ? 3600 : options.timeframe === "4h" ? 14400 : 86400;
    const rawCandles = await this.client.getCandles(options.product_id, granularity);

    if (rawCandles.length < 50) {
      return {
        product_id: options.product_id,
        timeframe: options.timeframe,
        price: null,
        rsi14: null,
        ema20: null,
        ema50: null,
        atr14: null,
        trend_label: "neutral",
        notes: ["Insufficient data"]
      };
    }

    const candles = rawCandles.map(c => ({
      time: c[0],
      low: c[1],
      high: c[2],
      open: c[3],
      close: c[4],
      volume: c[5]
    }));

    const closes = candles.map(c => c.close);
    const rsi14 = calculateRSI(closes, 14);
    const ema20 = calculateEMA(closes, 20);
    const ema50 = calculateEMA(closes, 50);
    const atr14 = calculateATR(candles, 14);
    const trend_label = determineTrend(rsi14, ema20, ema50);

    return {
      product_id: options.product_id,
      timeframe: options.timeframe,
      price: closes[closes.length - 1],
      rsi14,
      ema20,
      ema50,
      atr14,
      trend_label,
      notes: []
    };
  }

  async multiTimeframeSummary(options: {
    product_id: string;
  }): Promise<MultiTimeframeResult> {
    const [tf1h, tf4h, tf1d] = await Promise.all([
      this.trendSignal({ product_id: options.product_id, timeframe: "1h" }),
      this.trendSignal({ product_id: options.product_id, timeframe: "4h" }),
      this.trendSignal({ product_id: options.product_id, timeframe: "1d" })
    ]);

    const trends = [tf1h.trend_label, tf4h.trend_label, tf1d.trend_label];
    const conflicts: string[] = [];

    if (new Set(trends).size > 1) {
      conflicts.push(`1H: ${tf1h.trend_label}, 4H: ${tf4h.trend_label}, 1D: ${tf1d.trend_label}`);
    }

    const bullishCount = trends.filter(t => t === "bullish").length;
    const bearishCount = trends.filter(t => t === "bearish").length;

    let unified_verdict: "bullish" | "neutral" | "bearish" | "conflicted";
    if (bullishCount >= 2) unified_verdict = "bullish";
    else if (bearishCount >= 2) unified_verdict = "bearish";
    else if (conflicts.length > 0) unified_verdict = "conflicted";
    else unified_verdict = "neutral";

    const summary = `${options.product_id}: ${unified_verdict.toUpperCase()} (1H: ${tf1h.trend_label}, 4H: ${tf4h.trend_label}, 1D: ${tf1d.trend_label})`;

    return {
      product_id: options.product_id,
      timeframes: { "1h": tf1h, "4h": tf4h, "1d": tf1d },
      unified_verdict,
      conflicts,
      summary
    };
  }

  async analyzeMarkets(options: {
    quote_currency?: string;
    window?: "1h" | "4h" | "24h";
    limit?: number;
    min_volume?: number;
  }): Promise<AnalysisResult> {
    const quote_currency = options.quote_currency || "USD";
    const window = options.window || "24h";
    const limit = options.limit || 20;

    const [movers, volatility, liquidity] = await Promise.all([
      this.topMovers({ window, quote_currency, limit, min_volume: options.min_volume }),
      this.volatilityRank({ window, quote_currency, limit: 10 }),
      this.liquiditySnapshot({ quote_currency, limit: 10 })
    ]);

    const merged = new Map<string, MarketAnalysisRow>();

    for (const mover of movers) {
      merged.set(mover.product_id, { ...mover, reasons: [`Top ${window} mover`] });
    }

    for (const vol of volatility) {
      const existing = merged.get(vol.product_id);
      if (existing) {
        existing.volatility = vol.volatility;
        existing.reasons.push("High volatility");
      }
    }

    for (const liq of liquidity) {
      const existing = merged.get(liq.product_id);
      if (existing) {
        existing.spread = liq.spread;
        if (liq.spread! < 0.1) existing.reasons.push("Tight spread");
      }
    }

    const markets = Array.from(merged.values()).slice(0, limit);

    const summary = `Found ${markets.length} high-potential markets. Top mover: ${markets[0]?.product_id} (${markets[0]?.change_pct?.toFixed(2)}%). Analysis window: ${window}.`;

    return {
      markets,
      summary,
      timestamp: new Date().toISOString()
    };
  }

  async coinbasDoctor(): Promise<DiagnosticResult> {
    const checks: DiagnosticResult["checks"] = [];
    const next_steps: string[] = [];

    const hasApiKey = !!process.env.COINBASE_API_KEY;
    const hasApiSecret = !!process.env.COINBASE_API_SECRET;

    checks.push({
      name: "COINBASE_API_KEY present",
      passed: hasApiKey,
      message: hasApiKey ? "✓ API key found" : "✗ API key missing"
    });

    checks.push({
      name: "COINBASE_API_SECRET present",
      passed: hasApiSecret,
      message: hasApiSecret ? "✓ API secret found" : "✗ API secret missing"
    });

    if (!hasApiKey || !hasApiSecret) {
      next_steps.push("Set COINBASE_API_KEY and COINBASE_API_SECRET in openclaw.json under skills.entries.coinbase-market-analyzer.env");
      return { status: "error", checks, next_steps };
    }

    try {
      const healthy = await this.client.healthCheck();
      checks.push({
        name: "Coinbase API connectivity",
        passed: healthy,
        message: healthy ? "✓ Successfully connected" : "✗ Connection failed"
      });

      if (!healthy) {
        next_steps.push("Check network connectivity and Coinbase API status");
        return { status: "error", checks, next_steps };
      }
    } catch (error: any) {
      checks.push({
        name: "Coinbase API connectivity",
        passed: false,
        message: `✗ Error: ${error.message}`
      });
      next_steps.push("Verify API credentials are valid");
      next_steps.push("Check if IP is whitelisted (if required)");
      return { status: "error", checks, next_steps };
    }

    try {
      const products = await this.client.getProducts();
      checks.push({
        name: "Market data access",
        passed: true,
        message: `✓ Retrieved ${products.length} products`
      });
    } catch (error: any) {
      checks.push({
        name: "Market data access",
        passed: false,
        message: `✗ Failed to fetch products: ${error.message}`
      });
      next_steps.push("Check authentication signature generation");
      return { status: "warning", checks, next_steps };
    }

    next_steps.push("All checks passed! Ready to analyze markets.");
    return { status: "ok", checks, next_steps };
  }
}