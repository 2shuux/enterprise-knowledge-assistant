import ChatIcon from "@mui/icons-material/ChatBubbleOutline";
import DescriptionIcon from "@mui/icons-material/DescriptionOutlined";
import InsightsIcon from "@mui/icons-material/InsightsOutlined";
import SearchIcon from "@mui/icons-material/SearchOutlined";
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography,
} from "@mui/material";
import { Link, Outlet, useLocation } from "react-router-dom";

const DRAWER_WIDTH = 240;

const NAV = [
  { label: "Chat", to: "/chat", icon: <ChatIcon /> },
  { label: "Documents", to: "/documents", icon: <DescriptionIcon /> },
  { label: "Search", to: "/search", icon: <SearchIcon /> },
  { label: "Admin", to: "/admin", icon: <InsightsIcon /> },
];

/** Persistent sidebar shell — every authenticated page renders inside <Outlet />. */
export function AppLayout() {
  const { pathname } = useLocation();
  return (
    <Box sx={{ display: "flex" }}>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar>
          <Typography variant="h6" component={Link} to="/" sx={{ textDecoration: "none", color: "inherit" }}>
            ✦ EKA
          </Typography>
        </Toolbar>
        <List>
          {NAV.map((item) => (
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
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 4 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
