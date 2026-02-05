import json
import os
from openai import OpenAI

# =========================
# 📁 Path Setup (FIX)
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

MISSION_DATA_FILE = os.path.join(BASE_DIR, "mission_data.json")
HISTORY_FILE = os.path.join(PROJECT_ROOT, "mission_history.json")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
EARTH_REPORT_FILE = os.path.join(REPORTS_DIR, "earth_report.txt")

# =========================
# 📁 Mission History Setup
# =========================


def load_previous_state():
    if not os.path.exists(HISTORY_FILE):
        return None

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except json.JSONDecodeError:
        return None


def save_current_state(state):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def compare_states(prev, current):
    trends = []

    def trend(name, old, new, higher_is_better=True):
        if old == new:
            return
        if higher_is_better:
            direction = "improving" if new > old else "degrading"
        else:
            direction = "improving" if new < old else "degrading"
        trends.append(f"{name} is {direction} ({old} → {new})")

    trend("Power level", prev["power"], current["power"])
    trend("Oxygen level", prev["oxygen"], current["oxygen"])
    trend("Temperature", prev["temperature"],
          current["temperature"], higher_is_better=False)

    return trends


# =========================
# 🚦 Risk Evaluation
# =========================

def evaluate_risk_level(power, oxygen, alerts):
    if power < 50 or oxygen < 75:
        return "🔴 RED", "Critical risk detected. Immediate action required."

    if power < 70 or oxygen < 85 or len(alerts) >= 2:
        return "🟠 AMBER", "Elevated risk. Mission adjustments recommended."

    return "🟢 GREEN", "All systems operating within safe parameters."


# =========================
# 🧠 AI Mission Summary
# =========================

def generate_ai_summary(alerts, recommendations, risk_level, trends):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
You are an onboard AI assistant supporting astronauts during a lunar mission under the Artemis program.

Mission risk level: {risk_level}

Mission alerts:
{alerts}

Mission recommendations:
{recommendations}

Mission trends:
{trends}

Write a concise mission status summary suitable for low-bandwidth transmission to Earth.
Focus on priorities, risks, and next actions.
"""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0.3
        )

        return response.output_text

    except Exception:
        summary = "AUTONOMOUS MODE ACTIVE. "

        if alerts:
            summary += "Priority issues detected: " + "; ".join(alerts) + ". "
        else:
            summary += "All monitored systems nominal. "

        if trends:
            summary += "Observed trends: " + "; ".join(trends) + ". "

        if recommendations:
            summary += "Recommended actions include: " + \
                "; ".join(recommendations) + ". "

        summary += f"Mission risk level is {risk_level.replace('🔴 ', '').replace('🟠 ', '').replace('🟢 ', '')}."

        return summary


# =========================
# 📡 Main Mission Logic
# =========================

with open(MISSION_DATA_FILE, "r", encoding="utf-8") as file:
    mission_data = json.load(file)

timestamp = mission_data["timestamp"]
habitat = mission_data["habitat"]
tasks = mission_data["tasks"]

power = habitat["power_level"]
oxygen = habitat["oxygen_level"]
temperature = habitat["temperature"]

alerts = []
recommendations = []

if power < 70:
    alerts.append("Power levels are below optimal threshold.")
    recommendations.append("Reduce non-essential systems usage.")

if oxygen < 85:
    alerts.append("Oxygen levels slightly below normal.")
    recommendations.append("Inspect life support systems.")

if temperature < 18 or temperature > 26:
    alerts.append("Habitat temperature outside safe range.")
    recommendations.append("Adjust thermal control systems.")

for task in tasks:
    if task["status"] == "delayed":
        alerts.append(f"Task delayed: {task['name']}")
        recommendations.append(f"Prioritize '{task['name']}'.")

risk_level, risk_message = evaluate_risk_level(power, oxygen, alerts)

previous_state = load_previous_state()

current_state = {
    "timestamp": timestamp,
    "power": power,
    "oxygen": oxygen,
    "temperature": temperature
}

if previous_state is None:
    trends = None
else:
    trends = compare_states(previous_state, current_state)


# =========================
# 🖨️ Reporting
# =========================

print("\n🌙 LUNAOPS – Mission Status Report")
print("---------------------------------")
print(f"Timestamp: {timestamp}")
print(f"Power Level: {power}%")
print(f"Oxygen Level: {oxygen}%")
print(f"Temperature: {temperature}°C")

print(f"\n🚦 Mission Risk Level: {risk_level}")
print(f"Status: {risk_message}")

print("\n📈 Mission Trends:")
if trends is None:
    print("- No previous data available.")
elif not trends:
    print("- All monitored systems stable.")
else:
    for t in trends:
        print(f"- {t}")


ai_mode = "CONNECTED" if os.getenv("OPENAI_API_KEY") else "AUTONOMOUS"
print(f"\n🤖 AI Mode: {ai_mode}")

summary = generate_ai_summary(alerts, recommendations, risk_level, trends)
print("\n🧠 AI Mission Summary:")
print(summary)

save_current_state(current_state)

print("\n📡 Report ready for transmission to Earth.\n")

# =========================
# 📄 Save Earth Transmission
# =========================

os.makedirs("reports", exist_ok=True)

safe_timestamp = timestamp.replace(":", "-")
report_path = f"reports/earth_report_{safe_timestamp}.txt"

with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join([
        "LUNAOPS – EARTH TRANSMISSION REPORT",
        "----------------------------------",
        f"Timestamp: {timestamp}",
        f"Power Level: {power}%",
        f"Oxygen Level: {oxygen}%",
        f"Temperature: {temperature}°C",
        "",
        f"Mission Risk Level: {risk_level}",
        f"Status: {risk_message}",
        "",
        "Mission Trends:",
        *(
            ["- No previous data available."]
            if trends is None
            else ["- All monitored systems stable."]
            if not trends
            else [f"- {t}" for t in trends]
        ),
        "",
        "Alerts:",
        *([f"- {a}" for a in alerts] if alerts else ["- None"]),
        "",
        "Recommendations:",
        *([f"- {r}" for r in recommendations]
          if recommendations else ["- None"]),
        "",
        f"AI Mode: {ai_mode}",
        "",
        "AI Mission Summary:",
        summary,
        "",
        "End of transmission."
    ]))
