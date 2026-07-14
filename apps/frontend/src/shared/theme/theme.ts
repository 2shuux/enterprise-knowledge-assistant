import { createTheme } from "@mui/material";

/** Dark-first enterprise theme. Light mode toggle arrives with Settings. */
export const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#7aa2ff" },
    background: { default: "#0f1115", paper: "#161a22" },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: `"Inter", "Segoe UI", "Roboto", "Helvetica Neue", sans-serif`,
    h4: { fontWeight: 700 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
  },
});
