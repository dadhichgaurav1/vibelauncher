import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const { searchParams } = req.nextUrl;

  const oauth_token = searchParams.get("oauth_token");
  const oauth_verifier = searchParams.get("oauth_verifier");

  const res = await fetch(
    `${backendUrl}/auth/x/callback?oauth_token=${oauth_token}&oauth_verifier=${oauth_verifier}`
  );
  const data = await res.json();

  if (data.success) {
    // Store screen_name in a cookie for the UI
    const response = NextResponse.redirect(new URL("/", req.url));
    response.cookies.set("x_screen_name", data.screen_name, {
      httpOnly: false,
      maxAge: 60 * 60 * 24 * 30,
    });
    response.cookies.set("x_connected", "true", {
      httpOnly: false,
      maxAge: 60 * 60 * 24 * 30,
    });
    return response;
  }

  return NextResponse.redirect(new URL("/?error=auth_failed", req.url));
}
