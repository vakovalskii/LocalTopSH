/**
 * Message formatting utilities
 */

import { CONFIG } from './config.js';

// Escape HTML
export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Convert Markdown table to readable list format
function convertTable(tableText: string): string {
  const lines = tableText.trim().split('\n');
  if (lines.length < 2) return tableText;
  
  const headerCells = lines[0].split('|').map(c => c.trim()).filter(c => c);
  const dataLines = lines.slice(2);
  
  const result: string[] = [];
  for (const line of dataLines) {
    const cells = line.split('|').map(c => c.trim()).filter(c => c);
    if (cells.length === 0) continue;
    
    const parts = cells.map((cell, i) => {
      const header = headerCells[i] || '';
      return header ? `${header}: ${cell}` : cell;
    });
    result.push(`• ${parts.join(' | ')}`);
  }
  
  return result.join('\n');
}

// Markdown → Telegram HTML
export function mdToHtml(text: string): string {
  // Use \x00 (null byte) as delimiter
  const codeBlocks: string[] = [];
  let result = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const idx = codeBlocks.length;
    const langAttr = lang ? ` class="language-${lang}"` : '';
    const block = `<pre><code${langAttr}>${escapeHtml(code.trim())}</code></pre>`;
    codeBlocks.push(block);
    return `\x00CODEBLOCK${idx}\x00`;
  });
  
  result = result.replace(/(?:^\|.+\|$\n?)+/gm, (table) => {
    return convertTable(table);
  });
  
  const inlineCode: string[] = [];
  result = result.replace(/`([^`]+)`/g, (_, code) => {
    const idx = inlineCode.length;
    inlineCode.push(`<code>${escapeHtml(code)}</code>`);
    return `\x00INLINECODE${idx}\x00`;
  });
  
  // Protect @mentions
  const mentions: string[] = [];
  result = result.replace(/@[\w_]+/g, (mention) => {
    const idx = mentions.length;
    mentions.push(mention);
    return `\x00MENTION${idx}\x00`;
  });
  
  // Protect URLs
  const urls: string[] = [];
  result = result.replace(/https?:\/\/[^\s<>]+/g, (url) => {
    const idx = urls.length;
    urls.push(url);
    return `\x00URL${idx}\x00`;
  });
  
  // Protect file paths
  const files: string[] = [];
  result = result.replace(/(?:\[[^\]]+\]\([^)]+\))|(?:\/[\w\/_.-]+)|(?:\b\w+_[\w_]*\.\w+\b)/g, (match) => {
    if (match.includes('_') || match.startsWith('[')) {
      const idx = files.length;
      files.push(match);
      return `\x00FILE${idx}\x00`;
    }
    return match;
  });
  
  // Protect IDs
  const ids: string[] = [];
  result = result.replace(/\b[A-Za-z0-9_-]{15,}\b/g, (id) => {
    if (id.includes('_')) {
      const idx = ids.length;
      ids.push(id);
      return `\x00ID${idx}\x00`;
    }
    return id;
  });
  
  result = escapeHtml(result);
  
  // Apply markdown formatting
  result = result
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/\*(.+?)\*/g, '<i>$1</i>')
    .replace(/__(.+?)__/g, '<b>$1</b>')
    .replace(/_(.+?)_/g, '<i>$1</i>')
    .replace(/~~(.+?)~~/g, '<s>$1</s>');
  
  // Restore everything
  codeBlocks.forEach((block, i) => {
    result = result.replace(`\x00CODEBLOCK${i}\x00`, block);
  });
  inlineCode.forEach((code, i) => {
    result = result.replace(`\x00INLINECODE${i}\x00`, code);
  });
  mentions.forEach((mention, i) => {
    result = result.replace(`\x00MENTION${i}\x00`, mention);
  });
  urls.forEach((url, i) => {
    result = result.replace(`\x00URL${i}\x00`, url);
  });
  ids.forEach((id, i) => {
    result = result.replace(`\x00ID${i}\x00`, id);
  });
  files.forEach((file, i) => {
    result = result.replace(`\x00FILE${i}\x00`, file);
  });
  
  // Cleanup leftover placeholders
  result = result
    .replace(/\x00CODEBLOCK\d+\x00/g, '[code]')
    .replace(/\x00INLINECODE\d+\x00/g, '')
    .replace(/\x00FILE\d+\x00/g, '')
    .replace(/\x00ID\d+\x00/g, '')
    .replace(/\x00URL\d+\x00/g, '')
    .replace(/\x00MENTION\d+\x00/g, '');
  
  return result;
}

// Split long messages
export function splitMessage(text: string, maxLen = CONFIG.messages.maxLength): string[] {
  if (text.length <= maxLen) return [text];
  
  const parts: string[] = [];
  let current = '';
  
  for (const line of text.split('\n')) {
    if (current.length + line.length + 1 > maxLen) {
      if (current) parts.push(current);
      current = line;
    } else {
      current += (current ? '\n' : '') + line;
    }
  }
  if (current) parts.push(current);
  
  return parts;
}
