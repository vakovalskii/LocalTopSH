/**
 * Emoji reactions
 */

import OpenAI from 'openai';
import { CONFIG, getAllReactions } from './config.js';

export const POSITIVE_REACTIONS = CONFIG.allReactions.positive;
export const NEGATIVE_REACTIONS = CONFIG.allReactions.negative;
export const NEUTRAL_REACTIONS = CONFIG.allReactions.neutral;
export const ALL_REACTIONS = getAllReactions();

export function getRandomReaction(sentiment: 'positive' | 'negative' | 'neutral' | 'random'): string {
  let pool: string[];
  const weights = CONFIG.reactions.weights;
  
  if (sentiment === 'random') {
    const rand = Math.random();
    if (rand < weights.positive) pool = POSITIVE_REACTIONS;
    else if (rand < weights.positive + weights.neutral) pool = NEUTRAL_REACTIONS;
    else pool = NEGATIVE_REACTIONS;
  } else if (sentiment === 'positive') {
    pool = POSITIVE_REACTIONS;
  } else if (sentiment === 'negative') {
    pool = NEGATIVE_REACTIONS;
  } else {
    pool = NEUTRAL_REACTIONS;
  }
  
  return pool[Math.floor(Math.random() * pool.length)];
}

let reactionLLM: OpenAI | null = null;
let reactionModel = '';

export function initReactionLLM(client: OpenAI, model: string) {
  reactionLLM = client;
  reactionModel = model;
}

export async function getSmartReaction(text: string, username: string): Promise<string> {
  if (!reactionLLM) {
    return ALL_REACTIONS[Math.floor(Math.random() * ALL_REACTIONS.length)];
  }
  
  try {
    const response = await reactionLLM.chat.completions.create({
      model: reactionModel,
      messages: [
        {
          role: 'system',
          content: `Ты выбираешь эмодзи-реакцию на сообщение. Отвечай ТОЛЬКО одним эмодзи из списка.
Доступные: ${ALL_REACTIONS.join(' ')}

ПРАВИЛА:
- Смешное → 😂🤣😈
- Крутое → 🔥💯🏆👏❤️👍
- Вопрос → 🤔👀
- Милое → 😍🤗❤️
- 🤡💩 только для явной глупости

Отвечай ОДНИМ эмодзи!`
        },
        { role: 'user', content: `@${username}: ${text.slice(0, 200)}` }
      ],
      max_tokens: CONFIG.reactions.llmMaxTokens,
      temperature: 0.9,
    });
    
    const emoji = response.choices[0]?.message?.content?.trim() || '';
    
    if (ALL_REACTIONS.includes(emoji)) return emoji;
    for (const r of ALL_REACTIONS) {
      if (emoji.includes(r)) return r;
    }
    
    return ALL_REACTIONS[Math.floor(Math.random() * ALL_REACTIONS.length)];
  } catch {
    return ALL_REACTIONS[Math.floor(Math.random() * ALL_REACTIONS.length)];
  }
}

let lastReactionTime = 0;

export function shouldReact(text: string): boolean {
  const now = Date.now();
  if (now - lastReactionTime < CONFIG.reactions.minInterval) return false;
  
  const linkPattern = /https?:\/\/\S+/g;
  const textWithoutLinks = text.replace(linkPattern, '').trim();
  if (textWithoutLinks.length < CONFIG.reactions.minTextLength) return false;
  if (text.length < 5) return false;
  
  if (Math.random() < CONFIG.reactions.randomChance) {
    lastReactionTime = now;
    return true;
  }
  return false;
}
