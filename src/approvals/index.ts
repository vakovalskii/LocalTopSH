/**
 * Exec Approvals - confirmation for dangerous commands
 * Non-blocking architecture: save command, execute on approve
 */

export interface PendingCommand {
  id: string;
  sessionId: string;
  chatId: number;
  command: string;
  cwd: string;
  reason: string;
  createdAt: number;
}

// Dangerous command patterns
const DANGEROUS_PATTERNS: { pattern: RegExp; reason: string }[] = [
  // Destructive file operations
  { pattern: /\brm\s+(-[rf]+\s+)*[\/~]/, reason: 'Recursive delete from root/home' },
  { pattern: /\brm\s+-[rf]*\s*\*/, reason: 'Wildcard delete' },
  { pattern: /\brm\s+-rf\b/, reason: 'Force recursive delete' },
  { pattern: /\brmdir\s+--ignore-fail-on-non-empty/, reason: 'Force directory removal' },
  
  // Privilege escalation
  { pattern: /\bsudo\b/, reason: 'Root privileges' },
  { pattern: /\bsu\s+-?\s*$/, reason: 'Switch to root' },
  { pattern: /\bchown\s+-R\s+root/, reason: 'Change ownership to root' },
  
  // Dangerous permissions
  { pattern: /\bchmod\s+(-R\s+)?[0-7]*7[0-7]{2}\b/, reason: 'World-writable permissions' },
  { pattern: /\bchmod\s+(-R\s+)?777\b/, reason: 'Full permissions to everyone' },
  { pattern: /\bchmod\s+\+s\b/, reason: 'Set SUID/SGID bit' },
  
  // System modification
  { pattern: /\bmkfs\b/, reason: 'Format filesystem' },
  { pattern: /\bdd\s+.*of=\/dev\//, reason: 'Direct disk write' },
  { pattern: />\s*\/dev\/[sh]d[a-z]/, reason: 'Redirect to disk device' },
  { pattern: /\bfdisk\b/, reason: 'Partition manipulation' },
  { pattern: /\bparted\b/, reason: 'Partition manipulation' },
  
  // Network/Security
  { pattern: /\biptables\s+(-F|--flush)/, reason: 'Flush firewall rules' },
  { pattern: /\bufw\s+disable/, reason: 'Disable firewall' },
  { pattern: /\bsystemctl\s+(stop|disable)\s+(ssh|firewall|ufw)/, reason: 'Stop security service' },
  
  // Package management (can break system)
  { pattern: /\bapt(-get)?\s+(remove|purge)\s+.*-y/, reason: 'Auto-confirm package removal' },
  { pattern: /\byum\s+remove\s+.*-y/, reason: 'Auto-confirm package removal' },
  { pattern: /\bpip\s+uninstall\s+.*-y/, reason: 'Auto-confirm pip uninstall' },
  
  // Data destruction
  { pattern: /\btruncate\s+-s\s*0/, reason: 'Truncate file to zero' },
  { pattern: />\s*\/etc\//, reason: 'Overwrite system config' },
  { pattern: /\bshred\b/, reason: 'Secure file deletion' },
  
  // Process/System control
  { pattern: /\bkill\s+-9\s+-1\b/, reason: 'Kill all processes' },
  { pattern: /\bkillall\s+-9/, reason: 'Force kill processes' },
  { pattern: /\bshutdown\b/, reason: 'System shutdown' },
  { pattern: /\breboot\b/, reason: 'System reboot' },
  { pattern: /\binit\s+[06]\b/, reason: 'System halt/reboot' },
  
  // Dangerous downloads/execution
  { pattern: /curl.*\|\s*(ba)?sh/, reason: 'Pipe URL to shell' },
  { pattern: /wget.*\|\s*(ba)?sh/, reason: 'Pipe URL to shell' },
  { pattern: /\beval\s+"?\$\(curl/, reason: 'Eval remote code' },
  
  // Git dangerous operations
  { pattern: /\bgit\s+push\s+.*--force/, reason: 'Force push (rewrites history)' },
  { pattern: /\bgit\s+reset\s+--hard\s+HEAD~/, reason: 'Hard reset (lose commits)' },
  { pattern: /\bgit\s+clean\s+-fd/, reason: 'Force clean untracked files' },
  
  // Database
  { pattern: /\bDROP\s+(DATABASE|TABLE)\b/i, reason: 'Drop database/table' },
  { pattern: /\bTRUNCATE\s+TABLE\b/i, reason: 'Truncate table' },
  { pattern: /\bDELETE\s+FROM\s+\w+\s*;?\s*$/i, reason: 'Delete all rows (no WHERE)' },
  
  // Environment
  { pattern: /\bexport\s+(PATH|LD_PRELOAD|LD_LIBRARY_PATH)=/, reason: 'Modify critical env var' },
  { pattern: /\bunset\s+(PATH|HOME)\b/, reason: 'Unset critical env var' },
  
  // Fork bomb / resource exhaustion
  { pattern: /:\(\)\s*{\s*:\|:&\s*}/, reason: 'Fork bomb' },
  { pattern: /while\s+true.*do.*done/, reason: 'Infinite loop' },
];

// In-memory storage for pending commands
const pendingCommands = new Map<string, PendingCommand>();

// Timeout for pending commands (5 minutes)
const COMMAND_TIMEOUT = 5 * 60 * 1000;

/**
 * Check if command is dangerous
 */
export function checkCommand(command: string): { dangerous: boolean; reason?: string } {
  for (const { pattern, reason } of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      return { dangerous: true, reason };
    }
  }
  return { dangerous: false };
}

/**
 * Store a pending command for later approval
 * Returns ID for the approval buttons
 */
export function storePendingCommand(
  sessionId: string,
  chatId: number,
  command: string,
  cwd: string,
  reason: string
): string {
  const id = `cmd_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  
  pendingCommands.set(id, {
    id,
    sessionId,
    chatId,
    command,
    cwd,
    reason,
    createdAt: Date.now(),
  });
  
  // Auto-cleanup after timeout
  setTimeout(() => {
    pendingCommands.delete(id);
  }, COMMAND_TIMEOUT);
  
  return id;
}

/**
 * Get pending command by ID and remove it
 */
export function consumePendingCommand(id: string): PendingCommand | undefined {
  const cmd = pendingCommands.get(id);
  if (cmd) {
    pendingCommands.delete(id);
  }
  return cmd;
}

/**
 * Get all pending commands for a session
 */
export function getSessionPendingCommands(sessionId: string): PendingCommand[] {
  return Array.from(pendingCommands.values())
    .filter(c => c.sessionId === sessionId);
}

/**
 * Cancel pending command
 */
export function cancelPendingCommand(id: string): boolean {
  return pendingCommands.delete(id);
}
