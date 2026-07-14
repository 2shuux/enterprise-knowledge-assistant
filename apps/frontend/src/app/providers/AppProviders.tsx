import { CssBaseline, ThemeProvider } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { theme } from "../../shared/theme/theme";

/**
 * Single place where every global provider is stacked.
 * Order matters: theme wraps everything visual; QueryClient wraps
 * everything that fetches. Auth provider joins this stack in Milestone 1.
 */
export function AppProviders({ children }: { children: ReactNode }) {
  // useState(() => ...) ensures ONE QueryClient for the app's lifetime,
  // not a new one per render (which would wipe the cache constantly).
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 1, staleTime: 30_000, refetchOnWindowFocus: false },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
