# GitHub Secrets Configuration Guide

## Quick Links

- **GitHub Secrets Settings:** https://github.com/Skybee2027/ghgf-complete/settings/secrets/actions
- **Repository:** https://github.com/Skybee2027/ghgf-complete
- **Actions Workflows:** https://github.com/Skybee2027/ghgf-complete/actions

---

## All Required Secrets

### 🗄️ DATABASE CONFIGURATION (REQUIRED)

| Secret Name | Value | Source | Status |
|---|---|---|---|
| `DB_HOST` | Your MySQL database hostname/IP | cPanel → Databases → MySQL Databases | ❌ **NOT SET** |
| `DB_USER` | Your MySQL database username | cPanel → MySQL Databases | ⚠️ Check |
| `DB_PASSWORD` | Your MySQL database password | cPanel setup email or your password manager | ⚠️ Check |
| `DB_NAME` | `ghgf_blogging` | Fixed database name | ⚠️ Check |

**CRITICAL:** `DB_HOST` is the most common problem. It must be:
- Your actual database hostname/IP (NOT `localhost`)
- Something like: `db.example.com`, `192.168.1.100`, or a specific server address
- Ask your hosting provider if unsure!

### 🔑 LLM API KEYS (At least ONE required)

| Secret Name | Provider | Value | Status |
|---|---|---|---|
| `GROQ_API_KEY` | Groq (recommended - fast & cheap) | Get from https://console.groq.com | ⚠️ Check |
| `GEMINI_API_KEY` | Google Gemini (fallback #1) | Get from https://makersuite.google.com | ⚠️ Check |
| `COHERE_API_KEY` | Cohere (fallback #2) | Get from https://dashboard.cohere.com | ⚠️ Check |
| `OPENAI_API_KEY` | OpenAI (fallback #3) | Get from https://platform.openai.com/api-keys | ⚠️ Check |

**Note:** Only ONE is required, but having multiple enables the fallback system. Groq is fastest and cheapest.

### 🎯 LLM MODEL NAMES (Optional - uses defaults if not set)

| Secret Name | Default Value | Recommended |
|---|---|---|
| `GROQ_MODEL` | `openai/gpt-oss-120b` | (leave as default or check Groq console) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | (auto-selected if empty) |
| `COHERE_MODEL` | `command-a-plus-05-2026` | (leave as default or check Cohere) |
| `OPENAI_MODEL` | `gpt-4o-mini` | (or use `gpt-4-turbo` for better quality) |

### 📝 WORDPRESS CONFIGURATION (For Publishing)

| Secret Name | Value | Source | Status |
|---|---|---|---|
| `WORDPRESS_URL` | `https://greathealthgreatfitness.com` | Your WordPress site URL | ⚠️ Check |
| `WORDPRESS_USER` | `GHGF` | Your WordPress Application Password username | ⚠️ Check |
| `WORDPRESS_PASSWORD` | (Application password from WordPress) | WordPress → Users → Application Passwords | ❌ **CRITICAL** |

**Note:** `WORDPRESS_PASSWORD` is required for R31 to publish posts. Without it, posts are created but not published.

---

## How to Add/Update Secrets

### Step 1: Go to GitHub Secrets Settings

```
https://github.com/Skybee2027/ghgf-complete/settings/secrets/actions
```

Or:
1. Go to Repository: https://github.com/Skybee2027/ghgf-complete
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)

### Step 2: Create or Update Each Secret

**To CREATE a new secret:**
1. Click **New repository secret**
2. Name: (e.g., `DB_HOST`)
3. Value: (your actual value)
4. Click **Add secret**

**To UPDATE an existing secret:**
1. Click the secret name
2. Update the value
3. Click **Update secret**

### Step 3: Verify All Secrets Are Set

Go back to the Secrets list and verify you see:
- ✅ `DB_HOST` (most critical!)
- ✅ At least one LLM API key
- ✅ `WORDPRESS_PASSWORD` (if you want automatic publishing)

---

## Finding Your Values

### Finding DB_HOST (Most Important!)

**For cPanel Hosting:**
1. Login to cPanel: `https://cpanel.greathealthgreatfitness.com`
2. Look for **Databases** or **MySQL Databases**
3. Find your database `ghgf_blogging`
4. The hostname is listed as:
   - "Database Server" or
   - "Server:" or
   - Shows something like `localhost`, `127.0.0.1`, or an IP/hostname

**If it shows `localhost`:**
- This means the database is on the same server as WordPress
- For GitHub Actions to reach it, you need the **server's public IP or hostname**
- Contact your hosting provider: "What is the remote database hostname for external connections?"

### Finding LLM API Keys

**Groq (Recommended):**
1. Go to https://console.groq.com
2. Login or create account
3. Go to **API Keys**
4. Create new API key
5. Copy the key to `GROQ_API_KEY` secret

**Google Gemini:**
1. Go to https://makersuite.google.com
2. Create API key
3. Copy to `GEMINI_API_KEY` secret

**Cohere:**
1. Go to https://dashboard.cohere.com
2. Get API key
3. Copy to `COHERE_API_KEY` secret

**OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy to `OPENAI_API_KEY` secret

### Finding WordPress Application Password

1. Go to: `https://greathealthgreatfitness.com/wp-admin`
2. Go to **Users** → **Your Profile**
3. Scroll down to **Application Passwords**
4. Find the application created for GHGF
5. Copy the password (if you don't see it, create a new one)
6. The password should look like: `NpIj JWDn RUsj yQgf Xk0i ZsGr`

---

## Testing Your Secrets

After setting all secrets, test them:

### Method 1: Run the Workflow

1. Go to **Actions**
2. Click **GHGF 42-Robot Autonomous Blogging Pipeline**
3. Click **Run workflow** → **Run workflow**
4. Check the **"Verify environment variables are set"** step
5. If it shows ✅ checks, your secrets are correct

### Method 2: Test Database Locally

If you have Python and MySQL client installed:

```bash
# Run the test script
python3 test_database_connection.py

# Enter your values when prompted
# It will test the connection and tell you if it works
```

---

## Troubleshooting

### Problem: "DB_HOST is not properly configured"

**Solution:**
1. Go to GitHub Secrets
2. Make sure `DB_HOST` is NOT `localhost`
3. Set it to your actual database hostname/IP
4. Re-run the workflow

### Problem: "Could not connect to database"

**Possible causes:**
1. Wrong hostname/IP
2. Wrong username or password
3. Database server is offline
4. Firewall blocking connection

**Solutions:**
1. Test locally: `python3 test_database_connection.py`
2. Contact hosting provider for correct hostname
3. Verify MySQL user has remote access enabled

### Problem: "LLM API key not working"

**Solutions:**
1. Verify the key is active in the provider's dashboard
2. Check for typos or extra spaces
3. Try a different provider's API key
4. Check API key hasn't been revoked

### Problem: "Posts created but not published to WordPress"

**Solution:**
1. Make sure `WORDPRESS_PASSWORD` is set in GitHub Secrets
2. Verify username/password are correct
3. Test WordPress REST API access
4. Check if WordPress site is in maintenance mode

---

## Security Notes

1. **Never** commit secrets to GitHub (they're in GitHub Secrets, not the repo) ✓
2. **Never** share your API keys or passwords
3. **Never** paste secrets in issues or comments
4. Secrets are encrypted and only visible to GitHub Actions
5. If a key is compromised, revoke it immediately from the provider's dashboard

---

## After Everything is Set

Once all secrets are configured:

1. ✅ Go to **Actions** tab
2. ✅ Select **GHGF 42-Robot Autonomous Blogging Pipeline**
3. ✅ Click **Run workflow** → **Run workflow**
4. ✅ Wait 2-3 minutes for execution
5. ✅ Check logs for success
6. ✅ Visit https://greathealthgreatfitness.com to see new blog post

The workflow will then run automatically every 6 hours (or whenever you trigger it).

---

## Need Help?

1. **Database connection:** See `WORKFLOW_FAILURE_ROOT_CAUSE_ANALYSIS.md`
2. **Fix instructions:** See `FIX_DATABASE_CONNECTION_ERROR.md`
3. **Test script:** Run `python3 test_database_connection.py`

Good luck! 🚀
