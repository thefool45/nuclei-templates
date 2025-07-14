#!/usr/bin/env python3
"""
Send a rich Discord embed whenever a new nuclei-template YAML is added.
– severity & description now read from data["info"][…]
– pretty colours that match severity
"""

import os, sys, yaml, pathlib, requests, time

# Hex colours → int for Discord embeds
SEVERITY_COLOURS = {
    "critical": 0xB71C1C,  # 🔥 Darker red
    "high":     0xE53935,  # Bright red
    "medium":   0xFB8C00,  # Orange
    "low":      0x03A9F4,  # Light blue
    "info":     0x90A4AE,  # Soft grey-blue
    "unknown":  0xB0BEC5
}

SEVERITY_ICONS = {
    "critical": "🛑",  # stop sign = urgent + highly visible
    "high":     "🔴",  # red circle
    "medium":   "🟠",  # orange
    "low":      "🔵",  # blue
    "info":     "⚪",  # white
    "unknown":  "⚪"
}

def main(action, template_path):
    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), template_path)
    with open(template_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # ── Extract info ────────────────────────────────────────────────────────────
    info        = data.get("info", {})                       # new nesting
    name        = pathlib.Path(template_path).name
    severity    = str(info.get("severity", "unknown")).lower()
    description = str(info.get("description", "No description"))
    template_id = str(data.get("id", "unknown"))
    root_path   = template_path.replace("\\", "/")

    reference = "\n".join(info.get("reference", [])).strip()

    # pick a colour; default = mid-grey
    colour      = SEVERITY_COLOURS.get(severity, 0x95A5A6)
    
    shodan_query = info.get("metadata", {}).get("shodan-query", None)
    fofa_query   = info.get("metadata", {}).get("fofa-query", None)
    severity_icon = SEVERITY_ICONS.get(severity, "⚪")

    fields = [
        {"name": "Template ID", "value": template_id, "inline": True},
        {"name": "Severity",    "value": f"{severity_icon} {severity.upper()}",    "inline": True},
    ]

    if shodan_query:
        if isinstance(shodan_query, list):
            shodan_query = "`\n- `".join(shodan_query)
        fields.append({"name": "Shodan", "value": f"- `{shodan_query}`", "inline": False})

    if fofa_query:
        if isinstance(fofa_query, list):
            fofa_query = "`\n- `".join(fofa_query)
        fields.append({"name": "Fofa", "value": f"- `{fofa_query}`", "inline": False})

    if reference:
        fields.append({"name": "Reference", "value": reference, "inline": False})

    root_path = root_path.replace("/workspaces/nuclei-templates/", "") \
                   .replace("/home/runner/work/nuclei-templates/nuclei-templates/", "")
    fields.append({"name": "Path", "value": "`" + root_path + "`", "inline": True})
    
    if action == "A":
        title = f"🆕 `{name}`"
    else:
        # Temporary Disable Notify Modified Template
        return
        # title = f"✏️ `{name}`"

    # ── Build Discord embed ────────────────────────────────────────────────────
    payload = {
        "embeds": [{
            "title": title,
            "url":   f"https://github.com/projectdiscovery/nuclei-templates/blob/main/{root_path}",
            "color": colour,
            "fields": fields,
            "description": f"```{description}```"
        }]
    }

    # ── Send ────────────────────────────────────────────────────────────────────
    while True:
        resp = requests.post(os.environ["DISCORD_WEBHOOK"], json=payload, timeout=10)
        if resp.status_code == 429:
            time.sleep(1)
            continue
        break
    resp.raise_for_status()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: notify.py <state> <template.yaml>")
    main(sys.argv[1], sys.argv[2])