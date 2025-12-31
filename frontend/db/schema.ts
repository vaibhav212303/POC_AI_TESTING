import { pgTable, serial, text, timestamp, integer, jsonb, unique } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

export const automationBuilds = pgTable('automation_builds', {
  id: serial('id').primaryKey(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  status: text('status').default('running').notNull(),
  environment: text('environment').default('dev'),
});

export const testResults = pgTable('test_results', {
  id: serial('id').primaryKey(),
  buildId: integer('build_id').references(() => automationBuilds.id, { onDelete: 'cascade' }),
  specFile: text('spec_file').notNull(),
  tests: jsonb('tests').default([]).notNull(), // Stores array of test objects
  executedAt: timestamp('executed_at').defaultNow().notNull(),
}, (table) => ({
  // CONCURRENCY CONTROL: Prevents race conditions during parallel execution
  buildSpecUnique: unique().on(table.buildId, table.specFile),
}));

export const buildsRelations = relations(automationBuilds, ({ many }) => ({
  results: many(testResults),
}));

export const resultsRelations = relations(testResults, ({ one }) => ({
  build: one(automationBuilds, {
    fields: [testResults.buildId],
    references: [automationBuilds.id],
  }),
}));