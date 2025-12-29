"use server"


import { desc } from 'drizzle-orm';
import { automationBuilds } from '../../db/schema';
import { db } from '../../db';

export async function getBuildHistory() {
  try {
    // This will now work because 'db' is initialized with the client
    const builds = await db.query.automationBuilds.findMany({
      with: {
        results: true,
      },
      orderBy: [desc(automationBuilds.id)],
    });
    return builds;
  } catch (error) {
    console.error("Database Fetch Error:", error);
    return [];
  }
}