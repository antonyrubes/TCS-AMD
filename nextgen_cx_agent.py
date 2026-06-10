# ============================================================
#  NextGen CX Agent  —  Streamlit + OpenRouter (Free API)
#  Run:  streamlit run nextgen_cx_agent.py
#  Deps: pip install streamlit anthropic plotly
#
#  API Key: Get free key at https://openrouter.ai
#  Set in .streamlit/secrets.toml:
#    ANTHROPIC_API_KEY = "sk-or-your-openrouter-key-here"
# ============================================================

import streamlit as st
import anthropic
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="NextGen CX Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Global resets ── */
  [data-testid="stAppViewContainer"] { background: #0f1117; }
  [data-testid="stSidebar"] { background: #161b27; border-right: 1px solid #2a3145; }
  .block-container { padding: 1.5rem 2rem; }

  /* ── Header bar ── */
  .cx-header {
    background: linear-gradient(135deg, #1a2035 0%, #1e2d4a 100%);
    border: 1px solid #2a3a5c;
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .cx-header-title { font-size: 22px; font-weight: 700; color: #e8f0ff; margin: 0; }
  .cx-header-sub { font-size: 13px; color: #8896b3; margin: 2px 0 0; }
  .cx-badge {
    background: #1a3a6b; color: #60a5fa;
    border: 1px solid #2563eb44;
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.05em;
  }

  /* ── Metric cards ── */
  .metric-row { display: flex; gap: 12px; margin-bottom: 20px; }
  .metric-card {
    flex: 1; background: #161b27;
    border: 1px solid #2a3145;
    border-radius: 10px; padding: 14px 18px;
  }
  .metric-label { font-size: 11px; color: #8896b3; text-transform: uppercase; letter-spacing: 0.06em; margin: 0; }
  .metric-value { font-size: 26px; font-weight: 700; margin: 4px 0 0; }
  .mv-blue { color: #60a5fa; }
  .mv-green { color: #34d399; }
  .mv-amber { color: #fbbf24; }
  .mv-purple { color: #a78bfa; }

  /* ── Customer card ── */
  .customer-card {
    background: #1a2035; border: 1px solid #2a3145;
    border-radius: 10px; padding: 16px;
    margin-bottom: 12px; cursor: pointer;
    transition: border-color 0.2s;
  }
  .customer-card:hover { border-color: #3b82f6; }
  .customer-card.selected { border-color: #3b82f6; background: #1e2d4a; }
  .customer-name { font-size: 14px; font-weight: 600; color: #e8f0ff; margin: 0; }
  .customer-meta { font-size: 12px; color: #8896b3; margin: 3px 0 0; }

  /* ── Tier badges ── */
  .tier-platinum { background: #2d1b69; color: #c4b5fd; border: 1px solid #7c3aed44; border-radius: 6px; padding: 2px 8px; font-size: 10px; font-weight: 700; }
  .tier-gold { background: #2d1f00; color: #fbbf24; border: 1px solid #d9770044; border-radius: 6px; padding: 2px 8px; font-size: 10px; font-weight: 700; }
  .tier-silver { background: #1e2535; color: #94a3b8; border: 1px solid #47556944; border-radius: 6px; padding: 2px 8px; font-size: 10px; font-weight: 700; }
  .tier-bronze { background: #2d1200; color: #fb923c; border: 1px solid #c2410c44; border-radius: 6px; padding: 2px 8px; font-size: 10px; font-weight: 700; }

  /* ── Chat bubbles ── */
  .chat-container { display: flex; flex-direction: column; gap: 14px; padding: 8px 0; }
  .msg-user { display: flex; justify-content: flex-end; }
  .msg-agent { display: flex; justify-content: flex-start; gap: 10px; align-items: flex-end; }
  .bubble-user {
    background: #1d4ed8; color: #eff6ff;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px; max-width: 72%;
    font-size: 14px; line-height: 1.5;
  }
  .bubble-agent {
    background: #1a2035; border: 1px solid #2a3145; color: #d1d9f0;
    border-radius: 4px 18px 18px 18px;
    padding: 12px 16px; max-width: 72%;
    font-size: 14px; line-height: 1.5;
  }
  .agent-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: #1e3a6e; border: 1px solid #3b82f644;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
  }
  .resolution-pill {
    display: inline-block; margin-top: 8px;
    font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 20px;
  }
  .pill-resolved { background: #065f4633; color: #34d399; border: 1px solid #34d39933; }
  .pill-escalated { background: #78350f33; color: #fbbf24; border: 1px solid #fbbf2433; }
  .pill-pending   { background: #1e2d4a; color: #60a5fa; border: 1px solid #3b82f633; }

  /* ── Module cards ── */
  .module-card {
    background: #161b27; border: 1px solid #2a3145;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 12px;
  }
  .module-title { font-size: 10px; font-weight: 700; color: #4b6cb7;
    text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 10px; }
  .module-value { font-size: 15px; font-weight: 600; color: #e8f0ff; margin: 0 0 4px; }
  .module-detail { font-size: 12px; color: #8896b3; line-height: 1.55; margin: 0; }

  /* ── Confidence bar ── */
  .conf-bar-bg { background: #2a3145; border-radius: 4px; height: 5px; margin: 6px 0 4px; }
  .conf-bar-fill { height: 5px; border-radius: 4px; background: #3b82f6; }
  .conf-label { font-size: 11px; color: #8896b3; }

  /* ── Workflow steps ── */
  .workflow-step {
    display: flex; gap: 12px; align-items: flex-start;
    padding: 10px 0; border-bottom: 1px solid #2a3145;
  }
  .workflow-step:last-child { border-bottom: none; }
  .step-icon {
    width: 26px; height: 26px; border-radius: 50%;
    background: #065f4633; border: 1px solid #34d39933;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; flex-shrink: 0; color: #34d399;
  }
  .step-action { font-size: 13px; font-weight: 600; color: #d1d9f0; margin: 0 0 2px; }
  .step-detail { font-size: 12px; color: #8896b3; margin: 0; }

  /* ── Summary items ── */
  .summary-item { margin-bottom: 14px; }
  .summary-label { font-size: 10px; font-weight: 700; color: #4b6cb7;
    text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 4px; }
  .summary-text { font-size: 13px; color: #d1d9f0; line-height: 1.6; margin: 0; }
  .action-item {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: #d1d9f0; padding: 4px 0;
  }
  .action-dot { width: 6px; height: 6px; border-radius: 50%; background: #34d399; flex-shrink: 0; }

  /* ── Input area ── */
  .stTextInput > div > div > input {
    background: #161b27 !important; border: 1px solid #2a3145 !important;
    color: #e8f0ff !important; border-radius: 8px !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important; box-shadow: 0 0 0 2px #3b82f622 !important;
  }
  .stButton > button {
    background: #1d4ed8 !important; border: none !important;
    color: white !important; border-radius: 8px !important;
    font-weight: 600 !important; padding: 0.5rem 1.4rem !important;
  }
  .stButton > button:hover { background: #2563eb !important; }

  /* ── Sample buttons ── */
  .sample-btn {
    background: #1a2035; border: 1px solid #2a3145;
    border-radius: 8px; padding: 8px 12px;
    font-size: 12px; color: #8896b3;
    cursor: pointer; margin-bottom: 6px;
    width: 100%; text-align: left;
    transition: all 0.2s;
  }
  .sample-btn:hover { border-color: #3b82f6; color: #60a5fa; background: #1e2d4a; }

  /* ── Sidebar labels ── */
  .sidebar-section-label {
    font-size: 10px; font-weight: 700; color: #4b6cb7;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 16px 0 8px; padding-bottom: 6px;
    border-bottom: 1px solid #2a3145;
  }
  .profile-row { display: flex; justify-content: space-between;
    align-items: center; padding: 5px 0; }
  .profile-key { font-size: 12px; color: #8896b3; }
  .profile-val { font-size: 12px; font-weight: 600; color: #d1d9f0; }
</style>
""", unsafe_allow_html=True)

# ── Customer data ────────────────────────────────────────────
CUSTOMERS = {
    "C001": {
        "id": "C001", "name": "Sarah Mitchell", "email": "sarah.m@email.com",
        "tier": "Gold", "value_score": 87, "join_date": "2021-03-15",
        "purchase_history": ["Laptop Pro X1 ($1,299)", "Wireless Headphones ($249)", "USB-C Hub ($89)"],
        "past_complaints": ["Late delivery — resolved 2024-01-10", "Wrong item sent — refund issued 2023-11-22"],
        "interactions": 14, "lifetime_value": 4820, "avatar": "SM",
    },
    "C002": {
        "id": "C002", "name": "James Okonkwo", "email": "j.okonkwo@corp.com",
        "tier": "Platinum", "value_score": 96, "join_date": "2019-07-02",
        "purchase_history": ["Enterprise Suite License ($4,200)", "Server Hardware ($12,500)", "Support Plan ($800/yr)"],
        "past_complaints": ["Billing error — credited 2024-03-05"],
        "interactions": 38, "lifetime_value": 31200, "avatar": "JO",
    },
    "C003": {
        "id": "C003", "name": "Priya Sharma", "email": "priya.sharma@gmail.com",
        "tier": "Silver", "value_score": 62, "join_date": "2022-09-18",
        "purchase_history": ["Smartphone S22 ($799)", "Phone Case ($29)"],
        "past_complaints": ["Product defect — replacement sent 2023-08-14"],
        "interactions": 5, "lifetime_value": 1100, "avatar": "PS",
    },
    "C004": {
        "id": "C004", "name": "Carlos Rivera", "email": "carlos.r@startup.io",
        "tier": "Bronze", "value_score": 41, "join_date": "2023-11-01",
        "purchase_history": ["Starter Plan ($49/mo)"],
        "past_complaints": [],
        "interactions": 2, "lifetime_value": 294, "avatar": "CR",
    },
}

SAMPLE_MESSAGES = [
    "I need a refund for my laptop — it's defective.",
    "My package hasn't arrived and it's been 10 days!",
    "I want to cancel my subscription immediately.",
    "The product I received won't turn on at all.",
    "Can you help me track my order #ORD-8821?",
]

# ── Session state ────────────────────────────────────────────
if "messages"       not in st.session_state: st.session_state.messages       = []
if "agent_result"   not in st.session_state: st.session_state.agent_result   = None
if "selected_cid"   not in st.session_state: st.session_state.selected_cid   = "C001"
if "analytics"      not in st.session_state: st.session_state.analytics      = {"total": 0, "resolved": 0, "escalated": 0}
if "input_key"      not in st.session_state: st.session_state.input_key      = 0

# ── OpenRouter client (free API) ─────────────────────────────
@st.cache_resource
def get_client():
    return anthropic.Anthropic(
        api_key=st.secrets["ANTHROPIC_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )

# ── Agent logic ──────────────────────────────────────────────
def build_system_prompt(customer: dict, history: list) -> str:
    history_text = "\n".join(
        f"{'Customer' if m['role']=='user' else 'Agent'}: {m['content']}"
        for m in history
    ) or "No prior messages."
    return f"""You are the NextGen CX Agent — an autonomous AI customer experience agent.
Respond ONLY with a valid JSON object. No markdown, no text outside the JSON.

CUSTOMER MEMORY:
- Name: {customer['name']} | Tier: {customer['tier']} | Value Score: {customer['value_score']}/100
- Join Date: {customer['join_date']} | Lifetime Value: ${customer['lifetime_value']:,}
- Past Interactions: {customer['interactions']}
- Purchase History: {', '.join(customer['purchase_history'])}
- Past Complaints: {'; '.join(customer['past_complaints']) if customer['past_complaints'] else 'None'}

CONVERSATION HISTORY:
{history_text}

Return this exact JSON:
{{
  "intent_module": {{
    "classified_intent": "one of: Refund Request|Delivery Issue|Product Complaint|Subscription Cancellation|Technical Issue|General Inquiry",
    "confidence": 0.00,
    "reasoning": "why this intent was chosen"
  }},
  "context_module": {{
    "sentiment": "Frustrated|Neutral|Positive|Angry|Concerned",
    "sentiment_score": 0.00,
    "customer_value_score": {customer['value_score']},
    "issue_severity": "Low|Medium|High|Critical",
    "historical_summary": "1-2 sentence customer history summary relevant to this issue"
  }},
  "decision_module": {{
    "recommendation": "one of: Refund|Replacement|Escalation|Discount|Tracking Update|Self-Service Resolution",
    "reasoning": "why this action fits the customer tier and history",
    "confidence": 0.00,
    "priority": "Standard|High|Urgent"
  }},
  "action_module": {{
    "workflow_name": "workflow name",
    "steps": [
      {{"step": 1, "action": "action", "status": "completed", "detail": "specific detail"}},
      {{"step": 2, "action": "action", "status": "completed", "detail": "specific detail"}},
      {{"step": 3, "action": "action", "status": "completed", "detail": "specific detail"}}
    ],
    "auto_resolved": true
  }},
  "summary_module": {{
    "issue": "one sentence describing the issue",
    "detected_intent": "intent class",
    "agent_reasoning": "2-3 sentence decision logic",
    "actions_performed": ["action 1", "action 2", "action 3"],
    "resolution_status": "Resolved|Escalated|Pending"
  }},
  "response_to_customer": "Personalized reply referencing the customer name and tier, explaining exactly what was done."
}}"""


def run_agent(customer: dict, history: list, user_message: str) -> dict:
    client = get_client()
    system = build_system_prompt(customer, history)
    response = client.messages.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

# ── Helper renderers ─────────────────────────────────────────
def tier_badge(tier: str) -> str:
    return f'<span class="tier-{tier.lower()}">{tier}</span>'


def confidence_bar(value: float, color: str = "#3b82f6") -> str:
    pct = int(value * 100)
    return f"""
    <div class="conf-bar-bg">
      <div class="conf-bar-fill" style="width:{pct}%; background:{color};"></div>
    </div>
    <span class="conf-label">{pct}% confidence</span>"""


def resolution_pill(status: str) -> str:
    cls = {"Resolved": "pill-resolved", "Escalated": "pill-escalated"}.get(status, "pill-pending")
    return f'<span class="resolution-pill {cls}">{status}</span>'


def analytics_chart(analytics: dict) -> go.Figure:
    labels  = ["Auto-Resolved", "Escalated", "Pending"]
    pending = analytics["total"] - analytics["resolved"] - analytics["escalated"]
    values  = [analytics["resolved"], analytics["escalated"], max(0, pending)]
    colors  = ["#34d399", "#fbbf24", "#60a5fa"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.65,
        marker=dict(colors=colors, line=dict(color="#0f1117", width=2)),
        textfont=dict(color="#d1d9f0", size=12),
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=0, l=0, r=0), height=200,
        showlegend=True,
        legend=dict(font=dict(color="#8896b3", size=11), bgcolor="rgba(0,0,0,0)"),
        annotations=[dict(text=f"<b>{analytics['total']}</b><br><span style='font-size:10px'>total</span>",
                          showarrow=False, font=dict(color="#e8f0ff", size=14), x=0.5, y=0.5)],
    )
    return fig


def intent_bar_chart(result: dict) -> go.Figure:
    conf   = result["intent_module"]["confidence"]
    intent = result["intent_module"]["classified_intent"]
    all_intents = ["Refund Request","Delivery Issue","Product Complaint",
                   "Subscription Cancellation","Technical Issue","General Inquiry"]
    vals   = [conf if i == intent else round(max(0.02, (1 - conf) / 5), 2) for i in all_intents]
    colors = ["#3b82f6" if i == intent else "#2a3a5c" for i in all_intents]
    fig = go.Figure(go.Bar(
        x=all_intents, y=vals,
        marker_color=colors,
        text=[f"{int(v*100)}%" for v in vals],
        textposition="outside",
        textfont=dict(color="#8896b3", size=10),
        hovertemplate="%{x}: %{y:.0%}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=0, l=0, r=0), height=180,
        yaxis=dict(visible=False), xaxis=dict(tickfont=dict(color="#8896b3", size=10)),
        showlegend=False,
    )
    return fig

# ════════════════════════════════════════════════════════════
#  LAYOUT
# ════════════════════════════════════════════════════════════

# ── Header ───────────────────────────────────────────────────
a = st.session_state.analytics
rate = f"{int(a['resolved']/a['total']*100)}%" if a["total"] else "—"
st.markdown(f"""
<div class="cx-header">
  <div style="font-size:28px">🤖</div>
  <div style="flex:1">
    <p class="cx-header-title">NextGen CX Agent</p>
    <p class="cx-header-sub">Autonomous · Multi-module · Real-time AI resolution</p>
  </div>
  <div style="display:flex;gap:10px;align-items:center">
    <div style="text-align:center">
      <div style="font-size:20px;font-weight:700;color:#60a5fa">{a['total']}</div>
      <div style="font-size:10px;color:#8896b3">Requests</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:20px;font-weight:700;color:#34d399">{a['resolved']}</div>
      <div style="font-size:10px;color:#8896b3">Resolved</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:20px;font-weight:700;color:#fbbf24">{a['escalated']}</div>
      <div style="font-size:10px;color:#8896b3">Escalated</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:20px;font-weight:700;color:#a78bfa">{rate}</div>
      <div style="font-size:10px;color:#8896b3">Rate</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 3-column layout ──────────────────────────────────────────
col_left, col_mid, col_right = st.columns([1, 2.2, 1.6], gap="medium")

# ════════════ LEFT — Customer panel ══════════════════════════
with col_left:
    st.markdown('<p class="sidebar-section-label">Select Customer</p>', unsafe_allow_html=True)
    for cid, c in CUSTOMERS.items():
        selected = cid == st.session_state.selected_cid
        border   = "#3b82f6" if selected else "#2a3145"
        bg       = "#1e2d4a" if selected else "#1a2035"
        if st.button(
            f"{'● ' if selected else '○ '}{c['name']}  |  {c['tier']}",
            key=f"btn_{cid}",
            use_container_width=True,
        ):
            if cid != st.session_state.selected_cid:
                st.session_state.selected_cid = cid
                st.session_state.messages     = []
                st.session_state.agent_result = None
                st.rerun()

    customer = CUSTOMERS[st.session_state.selected_cid]
    st.markdown('<p class="sidebar-section-label">Customer Profile</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="module-card">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <div style="width:42px;height:42px;border-radius:50%;background:#1e3a6e;
          border:1px solid #3b82f644;display:flex;align-items:center;justify-content:center;
          font-size:14px;font-weight:700;color:#93c5fd;">{customer['avatar']}</div>
        <div>
          <p style="margin:0;font-size:14px;font-weight:600;color:#e8f0ff">{customer['name']}</p>
          <p style="margin:2px 0 0;font-size:11px;color:#8896b3">{customer['email']}</p>
        </div>
      </div>
      <div class="profile-row"><span class="profile-key">Tier</span>{tier_badge(customer['tier'])}</div>
      <div class="profile-row"><span class="profile-key">Value score</span><span class="profile-val">{customer['value_score']}/100</span></div>
      <div class="profile-row"><span class="profile-key">Lifetime value</span><span class="profile-val">${customer['lifetime_value']:,}</span></div>
      <div class="profile-row"><span class="profile-key">Interactions</span><span class="profile-val">{customer['interactions']}</span></div>
      <div class="profile-row"><span class="profile-key">Member since</span><span class="profile-val">{customer['join_date']}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="sidebar-section-label">Purchase History</p>', unsafe_allow_html=True)
    for p in customer["purchase_history"]:
        st.markdown(f'<p style="font-size:12px;color:#8896b3;margin:0 0 5px;padding:4px 8px;background:#161b27;border-radius:6px;border:1px solid #2a3145">📦 {p}</p>', unsafe_allow_html=True)

    if customer["past_complaints"]:
        st.markdown('<p class="sidebar-section-label">Past Complaints</p>', unsafe_allow_html=True)
        for complaint in customer["past_complaints"]:
            st.markdown(f'<p style="font-size:11px;color:#fbbf24;margin:0 0 5px;padding:4px 8px;background:#2d1f0033;border-radius:6px;border:1px solid #fbbf2422">⚠ {complaint}</p>', unsafe_allow_html=True)

    # Analytics chart
    if a["total"] > 0:
        st.markdown('<p class="sidebar-section-label">Resolution Analytics</p>', unsafe_allow_html=True)
        st.plotly_chart(analytics_chart(a), use_container_width=True, config={"displayModeBar": False})

# ════════════ MIDDLE — Chat ═══════════════════════════════════
with col_mid:
    st.markdown(f"""
    <div style="background:#161b27;border:1px solid #2a3145;border-radius:10px;
      padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:12px">
      <div style="width:36px;height:36px;border-radius:50%;background:#1e3a6e;
        border:1px solid #3b82f644;display:flex;align-items:center;justify-content:center;
        font-size:13px;font-weight:700;color:#93c5fd;">{customer['avatar']}</div>
      <div style="flex:1">
        <p style="margin:0;font-size:14px;font-weight:600;color:#e8f0ff">{customer['name']}</p>
        <p style="margin:2px 0 0;font-size:12px;color:#8896b3">Active session · {customer['tier']} tier</p>
      </div>
      <div style="width:8px;height:8px;border-radius:50%;background:#34d399"></div>
    </div>
    """, unsafe_allow_html=True)

    # Messages
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:32px 0;color:#4b6cb7">
          <div style="font-size:40px;margin-bottom:10px">💬</div>
          <p style="font-size:14px;color:#8896b3;margin:0">Start a conversation to activate the agent</p>
          <p style="font-size:12px;color:#4b6cb7;margin:6px 0 0">Try a sample message below</p>
        </div>""", unsafe_allow_html=True)
    else:
        html_parts = ['<div class="chat-container">']
        for msg in st.session_state.messages:
            ts = msg.get("ts", "")
            if msg["role"] == "user":
                html_parts.append(f"""
                <div class="msg-user">
                  <div>
                    <div class="bubble-user">{msg['content']}</div>
                    <p style="font-size:10px;color:#4b6cb7;text-align:right;margin:3px 4px 0">{ts}</p>
                  </div>
                </div>""")
            else:
                status = msg.get("status", "")
                intent = msg.get("intent", "")
                pill   = resolution_pill(status) if status else ""
                html_parts.append(f"""
                <div class="msg-agent">
                  <div class="agent-avatar">🤖</div>
                  <div>
                    <div class="bubble-agent">
                      {msg['content']}
                      {f'<br>{pill}' if pill else ''}
                      {f'<span style="display:inline-block;margin-left:8px;font-size:10px;color:#4b6cb7">{intent}</span>' if intent else ''}
                    </div>
                    <p style="font-size:10px;color:#4b6cb7;margin:3px 4px 0">{ts}</p>
                  </div>
                </div>""")
        html_parts.append("</div>")
        st.markdown("".join(html_parts), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Sample messages
    st.markdown('<p style="font-size:11px;color:#4b6cb7;margin:0 0 6px;text-transform:uppercase;letter-spacing:0.06em;font-weight:700">Quick messages</p>', unsafe_allow_html=True)
    sample_cols = st.columns(2)
    for i, sm in enumerate(SAMPLE_MESSAGES):
        with sample_cols[i % 2]:
            if st.button(f"↗ {sm[:42]}…" if len(sm) > 42 else f"↗ {sm}", key=f"sample_{i}", use_container_width=True):
                st.session_state[f"pending_msg"] = sm
                st.rerun()

    # Chat input
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    input_col, send_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input(
            "message",
            key=f"chat_input_{st.session_state.input_key}",
            placeholder=f"Type as {customer['name']}...",
            label_visibility="collapsed",
        )
    with send_col:
        send_clicked = st.button("Send →", use_container_width=True)

    # Handle pending sample message
    pending = st.session_state.pop("pending_msg", None)
    final_input = pending or (user_input if send_clicked else None)

    if final_input and final_input.strip():
        ts_now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "user", "content": final_input.strip(), "ts": ts_now})

        with st.spinner("🤖 Agent processing…"):
            try:
                result = run_agent(customer, st.session_state.messages[:-1], final_input.strip())
                st.session_state.agent_result = result
                status = result["summary_module"]["resolution_status"]
                intent = result["intent_module"]["classified_intent"]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response_to_customer"],
                    "status": status, "intent": intent, "ts": ts_now,
                })
                a = st.session_state.analytics
                a["total"] += 1
                if status == "Resolved":   a["resolved"]  += 1
                if status == "Escalated":  a["escalated"] += 1
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Agent error: {e}",
                    "ts": ts_now,
                })
        st.session_state.input_key += 1
        st.rerun()

# ════════════ RIGHT — Agent intelligence ══════════════════════
with col_right:
    result = st.session_state.agent_result

    tab1, tab2, tab3 = st.tabs(["🧠 Agent Thoughts", "⚡ Actions", "📋 Summary"])

    with tab1:
        if not result:
            st.markdown('<p style="font-size:13px;color:#4b6cb7;text-align:center;padding:30px 0">Analysis appears here after a message</p>', unsafe_allow_html=True)
        else:
            im  = result["intent_module"]
            ctx = result["context_module"]
            dec = result["decision_module"]

            # Intent
            severity_color = {"Low":"#34d399","Medium":"#60a5fa","High":"#fbbf24","Critical":"#f87171"}.get(ctx["issue_severity"],"#8896b3")
            st.markdown(f"""
            <div class="module-card">
              <p class="module-title">🎯 Intent Analysis</p>
              <p class="module-value">{im['classified_intent']}</p>
              {confidence_bar(im['confidence'])}
              <p class="module-detail" style="margin-top:8px">{im['reasoning']}</p>
            </div>""", unsafe_allow_html=True)

            st.plotly_chart(intent_bar_chart(result), use_container_width=True, config={"displayModeBar": False})

            # Context
            st.markdown(f"""
            <div class="module-card">
              <p class="module-title">🔍 Context Understanding</p>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
                <div style="background:#0f1117;border-radius:6px;padding:8px">
                  <p style="margin:0;font-size:10px;color:#4b6cb7">Sentiment</p>
                  <p style="margin:3px 0 0;font-size:13px;font-weight:600;color:#e8f0ff">{ctx['sentiment']}</p>
                </div>
                <div style="background:#0f1117;border-radius:6px;padding:8px">
                  <p style="margin:0;font-size:10px;color:#4b6cb7">Severity</p>
                  <p style="margin:3px 0 0;font-size:13px;font-weight:600;color:{severity_color}">{ctx['issue_severity']}</p>
                </div>
                <div style="background:#0f1117;border-radius:6px;padding:8px">
                  <p style="margin:0;font-size:10px;color:#4b6cb7">Value Score</p>
                  <p style="margin:3px 0 0;font-size:13px;font-weight:600;color:#e8f0ff">{ctx['customer_value_score']}/100</p>
                </div>
                <div style="background:#0f1117;border-radius:6px;padding:8px">
                  <p style="margin:0;font-size:10px;color:#4b6cb7">Sentiment %</p>
                  <p style="margin:3px 0 0;font-size:13px;font-weight:600;color:#e8f0ff">{int(ctx['sentiment_score']*100)}%</p>
                </div>
              </div>
              <p class="module-detail">{ctx['historical_summary']}</p>
            </div>""", unsafe_allow_html=True)

            # Decision
            priority_color = {"Urgent":"#f87171","High":"#fbbf24","Standard":"#34d399"}.get(dec["priority"],"#8896b3")
            st.markdown(f"""
            <div class="module-card">
              <p class="module-title">⚖️ Decision Engine</p>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <p class="module-value" style="margin:0">{dec['recommendation']}</p>
                <span style="font-size:10px;padding:3px 9px;border-radius:20px;background:{priority_color}22;color:{priority_color};border:1px solid {priority_color}44;font-weight:700">{dec['priority']}</span>
              </div>
              {confidence_bar(dec['confidence'], '#34d399')}
              <p class="module-detail" style="margin-top:8px">{dec['reasoning']}</p>
            </div>""", unsafe_allow_html=True)

    with tab2:
        if not result:
            st.markdown('<p style="font-size:13px;color:#4b6cb7;text-align:center;padding:30px 0">Workflow steps appear after processing</p>', unsafe_allow_html=True)
        else:
            am = result["action_module"]
            auto_label = "Auto-Resolved ✓" if am["auto_resolved"] else "Manual Required"
            auto_color = "#34d399" if am["auto_resolved"] else "#fbbf24"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
              <p style="margin:0;font-size:14px;font-weight:600;color:#e8f0ff">{am['workflow_name']}</p>
              <span style="font-size:11px;padding:3px 10px;border-radius:20px;
                background:{auto_color}22;color:{auto_color};border:1px solid {auto_color}44;font-weight:600">{auto_label}</span>
            </div>""", unsafe_allow_html=True)

            steps_html = ['<div class="module-card">']
            for step in am["steps"]:
                steps_html.append(f"""
                <div class="workflow-step">
                  <div class="step-icon">✓</div>
                  <div>
                    <p class="step-action">Step {step['step']}: {step['action']}</p>
                    <p class="step-detail">{step['detail']}</p>
                  </div>
                </div>""")
            steps_html.append("</div>")
            st.markdown("".join(steps_html), unsafe_allow_html=True)

    with tab3:
        if not result:
            st.markdown('<p style="font-size:13px;color:#4b6cb7;text-align:center;padding:30px 0">Summary generated after processing</p>', unsafe_allow_html=True)
        else:
            sm = result["summary_module"]
            status_color = {"Resolved":"#34d399","Escalated":"#fbbf24","Pending":"#60a5fa"}.get(sm["resolution_status"],"#8896b3")
            actions_html = "".join(f'<div class="action-item"><div class="action-dot"></div>{a}</div>' for a in sm["actions_performed"])
            st.markdown(f"""
            <div class="module-card">
              <div class="summary-item">
                <p class="summary-label">Issue</p>
                <p class="summary-text">{sm['issue']}</p>
              </div>
              <div class="summary-item">
                <p class="summary-label">Detected Intent</p>
                <p class="summary-text">{sm['detected_intent']}</p>
              </div>
              <div class="summary-item">
                <p class="summary-label">Agent Reasoning</p>
                <p class="summary-text">{sm['agent_reasoning']}</p>
              </div>
              <div class="summary-item">
                <p class="summary-label">Actions Performed</p>
                {actions_html}
              </div>
              <div style="margin-top:14px;padding-top:12px;border-top:1px solid #2a3145;
                display:flex;justify-content:space-between;align-items:center">
                <p style="margin:0;font-size:12px;color:#8896b3">Resolution Status</p>
                <span style="font-size:13px;font-weight:700;color:{status_color};
                  background:{status_color}22;padding:4px 12px;border-radius:20px;
                  border:1px solid {status_color}44">{sm['resolution_status']}</span>
              </div>
            </div>""", unsafe_allow_html=True)
