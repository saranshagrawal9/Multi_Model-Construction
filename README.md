# Multimodal Construction Intelligence Platform
**Skill Wallet Capstone Project 1**

A modular Streamlit app covering image-based PPE/safety review, preliminary crack triage, construction planning estimates, conceptual rendering prompts, and weather-aware site assistance.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud
1. Push `app.py` and `requirements.txt` to a GitHub repository.
2. Create a Streamlit Community Cloud app using `app.py` as the entry point.
3. Optionally configure `GEMINI_API_KEY` in app secrets or enter a key in the sidebar.

For environment-based key use, add this to the sidebar initialization before the text input:
```python
api_key = st.text_input(
    "Google Gemini API key",
    type="password",
    value=st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")),
)
```
The app currently supports entering the key directly in the sidebar. Keys are not written to disk or a database; session/UI handling is subject to Streamlit's session behavior.

## Modules
- **Site Safety & PPE Audit:** Gemini image prompt, structured JSON, PPE checklist, hazard severity/remedies, downloadable report. Demo fallback.
- **Crack Diagnostics:** defect class, estimated width (nullable), causes, potential repairs, urgency, JSON report. Demo fallback.
- **Planning & Real Estate:** adjustable planning assumptions, budget/CapEx/asset estimate, material rule-of-thumb indicators, progress, Pollinations prompt link.
- **Daily Site Assistant:** condition-specific advisories and session-persistent multi-turn Gemini chat (demo response without key).

## Important limitations
- Not a code-compliance engine. OSHA/IS references are contextual, and IS 456 is not a PPE checklist.
- Image inference cannot reliably determine hidden PPE, crack depth, load paths, or structural adequacy.
- Budget, market valuation, steel, and cement figures are heuristic estimates, not a BOQ, appraisal, or design.
- Obtain review by competent safety personnel and licensed/qualified engineers. Check applicable current standards and local requirements.
