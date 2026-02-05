/**
 * Bot configuration
 */

export const CONFIG = {
  // Rate limits
  rateLimit: {
    globalMinInterval: 200,
    groupMinInterval: 5000,
    maxRetries: 3,
    retryBuffer: 5,
  },
  
  // Messages
  messages: {
    maxLength: 4000,
  },
  
  // Bot behavior
  bot: {
    typingInterval: 4000,
    thinkDelayMin: 500,
    thinkDelayMax: 2000,
    ignoreChance: 0.05,
    ignorePrivateChance: 0.02,
    delayedResponseChance: 0.1,
    delayedResponseMin: 3000,
    delayedResponseMax: 15000,
    trollDelay: 2000,
  },
  
  // Reactions
  reactions: {
    randomChance: 0.15,
    minInterval: 5000,
    minTextLength: 10,
    llmMaxTokens: 10,
    weights: { positive: 0.5, neutral: 0.35, negative: 0.15 },
  },
  
  allReactions: {
    positive: ['👍', '❤️', '🔥', '🎉', '💯', '🏆', '👏', '😍', '🤗'],
    negative: ['👎', '💩', '🤡', '🗿', '😴', '🤮'],
    neutral: ['👀', '🤔', '😈', '🤯', '😱'],
  },
  
  // Triggers
  triggers: {
    randomReplyChance: 0.08,
    minTextForRandom: 30,
  },
  
  // Users
  users: {
    maxConcurrent: 10,
  },
  
  // Admin
  admin: {
    userId: parseInt(process.env.ADMIN_USER_ID || '0'),
  },
  
  // AFK
  afk: {
    defaultMinutes: 30,
    maxMinutes: 480,
  },
  
  // Done emojis
  doneEmojis: ['👍', '✅', '🔥', '💯', '🎉', '👏', '🏆'] as const,
};

export function getRandomDoneEmoji(): string {
  return CONFIG.doneEmojis[Math.floor(Math.random() * CONFIG.doneEmojis.length)];
}

export function getAllReactions(): string[] {
  return [
    ...CONFIG.allReactions.positive,
    ...CONFIG.allReactions.negative,
    ...CONFIG.allReactions.neutral,
  ];
}
