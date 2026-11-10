import json
import os
import urllib.error
import urllib.request


class GroqRoaster:
    MODES = {
        "nuclear": (
            "You are a brutally sarcastic, chronically exhausted senior engineer "
            "reviewing a chaotic git history. Mock vague commit messages like 'fixed bug' "
            "or 'oops', treat every messy commit like an existential crisis, "
            "and roast the developer like an absolute chaotic gremlin."
        ),
        "passive-aggressive": (
            "You are a disappointed senior tech lead leaving subtle, deeply "
            "passive-aggressive code review comments on a disastrous commit history."
        ),
        "shakespearean": (
            "You are William Shakespeare witnessing a catastrophic git repository. "
            "Narrate the downfall of the developers in dramatic, poetic early modern English iambic pentameter."
        ),
        "corporate": (
            "You are a detached corporate executive translating catastrophic code failures into "
            "synergistic buzzwords, actionable learnings, and passive layoffs."
        ),
        "noir": (
            "You are a cynical 1940s private detective investigating a crime scene made of terrible commits. "
            "Rain is pouring, coffee is stale, and every commit message is a dirty secret."
        )
    }

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        # Fallback: parse .env if present in current or parent directory
        if not self.api_key and os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == "GROQ_API_KEY":
                                self.api_key = v.strip().strip("'\"")
                                os.environ["GROQ_API_KEY"] = self.api_key
                                break
            except Exception:
                pass
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def roast(self, commit_data, mode="nuclear"):
        if not self.api_key:
            return "❌ Error: GROQ_API_KEY environment variable is missing. Set it in your terminal or in a .env file."

        system_prompt = self.MODES.get(mode, self.MODES["nuclear"])

        history_text = "\n".join([
            f"- [{c['hash']}] {c['author']}: '{c['message']}' ({c['stats']})"
            for c in commit_data
        ])

        candidate_models = []
        custom_model = os.getenv("GROQ_MODEL")
        if custom_model:
            candidate_models.append(custom_model.strip())
        candidate_models.extend([
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ])

        # Deduplicate while preserving order
        unique_models = []
        for m in candidate_models:
            if m not in unique_models:
                unique_models.append(m)

        last_error = None

        for model_id in unique_models:
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Here is the raw git log. Tell me the tragic story of how this code got ruined:\n\n{history_text}"
                    }
                ],
                "temperature": 0.85,
                "max_tokens": 800
            }

            req = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": "Git-Trace-Storyteller/1.0"
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    return result["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8", errors="replace")
                detail = error_body or str(e.reason)
                # If model is not found / deprecated, fall back to next model candidate
                if e.code == 404 or "model_not_found" in detail or "decommissioned" in detail:
                    print(f"DEBUG: Model '{model_id}' unavailable ({detail}). Trying next candidate...")
                    last_error = f"HTTP {e.code}: {detail}"
                    continue
                else:
                    print(f"DEBUG API ERROR: HTTP {e.code}: {detail}")
                    return f"❌ Groq API request failed: HTTP {e.code}: {detail}"
            except Exception as e:
                print(f"DEBUG API ERROR: {e}")
                return f"❌ Groq API request failed: {e}"

        return f"❌ Groq API request failed: All candidate models failed. Last error: {last_error}"
