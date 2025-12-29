import { NextResponse } from 'next/server';
import { testResults } from '../../../../../db/schema';
import { db } from '../../../../../db';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    console.log("📩 API: Received Result for TC:", body.case_code, "Status:", body.status);

    await db.insert(testResults).values({
      buildId: body.build_id,
      caseCode: body.case_code,
      title: body.title,
      status: body.status,
      duration: body.duration,
      errorMessage: body.error_message
    });

    console.log("✅ API: Saved result for", body.case_code);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("❌ API: Error saving result:", error);
    return NextResponse.json({ error: error }, { status: 500 });
  }
}