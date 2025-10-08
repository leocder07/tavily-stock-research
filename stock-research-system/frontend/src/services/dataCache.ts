/**
 * Data Caching Service
 * Persists market data to localStorage for instant display while fresh data loads
 */

interface CachedData<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

class DataCacheService {
  private readonly CACHE_PREFIX = 'stock_ai_cache_';
  private readonly DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Save data to cache with timestamp
   */
  set<T>(key: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    try {
      const cacheKey = `${this.CACHE_PREFIX}${key}`;
      const cachedData: CachedData<T> = {
        data,
        timestamp: Date.now(),
        expiresAt: Date.now() + ttl,
      };
      localStorage.setItem(cacheKey, JSON.stringify(cachedData));
    } catch (error) {
      console.warn(`Failed to cache data for ${key}:`, error);
    }
  }

  /**
   * Get cached data if available and not expired
   */
  get<T>(key: string, allowStale: boolean = false): T | null {
    try {
      const cacheKey = `${this.CACHE_PREFIX}${key}`;
      const cached = localStorage.getItem(cacheKey);

      if (!cached) return null;

      const cachedData: CachedData<T> = JSON.parse(cached);

      // Return data even if stale if allowStale is true
      if (allowStale) {
        return cachedData.data;
      }

      // Check if expired
      if (Date.now() > cachedData.expiresAt) {
        return null;
      }

      return cachedData.data;
    } catch (error) {
      console.warn(`Failed to get cached data for ${key}:`, error);
      return null;
    }
  }

  /**
   * Get cache metadata (age, freshness)
   */
  getMetadata(key: string): { age: number; isStale: boolean; timestamp: number } | null {
    try {
      const cacheKey = `${this.CACHE_PREFIX}${key}`;
      const cached = localStorage.getItem(cacheKey);

      if (!cached) return null;

      const cachedData: CachedData<unknown> = JSON.parse(cached);
      const age = Date.now() - cachedData.timestamp;
      const isStale = Date.now() > cachedData.expiresAt;

      return {
        age,
        isStale,
        timestamp: cachedData.timestamp,
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * Clear specific cache entry
   */
  clear(key: string): void {
    const cacheKey = `${this.CACHE_PREFIX}${key}`;
    localStorage.removeItem(cacheKey);
  }

  /**
   * Clear all cached data
   */
  clearAll(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.CACHE_PREFIX))
      .forEach(key => localStorage.removeItem(key));
  }

  /**
   * Get formatted age string (e.g., "2 minutes ago")
   */
  getAgeString(key: string): string {
    const metadata = this.getMetadata(key);
    if (!metadata) return '';

    const seconds = Math.floor(metadata.age / 1000);
    if (seconds < 60) return 'Just now';

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;

    const hours = Math.floor(minutes / 60);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  }
}

export const dataCache = new DataCacheService();
export default dataCache;
