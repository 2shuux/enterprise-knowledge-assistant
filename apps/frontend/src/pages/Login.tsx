import { Alert, Box, Button, Container, Paper, Stack, TextField, Typography } from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { login } from "../features/auth/api";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  // If a guard bounced the user here, send them back where they wanted to go.
  const from = (location.state as { from?: string } | null)?.from ?? "/chat";

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: () => navigate(from, { replace: true }),
  });

  return (
    <Container maxWidth="xs">
      <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center" }}>
        <Paper sx={{ p: 4, width: "100%" }}>
          <Stack
            component="form"
            spacing={2.5}
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <Typography variant="h5">Sign in</Typography>
            {mutation.isError && (
              <Alert severity="error">Invalid email or password. Please try again.</Alert>
            )}
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Button type="submit" variant="contained" size="large" disabled={mutation.isPending}>
              {mutation.isPending ? "Signing in…" : "Sign in"}
            </Button>
            <Typography variant="body2" color="text.secondary">
              No account? <Link to="/register" style={{ color: "inherit" }}>Create one</Link>
            </Typography>
          </Stack>
        </Paper>
      </Box>
    </Container>
  );
}
