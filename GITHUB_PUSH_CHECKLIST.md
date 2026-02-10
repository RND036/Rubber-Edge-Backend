# ✅ GitHub Push Checklist

Before pushing your Rubber Farm Backend to GitHub, complete these steps:

## 🔒 Security Check

- [ ] **SECRET_KEY is environment-based**
  - Verify in `settings.py`: `SECRET_KEY = os.environ.get('SECRET_KEY', ...)`
  - Never commit real SECRET_KEY values

- [ ] **DEBUG is configurable**
  - Verify: `DEBUG = os.environ.get('DEBUG', 'True') == 'True'`
  - Set to `False` before deploying

- [ ] **ALLOWED_HOSTS is configurable**
  - Verify: `ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', ...).split(',')`
  - Will be set per deployment

- [ ] **AWS credentials are NOT hardcoded**
  - Search for `AWS_SECRET_ACCESS_KEY` - should be: `os.environ.get('AWS_SECRET_ACCESS_KEY')`
  - All AWS configs should use `os.environ.get()`

- [ ] **No actual API keys in code**
  - Grep for: `TWILIO_ACCOUNT_SID`, `AWS_ACCESS_KEY_ID`, etc.
  - All should be environment variables

## 📁 File Check

- [ ] `.env` file is in `.gitignore` ✓ (Already configured)
- [ ] `.env.example` exists (✓ Already exists - updated)
- [ ] `.gitignore` includes:
  ```
  .env
  .env.local
  .env.production
  *.pem
  AWS_CREDENTIALS.txt (Keep AWS files EXCEPT credentials)
  db.sqlite3
  __pycache__/
  .DS_Store
  ```

- [ ] These files CAN be committed (they're safe):
  - ✅ `AWS_DEPLOYMENT.md` - Documentation only
  - ✅ `aws_settings.py` - Configuration template
  - ✅ `AWS_QUICK_START.md` - Setup guide
  - ✅ `deployment/setup_aws.sh` - Scripts
  - ✅ `railway.toml` - Railway config
  - ✅ `render.yaml` - Render config

## 📝 Documentation Check

- [ ] `GITHUB_SETUP.md` exists with:
  - [ ] Local development setup instructions
  - [ ] Mobile app integration guide
  - [ ] Deployment options (Railway, Render, AWS)
  - [ ] Environment variables documentation
  - [ ] Security checklist
  - [ ] Troubleshooting section

- [ ] `MOBILE_API_INTEGRATION.md` exists with:
  - [ ] API endpoint examples
  - [ ] Authentication flow
  - [ ] Code examples (Flutter, React Native, Swift)
  - [ ] WebSocket integration guide
  - [ ] Security best practices

- [ ] `README.md` updated (or create comprehensive one)

- [ ] `requirements.txt` is complete and up-to-date

## 🧪 Code Check

- [ ] Run migrations locally: `python manage.py migrate`
- [ ] Test API endpoints: `python manage.py runserver`
- [ ] Check for syntax errors: `python -m py_compile **/*.py`
- [ ] Test with `.env.example` settings (copy to `.env` locally)

## 🚀 Pre-Push Commands

```bash
# 1. Check git status (ensure .env is NOT being pushed)
git status

# 2. Verify .env is in gitignore
git check-ignore -v .env

# 3. See what will be committed
git diff --cached

# 4. Verify no credentials in staged files
git diff --cached | grep -i "secret\|password\|key\|aws_"

# 5. Final safety check before push
git log --oneline -5  # See recent commits

# 6. Push to GitHub
git push origin main
```

## 📋 GitHub Repository Setup

After pushing:

1. **Add repository description:**
   ```
   Django REST API backend for Rubber Farm mobile app with AI disease detection, 
   real-time chat, and market price tracking.
   ```

2. **Add topics:** `django`, `rest-api`, `backend`, `websocket`, `channels`

3. **Add to README:**
   - Link to GITHUB_SETUP.md
   - Link to MOBILE_API_INTEGRATION.md
   - Quick start instructions

4. **Configure GitHub Pages (Optional):**
   - Can host API documentation

5. **Set up branch protection rules (Optional):**
   - Require pull requests for main branch
   - Add CI/CD checks if desired

## 🔑 Per-Deployment Setup

After pushing, for each deployment platform:

### Railway
```bash
# Set environment variables in Railway dashboard
DEBUG=False
SECRET_KEY=<generate-new>
ALLOWED_HOSTS=your-railway-domain.up.railway.app
DB_PASSWORD=<set-by-railway>
```

### Render
```bash
# Set in render.yaml or Render dashboard
DEBUG=False
SECRET_KEY=<generate-new>
ALLOWED_HOSTS=your-render-domain.onrender.com
```

### AWS
```bash
# Use deployment scripts and set in EC2/RDS
DEBUG=False
SECRET_KEY=<generate-new>
ALLOWED_HOSTS=your-domain.com
AWS_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
```

## ✨ Final Verification

- [ ] Can clone from GitHub: `git clone <your-repo>`
- [ ] Can install deps: `pip install -r requirements.txt`
- [ ] Can create .env from .env.example
- [ ] Can run migrations: `python manage.py migrate`
- [ ] Can start server: `python manage.py runserver`
- [ ] Can test API endpoints
- [ ] Documentation is clear and complete

---

## 🚨 If You Accidentally Pushed Credentials

**IMMEDIATELY DO THIS:**

1. **Rotate all credentials:**
   ```bash
   # Generate new SECRET_KEY
   python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Remove sensitive commits:**
   ```bash
   # Remove file from history (keep locally)
   git rm --cached AWS_CREDENTIALS.txt
   echo "AWS_CREDENTIALS.txt" >> .gitignore
   git add .gitignore
   git commit -m "Remove sensitive file from history"
   git push
   ```

3. **Use git-filter-repo to remove from history (if already pushed):**
   ```bash
   pip install git-filter-repo
   git filter-repo --invert-paths --path AWS_CREDENTIALS.txt
   git push --force-with-lease
   ```

4. **On platforms (Railway, Render, AWS):**
   - Update all credentials with new values
   - Invalidate old credentials immediately

---

**Ready? Run the pre-push commands above and push with confidence!** 🚀
