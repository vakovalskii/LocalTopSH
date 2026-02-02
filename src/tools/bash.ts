/**
 * run_command - Execute shell commands
 * Pattern: Action (run) + Object (command)
 * Security: Dangerous commands require user approval
 * Background: Commands ending with & run in background
 */

import { execSync, spawn } from 'child_process';
import { checkCommand, storePendingCommand } from '../approvals/index.js';

// Patterns to sanitize from output
const SECRET_PATTERNS = [
  // API Keys and Tokens
  /([A-Za-z0-9_]*(?:API[_-]?KEY|APIKEY|TOKEN|SECRET|PASSWORD|PASS|CREDENTIAL|AUTH)[A-Za-z0-9_]*)=([^\s\n]+)/gi,
  // Common key formats
  /sk-[A-Za-z0-9]{20,}/g,  // OpenAI-style keys
  /tvly-[A-Za-z0-9-]{20,}/g,  // Tavily keys
  /[a-f0-9]{32}\.[A-Za-z0-9]{20,}/g,  // ZAI-style keys
  /ghp_[A-Za-z0-9]{36,}/g,  // GitHub tokens
  /gho_[A-Za-z0-9]{36,}/g,  // GitHub OAuth
  /github_pat_[A-Za-z0-9_]{36,}/g,  // GitHub PAT
  /xox[baprs]-[A-Za-z0-9-]{10,}/g,  // Slack tokens
  /\b[0-9]{8,12}:[A-Za-z0-9_-]{35}\b/g,  // Telegram bot tokens
  /Bearer\s+[A-Za-z0-9._-]{20,}/gi,  // Bearer tokens
  /Basic\s+[A-Za-z0-9+/=]{20,}/gi,  // Basic auth
  // AWS
  /AKIA[0-9A-Z]{16}/g,  // AWS Access Key ID
  /[A-Za-z0-9/+=]{40}(?=\s|$|")/g,  // AWS Secret (heuristic)
  // Private keys
  /-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----/g,
  // Generic secrets with common env var names
  /(?:TELEGRAM_TOKEN|API_KEY|APIKEY|ZAI_API_KEY|TAVILY_API_KEY)=\S+/gi,
];

/**
 * Remove secrets from output
 */
function sanitizeOutput(output: string): string {
  let sanitized = output;
  
  for (const pattern of SECRET_PATTERNS) {
    sanitized = sanitized.replace(pattern, (match) => {
      // For key=value patterns, keep the key name
      if (match.includes('=')) {
        const key = match.split('=')[0];
        return `${key}=[REDACTED]`;
      }
      // For raw secrets, show partial
      if (match.length > 10) {
        return match.slice(0, 4) + '***[REDACTED]***';
      }
      return '[REDACTED]';
    });
  }
  
  return sanitized;
}

// Callback for showing approval buttons (non-blocking)
let showApprovalCallback: ((
  chatId: number,
  commandId: string,
  command: string,
  reason: string
) => void) | null = null;

/**
 * Set the callback to show approval buttons
 */
export function setApprovalCallback(
  callback: (chatId: number, commandId: string, command: string, reason: string) => void
) {
  showApprovalCallback = callback;
}

export const definition = {
  type: "function" as const,
  function: {
    name: "run_command",
    description: "Run a shell command. Use for: git, npm, pip, system operations. DANGEROUS commands (rm -rf, sudo, etc.) require user approval.",
    parameters: {
      type: "object",
      properties: {
        command: { 
          type: "string", 
          description: "The shell command to execute" 
        },
      },
      required: ["command"],
    },
  },
};

export interface ExecuteContext {
  cwd: string;
  sessionId?: string;
  chatId?: number;
  chatType?: 'private' | 'group' | 'supergroup' | 'channel';
}

/**
 * Check if command tries to access other user's workspace
 */
function checkWorkspaceIsolation(command: string, userWorkspace: string): { blocked: boolean; reason?: string } {
  // Extract user ID from workspace path (e.g., /workspace/123456789 -> 123456789)
  const userMatch = userWorkspace.match(/\/workspace\/(\d+)/);
  if (!userMatch) {
    return { blocked: false };  // Not in workspace structure
  }
  const userId = userMatch[1];
  
  // Patterns that access other workspaces
  const otherWorkspacePatterns = [
    // Direct access to /workspace/OTHER_ID
    new RegExp(`/workspace/(?!${userId})\\d+`, 'i'),
    // Wildcard access to all workspaces
    /\/workspace\/\*/,
    // Find/ls across /workspace root
    /\b(find|ls|cat|head|tail|grep|less|more)\s+[^|]*\/workspace\s*($|[|;>&])/,
    // Parent directory traversal from workspace
    /\.\.\/\.\./,
  ];
  
  for (const pattern of otherWorkspacePatterns) {
    if (pattern.test(command)) {
      return { 
        blocked: true, 
        reason: 'BLOCKED: Cannot access other user workspaces. Use only your own workspace.' 
      };
    }
  }
  
  return { blocked: false };
}

export async function execute(
  args: { command: string },
  cwd: string | ExecuteContext
): Promise<{ success: boolean; output?: string; error?: string; approval_required?: boolean }> {
  // Handle both old (string) and new (object) signatures
  const context: ExecuteContext = typeof cwd === 'string' ? { cwd } : cwd;
  const workDir = context.cwd;
  const sessionId = context.sessionId || 'default';
  const chatId = context.chatId || 0;
  const chatType = context.chatType;
  
  // Check workspace isolation first
  const workspaceCheck = checkWorkspaceIsolation(args.command, workDir);
  if (workspaceCheck.blocked) {
    console.log(`[SECURITY] Workspace isolation: ${args.command}`);
    return {
      success: false,
      error: `🚫 ${workspaceCheck.reason}`,
    };
  }
  
  // Check if command is dangerous or blocked
  // In groups: dangerous = blocked (no approval possible)
  const { dangerous, blocked, reason } = checkCommand(args.command, chatType);
  
  // BLOCKED commands - never allowed, even with approval
  if (blocked) {
    console.log(`[SECURITY] BLOCKED command: ${args.command}`);
    console.log(`[SECURITY] Reason: ${reason}`);
    return {
      success: false,
      error: `🚫 ${reason}\n\nThis command is not allowed for security reasons.`,
    };
  }
  
  // DANGEROUS commands - require approval
  if (dangerous) {
    console.log(`[SECURITY] Dangerous command detected: ${args.command}`);
    console.log(`[SECURITY] Reason: ${reason}`);
    
    // Store command and show approval buttons
    const commandId = storePendingCommand(sessionId, chatId, args.command, workDir, reason!);
    
    // Show buttons (non-blocking)
    if (showApprovalCallback && chatId) {
      showApprovalCallback(chatId, commandId, args.command, reason!);
    }
    
    return {
      success: false,
      error: `⚠️ APPROVAL REQUIRED: "${reason}"\n\nWaiting for user to click Approve/Deny button.`,
      approval_required: true,
    };
  }
  
  return executeCommand(args.command, workDir);
}

/**
 * Execute a command (used for both regular and approved commands)
 */
export function executeCommand(
  command: string,
  cwd: string
): { success: boolean; output?: string; error?: string } {
  // Check if command should run in background
  const isBackground = /&\s*$/.test(command.trim()) || command.includes('nohup');
  
  // Execute background commands with spawn (non-blocking)
  if (isBackground) {
    try {
      // Remove trailing & for spawn
      const cleanCmd = command.trim().replace(/&\s*$/, '').trim();
      
      const child = spawn('sh', ['-c', cleanCmd], {
        cwd,
        detached: true,
        stdio: 'ignore',
      });
      
      child.unref();
      
      return { 
        success: true, 
        output: `Started in background (PID: ${child.pid})` 
      };
    } catch (e: any) {
      return { 
        success: false, 
        error: `Failed to start background process: ${e.message}` 
      };
    }
  }
  
  // Execute regular commands with execSync (blocking)
  try {
    const output = execSync(command, {
      cwd,
      encoding: 'utf-8',
      timeout: 180000, // 3 min
      maxBuffer: 1024 * 1024 * 10,
    });
    
    // Sanitize secrets from output
    const sanitized = sanitizeOutput(output);
    
    // Limit output to prevent context overflow and rate limits
    const maxOutput = 4000;
    const trimmed = sanitized.length > maxOutput 
      ? sanitized.slice(0, 2000) + '\n\n...(truncated ' + (sanitized.length - maxOutput) + ' chars)...\n\n' + sanitized.slice(-1500)
      : sanitized;
    
    return { success: true, output: trimmed || "(empty output)" };
  } catch (e: any) {
    const stderr = e.stderr?.toString() || '';
    const stdout = e.stdout?.toString() || '';
    const full = stderr || stdout || e.message;
    
    // Sanitize secrets from error output too
    const sanitized = sanitizeOutput(full);
    
    // Truncate error output
    const trimmed = sanitized.length > 5000 
      ? sanitized.slice(0, 2500) + '\n...(truncated)...\n' + sanitized.slice(-2000)
      : sanitized;
    
    return { 
      success: false, 
      error: `Exit ${e.status || 1}: ${trimmed}`
    };
  }
}
