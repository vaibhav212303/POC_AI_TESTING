import { pgTable, serial, text, timestamp, integer, pgEnum } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

export const statusEnum = pgEnum('status', ['running', 'completed', 'failed', 'passed']);

export const automationBuilds = pgTable('automation_builds', {
  id: serial('id').primaryKey(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  status: text('status').default('running').notNull(),
  environment: text('environment').default('dev'),
});

export const testResults = pgTable('test_results', {
  id: serial('id').primaryKey(),
  buildId: integer('build_id').references(() => automationBuilds.id, { onDelete: 'cascade' }),
  caseCode: text('case_code').notNull(), // TC5073
  title: text('title').notNull(),
  status: text('status').notNull(), // passed, failed
  duration: text('duration'),
  errorMessage: text('error_message'),
  executedAt: timestamp('executed_at').defaultNow().notNull(),
});

// Relationships
export const buildsRelations = relations(automationBuilds, ({ many }) => ({
  results: many(testResults),
}));

export const resultsRelations = relations(testResults, ({ one }) => ({
  build: one(automationBuilds, {
    fields: [testResults.buildId],
    references: [automationBuilds.id],
  }),
}));