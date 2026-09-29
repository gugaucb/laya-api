# Laya API: Docker Hub & GitHub Actions Setup Guide

This guide walks you step-by-step through configuring **Docker Hub** access tokens and **GitHub Repository Secrets** to enable automated multi-arch and CUDA image publishing on every release.

---

## 🔑 Step 1: Generate Docker Hub Access Token (PAT)

Never use your raw Docker Hub account password in CI/CD pipelines. Generate a Personal Access Token (PAT) instead:

1. Log into your account at [https://hub.docker.com/](https://hub.docker.com/).
2. In the top-right corner, click on your username/avatar and select **Account Settings**.
3. In the left navigation menu, click **Security**.
4. Click **New Access Token**.
5. Set the token description (e.g. `GitHub Actions - Laya API`).
6. Set **Access permissions** to **Read, Write, Delete** (or **Read & Write**).
7. Click **Generate**.
8. ⚠️ **Copy and save the generated token immediately** (it will only be displayed once).

---

## 🔒 Step 2: Configure GitHub Repository Secrets

Now add the credentials as encrypted secrets in your GitHub repository:

1. Open your repository on GitHub: [https://github.com/gugaucb/laya-api](https://github.com/gugaucb/laya-api).
2. Click **Settings** (top bar).
3. In the left sidebar, expand **Secrets and variables** and click **Actions**.
4. Click the green button: **New repository secret**.
5. Add the first secret:
   - **Name**: `DOCKERHUB_USERNAME`
   - **Secret**: Your Docker Hub username (e.g. `gugaucb`).
   - Click **Add secret**.
6. Click **New repository secret** again for the token:
   - **Name**: `DOCKERHUB_TOKEN`
   - **Secret**: Paste the Personal Access Token generated in Step 1.
   - Click **Add secret**.

---

## 🚀 Step 3: Trigger an Automated Docker Hub Release

Once the secrets are configured, you can trigger a release in two ways:

### Option A: Create and Push a SemVer Git Tag (Recommended)
```bash
# 1. Ensure working directory is clean
git status

# 2. Create an annotated version tag
git tag -a v0.1.0 -m "Release v0.1.0"

# 3. Push the tag to GitHub
git push origin v0.1.0
```

### Option B: Trigger Manually via GitHub UI (`workflow_dispatch`)
1. Go to your repository's **Actions** tab on GitHub.
2. Select **Publish Docker Images to Docker Hub** in the left workflow list.
3. Click **Run workflow**, enter the version tag (e.g. `v0.1.0`), and confirm.

---

## 🐳 Step 4: Verify Published Images on Docker Hub

After the workflow completes successfully (typically 2–4 minutes), your images will be live on Docker Hub:

```bash
# Test pulling the multi-arch CPU image:
docker pull gugaucb/laya-api:latest
docker pull gugaucb/laya-api:v0.1.0

# Test pulling the NVIDIA CUDA image:
docker pull gugaucb/laya-api:cuda
docker pull gugaucb/laya-api:v0.1.0-cuda
```
