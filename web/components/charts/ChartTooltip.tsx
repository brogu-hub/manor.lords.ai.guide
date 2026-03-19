"use client";

interface TooltipEntry {
  name?: string;
  value?: number | string;
  color?: string;
}

interface Props {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
}

export function ChartTooltip({ active, payload, label }: Props) {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-[var(--color-panel)] border border-[var(--color-gold-dim)] rounded-sm px-3 py-2 shadow-lg">
      <p className="font-heading text-xs text-primary mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-xs" style={{ color: entry.color }}>
          {entry.name}: <span className="font-semibold">{typeof entry.value === "number" ? entry.value.toFixed(1) : entry.value}</span>
        </p>
      ))}
    </div>
  );
}
