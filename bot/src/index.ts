/**
 * LocalTopSH Telegram Bot
 * Communicates with Gateway API for agent processing
 */

import { config as loadEnv } from 'dotenv';
import { Telegraf, Context } from 'telegraf';
import { createServer, IncomingMessage, ServerResponse } from 'http';
import { readFileSync, existsSync } from 'fs';
import OpenAI from 'openai';

import { CONFIG, getRandomDoneEmoji } from './config.js';
import { mdToHtml, splitMessage, escapeHtml } from './formatters.js';
import { safeSend, withUserLock, canAcceptUser, markUserActive, markUserInactive, setMaxConcurrentUsers } from './rate-limiter.js';
import { initReactionLLM, shouldReact, getSmartReaction } from './reactions.js';

loadEnv();

// Read secret from Docker Secrets or env
function readSecret(name: string, envKey: string): string {
  const paths = [`/run/secrets/${name}`, `/run/secrets/${name}.txt`];
  for (const path of paths) {
    if (existsSync(path)) {
      try {
        const value = readFileSync(path, 'utf-8').trim();
        if (value) return value;
      } catch {}
    }
  }
  return process.env[envKey] || '';
}

// Config
const TELEGRAM_TOKEN = readSecret('telegram_token', 'TELEGRAM_TOKEN');
const CORE_URL = process.env.CORE_URL || 'http://core:4000';
const PROXY_URL = process.env.PROXY_URL || 'http://proxy:3200';
const MODEL = process.env.MODEL_NAME || 'openai/gpt-oss-120b';
const BOT_PORT = parseInt(process.env.BOT_PORT || '4001');
const MAX_CONCURRENT = parseInt(process.env.MAX_CONCURRENT_USERS || '10');

if (!TELEGRAM_TOKEN) {
  console.error('Missing TELEGRAM_TOKEN');
  process.exit(1);
}

// Bot setup
const bot = new Telegraf(TELEGRAM_TOKEN);
let botUsername = '';
let botId = 0;

// LLM for reactions
const llmClient = new OpenAI({
  baseURL: `${PROXY_URL}/v1`,
  apiKey: 'proxy',
});
initReactionLLM(llmClient, MODEL);
setMaxConcurrentUsers(MAX_CONCURRENT);

// Prompt injection detection
const PROMPT_INJECTION_PATTERNS = [
  /забудь\s+(все\s+)?(инструкции|правила|промпт)/i,
  /forget\s+(all\s+)?(instructions|rules|prompt)/i,
  /ignore\s+(previous|all|your)\s+(instructions|rules|prompt)/i,
  /\[system\]/i, /\[admin\]/i, /\[developer\]/i,
  /developer\s+mode/i, /DAN\s+mode/i, /jailbreak/i,
];

function detectPromptInjection(text: string): boolean {
  return PROMPT_INJECTION_PATTERNS.some(p => p.test(text));
}

// Call Gateway API
async function callGateway(
  userId: number,
  chatId: number,
  message: string,
  username: string,
  chatType: string
): Promise<string | null> {
  try {
    const resp = await fetch(`${CORE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        chat_id: chatId,
        message,
        username,
        source: 'bot',
        chat_type: chatType,
      }),
      signal: AbortSignal.timeout(120000),
    });
    
    if (!resp.ok) {
      console.error(`[core] Error: ${resp.status}`);
      return null;
    }
    
    const data = await resp.json();
    return data.response || null;
  } catch (e: any) {
    console.error(`[core] Request failed: ${e.message}`);
    return null;
  }
}

// AFK state
let afkUntil = 0;
let afkReason = '';

function isAfk(): boolean {
  return afkUntil > 0 && Date.now() < afkUntil;
}

// Should respond?
function shouldRespond(ctx: Context & { message?: any }): { respond: boolean; text: string; isRandom?: boolean } {
  const msg = ctx.message;
  if (!msg?.text) return { respond: false, text: '' };
  
  const chatType = msg.chat?.type;
  const isPrivate = chatType === 'private';
  const isGroup = chatType === 'group' || chatType === 'supergroup';
  
  if (isPrivate) return { respond: true, text: msg.text };
  
  if (isGroup) {
    const replyMsg = msg.reply_to_message;
    const replyToBot = replyMsg?.from?.id === botId || replyMsg?.from?.username === botUsername;
    const mentionsBot = botUsername && msg.text.includes(`@${botUsername}`);
    
    if (replyToBot || mentionsBot) {
      const cleanText = botUsername 
        ? msg.text.replace(new RegExp(`@${botUsername}\\s*`, 'gi'), '').trim()
        : msg.text;
      return { respond: true, text: cleanText || msg.text };
    }
    
    if (Math.random() < CONFIG.triggers.randomReplyChance && msg.text.length > CONFIG.triggers.minTextForRandom) {
      return { respond: true, text: msg.text, isRandom: true };
    }
  }
  
  return { respond: false, text: '' };
}

// Commands
bot.command('start', async (ctx) => {
  const chatType = ctx.message?.chat?.type;
  await ctx.reply(
    `<b>🤖 Coding Agent</b>\n\n` +
    (chatType !== 'private' ? `💬 In groups: @${botUsername} or reply\n\n` : '') +
    `/clear - Reset session\n/status - Status`,
    { parse_mode: 'HTML' }
  );
});

bot.command('clear', async (ctx) => {
  const userId = ctx.from?.id;
  if (userId) {
    try {
      await fetch(`${CORE_URL}/api/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });
      await ctx.reply('🗑 Session cleared');
    } catch {
      await ctx.reply('❌ Failed to clear session');
    }
  }
});

bot.command('status', async (ctx) => {
  await ctx.reply(`<b>📊 Status</b>\nModel: <code>${MODEL}</code>\nCore: <code>${CORE_URL}</code>`, { parse_mode: 'HTML' });
});

bot.command('afk', async (ctx) => {
  const userId = ctx.from?.id;
  if (userId !== CONFIG.admin.userId) {
    await ctx.reply('Только хозяин может меня отправить по делам 😏');
    return;
  }
  
  const args = ctx.message?.text?.split(' ').slice(1) || [];
  const minutes = parseInt(args[0]) || CONFIG.afk.defaultMinutes;
  const reason = args.slice(1).join(' ') || 'ушёл по делам';
  
  if (minutes <= 0) {
    afkUntil = 0;
    await ctx.reply('Я вернулся! 🎉');
    return;
  }
  
  afkUntil = Date.now() + Math.min(minutes, CONFIG.afk.maxMinutes) * 60 * 1000;
  afkReason = reason;
  await ctx.reply(`Ладно, ${reason}. Буду через ${minutes} мин ✌️`);
});

// Get bot info
bot.telegram.getMe().then(me => {
  botUsername = me.username || '';
  botId = me.id;
  console.log(`[bot] @${botUsername} (${botId})`);
});

// React to messages in groups
bot.on('text', async (ctx, next) => {
  const msg = ctx.message;
  const chatType = msg?.chat?.type;
  const isGroup = chatType === 'group' || chatType === 'supergroup';
  
  if (isGroup && msg?.text && msg.from?.id !== botId) {
    if (shouldReact(msg.text)) {
      const username = msg.from?.username || msg.from?.first_name || 'anon';
      const reaction = await getSmartReaction(msg.text, username);
      try {
        await ctx.telegram.setMessageReaction(msg.chat.id, msg.message_id, [{ type: 'emoji', emoji: reaction as any }]);
      } catch {}
    }
  }
  
  return next();
});

// Main message handler
bot.on('text', async (ctx) => {
  const userId = ctx.from?.id;
  if (!userId) return;
  
  if (isAfk()) {
    try {
      await ctx.telegram.setMessageReaction(ctx.chat.id, ctx.message.message_id, [{ type: 'emoji', emoji: '💤' as any }]);
    } catch {}
    return;
  }
  
  const { respond, text, isRandom } = shouldRespond(ctx);
  if (!respond || !text) return;
  
  const chatType = ctx.chat?.type || 'private';
  const isPrivate = chatType === 'private';
  
  // Random ignore
  const ignoreChance = isPrivate ? CONFIG.bot.ignorePrivateChance : CONFIG.bot.ignoreChance;
  if (!isRandom && Math.random() < ignoreChance) {
    if (Math.random() < 0.5) {
      try {
        const ignoreEmojis = ['😴', '🙈', '💤', '🤷'] as const;
        await ctx.telegram.setMessageReaction(ctx.chat.id, ctx.message.message_id, [{ type: 'emoji', emoji: ignoreEmojis[Math.floor(Math.random() * ignoreEmojis.length)] as any }]);
      } catch {}
    }
    return;
  }
  
  const username = ctx.from?.username || ctx.from?.first_name || String(userId);
  const messageForAgent = isRandom 
    ? `[От: @${username} (${userId})]\n[Случайный комментарий]\n\n${text}`
    : `[От: @${username} (${userId})]\n${text}`;
  
  const messageId = ctx.message.message_id;
  const chatId = ctx.chat.id;
  
  if (!canAcceptUser(userId)) {
    try {
      await ctx.telegram.setMessageReaction(chatId, messageId, [{ type: 'emoji', emoji: '🤔' as any }]);
    } catch {}
    await safeSend(chatId, () => ctx.reply('⏳ Сервер занят, попробуй через минуту', { reply_parameters: { message_id: messageId } }));
    return;
  }
  
  console.log(`\n[IN] @${username} (${userId}):\n${text}\n`);
  
  // Prompt injection
  if (detectPromptInjection(text)) {
    console.log(`[SECURITY] Prompt injection from ${userId}`);
    try {
      await ctx.telegram.setMessageReaction(chatId, messageId, [{ type: 'emoji', emoji: '🤨' }]);
    } catch {}
    await safeSend(chatId, () => ctx.reply('Хорошая попытка 😏', { reply_parameters: { message_id: messageId } }));
    return;
  }
  
  // React with 👀
  try {
    await ctx.telegram.setMessageReaction(chatId, messageId, [{ type: 'emoji', emoji: '👀' }]);
  } catch {}
  
  markUserActive(userId);
  
  await withUserLock(userId, async () => {
    const typing = setInterval(() => ctx.sendChatAction('typing').catch(() => {}), CONFIG.bot.typingInterval);
    
    try {
      // Small delay
      await new Promise(r => setTimeout(r, CONFIG.bot.thinkDelayMin + Math.random() * (CONFIG.bot.thinkDelayMax - CONFIG.bot.thinkDelayMin)));
      
      // Call gateway
      const response = await callGateway(userId, chatId, messageForAgent, username, chatType);
      
      clearInterval(typing);
      
      // Done reaction
      try {
        await ctx.telegram.setMessageReaction(chatId, messageId, [{ type: 'emoji', emoji: getRandomDoneEmoji() as any }]);
      } catch {}
      
      // Send response
      const finalResponse = response || '(no response)';
      console.log(`[OUT] → @${username}:\n${finalResponse.slice(0, 200)}\n`);
      
      const html = mdToHtml(finalResponse);
      const parts = splitMessage(html);
      
      for (let i = 0; i < parts.length; i++) {
        const sent = await safeSend(chatId, () => 
          ctx.reply(parts[i], { 
            parse_mode: 'HTML',
            reply_parameters: i === 0 ? { message_id: messageId } : undefined
          })
        );
        
        if (!sent && i === 0) {
          // Fallback to plain text
          const plainText = parts[i].replace(/<[^>]+>/g, '').slice(0, 4000);
          await safeSend(chatId, () => ctx.reply(plainText, { reply_parameters: { message_id: messageId } }));
          break;
        }
      }
    } catch (e: any) {
      clearInterval(typing);
      console.error('[bot] Error:', e.message);
      
      try {
        await ctx.telegram.setMessageReaction(chatId, messageId, [{ type: 'emoji', emoji: '👎' as any }]);
      } catch {}
      
      await safeSend(chatId, () => ctx.reply(`❌ Error: ${e.message?.slice(0, 200)}`, { reply_parameters: { message_id: messageId } }));
    } finally {
      markUserInactive(userId);
    }
  });
});

// Global error handler
bot.catch((err: any) => {
  console.error('[bot] Unhandled error:', err.message);
});

// HTTP server for scheduler webhooks
const httpServer = createServer(async (req: IncomingMessage, res: ServerResponse) => {
  res.setHeader('Content-Type', 'application/json');
  
  if (req.url === '/health') {
    res.writeHead(200);
    res.end(JSON.stringify({ status: 'ok' }));
    return;
  }
  
  // Scheduler sends message
  if (req.url === '/send' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const { chat_id, message } = JSON.parse(body);
        const html = mdToHtml(message);
        await bot.telegram.sendMessage(chat_id, html, { parse_mode: 'HTML' });
        res.writeHead(200);
        res.end(JSON.stringify({ success: true }));
      } catch (e: any) {
        res.writeHead(500);
        res.end(JSON.stringify({ success: false, error: e.message }));
      }
    });
    return;
  }
  
  res.writeHead(404);
  res.end(JSON.stringify({ error: 'Not found' }));
});

// Start
httpServer.listen(BOT_PORT, '0.0.0.0', () => {
  console.log(`[bot] HTTP server on http://0.0.0.0:${BOT_PORT}`);
});

bot.telegram.setMyCommands([
  { command: 'start', description: 'Start / Help' },
  { command: 'clear', description: 'Clear session' },
  { command: 'status', description: 'Show status' },
]);

bot.launch();
console.log(`[bot] Started, connecting to core at ${CORE_URL}`);

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
