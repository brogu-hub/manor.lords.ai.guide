import { API_BASE_URL } from "~/config.server";
import type { Route } from "./+types/api.$";

async function proxyRequest(request: Request) {
  const url = new URL(request.url);
  const upstream = `${API_BASE_URL}${url.pathname}${url.search}`;

  const headers: Record<string, string> = {};
  const contentType = request.headers.get("Content-Type");
  if (contentType) headers["Content-Type"] = contentType;

  try {
    const resp = await fetch(upstream, {
      method: request.method,
      headers,
      body: request.method !== "GET" ? await request.text() : undefined,
      signal: request.signal,
    });

    return new Response(resp.body, {
      status: resp.status,
      headers: {
        "Content-Type": resp.headers.get("Content-Type") ?? "application/json",
      },
    });
  } catch (err) {
    return Response.json(
      { status: "error", message: "API unavailable" },
      { status: 502 }
    );
  }
}

export function loader({ request }: Route.LoaderArgs) {
  return proxyRequest(request);
}

export function action({ request }: Route.ActionArgs) {
  return proxyRequest(request);
}
