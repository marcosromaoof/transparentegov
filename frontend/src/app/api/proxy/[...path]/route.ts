import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
const adminApiKey = process.env.BACKEND_ADMIN_API_KEY || "";

async function proxy(request: NextRequest, path: string[]) {
  const search = request.nextUrl.search || "";
  const url = `${backendUrl}/api/v1/${path.join("/")}${search}`;

  const headers = new Headers();
  headers.set("Accept", "application/json");

  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  const targetPath = path.join("/");
  const needsAdmin = targetPath.startsWith("admin") || targetPath.startsWith("collectors");
  if (needsAdmin && adminApiKey) {
    headers.set("X-Admin-Key", adminApiKey);
  }

  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();

  const response = await fetch(url, {
    method: request.method,
    headers,
    body,
    cache: "no-store"
  });

  const text = await response.text();
  const responseHeaders = new Headers();
  const responseContentType = response.headers.get("content-type") || "application/json";
  responseHeaders.set("content-type", responseContentType);

  return new NextResponse(text, {
    status: response.status,
    headers: responseHeaders
  });
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolved = await params;
  return proxy(request, resolved.path);
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolved = await params;
  return proxy(request, resolved.path);
}

export async function PUT(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolved = await params;
  return proxy(request, resolved.path);
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolved = await params;
  return proxy(request, resolved.path);
}
