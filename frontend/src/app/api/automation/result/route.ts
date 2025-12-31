import { NextResponse } from 'next/server';
import { sql, eq } from 'drizzle-orm';
import { db } from '../../../../../db';
import { automationBuilds, testResults } from '../../../../../db/schema';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { build_id, spec_file, test_entry } = body;

    // 1. Verify the Build exists first (Optional but helpful for debugging)
    const buildExists = await db.query.automationBuilds.findFirst({
        where: eq(automationBuilds.id, build_id)
    });

    if (!buildExists) {
        console.error(`❌ ERROR: Build ID ${build_id} not found. Did you delete the builds?`);
        return NextResponse.json({ error: `Build ID ${build_id} not found.` }, { status: 400 });
    }

    // 2. Clean ANSI colors
    if (test_entry.error) {
      test_entry.error = test_entry.error.replace(/\u001b\[\d+m/g, '');
    }

    // 3. Atomic Upsert
    await db.insert(testResults)
      .values({
        buildId: build_id,
        specFile: spec_file,
        tests: [test_entry],
      })
      .onConflictDoUpdate({
        target: [testResults.buildId, testResults.specFile],
        set: {
          // Explicitly concatenate to the existing jsonb column
          tests: sql`test_results.tests || ${JSON.stringify([test_entry])}::jsonb`
        }
      });

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error("❌ DATABASE ERROR:", error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}