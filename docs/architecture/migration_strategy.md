# Migration Strategy

The project now uses a lightweight application-managed migration runner in `backend/common/database.py`.

## Current responsibilities

- preserve older installs that predate `DerivedMemory.user_id`
- backfill `AuthIdentity` rows for existing `User` records
- ensure wallet rows exist for migrated users
- provide a stable place for future auth/storage migrations

## Current migration model

- `SQLModel.metadata.create_all()` creates the latest tables first
- a `SchemaMigration` table records applied migration ids
- ordered Python migrations run once per database

## Current auth-related schema additions

- `AuthIdentity`: provider-specific identity records decoupled from business user data
- `AuthSession`: server-stored opaque interactive sessions
- `SchemaMigration`: applied migration tracking

## Rules for future migrations

1. make each migration idempotent enough to survive retries safely
2. preserve existing user access whenever possible
3. keep trusted-LAN synthetic identities explicit, not implicit special cases
4. use migrations for schema changes instead of ad-hoc startup writes in unrelated modules
