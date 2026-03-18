import { useState, useCallback } from "react";
import { Card, CardContent } from "~/components/ui/card";

interface Props {
  onUploaded: () => void;
}

export function UploadZone({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (!file || !file.name.endsWith(".sav")) return;
      await uploadFile(file);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  async function uploadFile(file: File) {
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      await fetch("/api/upload", { method: "POST", body: form });
      onUploaded();
    } catch {
      // handled by SSE error event
    } finally {
      setUploading(false);
    }
  }

  return (
    <Card
      className={`col-span-full border-2 border-dashed transition-colors cursor-pointer ${
        dragging ? "border-primary bg-primary/5" : "border-border bg-card"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".sav";
        input.onchange = () => {
          if (input.files?.[0]) uploadFile(input.files[0]);
        };
        input.click();
      }}
    >
      <CardContent className="flex items-center justify-center py-8 text-center">
        <p className="text-muted-foreground text-sm italic">
          {uploading
            ? "Uploading..."
            : "Drop a .sav file here or click to upload"}
        </p>
      </CardContent>
    </Card>
  );
}
