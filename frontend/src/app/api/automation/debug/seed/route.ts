
import { NextResponse } from "next/server";
import { automationBuilds, testResults } from "../../../../../../db/schema";
import { db } from "../../../../../../db";

export async function GET() {
  // 1. Create Build #1
  const [build] = await db.insert(automationBuilds).values({
    status: 'completed',
    environment: 'development'
  }).returning();

  // 2. Add Test Cases from your CSV
  await db.insert(testResults).values([
    {
      buildId: build.id,
      caseCode: 'TC5073',
      title: 'Validate Login page loads',
      status: 'passed',
      duration: '1.5s'
    },
    {
      buildId: build.id,
      caseCode: 'TC7133',
      title: 'Validate back arrow button',
      status: 'failed',
      duration: '4.2s',
      errorMessage: 'Timed out retrying after 4000ms: Expected to find element: .back-arrow'
    }
  ]);

  return NextResponse.json({ message: "Seed Successful!", buildId: build.id });
}