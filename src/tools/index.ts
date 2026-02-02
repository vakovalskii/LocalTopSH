/**
 * Tools Registry
 * Pattern: Action + Object
 * 
 * Core tools:
 * - run_command      : Execute shell commands
 * - read_file        : Read file contents
 * - write_file       : Write/create files
 * - edit_file        : Edit files (find & replace)
 * - delete_file      : Delete files
 * - search_files     : Find files by glob pattern
 * - search_text      : Search text in files (grep)
 * - list_directory   : List directory contents
 * - search_web       : Search the internet (Z.AI + Tavily)
 * - fetch_page       : Fetch URL content
 * - manage_tasks     : Task management (todo list)
 * - ask_user         : Ask user with button options
 */

import * as bash from './bash.js';
import * as files from './files.js';
import * as web from './web.js';
import * as tasks from './tasks.js';
import * as ask from './ask.js';
import * as memory from './memory.js';

// Re-export callback setters
export { setApprovalCallback } from './bash.js';
export { setAskCallback } from './ask.js';
export { getMemoryForPrompt, logGlobal, getGlobalLog, shouldTroll, getTrollMessage, saveChatMessage, getChatHistory } from './memory.js';
export { getChatHistory as getChatHistoryForPrompt } from './memory.js';

// Tool definitions for OpenAI
export const definitions = [
  bash.definition,
  files.readDefinition,
  files.writeDefinition,
  files.editDefinition,
  files.deleteDefinition,
  files.searchFilesDefinition,
  files.searchTextDefinition,
  files.listDirectoryDefinition,
  web.searchWebDefinition,
  web.fetchPageDefinition,
  tasks.manageTasksDefinition,
  ask.definition,
  memory.definition,
];

// Tool names
export const toolNames = definitions.map(d => d.function.name);

// Result type
export interface ToolResult {
  success: boolean;
  output?: string;
  error?: string;
}

// Context
export interface ToolContext {
  cwd: string;
  sessionId?: string;
  chatId?: number;
  chatType?: 'private' | 'group' | 'supergroup' | 'channel';
  zaiApiKey?: string;
  tavilyApiKey?: string;
}

// Format args for logging (truncate long values)
function formatArgs(args: Record<string, any>): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(args)) {
    let v = typeof value === 'string' ? value : JSON.stringify(value);
    if (v.length > 60) v = v.slice(0, 60) + '...';
    parts.push(`${key}=${v}`);
  }
  return parts.join(', ');
}

// Execute tool by name
export async function execute(
  name: string, 
  args: Record<string, any>,
  ctx: ToolContext
): Promise<ToolResult> {
  const argsStr = formatArgs(args);
  console.log(`[tool] ${name}(${argsStr})`);
  
  let result: ToolResult;
  
  switch (name) {
    case 'run_command':
      result = await bash.execute(args as any, { cwd: ctx.cwd, sessionId: ctx.sessionId, chatId: ctx.chatId, chatType: ctx.chatType });
      break;
    
    case 'read_file':
      result = await files.executeRead(args as any, ctx.cwd);
      break;
    
    case 'write_file':
      result = await files.executeWrite(args as any, ctx.cwd);
      break;
    
    case 'edit_file':
      result = await files.executeEdit(args as any, ctx.cwd);
      break;
    
    case 'delete_file':
      result = await files.executeDelete(args as any, ctx.cwd);
      break;
    
    case 'search_files':
      result = await files.executeSearchFiles(args as any, ctx.cwd);
      break;
    
    case 'search_text':
      result = await files.executeSearchText(args as any, ctx.cwd);
      break;
    
    case 'list_directory':
      result = await files.executeListDirectory(args as any, ctx.cwd);
      break;
    
    case 'search_web':
      result = await web.executeSearchWeb(args as any, ctx.zaiApiKey, ctx.tavilyApiKey);
      break;
    
    case 'fetch_page':
      result = await web.executeFetchPage(args as any, ctx.zaiApiKey);
      break;
    
    case 'manage_tasks':
      result = await tasks.executeManageTasks(args as any, ctx.sessionId || 'default');
      break;
    
    case 'ask_user':
      result = await ask.execute(args as any, ctx.sessionId || 'default');
      break;
    
    case 'memory':
      result = await memory.execute(args as any, ctx.cwd);
      break;
    
    default:
      result = { success: false, error: `Unknown tool: ${name}` };
  }
  
  // Log result
  const output = result.success ? (result.output?.slice(0, 80) || 'ok') : `ERROR: ${result.error?.slice(0, 60)}`;
  console.log(`[tool] → ${output}${(result.output?.length || 0) > 80 ? '...' : ''}`);
  
  return result;
}
