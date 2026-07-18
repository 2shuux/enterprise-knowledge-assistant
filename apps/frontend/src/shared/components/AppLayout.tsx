import ChatIcon from "@mui/icons-material/ChatBubbleOutline";
import DescriptionIcon from "@mui/icons-material/DescriptionOutlined";
import InsightsIcon from "@mui/icons-material/InsightsOutlined";
import LogoutIcon from "@mui/icons-material/Logout";
import SearchIcon from "@mui/icons-material/SearchOutlined";
import {
  Avatar, Box, Divider, Drawer, IconButton, List, ListItemButton, ListItemIcon,
  ListItemText, Stack, Toolbar, Tooltip, Typography,
} from "@mui/material";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { logout } from "../../features/auth/api";
import { useAuthStore } from "../../features/auth/store";

const DRAWER_WIDTH = 240;

/** Admin-only entries are filtered out for normal users — the backend enforces
 * this too (require_admin); UI hiding is convenience, the API is the wall. */
export function AppLayout() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const nav = [
    { label: "Chat", to: "/chat", icon: <ChatIcon /> },
    { label: "Documents", to: "/documents", icon: <DescriptionIcon /> },
    { label: "Search", to: "/search", icon: <SearchIcon /> },
    ...(user?.role === "ADMIN" ? [{ label: "Admin", to: "/admin", icon: <InsightsIcon /> }] : []),
  ];

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <Box sx={{ display: "flex" }}>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          "& .MuiDrawer-paper": {
            width: DRAWER_WIDTH,
            boxSizing: "border-box",
            display: "flex",
            flexDirection: "column",
          },
        }}
      >
        <Toolbar>
          <Typography variant="h6" component={Link} to="/" sx={{ textDecoration: "none", color: "inherit" }}>
            ✦ EKA
          </Typography>
        </Toolbar>
        <List sx={{ flexGrow: 1 }}>
          {nav.map((item) => (
            <ListItemButton
              key={item.to}
              component={Link}
              to={item.to}
              selected={pathname.startsWith(item.to)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
        <Divider />
        <Stack direction="row" alignItems="center" spacing={1.5} sx={{ p: 2 }}>
          <Avatar sx={{ width: 32, height: 32 }}>{user?.full_name?.[0] ?? "?"}</Avatar>
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography variant="body2" noWrap>{user?.full_name}</Typography>
            <Typography variant="caption" color="text.secondary">{user?.role}</Typography>
          </Box>
          <Tooltip title="Log out">
            <IconButton size="small" onClick={handleLogout}>
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 4 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
