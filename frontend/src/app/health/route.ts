import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "healthy",
    service: "SkillBridge AI Frontend",
    timestamp: new Date().toISOString()
  });
}

