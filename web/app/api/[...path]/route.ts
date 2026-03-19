import { NextRequest } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:7861";

async function proxyRequest(request: NextRequest) {
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
  } catch {
    return Response.json(
      { status: "error", message: "API unavailable" },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest) {
  return proxyRequest(request);
}

export async function POST(request: NextRequest) {
  return proxyRequest(request);
}
