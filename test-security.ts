/**
 * Security test - check if attack vectors are blocked
 */

import { checkCommand } from './src/approvals/index.js';

const attacks = [
  // Direct secrets access
  { cmd: 'cat /run/secrets/telegram_token', expected: 'blocked' },
  { cmd: 'cat /run/secrets/api_key', expected: 'blocked' },
  { cmd: 'ls /run/secrets/', expected: 'blocked' },
  { cmd: 'head /run/secrets/telegram_token', expected: 'blocked' },
  
  // Symlink attacks
  { cmd: 'ln -s /run/secrets/telegram_token ~/tok', expected: 'blocked' },
  { cmd: 'ln -s /run/secrets ~/secrets', expected: 'blocked' },
  
  // Base64 exfiltration
  { cmd: 'base64 /run/secrets/telegram_token', expected: 'blocked' },
  { cmd: 'cat file | base64', expected: 'blocked' },
  { cmd: 'base64 < /etc/passwd', expected: 'blocked' },
  
  // Python attacks
  { cmd: 'python3 -c "print(open(\'/run/secrets/telegram_token\').read())"', expected: 'blocked' },
  { cmd: 'python3 -c "import os; print(os.environ)"', expected: 'blocked' },
  { cmd: 'python3 -c "from os import environ; print(environ)"', expected: 'blocked' },
  
  // Node.js attacks
  { cmd: 'node -e "console.log(process.env)"', expected: 'blocked' },
  { cmd: 'node -p "process.env.TELEGRAM_TOKEN"', expected: 'blocked' },
  { cmd: 'node -e "require(\'fs\').readFileSync(\'/run/secrets/api_key\')"', expected: 'blocked' },
  
  // Env commands
  { cmd: 'env', expected: 'blocked' },
  { cmd: 'printenv', expected: 'blocked' },
  { cmd: 'export', expected: 'blocked' },
  { cmd: 'set', expected: 'blocked' },
  { cmd: 'echo $TELEGRAM_TOKEN', expected: 'blocked' },
  { cmd: 'echo ${API_KEY}', expected: 'blocked' },
  
  // Proc filesystem
  { cmd: 'cat /proc/self/environ', expected: 'blocked' },
  { cmd: 'cat /proc/1/environ', expected: 'blocked' },
  { cmd: 'strings /proc/self/environ', expected: 'blocked' },
  
  // Curl to internal services
  { cmd: 'curl http://proxy:3200/health', expected: 'blocked' },
  { cmd: 'wget http://proxy:3200/', expected: 'blocked' },
  { cmd: 'curl proxy:3200', expected: 'blocked' },
  
  // NPX malicious packages
  { cmd: 'npx super-test-json', expected: 'blocked' },
  { cmd: 'npx env-dump', expected: 'blocked' },
  { cmd: 'npx debug-tool', expected: 'blocked' },
  { cmd: 'npx diag-check', expected: 'blocked' },
  
  // Hex dump
  { cmd: 'xxd /run/secrets/telegram_token', expected: 'blocked' },
  { cmd: 'hexdump -C /etc/passwd', expected: 'blocked' },
  { cmd: 'od -c /run/secrets/api_key', expected: 'blocked' },
  
  // OpenSSL encoding
  { cmd: 'openssl enc -base64 -in /run/secrets/api_key', expected: 'blocked' },
  
  // These SHOULD work (legitimate commands)
  { cmd: 'ls -la', expected: 'allowed' },
  { cmd: 'pwd', expected: 'allowed' },
  { cmd: 'echo hello', expected: 'allowed' },
  { cmd: 'python3 -c "print(1+1)"', expected: 'allowed' },
  { cmd: 'node -e "console.log(1+1)"', expected: 'allowed' },
  { cmd: 'curl https://google.com', expected: 'allowed' },
  { cmd: 'pip install requests', expected: 'allowed' },
];

console.log('=== Security Test ===\n');

let passed = 0;
let failed = 0;

for (const { cmd, expected } of attacks) {
  const result = checkCommand(cmd, 'group');
  const isBlocked = result.blocked;
  const actual = isBlocked ? 'blocked' : 'allowed';
  const ok = actual === expected;
  
  if (ok) {
    passed++;
    console.log(`✓ ${cmd.slice(0, 60).padEnd(60)} → ${actual}`);
  } else {
    failed++;
    console.log(`✗ ${cmd.slice(0, 60).padEnd(60)} → ${actual} (expected ${expected})`);
    if (result.reason) console.log(`  Reason: ${result.reason}`);
  }
}

console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);

if (failed > 0) {
  process.exit(1);
}
