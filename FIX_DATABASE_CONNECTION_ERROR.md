# 🔧 FIX: Database Connection Error (localhost:3306 refused)

## Problem Identified

**Error Log Shows:**
```
Database connection failed: 2003: Can't connect to MySQL server on 'localhost:3306' (Errno 111: Connection refused)
```

**Root Cause:**
- GitHub Actions runs in the cloud (ubuntu-latest)
- The `DB_HOST` GitHub Secret is NOT set (or empty)
- Workflow defaults to `localhost` which doesn't exist in cloud
- GitHub Actions cannot access your local machine's localhost

---

## Solution: Set DB_HOST in GitHub Secrets

### Step 1: Find Your Database Host Address

Your database is hosted remotely on cPanel. You need to find the database server address. This is typically:

**Option A: Check Your cPanel (Most Common)**
1. Login to cPanel for greathealthgreatfitness.com
2. Go to **Databases** or **MySQL Databases**
3. Look for the database hostname (usually something like):
   - `localhost` (if database is on same server)
   - `127.0.0.1` (local IP)
   - `dbserver.example.com` (remote database server)
   - A specific IP address like `193.203.166.xxx`

**Option B: Check Your Email from Hosting Provider**
- Look for setup emails that mention "Database Host"
- Usually named something like "Database Server" or "MySQL Server"

**Option C: Check Configuration Files**
- If you have access to the WordPress wp-config.php file, look for:
  ```php
  define('DB_HOST', 'your-database-host-here');
  ```

### Step 2: Update GitHub Secrets

1. Go to your GitHub Repository: https://github.com/Skybee2027/ghgf-complete
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

4. Add these secrets (if not already present):

   | Secret Name | Value | Where to Find |
   |---|---|---|
   | `DB_HOST` | `[Your database hostname/IP]` | cPanel → Databases |
   | `DB_USER` | `[Your database username]` | cPanel → MySQL Databases |
   | `DB_PASSWORD` | `[Your database password]` | cPanel setup email or your notes |
   | `DB_NAME` | `ghgf_blogging` | (Usually this name) |

5. **Important:** If the hostname is `localhost` and database is on same server as WordPress:
   - You may need to allow **remote access** to the database
   - Contact your hosting provider to enable remote MySQL access
   - Or ask them for the actual database server hostname/IP

### Step 3: Verify Secrets Are Set Correctly

Run this test in GitHub Actions:

1. Go to **Actions** → **GHGF 42-Robot Autonomous Blogging Pipeline**
2. Click **Run workflow** → **Run workflow**
3. Watch the **"Verify environment variables are set"** step
4. Check for these messages:

   ✅ **Expected (Success):**
   ```
   Checking required environment variables...
   ✅ Database and LLM configuration verified
   ```

   ❌ **Indicates Problem:**
   ```
   ERROR: DB_HOST not set
   ERROR: Could not connect to database
   ```

5. If you see connection errors, double-check the hostname/IP you entered

### Step 4: Check Database Access Permissions

If you still get connection refused:

**Contact your hosting provider and ask:**
1. "Can I connect to MySQL database remotely from external servers?"
2. "What is the MySQL hostname/IP for remote connections?"
3. "Do I need to enable remote MySQL access?"
4. "Should I use localhost or a specific hostname?"

Some hosts require:
- Creating a new MySQL user with "Allow remote access" enabled
- Or providing the hosting provider's database access credentials

---

## Common Database Hosts

These are typical values depending on your hosting:

| Hosting Provider | Typical DB_HOST |
|---|---|
| **cPanel (shared hosting)** | `localhost` or `127.0.0.1` |
| **cPanel (allow remote)** | `[server-ip-or-hostname]` |
| **AWS RDS** | `[endpoint].rds.amazonaws.com` |
| **Google Cloud SQL** | `[cloudsql-connection-name]` |
| **DigitalOcean Managed** | `[app-id].db.ondigitalocean.com` |
| **Local Server** | `[your-server-ip]` |

---

## Testing Database Connection Manually

If you want to test before running the workflow:

### Using Command Line (if you have MySQL client):
```bash
mysql -h "[YOUR_DB_HOST]" -u "[DB_USER]" -p"[DB_PASSWORD]" -e "SELECT 1;"
```

### Using cPanel:
1. Login to cPanel
2. Go to **phpMyAdmin**
3. Try to login with your database credentials
4. If login works → credentials are correct
5. If login fails → credentials need updating

---

## After Setting DB_HOST

Once you've set the correct `DB_HOST` in GitHub Secrets:

1. ✅ Go back to **Actions**
2. ✅ Click **Run workflow** → **Run workflow**
3. ✅ Monitor the workflow execution
4. ✅ Check that all robots complete (R2→R3→...→R36)
5. ✅ Verify blog posts appear at greathealthgreatfitness.com

---

## Summary of Fixes

| Issue | Cause | Solution |
|---|---|---|
| `localhost:3306` connection refused | `DB_HOST` not set in GitHub Secrets | Set `DB_HOST` to actual remote database hostname/IP |
| "Could not connect" error | Wrong hostname/credentials | Verify with cPanel or hosting provider |
| Slow workflow execution | Database not accessible | Ensure remote access enabled for MySQL |

---

## Questions to Ask Your Hosting Provider

If you're unsure about the database host, copy this and send to support:

> Hi, I'm trying to connect to my MySQL database from GitHub Actions (a cloud CI/CD platform). My WordPress site is at greathealthgreatfitness.com with database name `ghgf_blogging`. 
> 
> What is the correct database hostname/IP address I should use for remote connections from external servers?
> 
> Should I use `localhost`, `127.0.0.1`, or a specific IP/hostname?
> 
> Do I need to enable "Allow remote access" for my MySQL user?

---

**Next Step:** Once you've updated DB_HOST in GitHub Secrets, run the workflow again and check the logs!
