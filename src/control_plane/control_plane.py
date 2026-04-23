import requests
import logging
import json
from a2a.client import Client
import difflib
import asyncio
import uuid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("control_plane")


class ControlPlane:
    def __init__(self, host="localhost", port_range=(9000, 9999)):
        self.host = host
        self.port_range = port_range
        self.registry = {}

        self.discover_agents()

    def discover_agents(self):
        logger.info("[DISCOVERY] Scanning for A2A agents...")

        discovered = {}

        for port in range(self.port_range[0], self.port_range[1] + 1):
            url = f"http://{self.host}:{port}/.well-known/agent-card.json"

            try:
                response = requests.get(url, timeout=0.5)

                if response.status_code != 200:
                    continue

                card = response.json()

                agent_name = self._sanitize_name(
                    card.get("name", f"agent_{port}")
                )

                discovered[agent_name] = {
                    "url": f"http://{self.host}:{port}",
                    "card": card,
                    "port": port
                }

                logger.info(f"[OK] Found agent: {agent_name} @ {port}")

            except Exception:
                continue

        self.registry = discovered

    def _sanitize_name(self, name: str) -> str:
        return name.lower().replace(" ", "_").replace("-", "_")

    def get_alive_agents(self):
        alive = []

        for name, data in self.registry.items():
            try:
                url = f"{data['url']}/.well-known/agent-card.json"
                r = requests.get(url, timeout=0.5)

                if r.status_code == 200:
                    alive.append({
                        "name": name,
                        "description": data["card"].get("description"),
                        "skills": data["card"].get("skills"),
                        "url": data["url"]
                    })

            except Exception:
                continue

        return alive

    def _find_best_agent(self, agent_name: str) -> str:
        """
        Retorna o nome mais parecido do registry.
        """

        available = list(self.registry.keys())

        if agent_name in available:
            return agent_name

        matches = difflib.get_close_matches(agent_name, available, n=1, cutoff=0.5)

        if matches:
            logger.warning(f"[FUZZY MATCH] '{agent_name}' -> '{matches[0]}'")
            return matches[0]

        raise ValueError(f"Agent '{agent_name}' not found")


    def call_agent(self, agent_name: str, input_data):
        try:

            agent_name = self._find_best_agent(agent_name)
            agent = self.registry[agent_name]

            logger.info(f"[CALL] -> {agent_name}")
            logger.info(f"[INPUT RAW] {str(input_data)[:200]}")

            if isinstance(input_data, dict):
                input_text = json.dumps(input_data)
            else:
                input_text = str(input_data)

            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [
                            {
                                "kind": "text",
                                "text": input_text
                            }
                        ],
                        "messageId": str(uuid.uuid4())
                    },
                    "metadata": {}
                }
            }

            logger.info(f"[PAYLOAD] {json.dumps(payload)[:300]}")

            response = requests.post(
                agent["url"],
                json=payload,
                timeout=1200
            )

            raw = response.text.strip()

            logger.info(f"[HTTP] {response.status_code}")
            logger.info(f"[RAW] {raw[:500]}")

            if not raw:
                return {
                    "status": "error",
                    "message": "Empty response"
                }

            try:
                data = response.json()
            except:
                return {
                    "status": "error",
                    "message": "Invalid JSON",
                    "raw": raw[:300]
                }

            if "error" in data:
                return {
                    "status": "error",
                    "message": data["error"]
                }

            result = data.get("result")

            try:
                text = result["message"]["parts"][0]["text"]
            except:
                text = result

            return {
                "status": "ok",
                "result": text
            }

        except Exception as e:
            logger.exception("[ERROR]")
            return {
                "status": "error",
                "message": str(e)
            }
