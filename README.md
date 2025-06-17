# 🛠️ Auto Insurance Claim Demo

This project showcases an end-to-end prototype for processing auto insurance claims using LlamaIndex, LlamaCloud, and Streamlit.

---

## ⚙️ Step 1: LlamaCloud Setup & Indexing

1. Go to [LlamaCloud](https://cloud.llamaindex.ai/) and log in.
2. Create two indices:
   - One for **declarations** (e.g., `declarations`)
   - One for **insurance policy documents** (e.g., `insurance policies demo`)
3. Upload the following files:
   - `insurance policies demo` index → Upload `test_files/policies.pdf`
   - `declarations` index → Upload all client markdown files inside `test_files/declarations/` (e.g., `jane-declarations.md`, `john-declarations.md`)

📌 **Note:**
- You can use any names for `DECLARATIONS_INDEX_NAME`, `POLICY_INDEX_NAME`, and even `ORGANIZATION_ID`.
- But make sure you use **the same values** when adding them to **Streamlit Secrets** during deployment.

If multiple team members are collaborating:
- **Make a copy of this repo into your GitHub account** and customize index names as needed.

---

## 🚀 Step 2: Streamlit Cloud Deployment

1. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in.
2. Create a **new app** and link it to your forked GitHub repo.
3. In the sidebar, go to **Settings → Secrets** and add the following:

```toml
OPENAI_API_KEY = "your-openai-key"
LLAMA_CLOUD_API_KEY = "your-llama-cloud-key"
DECLARATIONS_INDEX_NAME = "declarations"
POLICY_INDEX_NAME = "insurance policies demo"
ORGANIZATION_ID = "your-organization-id"
```

4. Click **Deploy**.

Once deployed, your app will:
- Allow users to upload claim JSON files
- Process them through a LlamaIndex workflow
- Display the insurance decision result (Approved/Denied) and payout recommendation

---

## ✅ Sample Secrets Format (DO NOT PUSH)
```toml
OPENAI_API_KEY = "sk-..."
LLAMA_CLOUD_API_KEY = "llama-..."
DECLARATIONS_INDEX_NAME = "declarations"
POLICY_INDEX_NAME = "insurance policies demo"
ORGANIZATION_ID = "00ff99a1-76e4-4102-bfcd-c52dfb42cdc0"
```
