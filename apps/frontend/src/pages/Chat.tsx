import SendIcon from "@mui/icons-material/Send";
import {
  Box, Chip, CircularProgress, IconButton, Paper, Stack, TextField, Tooltip, Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import {
  askQuestion, createConversation, listConversations, listMessages, type Message,
} from "../features/chat/api";

function CitationChips({ message }: { message: Message }) {
  if (message.citations.length === 0) return null;
  return (
    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 1 }}>
      {message.citations.map((c) => (
        <Tooltip key={c.rank} title={`"${c.excerpt.slice(0, 180)}…"`}>
          {/* Clicking opens the document preview at the right page — Milestone 5 */}
          <Chip
            size="small"
            variant="outlined"
            label={`📄 ${c.document_name} · p.${c.page_number}`}
          />
        </Tooltip>
      ))}
    </Stack>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "USER";
  return (
    <Box sx={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <Paper
        elevation={0}
        sx={{
          p: 2,
          maxWidth: "75%",
          bgcolor: isUser ? "primary.dark" : "background.paper",
          border: 1,
          borderColor: "divider",
        }}
      >
        <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
          {message.content}
        </Typography>
        <CitationChips message={message} />
        {message.role === "ASSISTANT" && message.confidence !== null && (
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
            confidence {(message.confidence * 100).toFixed(0)}%
            {message.latency_ms ? ` · ${(message.latency_ms / 1000).toFixed(1)}s` : ""}
          </Typography>
        )}
      </Paper>
    </Box>
  );
}

export function Chat() {
  const [input, setInput] = useState("");
  const queryClient = useQueryClient();
  const bottomRef = useRef<HTMLDivElement>(null);

  // M3 keeps it simple: one active conversation (latest, or auto-created).
  // The full sidebar with rename/delete/search arrives in M4.
  const { data: conversation } = useQuery({
    queryKey: ["active-conversation"],
    queryFn: async () => {
      const existing = await listConversations();
      return existing[0] ?? (await createConversation());
    },
  });

  const { data: messages } = useQuery({
    queryKey: ["messages", conversation?.id],
    queryFn: () => listMessages(conversation!.id),
    enabled: Boolean(conversation),
  });

  const ask = useMutation({
    mutationFn: (content: string) => askQuestion(conversation!.id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", conversation?.id] });
      queryClient.invalidateQueries({ queryKey: ["active-conversation"] });
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, ask.isPending]);

  function submit() {
    const content = input.trim();
    if (!content || !conversation || ask.isPending) return;
    setInput("");
    ask.mutate(content);
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)" }}>
      <Box sx={{ flexGrow: 1, overflowY: "auto", pr: 1 }}>
        <Stack spacing={2}>
          {messages?.length === 0 && !ask.isPending && (
            <Typography color="text.secondary" align="center" sx={{ mt: 12 }}>
              Ask a question about your organization&apos;s documents.
            </Typography>
          )}
          {messages?.map((m) => <MessageBubble key={m.id} message={m} />)}
          {ask.isPending && (
            <Stack direction="row" spacing={1.5} alignItems="center" sx={{ pl: 1 }}>
              {/* Real token-by-token streaming replaces this spinner in M4 */}
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Searching documents and thinking…
              </Typography>
            </Stack>
          )}
          <div ref={bottomRef} />
        </Stack>
      </Box>

      <Stack direction="row" spacing={1} sx={{ pt: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Ask about your documents…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          multiline
          maxRows={4}
        />
        <IconButton color="primary" onClick={submit} disabled={ask.isPending || !input.trim()}>
          <SendIcon />
        </IconButton>
      </Stack>
    </Box>
  );
}
