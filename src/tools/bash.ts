/**
 * run_command - Execute shell commands
 * Pattern: Action (run) + Object (command)
 * Security: Dangerous commands require user approval
 * Background: Commands ending with & run in background
 */

import { execSync, spawn } from 'child_process';
import { checkCommand, storePendingCommand } from '../approvals/index.js';

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
  
  // Check if command is dangerous
  const { dangerous, reason } = checkCommand(args.command);
  
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
    
    // Limit output to prevent context overflow
    const trimmed = output.length > 10000 
      ? output.slice(0, 5000) + '\n...(truncated)...\n' + output.slice(-3000)
      : output;
    
    return { success: true, output: trimmed || "(empty output)" };
  } catch (e: any) {
    const stderr = e.stderr?.toString() || '';
    const stdout = e.stdout?.toString() || '';
    const full = stderr || stdout || e.message;
    
    // Truncate error output too
    const trimmed = full.length > 5000 
      ? full.slice(0, 2500) + '\n...(truncated)...\n' + full.slice(-2000)
      : full;
    
    return { 
      success: false, 
      error: `Exit ${e.status || 1}: ${trimmed}`
    };
  }
}
