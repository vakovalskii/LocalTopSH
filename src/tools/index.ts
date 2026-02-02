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

// Execute tool by name
export async function execute(
  name: string, 
  args: Record<string, any>,
  ctx: ToolContext
): Promise<ToolResult> {
  console.log(`[tool] ${name}`, Object.keys(args));
  
  switch (name) {
    case 'run_command':
      return bash.execute(args as any, { cwd: ctx.cwd, sessionId: ctx.sessionId, chatId: ctx.chatId, chatType: ctx.chatType });
    
    case 'read_file':
      return files.executeRead(args as any, ctx.cwd);
    
    case 'write_file':
      return files.executeWrite(args as any, ctx.cwd);
    
    case 'edit_file':
      return files.executeEdit(args as any, ctx.cwd);
    
    case 'delete_file':
      return files.executeDelete(args as any, ctx.cwd);
    
    case 'search_files':
      return files.executeSearchFiles(args as any, ctx.cwd);
    
    case 'search_text':
      return files.executeSearchText(args as any, ctx.cwd);
    
    case 'list_directory':
      return files.executeListDirectory(args as any, ctx.cwd);
    
    case 'search_web':
      return web.executeSearchWeb(args as any, ctx.zaiApiKey, ctx.tavilyApiKey);
    
    case 'fetch_page':
      return web.executeFetchPage(args as any);
    
    case 'manage_tasks':
      return tasks.executeManageTasks(args as any, ctx.sessionId || 'default');
    
    case 'ask_user':
      return ask.execute(args as any, ctx.sessionId || 'default');
    
    case 'memory':
      return memory.execute(args as any, ctx.cwd);
    
    default:
      return { success: false, error: `Unknown tool: ${name}` };
  }
}
