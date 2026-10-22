# Coolify Tips & Tricks

Useful snippets for managing storage permissions and databases in [Coolify](https://coolify.io).

---

## 1. Persistent Storage Permission Fix
Container users (e.g. Next.js, Node) often get `permission denied` on mounted host volumes.

1. Check UID/GID inside container terminal:
   ```bash
   id
   # Example: uid=100(nextjs) gid=101(nodejs)
   ```
2. Grant host directory ownership:
   ```bash
   sudo chown -R 100:101 /data/<app_name>/uploads
   sudo chmod 755 /data/<app_name>/uploads
   ```
3. Set Coolify volume mapping:
   * **Source:** `/data/<app_name>/uploads`
   * **Destination:** `/app/uploads`

---

## 2. PostgreSQL: Add User & Dedicated Database
In your Coolify PostgreSQL service terminal (`psql -U postgres`):

```sql
CREATE ROLE "<DB_USER>" LOGIN PASSWORD '<SECURE_PASSWORD>' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE "<DB_NAME>" OWNER "<DB_USER>";
\c "<DB_NAME>"
GRANT ALL ON SCHEMA public TO "<DB_USER>";
```

**Connection String:**
```text
postgres://<DB_USER>:<SECURE_PASSWORD>@<POSTGRES_HOST>:5432/<DB_NAME>
```
