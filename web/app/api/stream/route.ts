import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:7861";

export async function GET(request: NextRequest) {
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
