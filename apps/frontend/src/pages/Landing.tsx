import { Box, Button, Chip, Container, Stack, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Link } from "react-router-dom";

type Health = { status: string; app: string; env: string };

/**
 * Landing page — also our Milestone 0 proof of life:
 * the chip below performs a real API call through the Vite proxy,
 * demonstrating the full FE → proxy → FastAPI → JSON loop.
 */
export function Landing() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await axios.get<Health>("/api/v1/health")).data,
  });

  return (
    <Container maxWidth="md">
      <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center" }}>
        <Stack spacing={3}>
          <Typography variant="h4">Enterprise Knowledge Assistant</Typography>
          <Typography color="text.secondary" sx={{ maxWidth: 560 }}>
            Upload your organization&apos;s documents and get AI answers with page-level
            citations. Powered by RAG, hybrid search, and streaming responses.
          </Typography>
          <Stack direction="row" spacing={2} alignItems="center">
            <Button component={Link} to="/chat" variant="contained" size="large">
              Open App
            </Button>
            <Chip
              label={
                isLoading ? "API: checking…" : isError ? "API: offline" : `API: ${data?.status} (${data?.env})`
              }
              color={isLoading ? "default" : isError ? "error" : "success"}
              variant="outlined"
            />
          </Stack>
        </Stack>
      </Box>
    </Container>
  );
}
