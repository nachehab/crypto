export interface CoinbaseConfig {
  apiKey: string;
  apiSecret: string;
  baseUrl?: string;
}

export interface Product {
  id: string;
  base_currency: string;
  quote_currency: string;
  base_min_size?: string;
  base_max_size?: string;
  quote_increment?: string;
  status?: string;
  display_name?: string;
  trading_disabled?: boolean;
}

export interface Ticker {
  trade_id?: number;
  price: string;
  size?: string;
  time?: string;
  bid?: string;
  ask?: string;
  volume?: string;
}

export interface Stats24h {
  open: string;
  high: string;
  low: string;
  volume: string;
  last?: string;
  volume_30day?: string;
}

export interface Candle {
  time: number;
  low: number;
  high: number;
  open: number;
  close: number;
  volume: number;
}

export interface OrderBook {
  bids: [string, string, number][];
  asks: [string, string, number][];
  sequence?: number;
  auction_mode?: boolean;
  auction?: string;
  time?: string;
}

export interface MarketAnalysisRow {
  product_id: string;
  base: string;
  quote: string;
  price: number | null;
  change_pct: number | null;
  volume: number | null;
  volatility: number | null;
  spread: number | null;
  trend_label: "bullish" | "neutral" | "bearish" | null;
  notes: string[];
  reasons: string[];
}

export interface AnalysisResult {
  markets: MarketAnalysisRow[];
  summary: string;
  timestamp: string;
}

export interface TrendSignal {
  product_id: string;
  timeframe: string;
  price: number | null;
  rsi14: number | null;
  ema20: number | null;
  ema50: number | null;
  atr14: number | null;
  trend_label: "bullish" | "neutral" | "bearish";
  notes: string[];
}

export interface MultiTimeframeResult {
  product_id: string;
  timeframes: {
    "1h": TrendSignal;
    "4h": TrendSignal;
    "1d": TrendSignal;
  };
  unified_verdict: "bullish" | "neutral" | "bearish" | "conflicted";
  conflicts: string[];
  summary: string;
}

export interface DiagnosticResult {
  status: "ok" | "warning" | "error";
  checks: {
    name: string;
    passed: boolean;
    message: string;
  }[];
  next_steps: string[];
}