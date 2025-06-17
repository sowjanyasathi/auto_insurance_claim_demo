import streamlit as st
import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
import nest_asyncio
import asyncio

from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.core.workflow import Workflow, Context, StartEvent, StopEvent, Event, step
from llama_index.core.llms import LLM
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.vector_stores.types import MetadataFilters

# -------------------------
# Step 0: Init
# -------------------------
nest_asyncio.apply()

os.environ["DECLARATIONS_INDEX_NAME"] = st.secrets["DECLARATIONS_INDEX_NAME"]
os.environ["POLICY_INDEX_NAME"] = st.secrets["POLICY_INDEX_NAME"]
os.environ["ORGANIZATION_ID"] = st.secrets["ORGANIZATION_ID"]
os.environ["PROJECT_NAME"] = st.secrets.get("PROJECT_NAME", "Default")


os.environ["LLAMA_CLOUD_API_KEY"] = st.secrets["LLAMA_CLOUD_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# -------------------------
# Step 1: Define Models
# -------------------------
class ClaimInfo(BaseModel):
    claim_number: str
    policy_number: str
    claimant_name: str
    date_of_loss: str
    loss_description: str
    estimated_repair_cost: float
    vehicle_details: Optional[str] = None

class PolicyQueries(BaseModel):
    queries: List[str] = Field(default_factory=list)

class PolicyRecommendation(BaseModel):
    policy_section: str
    recommendation_summary: str
    deductible: Optional[float] = None
    settlement_amount: Optional[float] = None

class ClaimDecision(BaseModel):
    claim_number: str
    covered: bool
    deductible: float
    recommended_payout: float
    notes: Optional[str] = None

# -------------------------
# Step 1B: Define Events
# -------------------------
class ClaimInfoEvent(Event):
    claim_info: ClaimInfo

class PolicyQueryEvent(Event):
    queries: PolicyQueries

class PolicyMatchedEvent(Event):
    policy_text: str

class RecommendationEvent(Event):
    recommendation: PolicyRecommendation

class DecisionEvent(Event):
    decision: ClaimDecision

class LogEvent(Event):
    msg: str
    delta: bool = False

# -------------------------
# Step 2: Setup Llama Cloud
# -------------------------
declarations_index = LlamaCloudIndex(
    name=os.environ["DECLARATIONS_INDEX_NAME"],
    project_name=os.environ["PROJECT_NAME"],
    organization_id=os.environ["ORGANIZATION_ID"] ,
    api_key=os.environ["LLAMA_CLOUD_API_KEY"],
)

policy_index = LlamaCloudIndex(
    name=os.environ["POLICY_INDEX_NAME"],
    project_name=os.environ["PROJECT_NAME"],
    organization_id=os.environ["ORGANIZATION_ID"] ,
    api_key=os.environ["LLAMA_CLOUD_API_KEY"],
)

retriever = policy_index.as_retriever(rerank_top_n=3)

def get_declarations_docs(policy_number: str):
    filters = MetadataFilters.from_dicts([{ "key": "policy_number", "value": policy_number }])
    return declarations_index.as_retriever(filters=filters).retrieve(f"declarations page for {policy_number}")

# -------------------------
# Step 3: Prompts
# -------------------------
GEN_POLICY_QUERIES_PROMPT = """
You’re an expert assistant trained in processing auto insurance claims.
# Task:
Identify the key policy sections to review based on claim details.
# Instructions:
- Review the claim
- Generate 3 to 5 queries to find relevant clauses
# Result:
Return JSON matching PolicyQueries schema.
Claim Info:
{claim_info}
"""

POLICY_RECOMMENDATION_PROMPT = """
You’re an expert assistant analyzing insurance policy documents.
# Task:
Evaluate the claim and recommend coverage.
# Instructions:
- Determine if covered, deductible, payout, and policy section
# Result:
Return JSON matching PolicyRecommendation schema.
Claim Info:
{claim_info}
Policy Text:
{policy_text}
"""

# -------------------------
# Step 4: Workflow
# -------------------------
class AutoInsuranceWorkflow(Workflow):
    def __init__(self, policy_retriever: BaseRetriever, llm: LLM = None, **kwargs):
        super().__init__(timeout=180, **kwargs)
        self.policy_retriever = policy_retriever
        self.llm = llm or OpenAI(model="gpt-4o")

    @step
    async def load_claim_info(self, ctx: Context, ev: StartEvent) -> ClaimInfoEvent:
        claim_info = ev.payload["claim_info"]
        await ctx.set("claim_info", claim_info)
        return ClaimInfoEvent(claim_info=claim_info)

    @step
    async def generate_policy_queries(self, ctx: Context, ev: ClaimInfoEvent) -> PolicyQueryEvent:
        prompt = ChatPromptTemplate.from_messages([("user", GEN_POLICY_QUERIES_PROMPT)])
        queries = await self.llm.astructured_predict(
            PolicyQueries,
            prompt,
            claim_info=ev.claim_info.model_dump_json()
        )
        return PolicyQueryEvent(queries=queries)

    @step
    async def retrieve_policy_text(self, ctx: Context, ev: PolicyQueryEvent) -> PolicyMatchedEvent:
        claim_info = await ctx.get("claim_info")
        combined_docs = {}
        for query in ev.queries.queries:
            docs = await self.policy_retriever.aretrieve(query)
            for d in docs:
                combined_docs[d.id_] = d

        d_doc = get_declarations_docs(claim_info.policy_number)[0]
        combined_docs[d_doc.id_] = d_doc

        policy_text = "\n\n".join([doc.get_content() for doc in combined_docs.values()])
        await ctx.set("policy_text", policy_text)
        return PolicyMatchedEvent(policy_text=policy_text)

    @step
    async def generate_recommendation(self, ctx: Context, ev: PolicyMatchedEvent) -> RecommendationEvent:
        claim_info = await ctx.get("claim_info")
        prompt = ChatPromptTemplate.from_messages([("user", POLICY_RECOMMENDATION_PROMPT)])
        recommendation = await self.llm.astructured_predict(
            PolicyRecommendation,
            prompt,
            claim_info=claim_info.model_dump_json(),
            policy_text=ev.policy_text
        )
        return RecommendationEvent(recommendation=recommendation)

    @step
    async def finalize_decision(self, ctx: Context, ev: RecommendationEvent) -> DecisionEvent:
        claim_info = await ctx.get("claim_info")
        rec = ev.recommendation
        covered = (
            "not covered" not in rec.recommendation_summary.lower() and
            rec.settlement_amount is not None and
            rec.settlement_amount > 0
        )
        deductible = rec.deductible if rec.deductible else 0.0
        payout = rec.settlement_amount if rec.settlement_amount else 0.0
        decision = ClaimDecision(
            claim_number=claim_info.claim_number,
            covered=covered,
            deductible=deductible,
            recommended_payout=payout,
            notes=rec.recommendation_summary
        )
        return DecisionEvent(decision=decision)

    @step
    async def output_result(self, ctx: Context, ev: DecisionEvent) -> StopEvent:
        return StopEvent(result={"decision": ev.decision})

# -------------------------
# Step 5: Streamlit UI
# -------------------------
st.set_page_config(page_title="Auto Claim Decision", page_icon="📄")
st.title("📄 Auto Insurance Claim Decision")

uploaded_file = st.file_uploader("Upload Claim JSON File", type=["json"])

import asyncio

async def process_claim(claim_info):
    workflow = AutoInsuranceWorkflow(policy_retriever=retriever)
    return await workflow.run(payload={"claim_info": claim_info})

if uploaded_file:
    raw_json = uploaded_file.read().decode("utf-8")
    claim_data = json.loads(raw_json)
    claim_info = ClaimInfo.model_validate(claim_data)

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(process_claim(claim_info))
    decision = result["decision"]

    st.markdown("---")
    if decision.covered:
        st.success("\u2705 Claim Approved")
    else:
        st.error("\u274C Claim Denied")

    st.markdown(f"**Claim Number:** {decision.claim_number}")
    st.markdown(f"**Covered:** {'Yes' if decision.covered else 'No'}")
    st.markdown(f"**Deductible:** ${decision.deductible}")
    st.markdown(f"**Recommended Payout:** ${decision.recommended_payout}")
    st.markdown(f"**Notes:** {decision.notes}")
