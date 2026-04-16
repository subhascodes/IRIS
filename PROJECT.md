# 🌈 IRIS: Insurance Rule Impact Simulation System

**Portfolio-Level Impact Simulation & Autonomous Pricing Rule Governance**

---

## 🎯 What is IRIS?

**IRIS** (**Insurance Rule Impact Simulation** System) is an autonomous platform that simulates how pricing rules affect your entire insurance portfolio at scale, evaluates compliance automatically, and makes deterministic deployment decisions.

Think of it as a **"what-if simulator"** that answers: *"If I change pricing rules for customers under 30 to cost 1.85x, how will it impact my portfolio? Will it violate regulations? Should I deploy?"*

IRIS answers this in **~65ms** with full audit trail.

---

## ✨ Key Features

### 🔍 **Portfolio-Level Impact Simulation**
- Apply pricing rules to **5,000+ policies** instantly
- See exact impact on:
  - Number of affected customers
  - Average premium changes ($)
  - Total portfolio financial impact ($)  
  - Customer segments broken by age/demographics
- **Segment Analysis**: Understand policy-by-policy impact before deployment

### 🤖 **Autonomous Decision Making**
- Agent automatically evaluates rules against **5 regulatory constraints**
- Makes APPROVE/REJECT decisions based on policy (not opinion)
- **Deterministic**: Same rule params → Always same decision
- **Auditable**: Every decision logged immutably

### 💬 **Interactive Explanation (NEW)**
- **Qwen 7B Integration**: Ask why a rule was rejected
- **Natural Language Q&A**: "How many customers over 50?" → Instant answer
- **Chat Interface**: Discuss decision with AI in browser
- **No External APIs**: Runs locally on your machine

### 📊 **Data-Driven Analysis**
- Automatic compliance violation detection
- Impact metrics: affected policies, avg change, total delta
- Segment breakdown: understand impact by age band
- Risk exposure analysis

### 🔐 **Enterprise-Grade Governance**
- Immutable audit logs (append-only CSV)
- Role-based access control
- Pre-execution security hooks
- Compliance constraint enforcement

### 🚀 **Two Modes**
- **Manual Mode**: Traditional UI - full user control
- **Agent Mode**: Autonomous - runs without intervention (CI/CD ready)

---

## 🎬 Use Cases

### Use Case 1: Quick Rule Testing ⚡
Scenario: "What if we charge 20% more for drivers under 25?"
IRIS Response in 65ms: 803 policies affected (16%), REJECTED (exceeds portfolio limit)

### Use Case 2: Nightly Compliance Review 🌙
Batch evaluate 500 candidates overnight with full audit trail

### Use Case 3: Regulatory Audit Support 📋
Show auditors full decision history with parameters, impact, and compliance checks

### Use Case 4: What-If Analysis 🔮
Compare different multipliers and find optimal deployable rule

### Use Case 5: Portfolio Optimization 💰
Find maximum multiplier that passes all constraints

---

## 👥 Who Uses IRIS?

- **Pricing Actuaries**: Quick impact analysis, compliance pre-check
- **Compliance Officers**: Verify constraints, immutable audit trail  
- **Risk Managers**: Monitor portfolio exposure, track violations
- **Data Scientists**: API integration, batch evaluation, optimization
- **DevOps/SRE**: CI/CD pipeline deployment, automated gates

---

## 🏗️ Architecture

### 5-Step Pipeline

[1] Data Ingest → [2] Simulation → [3] Analysis → [4] Compliance → [5] Audit

### Core Components

| Component | Purpose |
|-----------|---------|
| Agent Orchestrator (`agent.py`) | Coordinates pipeline |
| Simulation Engine (`simulation.py`) | Portfolio rule simulator |
| Analysis Engine (`analysis.py`) | Impact metrics |
| Compliance Validator (`compliance.py`) | Constraint checks |
| Decision Engine (`decision.py`) | APPROVE/REJECT |
| Audit Logger (`audit.py`) | Immutable trail |
| Qwen Wrapper (`ollama_client.py`) | LLM explanations |
| Streamlit UI (`app.py`) | Web interface |

---

## 💻 Installation & Setup

```bash
# 1. Setup
git clone <repo> && cd iris
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Ollama + Qwen
ollama serve &
ollama pull qwen2:7b

# 3. Run
streamlit run app.py
```

---

## 🚀 Usage

### Agent Mode CLI
```bash
python agent.py --task full_pipeline --threshold 30 --multiplier 1.5
```

### Web UI
- Open browser → "Agent Mode"
- Enter threshold & multiplier  
- Click "🚀 Run Agent"
- See Qwen explanation + chat

---

**Last Updated**: April 16, 2026 | **Status**: ✅ Production Ready
