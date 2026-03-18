import { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";

interface SaveFile {
  name: string;
  modified: number;
  size: number;
}

interface Props {
  onSelect: (name: string | undefined) => void;
  selected: string | undefined;
}

export function SaveSelector({ onSelect, selected }: Props) {
  const [saves, setSaves] = useState<SaveFile[]>([]);

  useEffect(() => {
    fetch("/api/saves")
      .then((r) => r.json())
      .then((data) => setSaves(data.saves ?? []))
      .catch(() => {});
  }, []);

  return (
    <Select
      value={selected ?? "__latest__"}
      onValueChange={(v) => onSelect(v === "__latest__" ? undefined : v)}
    >
      <SelectTrigger className="w-[180px] bg-input border-border text-foreground font-sans text-sm h-8">
        <SelectValue placeholder="Latest save" />
      </SelectTrigger>
      <SelectContent className="bg-card border-border">
        <SelectItem value="__latest__">Latest save</SelectItem>
        {saves.map((s) => (
          <SelectItem key={s.name} value={s.name}>
            {s.name.replace(".sav", "")}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
