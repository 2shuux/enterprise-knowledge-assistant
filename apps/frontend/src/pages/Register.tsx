import { Alert, Box, Button, Container, Paper, Stack, TextField, Typography } from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../features/auth/api";

export function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: () => register(email, password, fullName),
    onSuccess: () => navigate("/chat", { replace: true }),
  });

  const errorMessage =
    mutation.error instanceof AxiosError && mutation.error.response?.status === 409
      ? "An account with this email already exists."
      : "Registration failed. Password must be at least 8 characters.";

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
            <Typography variant="h5">Create account</Typography>
            {mutation.isError && <Alert severity="error">{errorMessage}</Alert>}
            <TextField
              label="Full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              autoFocus
            />
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              helperText="At least 8 characters"
              required
            />
            <Button type="submit" variant="contained" size="large" disabled={mutation.isPending}>
              {mutation.isPending ? "Creating…" : "Create account"}
            </Button>
            <Typography variant="body2" color="text.secondary">
              Already registered? <Link to="/login" style={{ color: "inherit" }}>Sign in</Link>
            </Typography>
          </Stack>
        </Paper>
      </Box>
    </Container>
  );
}
