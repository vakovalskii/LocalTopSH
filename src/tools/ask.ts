/**
 * ask_user - Ask user for confirmation with inline buttons
 * Agent can use this to get user approval before actions
 */

// Callback for asking user (set from bot)
let askCallback: ((
  sessionId: string,
  question: string,
  options: string[]
) => Promise<string>) | null = null;

/**
 * Set the ask callback (called from bot)
 */
export function setAskCallback(
  callback: (sessionId: string, question: string, options: string[]) => Promise<string>
) {
  askCallback = callback;
}

export const definition = {
  type: "function" as const,
  function: {
    name: "ask_user",
    description: "Ask user a question with button options. ONLY works in PRIVATE chats (not groups). In groups, just ask in text.",
    parameters: {
      type: "object",
      properties: {
        question: {
          type: "string",
          description: "The question to ask the user"
        },
        options: {
          type: "array",
          items: { type: "string" },
          description: "Button options for user to choose from (2-4 options)"
        },
      },
      required: ["question", "options"],
    },
  },
};

export async function execute(
  args: { question: string; options: string[] },
  sessionId: string
): Promise<{ success: boolean; output?: string; error?: string }> {
  if (!askCallback) {
    return {
      success: false,
      error: 'Ask callback not configured',
    };
  }
  
  // Validate options
  if (!args.options || args.options.length < 2) {
    return {
      success: false,
      error: 'Need at least 2 options',
    };
  }
  
  if (args.options.length > 4) {
    args.options = args.options.slice(0, 4);
  }
  
  try {
    const answer = await askCallback(sessionId, args.question, args.options);
    return {
      success: true,
      output: `User selected: ${answer}`,
    };
  } catch (e: any) {
    return {
      success: false,
      error: `Failed to get user response: ${e.message}`,
    };
  }
}
