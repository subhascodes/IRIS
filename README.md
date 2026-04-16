# 🌈 IRIS: Insurance Rule Impact Simulation

**Policy Rule Impact Simulation & Audit Governance System with Both Manual and Agent Modes**

---

## What is IRIS?

IRIS simulates how pricing rule changes impact your entire insurance portfolio—across all 5,000+ policies—instantly.

✨ **Core Value**: Answer "What if...?" in **65ms**

```
"What if we charge 20% more for drivers under 25?"

IRIS responds:
├─ Policies affected: 803 (16% of portfolio)
├─ Avg premium change: +$238
├─ Total portfolio impact: +$1.19M
├─ Violations: 3 constraints breached
└─ Decision: ❌ REJECT (exceeds portfolio variance limit)
```

---

## 🎯 Why IRIS?

### Portfolio-Level Visibility
- **Real impact analysis**: See exact financial impact before deployment
- **Segment analysis**: Understand which customer groups are affected
- **Compliance checking**: Automatic violation detection
- **No guesswork**: Data-driven decisions, not spreadsheets

### Autonomous & Auditable
- **Deterministic**: Same input = Same decision (always)
- **Immutable logs**: Every decision logged with full context
- **No human bias**: Policy-based rules, not opinion
- **Regulatory ready**: Full audit trail for compliance

### Conversational AI (NEW)
- **Qwen 7B**: Ask "Why was this rejected?"
- **Chat**: Discuss decision interactively
- **Q&A**: "How many customers over 50?"
- **Local**: No external APIs

---

## ⚡ Quick Start

```bash
# Setup (5 minutes)
git clone <repo> && cd iris
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Ollama + Qwen (one-time)
ollama serve &                  # Terminal 2
ollama pull qwen2:7b

# Run (seconds)
streamlit run app.py
```

Browser: `http://localhost:8501`

---

## 🚀 Usage

### Web UI - Agent Mode (Recommended)

1. **Open Browser** → `http://localhost:8501`
2. **Select Agent Mode** (tab)
3. **Enter Rule Parameters**:
   - Age Threshold: 30
   - Premium Multiplier: 1.5
4. **Click "🚀 Run Agent"**
5. **See Portfolio Impact**:
   ```
   Affected: 450 policies
   Avg Change: +$152
   Total Impact: +$68,535
   Status: ✅ APPROVED
   ```
6. **Chat with Qwen**:
   - "Why was this approved?"
   - "How many customers over 50?"
   - "Can we increase the multiplier?"

### CLI - Use in CI/CD

```bash
python agent.py --task full_pipeline --threshold 30 --multiplier 1.5
```

Output (JSON):
```json
{
  "decision": "APPROVE",
  "affected_policies": 450,
  "avg_change": 152.30,
  "total_impact": 68535.00,
  "violations": 0
}
```

Exit code: `0` (APPROVE) or `1` (REJECT)

### Manual Mode - Full Control

1. Use sliders for parameters
2. Click "Run Simulation"
3. Review charts & metrics
4. Manually approve/reject

---

## 📊 Portfolio Impact Simulation

### What Gets Simulated?

IRIS applies your pricing rule to **5,000 real insurance policies**:

```
Rule: "For customers < 30, multiply premium × 1.5"

For Each Policy:
├─ Load: customer_age, base_premium
├─ Check: is age < 30?
├─ Apply: IF yes → premium × 1.5 ELSE premium × 1.2
├─ Calculate: delta = new - old
└─ Track: affected_count, total_impact, segment_breakdown

Results:
├─ 802 policies affected (age < 30)
├─ Avg impact: +$238.52 per policy
├─ Total portfolio: +$1.19M
├─ Segments:
│  ├─ <25 years: 500 policies, +$300 avg
│  ├─ 25-30: 302 policies, +$150 avg
│  └─ >30: 3,198 policies, unchanged
└─ Financial Risk: 15.2% avg portfolio change
```

### Compliance Constraints

IRIS validates against 5 regulatory guards:

```python
MAX_SINGLE_POLICY_CHANGE = 50%      # No policy >50% premium increase
MAX_PORTFOLIO_CHANGE = 15%          # Overall portfolio <15% avg change
MIN_PORTFOLIO_BREADTH = 10%         # Min 10% policies affected
MAX_VIOLATION_RATE = 5%             # Max 5% policies breaching limits

Decision Algorithm:
IF rule breaks ANY constraint:
    REJECT (show which constraint + how many violations)
ELSE:
    APPROVE (safe to deploy)
```

---

## 🏗️ Architecture

### 5-Step Portfolio Simulation Pipeline

```
┌──────────────┐
│ [1] INGEST   │ Load 5,000 policies
└──────┬───────┘
       ↓
┌──────────────┐
│[2] SIMULATE  │ Apply pricing rule to each policy
└──────┬───────┘
       ↓
┌──────────────┐
│ [3] ANALYZE  │ Calculate impact metrics
└──────┬───────┘
       │ └─ Affected count
       │ └─ Avg premium delta
       │ └─ Total portfolio delta
       │ └─ Segment breakdown
       ↓
┌──────────────┐
│[4] VALIDATE  │ Check compliance constraints
└──────┬───────┘
       │ └─ MAX_SINGLE_POLICY_CHANGE ✓/✗
       │ └─ MAX_PORTFOLIO_CHANGE ✓/✗
       │ └─ MIN_PORTFOLIO_BREADTH ✓/✗
       │ └─ MAX_VIOLATION_RATE ✓/✗
       ↓
┌──────────────┐
│[5] AUDIT     │ Log decision immutably
└──────────────┘
       ↓
   APPROVE or REJECT
   + full reasoning
```

### Key Files

| File | Purpose | Impact |
|------|---------|--------|
| `simulation.py` | Core portfolio simulator | Applies rule to all 5K policies |
| `analysis.py` | Impact calculation | Computes metrics & segments |
| `compliance.py` | Constraint validator | Checks 5 regulatory guards |
| `agent.py` | Orchestrator | Runs full pipeline |
| `app.py` | Web UI | Portfolio visualization |

---

## 💬 Qwen 7B Integration (NEW)

Ask questions about your portfolio impact:

```
User: "Why was this rejected?"
Qwen: "The rule impacted 803 policies (16%), exceeding 
      our 15% portfolio variance limit. This creates 
      unacceptable risk concentration..."

User: "How many customers over age 50?"
Qwen: "1,386 policies (27.7%) have customers over 50."

User: "What if we use multiplier 1.2 instead?"
Qwen: "A lower multiplier (1.2) would reduce affected 
      policies to 400, bringing portfolio change to 9%, 
      which would likely pass compliance..."
```

---

## 📋 Use Cases

### Case 1: Actuarial Planning
```
"I want to charge more for high-risk drivers.
What's the max multiplier that keeps us compliant?"

→ IRIS tests incrementally: 1.2 ✓ 1.3 ✓ 1.4 ✗ 1.5 ✗
→ Result: Max deployable = 1.3x
```

### Case 2: Regulatory Audit
```
"Show us how rule XYZ affects the portfolio"

→ Pull from audit log: timestamp, parameters, impact, decision
→ Full compliance validation shown
→ Auditor satisfied ✓
```

### Case 3: Risk Management
```
"Monitor our portfolio risk exposure daily"

→ Run IRIS nightly via CI/CD
→ Evaluate 500 candidate rules
→ Alert if any exceed portfolio variance
```

### Case 4: What-If Analysis
```
"How would a 20% increase for <30 year olds impact us?"

→ Simulate in 65ms
→ See: 803 policies, +$1.19M total, 3 constraints violated
→ Decide: Not deployable
```

---

## 🚢 Deployment

### Docker
```bash
docker build -t iris . && docker run -p 8501:8501 iris
```

### CI/CD (GitHub Actions)
```yaml
- name: Evaluate Pricing Rule
  run: |
    python agent.py --task full_pipeline \
      --threshold 30 --multiplier 1.5
```

Exit code: `0` (APPROVE → deploy) or `1` (REJECT → stop)

### Production (Systemd)
```bash
sudo systemctl enable iris && sudo systemctl start iris
```

---

## 📊 Example Output

```
RULE: "Multiply premium by 1.85 for customers < 25"

PORTFOLIO SIMULATION RESULTS:
├─ Total Policies: 5,000
├─ Affected: 803 (16.06%)
├─ Avg Premium Δ: +$238.52
├─ Total Portfolio Δ: +$1,192,613.30
│
├─ SEGMENT BREAKDOWN:
│  ├─ <25 years: 803 affected, +$500 avg
│  ├─ 25-40: 0 affected
│  └─ >40: 0 affected
│
├─ COMPLIANCE CHECK:
│  ├─ MAX_SINGLE_POLICY (50%): ✗ 803 violations
│  ├─ MAX_PORTFOLIO (15%): ✗ 15.2% change
│  ├─ MIN_BREADTH (10%): ✓ 16.06% affected
│  └─ MAX_VIOLATION_RATE (5%): ✗ 16% violation rate
│
└─ DECISION: ❌ REJECT
   Reason: 3 constraints violated
   
QWEN EXPLANATION:
"The rule was rejected because 803 policies would experience  
premium increases exceeding 50%, violating our portfolio 
risk controls..."
```

---

## 🔍 FAQ

**Q: How fast is "65ms"?**
A: Full pipeline (load, simulate, analyze, validate, log) on 5,000 policies

**Q: Can I use it in production?**
A: Yes - deterministic, auditable, with immutable logs

**Q: Does it need internet?**
A: No - Qwen runs locally on your machine via Ollama

**Q: What if a rule fails compliance?**
A: IRIS shows exactly which constraints were violated and why

**Q: Can I batch test rules?**
A: Yes - CLI mode supports scripting for batch evaluation

---

## 🛠️ Development

```bash
# Run tests
python -m pytest test_agent.py

# Check code
python -m pylint *.py

# Format
python -m black *.py
```

---

## 📚 Learn More

- **Full Technical Docs**: See `PROJECT.md`
- **Architecture Deep-Dive**: `.github/copilot-instructions.md`
- **API Reference**: `PROJECT.md` → API Reference section

---

## 👥 Users

- **Pricing Actuaries**: Quick what-if analysis
- **Compliance Officers**: Audit trail + constraint validation
- **Risk Managers**: Portfolio exposure monitoring
- **Data Scientists**: Batch optimization
- **DevOps**: CI/CD pipeline integration

---

## 📄 License

Proprietary — IRIS Insurance Platform

---

**Status**: ✅ Production Ready  
**Last Updated**: April 16, 2026
