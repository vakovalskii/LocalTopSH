/**
 * Rate limiting and user locking
 */

import { CONFIG } from './config.js';

// Global rate limiter
let globalLastSend = 0;
const lastGroupMessage = new Map<number, number>();
let sendMutex = Promise.resolve();

// Safe send with global rate limiting
export async function safeSend<T>(
  chatId: number,
  fn: () => Promise<T>,
  maxRetries = CONFIG.rateLimit.maxRetries
): Promise<T | null> {
  const myTurn = sendMutex;
  let release: () => void;
  sendMutex = new Promise(r => { release = r; });
  
  await myTurn;
  
  try {
    const now = Date.now();
    const globalWait = CONFIG.rateLimit.globalMinInterval - (now - globalLastSend);
    if (globalWait > 0) {
      await new Promise(r => setTimeout(r, globalWait));
    }
    
    if (chatId < 0) {
      const lastGroup = lastGroupMessage.get(chatId) || 0;
      const groupWait = CONFIG.rateLimit.groupMinInterval - (Date.now() - lastGroup);
      if (groupWait > 0) {
        await new Promise(r => setTimeout(r, groupWait));
      }
      lastGroupMessage.set(chatId, Date.now());
    }
    
    globalLastSend = Date.now();
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (e: any) {
        if (e.response?.error_code === 429) {
          const retryAfter = (e.response?.parameters?.retry_after || 30) + CONFIG.rateLimit.retryBuffer;
          console.log(`[rate-limit] 429, waiting ${retryAfter}s (${attempt}/${maxRetries})`);
          if (attempt < maxRetries) {
            await new Promise(r => setTimeout(r, retryAfter * 1000));
            globalLastSend = Date.now();
          }
        } else {
          console.error(`[send] Error: ${e.message?.slice(0, 100)}`);
          return null;
        }
      }
    }
    return null;
  } finally {
    release!();
  }
}

// Per-user rate limiter
const userLocks = new Map<number, Promise<void>>();

export async function withUserLock<T>(userId: number, fn: () => Promise<T>): Promise<T> {
  const existing = userLocks.get(userId);
  let resolve: () => void;
  const myLock = new Promise<void>(r => { resolve = r; });
  userLocks.set(userId, myLock);
  
  if (existing) await existing;
  
  try {
    return await fn();
  } finally {
    resolve!();
    if (userLocks.get(userId) === myLock) {
      userLocks.delete(userId);
    }
  }
}

// Concurrent users limiter
const activeUsers = new Set<number>();
let maxConcurrentUsers = CONFIG.users.maxConcurrent;

export function setMaxConcurrentUsers(max: number) {
  maxConcurrentUsers = max;
}

export function canAcceptUser(userId: number): boolean {
  if (activeUsers.has(userId)) return true;
  return activeUsers.size < maxConcurrentUsers;
}

export function markUserActive(userId: number) {
  activeUsers.add(userId);
}

export function markUserInactive(userId: number) {
  activeUsers.delete(userId);
}
