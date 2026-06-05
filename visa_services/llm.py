import os
import requests
import json

# LM Studio Configuration
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", "lm-studio")
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")

# Fallback to Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("MODEL_NAME", os.getenv("OLLAMA_MODEL", "llama2"))


def llm_explain(context, retrieved):
    """Generate AI explanation using LM Studio or Ollama"""
    if not isinstance(context, dict):
        context = {}
    if not isinstance(retrieved, list):
        retrieved = []

    failed_rules = context.get("rule_results", {}).get("failed_rules", [])
    
    # Build context from retrieved documents
    context_text = ""
    if retrieved:
        context_text = "\n\n".join([
            f"Policy: {doc.get('metadata', {}).get('title', 'Unknown')}\n{doc.get('text', '')}"
            for doc in retrieved[:3]  # Use top 3 results
        ])
    
    # Build the prompt
    rules_list = ", ".join(failed_rules) if failed_rules else "No specific rules"
    
    prompt = f"""Based on UK visa policy, provide a concise explanation for why the applicant is ineligible. 
    
Failed Rules: {rules_list}

Policy Context:
{context_text if context_text else "No policy context available"}

Provide a brief, professional explanation (2-3 sentences) for the ineligibility decision."""

    per_rule = []
    decision = ""
    
    # Try LM Studio first
    try:
        response = requests.post(
            f"{LM_STUDIO_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LM_STUDIO_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LM_STUDIO_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a UK visa policy expert providing concise eligibility assessments."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            decision = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        else:
            decision = f"LM Studio error: {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        # Fallback to Ollama
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                decision = result.get("response", "").strip()
            else:
                decision = "Unable to generate explanation - LLM service unavailable."
        
        except Exception as e:
            decision = f"Unable to generate explanation - LLM services not available. Error: {str(e)}"
    
    except requests.exceptions.Timeout:
        decision = "Unable to generate explanation - LLM service timeout. Please try again."
    except Exception as e:
        decision = f"Unable to generate explanation: {str(e)}"
    
    # Generate per-rule explanations
    for rule in failed_rules:
        per_rule.append({
            "rule": rule,
            "explanation": f"The rule {rule} failed based on the information provided."
        })

    return {
        "decision": decision,
        "per_rule": per_rule,
        "retrieved": retrieved
    }
