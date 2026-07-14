import ConstructionIcon from "@mui/icons-material/Construction";
import { Box, Chip, Stack, Typography } from "@mui/material";

export function ComingSoon({ feature, milestone }: { feature: string; milestone: string }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", mt: 12 }}>
      <Stack spacing={2} alignItems="center">
        <ConstructionIcon sx={{ fontSize: 56, color: "text.secondary" }} />
        <Typography variant="h6">{feature} is under construction</Typography>
        <Chip label={`Arriving in milestone ${milestone}`} variant="outlined" />
      </Stack>
    </Box>
  );
}
