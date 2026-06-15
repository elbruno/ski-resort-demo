export interface ResponsesStreamEvent {
  content?: string;
  contextId?: string;
}

const ADVISOR_AGENT_NAME = 'advisoragent-ha';

interface ResponseStreamPayload {
  type?: string;
  delta?: string;
  text?: string;
  conversation_id?: string;
  response?: { id?: string; output_text?: string; conversation_id?: string; conversation?: { id?: string } };
  item?: { id?: string; type?: string; role?: string; content?: Array<{ text?: string; type?: string }> };
  content_index?: number;
  output_index?: number;
}

function extractContextId(payload: ResponseStreamPayload): string | undefined {
  return payload.conversation_id ?? payload.response?.conversation_id ?? payload.response?.conversation?.id;
}

export async function* sendMessageStream(
  text: string,
  contextId?: string,
): AsyncGenerator<ResponsesStreamEvent, void, undefined> {
  const requestBody: Record<string, unknown> = {
    model: ADVISOR_AGENT_NAME,
    agent_reference: { type: 'agent_reference', name: ADVISOR_AGENT_NAME },
    input: [
      {
        type: 'message',
        role: 'user',
        content: [{ type: 'input_text', text }],
      },
    ],
    // NOTE: SSE streaming from the local dev proxy can occasionally remain open
    // after completion, leaving the UI in a perpetual "thinking" state.
    // Use non-streaming mode for deterministic completion in the dashboard chat.
    stream: false,
    metadata: { entity_id: ADVISOR_AGENT_NAME },
  };

  if (contextId) {
    requestBody.conversation = contextId;
  }

  const response = await fetch('/responses', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new Error(`Responses API request failed: ${response.status}${errorText ? ` ${errorText}` : ''}`);
  }

  const payload = (await response.json()) as ResponseStreamPayload & {
    output?: Array<{
      type?: string;
      content?: Array<{ type?: string; text?: string }>;
    }>;
    output_text?: string;
  };

  const nextContextId = extractContextId(payload) ?? contextId;

  let content = payload.output_text;
  if (!content && Array.isArray(payload.output)) {
    const lastMessage = [...payload.output].reverse().find((item) => item.type === 'message');
    const outputTextPart = lastMessage?.content?.find((part) => part.type === 'output_text');
    content = outputTextPart?.text;
  }

  if (!content && !nextContextId) {
    throw new Error('Responses API returned no assistant content.');
  }

  yield { content, contextId: nextContextId };
}

export function resetClient() {
  // No client instance is cached for the Responses API transport.
}