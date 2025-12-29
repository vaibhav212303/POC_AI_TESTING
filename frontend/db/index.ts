import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

// 1. Get connection string
const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error("DATABASE_URL is not defined in your .env file");
}

// 2. Initialize the Postgres client (The "Client")
// Supabase requires { prepare: false } when using the Transaction Pooler (Port 6543)
const client = postgres(connectionString, { prepare: false });

// 3. Initialize Drizzle by passing the client
export const db = drizzle(client, { schema });