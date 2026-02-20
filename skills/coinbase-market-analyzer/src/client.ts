import * as crypto from "crypto";
import * as https from "https";
import { CoinbaseConfig, Product, Ticker, Stats24h, Candle, OrderBook } from "./types";

export class CoinbaseClient {
  private apiKey: string;
  private apiSecret: string;
  private baseUrl: string;
  private requestCount = 0;
  private lastRequestTime = 0;

  constructor(config: CoinbaseConfig) {
    this.apiKey = config.apiKey;
    this.apiSecret = config.apiSecret;
    this.baseUrl = config.baseUrl || "https://api.exchange.coinbase.com";
  }

  private async rateLimitDelay(): Promise<void> {
    const minInterval = 100;
    const now = Date.now();
    const elapsed = now - this.lastRequestTime;
    if (elapsed < minInterval) {
      await new Promise(resolve => setTimeout(resolve, minInterval - elapsed));
    }
    this.lastRequestTime = Date.now();
  }

  private sign(timestamp: string, method: string, path: string, body: string = ""): string {
    const message = timestamp + method.toUpperCase() + path + body;
    const hmac = crypto.createHmac("sha256", Buffer.from(this.apiSecret, "base64"));
    hmac.update(message);
    return hmac.digest("base64");
  }

  private async request<T>(
    method: string,
    path: string,
    body?: any,
    retries = 3
  ): Promise<T> {
    await this.rateLimitDelay();

    const timestamp = Date.now() / 1000;
    const bodyStr = body ? JSON.stringify(body) : "";
    const signature = this.sign(timestamp.toString(), method, path, bodyStr);

    const options: https.RequestOptions = {
      method,
      headers: {
        "CB-ACCESS-KEY": this.apiKey,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp.toString(),
        "CB-ACCESS-PASSPHRASE": "",
        "Content-Type": "application/json",
        "User-Agent": "OpenClaw-Coinbase-Analyzer/1.0"
      }
    };

    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const url = new URL(this.baseUrl + path);
        options.hostname = url.hostname;
        options.path = url.pathname + url.search;
        options.port = url.port || 443;

        const response = await this.makeRequest(options, bodyStr);
        this.requestCount++;
        return response as T;
      } catch (error: any) {
        const isRetryable = error.statusCode >= 500 || error.code === "ECONNRESET" || error.code === "ETIMEDOUT";
        if (attempt < retries - 1 && isRetryable) {
          const backoff = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
          await new Promise(resolve => setTimeout(resolve, backoff));
          continue;
        }
        throw error;
      }
    }
    throw new Error("Max retries exceeded");
  }

  private makeRequest(options: https.RequestOptions, body: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        let data = "";
        res.on("data", chunk => data += chunk);
        res.on("end", () => {
          if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
            try {
              resolve(JSON.parse(data));
            } catch {
              resolve(data);
            }
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });
      req.on("error", reject);
      if (body) req.write(body);
      req.end();
    });
  }

  async getProducts(): Promise<Product[]> {
    return this.request<Product[]>("GET", "/products");
  }

  async getTicker(productId: string): Promise<Ticker> {
    return this.request<Ticker>("GET", `/products/${productId}/ticker`);
  }

  async get24HourStats(productId: string): Promise<Stats24h> {
    return this.request<Stats24h>("GET", `/products/${productId}/stats`);
  }

  async getCandles(
    productId: string,
    granularity: number,
    start?: string,
    end?: string
  ): Promise<number[][]> {
    let path = `/products/${productId}/candles?granularity=${granularity}`;
    if (start) path += `&start=${start}`;
    if (end) path += `&end=${end}`;
    const rawCandles = await this.request<number[][]>("GET", path);
    return rawCandles;
  }

  async getOrderBook(productId: string, level: number = 2): Promise<OrderBook> {
    return this.request<OrderBook>("GET", `/products/${productId}/book?level=${level}`);
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.request<any>("GET", "/time");
      return true;
    } catch {
      return false;
    }
  }
}