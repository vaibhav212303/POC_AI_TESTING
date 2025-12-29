
import { NextResponse } from 'next/server';
import { db } from '../../../../../db';
import { automationBuilds } from '../../../../../db/schema';

export async function POST() {
  console.log("🚀 API: Received request to start a new build");
  try {
    const [newBuild] = await db.insert(automationBuilds).values({
      status: 'running',
    }).returning();
    
    console.log("✅ API: Build created in DB with ID:", newBuild.id);
    return NextResponse.json(newBuild);
  } catch (error) {
    console.error("❌ API: Failed to create build:", error);
    return NextResponse.json({ error: "DB Insertion failed" }, { status: 500 });
  }
}