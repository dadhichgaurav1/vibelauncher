import { NextResponse } from "next/server";

// Proxy OAuth initiation to FastAPI backend
export async function GET() {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const res = await fetch(`${backendUrl}/auth/x/init`);
  const { redirect_url } = await res.json();
  return NextResponse.redirect(redirect_url);
}
