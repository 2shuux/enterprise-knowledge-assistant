import DeleteIcon from "@mui/icons-material/DeleteOutline";
import ReplayIcon from "@mui/icons-material/Replay";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent,
  DialogTitle, IconButton, Paper, Skeleton, Stack, Table, TableBody, TableCell,
  TableHead, TableRow, Tooltip, Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useRef, useState } from "react";
import { useAuthStore } from "../features/auth/store";
import {
  deleteDocument, listDocuments, reindexDocument, uploadDocument, type Doc,
} from "../features/documents/api";

function formatBytes(n: number) {
  if (n > 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
  if (n > 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${n} B`;
}

function StatusChip({ doc }: { doc: Doc }) {
  if (doc.status === "PROCESSING")
    return <Chip size="small" icon={<CircularProgress size={12} />} label="Processing" />;
  if (doc.status === "FAILED")
    return (
      <Tooltip title={doc.error_message ?? "Unknown error"}>
        <Chip size="small" color="error" label="Failed" />
      </Tooltip>
    );
  return <Chip size="small" color="success" variant="outlined" label="Indexed" />;
}

export function Documents() {
  const isAdmin = useAuthStore((s) => s.user?.role === "ADMIN");
  const queryClient = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [confirmDelete, setConfirmDelete] = useState<Doc | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    // Poll every 2.5s while anything is processing, stop when all settled —
    // simple, robust status updates without websockets.
    refetchInterval: (query) =>
      query.state.data?.items.some((d) => d.status === "PROCESSING") ? 2500 : false,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["documents"] });

  const upload = useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      setUploadError(null);
      invalidate();
    },
    onError: (err) => {
      const detail =
        err instanceof AxiosError ? err.response?.data?.detail : null;
      setUploadError(detail ?? "Upload failed. Supported: PDF, DOCX, TXT, MD (max 50 MB).");
    },
  });

  const remove = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      setConfirmDelete(null);
      invalidate();
    },
  });

  const reindex = useMutation({ mutationFn: reindexDocument, onSuccess: invalidate });

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h5">Documents</Typography>
        {isAdmin && (
          <>
            <input
              ref={fileInput}
              type="file"
              hidden
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) upload.mutate(file);
                e.target.value = ""; // allow re-selecting the same file
              }}
            />
            <Button
              variant="contained"
              startIcon={<UploadFileIcon />}
              disabled={upload.isPending}
              onClick={() => fileInput.current?.click()}
            >
              {upload.isPending ? "Uploading…" : "Upload"}
            </Button>
          </>
        )}
      </Stack>

      {uploadError && (
        <Alert severity="error" onClose={() => setUploadError(null)} sx={{ mb: 2 }}>
          {uploadError}
        </Alert>
      )}

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Size</TableCell>
              <TableCell align="right">Pages</TableCell>
              <TableCell align="right">Chunks</TableCell>
              <TableCell>Uploaded</TableCell>
              {isAdmin && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading &&
              [1, 2, 3].map((i) => (
                <TableRow key={i}>
                  {Array.from({ length: isAdmin ? 7 : 6 }).map((_, j) => (
                    <TableCell key={j}><Skeleton /></TableCell>
                  ))}
                </TableRow>
              ))}
            {data?.items.map((doc) => (
              <TableRow key={doc.id} hover>
                <TableCell sx={{ maxWidth: 320 }}>
                  <Typography variant="body2" noWrap>{doc.original_name}</Typography>
                </TableCell>
                <TableCell><StatusChip doc={doc} /></TableCell>
                <TableCell align="right">{formatBytes(doc.file_size_bytes)}</TableCell>
                <TableCell align="right">{doc.page_count || "—"}</TableCell>
                <TableCell align="right">{doc.chunk_count || "—"}</TableCell>
                <TableCell>{new Date(doc.uploaded_at).toLocaleDateString()}</TableCell>
                {isAdmin && (
                  <TableCell align="right">
                    <Tooltip title="Re-index">
                      <IconButton size="small" onClick={() => reindex.mutate(doc.id)}>
                        <ReplayIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => setConfirmDelete(doc)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                )}
              </TableRow>
            ))}
            {data && data.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={isAdmin ? 7 : 6}>
                  <Typography color="text.secondary" align="center" sx={{ py: 6 }}>
                    No documents yet.{isAdmin && " Upload a PDF, DOCX, TXT or MD file to begin."}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={confirmDelete !== null} onClose={() => setConfirmDelete(null)}>
        <DialogTitle>Delete document?</DialogTitle>
        <DialogContent>
          <Typography>
            “{confirmDelete?.original_name}” and all its indexed chunks will be permanently
            removed. The AI will no longer be able to answer from this document.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            disabled={remove.isPending}
            onClick={() => confirmDelete && remove.mutate(confirmDelete.id)}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
