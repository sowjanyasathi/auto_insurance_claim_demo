# 🛠️ Auto Insurance Claim Demo

This project showcases an end-to-end prototype for processing auto insurance claims using LlamaIndex, LlamaCloud, and Streamlit.

---

## ⚙️ Step 1: LlamaCloud Setup & Indexing

1. Go to [LlamaCloud](https://cloud.llamaindex.ai/) and log in.
2. Create two indices:
   - One for **declarations** (e.g., `declarations`)
   - One for **insurance policy documents** (e.g., `insurance policies demo`)
3. Upload markdown or text files to each index:
   - `declarations` index → Contains individual policy declarations (e.g., `jane-declarations.md`)
   - `insurance policies demo` index → Contains general insurance policies for claims evaluation

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

## 📂 Example Files
Include the following in your GitHub repo:
- `app.py` (main Streamlit app)
- `.streamlit/secrets.toml` (DO NOT push secrets to GitHub)
- Example claim files like `john.json`, `jane.json`
- Declarations/policy files in `.md` format

---

## ✅ Sample Secrets Format (DO NOT PUSH)
```toml
OPENAI_API_KEY = "sk-..."
LLAMA_CLOUD_API_KEY = "llama-..."
DECLARATIONS_INDEX_NAME = "declarations"
POLICY_INDEX_NAME = "insurance policies demo"
ORGANIZATION_ID = "00ff99a1-76e4-4102-bfcd-c52dfb42cdc0"
```

---

## 📞 Contact
If you're collaborating or demoing this to stakeholders, ensure they:
- Have their own LlamaCloud account
- Fork your repo
- Deploy to their own Streamlit workspace using their own keys

Let me know if you'd like to automate this setup or convert to a Docker deployment.
