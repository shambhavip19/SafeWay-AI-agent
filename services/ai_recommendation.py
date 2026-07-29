import os
import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def generate_recommendation(
    score: float,
    risk_level: str,
    threats: Optional[List[str]] = None,
    emergency_resources: Optional[List[Dict[str, Any]]] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    alternative_recommendation: Optional[str] = None
) -> str:
    """
    Generate customized travel safety recommendations based on calculated risks,
    detected threats, nearby resources, and route context.
    
    If OpenAI, Gemini, or Groq API keys are available, it uses the live LLM API.
    Otherwise, it falls back to a highly dynamic, context-aware rule template.
    """
    threats = threats or []
    emergency_resources = emergency_resources or []
    emergency_resources = [r for r in emergency_resources if isinstance(r, dict)]
    
    # 1. Check for live LLM API Keys in environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    # Prepare system & user prompts for the LLM
    system_prompt = (
        "You are SafeWay AI, an expert travel safety assistant. Your goal is to analyze travel routes "
        "and coordinates, detect risk factors, and provide highly specific, actionable, and personalized "
        "travel advice. Avoid generic boilerplates like 'stay alert'. Reference the specific threats, "
        "police stations, hospitals, and route details provided."
    )
    
    user_prompt = f"""
    Analyze the following travel safety data and generate a personalized recommendation:
    - Route: From {origin or 'Origin'} to {destination or 'Destination'}
    - Safety Score: {score}/10
    - Risk Level: {risk_level}
    - Detected Threats: {', '.join(threats) if threats else 'None detected'}
    - Nearby Emergency Resources: {', '.join([r['name'] + ' (' + r['resource_type'] + ')' for r in emergency_resources[:3]]) if emergency_resources else 'None found nearby'}
    - Alternative Route Status: {alternative_recommendation or 'No alternative routes analyzed'}
    
    Format the response as a short, structured safety brief with:
    1. Threat Analysis (Explain why the score was given)
    2. Proximity Resources (Mention nearest emergency services)
    3. Actionable Advice & Alternative Routes (How to make the trip safer)
    """

    # Try live LLM call if keys are present
    if groq_key:
        try:
            logger.info("Generating recommendation using Groq API")
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "role", "content": user_prompt}
                ],
                "temperature": 0.5
            }
            response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq API call failed: {e}. Falling back to templates.")
            
    elif openai_key:
        try:
            logger.info("Generating recommendation using OpenAI API")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.5
            }
            response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}. Falling back to templates.")

    # 2. Heuristics fallback (Context-aware rules engine)
    logger.info("Generating recommendation using rule-based heuristics engine")
    
    # Identify key elements for response
    police_stations = [r for r in emergency_resources if r["resource_type"] == "Police Station"]
    hospitals = [r for r in emergency_resources if r["resource_type"] == "Hospital"]
    
    nearest_police = police_stations[0]["name"] if police_stations else None
    nearest_hospital = hospitals[0]["name"] if hospitals else None
    
    # Build parts of the response
    # Segment 1: Score Explanation
    if score >= 7.5:
        explanation = f"The route between {origin or 'origin'} and {destination or 'destination'} is relatively safe, receiving a high safety score of {score}/10."
    elif score >= 4.5:
        explanation = f"Caution is advised when traveling between {origin or 'origin'} and {destination or 'destination'}. The safety score is moderate ({score}/10) due to some local risk factors."
    else:
        explanation = f"Warning: The path to {destination or 'destination'} has a low safety rating of {score}/10. High risk factors have been identified."

    # Segment 2: Threats breakdown
    threat_details = []
    if "Unsafe late-night travel" in threats:
        threat_details.append("traveling late at night (between 10 PM and 4 AM) when visibility is lower and active street presence is reduced")
    if "Low police coverage" in threats:
        threat_details.append("limited police station density along certain stretches")
    if "Poor lighting indicators" in threats:
        threat_details.append("community reports flagging poor lighting conditions or dark zones")
    if "High report density" in threats:
        threat_details.append("a high volume of community-reported safety issues in adjacent areas")
    if "Limited emergency access" in threats:
        threat_details.append("a lack of major hospital emergency facilities nearby")

    if threat_details:
        if len(threat_details) == 1:
            explanation += f" Main risk factor includes {threat_details[0]}."
        else:
            explanation += f" Contributing risk factors include: " + "; ".join(threat_details) + "."
    else:
        explanation += " No active critical threats were detected."

    # Segment 3: Resource Callout
    resource_msg = ""
    if nearest_police or nearest_hospital:
        resource_parts = []
        if nearest_police:
            dist_p = police_stations[0].get('distance_meters', 500)
            resource_parts.append(f"{nearest_police} (Police Station) is the closest law enforcement hub, located {dist_p}m away")
        if nearest_hospital:
            dist_h = hospitals[0].get('distance_meters', 800)
            resource_parts.append(f"{nearest_hospital} is the nearest hospital ({dist_h}m)")
        resource_msg = " For safety assurance, note that " + " and ".join(resource_parts) + "."
    else:
        resource_msg = " Note that emergency infrastructure coverage in the immediate area is sparse."

    # Segment 4: Routing recommendations
    route_advice = ""
    if alternative_recommendation and "safer" in alternative_recommendation.lower():
        route_advice = f"\n\n**Safer Alternative Route**: We strongly recommend using the alternative route provided by our system. {alternative_recommendation}"
    elif "Unsafe late-night travel" in threats:
        route_advice = "\n\n**Actionable Advice**: If possible, reschedule your trip to daylight hours. If you must travel now, choose well-lit main arteries, avoid shortcuts, keep emergency numbers active, and share your live location with a trusted contact."
    else:
        route_advice = f"\n\n**Actionable Advice**: Stick to primary transit routes. In the event of an emergency, proceed towards the nearest active checkpoint or station: {nearest_police or 'Main Police Station'}."

    recommendation = f"""### Travel Safety Assessment
{explanation}{resource_msg}{route_advice}"""

    return recommendation

