import { Button } from "~/components/ui/button";

export function PopOutButton() {
  function openPopout() {
    window.open(
      "/popout",
      "advisor-popout",
      "width=380,height=640,resizable=yes"
    );
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={openPopout}
      className="text-muted-foreground hover:text-primary text-xs"
      title="Open compact pop-out window"
    >
      <svg
        viewBox="0 0 24 24"
        width="14"
        height="14"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
      </svg>
    </Button>
  );
}
