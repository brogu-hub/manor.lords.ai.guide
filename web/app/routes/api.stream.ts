import { API_BASE_URL } from "~/config.server";
import type { Route } from "./+types/api.stream";

export async function loader({ request }: Route.LoaderArgs) {
  try {
    const upstream = await fetch(`${API_BASE_URL}/api/stream`, {
      signal: request.signal,
      headers: { Accept: "text/event-stream" },
    });

    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch {
    // Return an SSE-formatted error so EventSource handles it gracefully
    const body = `event: error\ndata: {"message":"API unavailable"}\n\n`;
    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  }
}
