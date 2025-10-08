/**
 * Exponential Backoff Polling Utility
 * Implements intelligent polling with exponential backoff to avoid rate limiting
 */

import { useRef, useEffect } from 'react';

export interface PollingOptions {
  /** Initial delay in milliseconds (default: 1000) */
  initialDelay?: number;
  /** Maximum delay in milliseconds (default: 30000) */
  maxDelay?: number;
  /** Backoff multiplier (default: 1.5) */
  backoffMultiplier?: number;
  /** Maximum number of attempts (default: Infinity) */
  maxAttempts?: number;
  /** Function to determine if polling should stop */
  shouldStop?: (data: any) => boolean;
}

export class ExponentialBackoffPoller {
  private currentDelay: number;
  private attempts: number = 0;
  private timeoutId: NodeJS.Timeout | null = null;
  private options: Required<PollingOptions>;

  constructor(options: PollingOptions = {}) {
    this.options = {
      initialDelay: options.initialDelay || 1000,
      maxDelay: options.maxDelay || 30000,
      backoffMultiplier: options.backoffMultiplier || 1.5,
      maxAttempts: options.maxAttempts || Infinity,
      shouldStop: options.shouldStop || (() => false),
    };
    this.currentDelay = this.options.initialDelay;
  }

  /**
   * Start polling with exponential backoff
   * @param fn Function to call on each poll
   * @param onError Error handler
   */
  start(fn: () => Promise<any>, onError?: (error: Error) => void): void {
    const poll = async () => {
      try {
        this.attempts++;
        const result = await fn();

        // Check if we should stop polling
        if (this.options.shouldStop(result)) {
          this.stop();
          return;
        }

        // Check if max attempts reached
        if (this.attempts >= this.options.maxAttempts) {
          this.stop();
          return;
        }

        // Calculate next delay with exponential backoff
        this.currentDelay = Math.min(
          this.currentDelay * this.options.backoffMultiplier,
          this.options.maxDelay
        );

        // Schedule next poll
        this.timeoutId = setTimeout(poll, this.currentDelay);
      } catch (error) {
        if (onError) {
          onError(error as Error);
        }

        // Continue polling even on error (with increased delay)
        this.currentDelay = Math.min(
          this.currentDelay * this.options.backoffMultiplier * 2, // Double the backoff on error
          this.options.maxDelay
        );

        this.timeoutId = setTimeout(poll, this.currentDelay);
      }
    };

    poll();
  }

  /**
   * Stop polling
   */
  stop(): void {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }

  /**
   * Reset the poller to initial state
   */
  reset(): void {
    this.stop();
    this.currentDelay = this.options.initialDelay;
    this.attempts = 0;
  }

  /**
   * Get current delay
   */
  getCurrentDelay(): number {
    return this.currentDelay;
  }

  /**
   * Get number of attempts
   */
  getAttempts(): number {
    return this.attempts;
  }
}

/**
 * Simple polling hook for React components
 */
export const usePolling = (
  fn: () => Promise<any>,
  options: PollingOptions = {}
): { start: () => void; stop: () => void; reset: () => void } => {
  const pollerRef = useRef<ExponentialBackoffPoller | null>(null);

  useEffect(() => {
    pollerRef.current = new ExponentialBackoffPoller(options);
    return () => {
      pollerRef.current?.stop();
    };
  }, []);

  return {
    start: () => pollerRef.current?.start(fn),
    stop: () => pollerRef.current?.stop(),
    reset: () => pollerRef.current?.reset(),
  };
};
