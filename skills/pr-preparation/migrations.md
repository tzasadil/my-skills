# DB migrations

- Each migration has a down/reverse path
- Destructive ops (`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`) -> extra scrutiny
- Migrations must not reference code-level constants or models. Standalone SQL.
- Many-to-many modeled as a scalar-list column (`String[]` / `Int[]` / `UUID[]`) whose name references an existing model -> use a join table (FK integrity, reverse lookups, real Prisma relation).
- **Never run down migrations.** Destructive and error-prone. Instead: run all up migrations, then delete the migration records from `_prisma_migrations` (or equivalent) to reset state.

## Consolidation (autofix)

Multiple migration files in the diff for the same logical schema change -> one file. Assume none have been run remotely. Everything in the diff is local unless already present upstream. Local migrations must run cleanly before consolidating.

1. Local dev setup (`just dev` or similar) so all local migrations are applied.
2. Concatenate local migration files, in order, into one new file. Exact append. Never dedupe, reorder, or alter. Down migrations cannot be consolidated by appending — they run in reverse.
3. Delete old migration records; mark the new one applied:

```bash
# use to reset Prisma migration history onto the consolidated file
psql -c "DELETE FROM _prisma_migrations WHERE migration_name IN ('old_migration_1', 'old_migration_2')"
npx prisma migrate resolve --applied <name-of-new-consolidated-migration>
```

4. Delete the now-redundant individual files and their wiring (imports, registrations, tracking entries).
