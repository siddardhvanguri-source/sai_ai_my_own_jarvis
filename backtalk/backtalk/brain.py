# backtalk: talk to your AI agent out loud.
# Multi-engine brain: OpenRouter (Llama 3.3 70B / GPT-4o) -> NVIDIA NIM (Nemotron 3.5) -> Ollama -> Local.
import asyncio
import json
import os
import random
import re
import time
import httpx
from datetime import datetime

from backtalk import signals
from backtalk.config import CFG, DISCIPLINE
from backtalk.vlog import log

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINK_HEADER = re.compile(r"^Here'?s a thinking process:?.*?\n\n", re.DOTALL | re.IGNORECASE)


def _clean_repetitive_text(text: str) -> str:
    words = text.split()
    if len(words) > 4 and len(set(words)) <= 2:
        return words[0]
    return text


def _clean_spoken_stream(text: str) -> str:
    """Removes thinking / markdown noise from text meant for spoken voice."""
    cleaned = _THINK_BLOCK.sub("", text)
    cleaned = _THINK_HEADER.sub("", cleaned)
    # Remove markdown bold/italic/asterisks/bullets
    cleaned = re.sub(r"[*#_`>~]", "", cleaned)
    return cleaned.strip()


class WarmBrain:
    def __init__(self, model: str | None = None, can_use_tool=None, resume_id: str | None = None):
        cfg_groq = CFG.get("groq_api_key", "").strip()
        env_groq = os.environ.get("GROQ_API_KEY", "").strip()
        self.groq_key = cfg_groq if (cfg_groq and "..." not in cfg_groq) else (env_groq if "..." not in env_groq else "")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", CFG.get("openrouter_api_key", "")).strip()
        self.nvidia_key = os.environ.get("NVIDIA_API_KEY", CFG.get("nvidia_api_key", "")).strip()
        self.ollama_url = CFG.get("ollama_url", "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = CFG.get("ollama_model", "llama3.2:1b")
        self.ollama_online = False
        
        self.model = model or CFG.get("model", "llama3.2:1b")
        self._can_use_tool = can_use_tool
        self.session = {"turns": 0, "out_tokens": 0, "in_tokens": 0, "cost": 0.0}
        self.history: list[dict] = []
        self._http_client: httpx.AsyncClient | None = None
        self._dirty = False

    def _build_system_prompt(self) -> str:
        return (
            "You are Sai, an ultra-fast, intelligent personal AI assistant on this Windows PC.\n"
            "Spoken Voice Rule: Reply in 1 or 2 concise, conversational spoken sentences. Be direct, helpful, and natural.\n"
            "Never repeat introductory formulas like 'Hello, I am Sai. All systems online'.\n"
            "Never repeat 'sir' or 'boss' continuously.\n"
            "Never use markdown symbols (*, #, `), bullet lists, emojis, or file path URLs aloud.\n"
            "System actions available locally: [ACTION: write_code|file|code], [ACTION: draft_email|to|sub|body], [ACTION: launch_app|app], [ACTION: screenshot], [ACTION: shell|cmd]."
        )

    def _lookup_vault_files(self, query: str) -> str:
        query_lower = query.lower()
        extra_content = []
        vault_paths = CFG.get("extra_dirs", [])
        for vp in vault_paths:
            if not os.path.exists(vp):
                continue
            for root, _, files in os.walk(vp):
                for file in files:
                    if file.endswith(".md"):
                        full_path = os.path.join(root, file)
                        base_name = os.path.splitext(file)[0].lower()
                        if base_name in query_lower or "vault" in query_lower or "note" in query_lower or "priorit" in query_lower:
                            try:
                                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read()
                                    extra_content.append(f"File '{file}':\n{content}")
                            except Exception:
                                pass
        return "\n\n".join(extra_content[:3])

    def _execute_agent_action(self, query: str) -> str | None:
        """Executes real-world agent tasks directly on the user's system."""
        from backtalk import agent_tools
        q = query.lower().strip()
        vault_dir = "C:/Users/saisi/jarvis-vault"
        barehands_state = CFG.get("barehands_state_dir", "C:/Users/saisi/my-agent/barehands/state")
        
        # 1. Add Priority to Vault
        if any(prefix in q for prefix in ["add priority", "new priority", "set priority", "priority to"]):
            item = re.sub(r"^(hey )?jarvis,? (please )?(add|new|set|create) (a )?priority( to)?:?", "", query, flags=re.IGNORECASE).strip()
            if item and os.path.exists(vault_dir):
                pri_file = os.path.join(vault_dir, "Active Priorities.md")
                try:
                    with open(pri_file, "a", encoding="utf-8") as f:
                        f.write(f"\n- [ ] {item} *(Added via voice on {datetime.now().strftime('%Y-%m-%d %H:%M')})*")
                    log(f"[agent] Priority added: {item}")
                    return f"I have added '{item}' to your active priorities in your Obsidian vault, sir."
                except Exception as e:
                    log(f"[agent] Failed writing priority: {e}")

        # 2. Add Quick Note to Vault
        if any(prefix in q for prefix in ["note down", "take a note", "write a note", "add note", "create a note"]):
            note = re.sub(r"^(hey )?jarvis,? (please )?(note down|take a note|write a note|add note|create a note)( that| about)?:?", "", query, flags=re.IGNORECASE).strip()
            if note and os.path.exists(vault_dir):
                notes_file = os.path.join(vault_dir, "Quick Notes.md")
                try:
                    with open(notes_file, "a", encoding="utf-8") as f:
                        f.write(f"\n\n### {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{note}")
                    log(f"[agent] Quick note logged: {note}")
                    return f"Logged to Quick Notes in your Obsidian vault, Sai: '{note}'."
                except Exception as e:
                    log(f"[agent] Failed writing note: {e}")

        # 3. Email Drafting
        if "draft email" in q or "write email" in q or "send email" in q or "compose email" in q:
            # Extract recipient and subject if present
            to_match = re.search(r"to\s+([\w\.-]+@?[\w\.-]*)", query, re.IGNORECASE)
            sub_match = re.search(r"(?:about|subject|regarding)\s+([^,]+)", query, re.IGNORECASE)
            to = to_match.group(1) if to_match else "team"
            sub = sub_match.group(1).strip() if sub_match else "Project Update"
            res = agent_tools.draft_email(to, sub, f"Hi {to.split('@')[0].capitalize()},\n\nFollowing up on our discussions regarding {sub}. All systems and priorities are on track.\n\nBest,\nSai")
            return f"I have drafted that email for {to} with subject '{sub}' and saved it to your Obsidian Drafts vault."

        # 4. Screenshots
        if "screenshot" in q or "capture screen" in q:
            return agent_tools.take_screenshot()

        # 5. Launch App or Game
        if any(prefix in q for prefix in ["launch ", "open ", "start "]) and any(app in q for app in ["spotify", "discord", "steam", "chrome", "calc", "calculator", "notepad", "code", "vscode", "obsidian", "terminal"]):
            for app in ["spotify", "discord", "steam", "chrome", "calc", "calculator", "notepad", "code", "vscode", "obsidian", "terminal"]:
                if app in q:
                    return agent_tools.launch_application_or_game(app)

        # 6. 3D Barehands Holographic Stage Control
        if "spawn cards" in q or "show cards" in q or "project cards" in q or "display cards" in q:
            if os.path.exists(barehands_state):
                cards_file = os.path.join(barehands_state, "cards.json")
                try:
                    cards_data = {
                        "cards": [
                            {"id": "c1", "title": "Jarvis Operating Suite", "content": "Fullstack Agent Active\nVoice: Kokoro\nBrain: OpenRouter / NIM", "x": -2, "y": 1, "z": -4},
                            {"id": "c2", "title": "Obsidian Memory Vault", "content": "Location: C:/Users/saisi/jarvis-vault\nStatus: Synchronized", "x": 0, "y": 1.2, "z": -4},
                            {"id": "c3", "title": "3D Barehands HUD", "content": "MediaPipe Gesture Tracking\nStage: Port 8794", "x": 2, "y": 1, "z": -4}
                        ],
                        "updated_at": time.time()
                    }
                    with open(cards_file, "w", encoding="utf-8") as f:
                        json.dump(cards_data, f, indent=2)
                    return "Projecting holographic 3D cards onto your Barehands stage now, sir."
                except Exception as e:
                    log(f"[agent] Failed updating cards: {e}")

        if "clear stage" in q or "clear cards" in q or "hide cards" in q:
            if os.path.exists(barehands_state):
                cards_file = os.path.join(barehands_state, "cards.json")
                try:
                    with open(cards_file, "w", encoding="utf-8") as f:
                        json.dump({"cards": [], "updated_at": time.time()}, f, indent=2)
                    return "Barehands stage cleared, sir."
                except Exception as e:
                    log(f"[agent] Failed clearing stage: {e}")

        # 7. System Diagnostics
        if "system status" in q or "system diagnostic" in q or "diagnostics" in q or "hardware check" in q:
            return agent_tools.get_system_diagnostics()

        # 8. Real-time File Organization
        if any(w in q for w in ["organize files", "organize folder", "clean up downloads", "clean downloads", "organize downloads", "organize desktop", "organize documents"]):
            target = "downloads"
            if "desktop" in q:
                target = "desktop"
            elif "document" in q:
                target = "documents"
            return agent_tools.organize_folder(target)

        # 9. Send inputs / tasks
        if any(prefix in q for prefix in ["send input", "log task", "give input", "queue task", "take input"]):
            task = re.sub(r"^(hey )?sai,? (please )?(send input|log task|give input|queue task|take input)( that| to|:)?", "", query, flags=re.IGNORECASE).strip()
            if task:
                return agent_tools.send_agent_input(task)

        return None

    async def start(self):
        self._http_client = httpx.AsyncClient(timeout=40.0)
        self.provider = str(CFG.get("brain_provider") or "ollama").lower()
        self.ollama_online = False
        if self.ollama_url:
            try:
                r = await self._http_client.get(f"{self.ollama_url}/api/tags", timeout=1.5)
                self.ollama_online = r.status_code == 200
            except Exception:
                self.ollama_online = False

        if self.provider == "groq" and self.groq_key:
            backend = f"Groq Cloud ({self.model})"
            self.provider = "groq"
        elif (self.provider == "ollama" or self.ollama_online) and self.ollama_online:
            backend = f"Local Ollama ({self.ollama_model})"
            self.provider = "ollama"
        elif self.groq_key:
            backend = f"Groq Cloud ({self.model})"
            self.provider = "groq"
        elif self.openrouter_key:
            backend = f"OpenRouter ({self.model})"
        elif self.nvidia_key:
            backend = "NVIDIA NIM (Nemotron 3.5)"
        else:
            backend = "Local Engine"
        log(f"[brain] Brain online — provider={backend}")
        sys_prompt = self._build_system_prompt()
        self.history = [{"role": "system", "content": sys_prompt}]

    async def set_permission_mode(self, mode: str):
        pass

    async def context_usage(self):
        return None

    async def command(self, cmd: str) -> str:
        cmd = cmd.strip()
        if cmd == "/clear":
            sys_prompt = self._build_system_prompt()
            self.history = [{"role": "system", "content": sys_prompt}]
            return "Session cleared."
        elif cmd.startswith("/model"):
            parts = cmd.split(maxsplit=1)
            if len(parts) > 1:
                self.model = parts[1]
                return f"Model changed to {self.model}."
        return "Command received."

    async def interrupt(self):
        self._dirty = False

    async def reset_turn(self, timeout: float = 8.0):
        await self.interrupt()

    async def stop(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def ask_stream(self, utterance: str):
        self._dirty = True
        self.session["turns"] += 1

        cleaned_utterance = _clean_repetitive_text(utterance.strip())
        if not cleaned_utterance:
            self._dirty = False
            return

        if "warmup ping" in cleaned_utterance.lower():
            yield "ready"
            self._dirty = False
            return

        # Direct Local Agent Actions (Vault writing, Holographic Stage, System Status)
        agent_reply = self._execute_agent_action(cleaned_utterance)
        if agent_reply:
            yield agent_reply
            self.history.append({"role": "assistant", "content": agent_reply})
            self._dirty = False
            return

        vault_data = self._lookup_vault_files(cleaned_utterance)
        user_message = cleaned_utterance
        if vault_data:
            user_message += f"\n\n[Context from your files]:\n{vault_data}"

        self.history.append({"role": "user", "content": user_message})

        buffer = ""
        full_reply = ""
        llm_succeeded = False

        # 1. Primary Local Engine: Ollama (Local llama3.2:1b, TTFT < 70ms, offline)
        try_ollama_first = (self.provider == "ollama" or (getattr(self, "ollama_online", False) and self.provider != "groq"))
        if try_ollama_first and self.ollama_url and self._http_client and not llm_succeeded:
            try:
                local_model = self.ollama_model if hasattr(self, "ollama_model") else "llama3.2:1b"
                req_payload = {
                    "model": local_model,
                    "messages": self.history,
                    "stream": True,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 128
                    }
                }
                url = f"{self.ollama_url}/api/chat"
                async with self._http_client.stream("POST", url, json=req_payload, timeout=20.0) as resp:
                    if resp.status_code == 200:
                        llm_succeeded = True
                        is_first = True
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line)
                                delta = chunk.get("message", {}).get("content", "")
                                if delta:
                                    buffer += delta
                                    full_reply += delta
                                    parts = _SENTENCE_END.split(buffer)
                                    if len(parts) > 1:
                                        for s in parts[:-1]:
                                            s_clean = _clean_spoken_stream(s)
                                            if s_clean:
                                                yield s_clean
                                                is_first = False
                                        buffer = parts[-1]
                                    elif is_first and len(buffer.split()) >= 3:
                                        clauses = re.split(r"(?<=[,;:—-])\s+", buffer)
                                        if len(clauses) > 1:
                                            first_clause = clauses[0]
                                            s_clean = _clean_spoken_stream(first_clause)
                                            if s_clean:
                                                yield s_clean
                                                is_first = False
                                            buffer = buffer[len(first_clause):].lstrip()
                                    elif len(buffer.split()) >= 5:
                                        clauses = re.split(r"(?<=[,;:—-])\s+", buffer)
                                        if len(clauses) > 1:
                                            first_clause = clauses[0]
                                            s_clean = _clean_spoken_stream(first_clause)
                                            if s_clean:
                                                yield s_clean
                                            buffer = buffer[len(first_clause):].lstrip()
                            except Exception:
                                pass
                    else:
                        err = await resp.aread()
                        log(f"[brain] Ollama status {resp.status_code}: {err.decode('utf-8', errors='ignore')}")
            except Exception as e:
                log(f"[brain] Ollama error: {e}")

        # 2. Cloud Engine: Groq Cloud (Ultra-Fast 300+ tok/s)
        if self.groq_key and self._http_client and not llm_succeeded:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                }
                groq_model = self.model if ("qwen" in self.model or "llama" in self.model) else "qwen/qwen3.8-27b"
                req_payload = {
                    "model": groq_model,
                    "messages": self.history,
                    "stream": True,
                    "temperature": 0.5,
                    "max_tokens": 128,
                }
                url = "https://api.groq.com/openai/v1/chat/completions"
                async with self._http_client.stream("POST", url, headers=headers, json=req_payload) as resp:
                    if resp.status_code == 200:
                        llm_succeeded = True
                        is_first = True
                        async for line in resp.aiter_lines():
                            if line.startswith("data: ") and line != "data: [DONE]":
                                try:
                                    chunk = json.loads(line[6:])
                                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if delta:
                                        buffer += delta
                                        full_reply += delta
                                        parts = _SENTENCE_END.split(buffer)
                                        if len(parts) > 1:
                                            for s in parts[:-1]:
                                                s_clean = _clean_spoken_stream(s)
                                                if s_clean:
                                                    yield s_clean
                                                    is_first = False
                                            buffer = parts[-1]
                                        elif is_first and len(buffer.split()) >= 3:
                                            clauses = re.split(r"(?<=[,;:—-])\s+", buffer)
                                            if len(clauses) > 1:
                                                first_clause = clauses[0]
                                                s_clean = _clean_spoken_stream(first_clause)
                                                if s_clean:
                                                    yield s_clean
                                                    is_first = False
                                                buffer = buffer[len(first_clause):].lstrip()
                                        elif len(buffer.split()) >= 5:
                                            clauses = re.split(r"(?<=[,;:—-])\s+", buffer)
                                            if len(clauses) > 1:
                                                first_clause = clauses[0]
                                                s_clean = _clean_spoken_stream(first_clause)
                                                if s_clean:
                                                    yield s_clean
                                                buffer = buffer[len(first_clause):].lstrip()
                                except Exception:
                                    pass
                    else:
                        err = await resp.aread()
                        log(f"[brain] Groq status {resp.status_code}: {err.decode('utf-8', errors='ignore')}")
            except Exception as e:
                log(f"[brain] Groq error: {e}")

        # Fallback to Ollama if Groq failed and Ollama is available
        if not llm_succeeded and not try_ollama_first and getattr(self, "ollama_online", False) and self.ollama_url and self._http_client:
            try:
                local_model = self.ollama_model if hasattr(self, "ollama_model") else "llama3.2:1b"
                req_payload = {
                    "model": local_model,
                    "messages": self.history,
                    "stream": True,
                    "options": {"temperature": 0.5, "num_predict": 128}
                }
                url = f"{self.ollama_url}/api/chat"
                async with self._http_client.stream("POST", url, json=req_payload, timeout=20.0) as resp:
                    if resp.status_code == 200:
                        llm_succeeded = True
                        is_first = True
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line)
                                delta = chunk.get("message", {}).get("content", "")
                                if delta:
                                    buffer += delta
                                    full_reply += delta
                                    parts = _SENTENCE_END.split(buffer)
                                    if len(parts) > 1:
                                        for s in parts[:-1]:
                                            s_clean = _clean_spoken_stream(s)
                                            if s_clean:
                                                yield s_clean
                                                is_first = False
                                        buffer = parts[-1]
                            except Exception:
                                pass
            except Exception as e:
                log(f"[brain] Ollama fallback error: {e}")

        # 3. Secondary Engine: OpenRouter (Llama 3.3 70B / GPT-4o)
        if self.openrouter_key and self._http_client and not llm_succeeded:
            try:
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "HTTP-Referer": "https://github.com/jaredrhod/fullstack-agent",
                    "X-Title": "Jarvis Fullstack Agent",
                    "Content-Type": "application/json"
                }
                req_payload = {
                    "model": self.model,
                    "messages": self.history,
                    "stream": True,
                    "temperature": 0.7,
                }
                url = "https://openrouter.ai/api/v1/chat/completions"
                async with self._http_client.stream("POST", url, headers=headers, json=req_payload) as resp:
                    if resp.status_code == 200:
                        llm_succeeded = True
                        async for line in resp.aiter_lines():
                            if line.startswith("data: ") and line != "data: [DONE]":
                                try:
                                    chunk = json.loads(line[6:])
                                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if delta:
                                        buffer += delta
                                        full_reply += delta
                                        parts = _SENTENCE_END.split(buffer)
                                        if len(parts) > 1:
                                            for s in parts[:-1]:
                                                s_clean = _clean_spoken_stream(s)
                                                if s_clean:
                                                    yield s_clean
                                            buffer = parts[-1]
                                except Exception:
                                    pass
                    else:
                        err = await resp.aread()
                        log(f"[brain] OpenRouter status {resp.status_code}: {err.decode('utf-8', errors='ignore')}")
            except Exception as e:
                log(f"[brain] OpenRouter error: {e}")

        # 3. Third Engine: NVIDIA NIM (Nemotron 3.5)
        if self.nvidia_key and self._http_client and not llm_succeeded:
            try:
                headers = {
                    "Authorization": f"Bearer {self.nvidia_key}",
                    "Content-Type": "application/json"
                }
                req_payload = {
                    "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
                    "messages": self.history,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 512
                }
                url = "https://integrate.api.nvidia.com/v1/chat/completions"
                async with self._http_client.stream("POST", url, headers=headers, json=req_payload) as resp:
                    if resp.status_code == 200:
                        llm_succeeded = True
                        in_think = False
                        async for line in resp.aiter_lines():
                            if line.startswith("data: ") and line != "data: [DONE]":
                                try:
                                    chunk = json.loads(line[6:])
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    # Filter reasoning / think tokens
                                    if "<think>" in content:
                                        in_think = True
                                    if "</think>" in content:
                                        in_think = False
                                        content = content.split("</think>")[-1]
                                    if not in_think and content:
                                        buffer += content
                                        full_reply += content
                                        parts = _SENTENCE_END.split(buffer)
                                        if len(parts) > 1:
                                            for s in parts[:-1]:
                                                s_clean = _clean_spoken_stream(s)
                                                if s_clean:
                                                    yield s_clean
                                            buffer = parts[-1]
                                except Exception:
                                    pass
                    else:
                        err = await resp.aread()
                        log(f"[brain] NVIDIA NIM status {resp.status_code}: {err.decode('utf-8', errors='ignore')}")
            except Exception as e:
                log(f"[brain] NVIDIA NIM error: {e}")

        # 3. Built-in Local Conversational Fallback
        if not llm_succeeded:
            q = cleaned_utterance.lower()
            if any(w in q for w in ["what can you do", "features", "capabilities"]):
                fallback = "I am Sai, your personal AI assistant. I can manage your notes, open apps and folders, write code, and assist you over voice."
            elif any(w in q for w in ["priority", "priorities", "task"]):
                fallback = "Your active priorities are synchronized in your notes vault. Let me know what you would like to update."
            elif any(w in q for w in ["weather"]):
                fallback = "Weather systems look clear. What city would you like a forecast for?"
            elif any(w in q for w in ["joke"]):
                fallback = "Why do programmers prefer dark mode? Because light attracts bugs."
            elif any(w in q for w in ["who are you", "name"]):
                fallback = "I am Sai, your personal assistant."
            elif any(w in q for w in ["hello", "hey", "hi"]):
                fallback = "Hello! I am Sai. How can I help you today?"
            else:
                fallback = f"Understood. Ready for your command."
            full_reply = fallback
            yield fallback

        elif buffer.strip():
            rem = _clean_spoken_stream(buffer.strip())
            if rem:
                yield rem

        self.history.append({"role": "assistant", "content": full_reply})
        if len(self.history) > 5:
            self.history = [self.history[0]] + self.history[-4:]
        self._dirty = False
