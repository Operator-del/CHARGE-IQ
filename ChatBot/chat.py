import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
import requests

def get_groq_keys():
    load_dotenv(override=True)
    keys = [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3")
    ]
    return [k.strip() for k in keys if k and k.strip() and not k.startswith("your_")]

def huggingface_chat(message, language="en"):
    """Backup API using Hugging Face"""
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        return None
    
    try:
        headers = {"Authorization": f"Bearer {hf_token}"}
        payload = {
            "inputs": message,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
        return None
    except Exception as e:
        print(f"HF Error: {e}")
        return None

def get_system_prompt(language):
    base_instructions = (
        "You are an EV Assistant expert on Electric Vehicles and Charging Infrastructure across India. "
        "When asked about EV charging stations in any city or location (such as Gandhidham, Ahmedabad, Delhi, Bangalore, Mumbai, etc.), "
        "always provide comprehensive technical and pricing details for each station:\n"
        "1. Station Name & Operator (Tata Power, Jio-bp pulse, ChargeZone, Statiq, Ather Grid, etc.)\n"
        "2. Exact Location / Landmark / Address\n"
        "3. Power Output / Wattage (e.g. 60 kW / 60,000 Watts DC Fast, 120 kW Ultra-Fast, 7.4 kW AC)\n"
        "4. Tariff / Charging Rate (e.g. ₹17.50 to ₹21.00 per kWh/unit + GST)\n"
        "5. Estimated Charging Time (e.g. 10% to 80% in ~40-45 mins on DC Fast; 0-100% in 6-7 hrs on AC)\n"
        "6. Connector Types (CCS2, Type-2 AC, CHAdeMO)\n"
        "7. Operating Hours & Availability (e.g. 24/7 Open)\n"
        "Only answer EV-related questions. Format clearly with numbered lists and bullet points with line breaks."
    )
    formatting = " Use clear line breaks and easy-to-read text formatting."
    
    if language == "en":
        return base_instructions + formatting + " Respond in English."
    elif language == "hinglish":
        return base_instructions + formatting + " Respond in conversational Hinglish (Hindi + English)."
    elif language == "gu":
        return base_instructions + formatting + " Respond in Gujarati."
    elif language == "hi":
        return base_instructions + formatting + " Respond in Hindi."
    else:
        return base_instructions + formatting + f" Always respond in {language}."

# City station directory with power, rates, and charging time specifications
CITY_STATIONS = {
    "gandhidham": [
        {
            "name": "Tata Power EZ Charge",
            "location": "Near Oslo Circle, Hotel Grand 3D, Gandhidham",
            "power": "60 kW (60,000 Watts/hr) DC Fast & 7.4 kW AC",
            "rate": "₹18.50 / kWh (unit) + 18% GST",
            "charging_time": "10% to 80% in ~45 mins (DC Fast) | Full AC in 6-7 hrs",
            "connectors": "CCS2 (Dual Gun), Type-2 AC",
            "hours": "24/7 Open"
        },
        {
            "name": "Jio-bp pulse EV Hub",
            "location": "Kandla Highway / NH-41, Sector 9, Gandhidham",
            "power": "60 kW (60,000 Watts/hr) DC Fast Charger",
            "rate": "₹17.90 / kWh (unit) + GST",
            "charging_time": "20% to 80% in ~40 mins (DC Fast)",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        },
        {
            "name": "ChargeZone Fast EV Station",
            "location": "Near Tagore Road, Sector 8, Gandhidham",
            "power": "30 kW / 60 kW DC Fast",
            "rate": "₹19.00 / kWh (unit)",
            "charging_time": "15% to 80% in ~45-50 mins",
            "connectors": "CCS2, Type-2",
            "hours": "6:00 AM – 11:00 PM"
        },
        {
            "name": "Statiq EV Charging Hub",
            "location": "Station Road, Near Railway Junction, Gandhidham",
            "power": "30 kW DC Fast & 7.4 kW AC (7,400 Watts/hr)",
            "rate": "₹16.50 / kWh (AC) | ₹19.50 / kWh (DC)",
            "charging_time": "10% to 80% in ~55 mins (30kW DC)",
            "connectors": "CCS2, Type-2 AC",
            "hours": "24/7 Open"
        },
        {
            "name": "Torrent Power / MG EV Point",
            "location": "National Highway 8A, Gandhidham - Kandla Bypass",
            "power": "50 kW (50,000 Watts/hr) DC Fast",
            "rate": "₹18.00 / kWh (unit)",
            "charging_time": "20% to 80% in ~45 mins",
            "connectors": "CCS2 Single Gun",
            "hours": "24/7 Open"
        }
    ],
    "ahmedabad": [
        {
            "name": "Tata Power EZ Charge",
            "location": "SG Highway, Near Iscon Cross Road, Ahmedabad",
            "power": "60 kW (60,000 Watts/hr) Dual DC Fast",
            "rate": "₹18.50 / kWh + GST",
            "charging_time": "10% to 80% in ~45 mins",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        },
        {
            "name": "ChargeZone Superfast Station",
            "location": "Sindhu Bhavan Road, Bodakdev, Ahmedabad",
            "power": "120 kW (120,000 Watts/hr) Ultra-Fast DC",
            "rate": "₹21.00 / kWh",
            "charging_time": "10% to 80% in ~25-30 mins (Ultra-Fast)",
            "connectors": "CCS2 High-Power Gun",
            "hours": "24/7 Open"
        },
        {
            "name": "Jio-bp pulse Charging Hub",
            "location": "Prahlad Nagar, SG Highway, Ahmedabad",
            "power": "60 kW DC Fast",
            "rate": "₹17.50 / kWh",
            "charging_time": "20% to 80% in ~40 mins",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        },
        {
            "name": "Ather Grid (2-Wheeler)",
            "location": "Vastrapur Lake Road, Ahmedabad",
            "power": "3.3 kW Fast 2W Charger",
            "rate": "Free for Ather users / ₹1.00 per min",
            "charging_time": "0 to 80% in ~60 mins for 2W",
            "connectors": "Ather Proprietary / Type 2",
            "hours": "24/7 Open"
        }
    ],
    "bhuj": [
        {
            "name": "Tata Power EV Charging Station",
            "location": "Mirzapar Highway, Near RTO, Bhuj",
            "power": "60 kW (60,000 Watts/hr) DC Fast & 7.4 kW AC",
            "rate": "₹18.50 / kWh",
            "charging_time": "10% to 80% in ~45 mins",
            "connectors": "CCS2, Type-2",
            "hours": "24/7 Open"
        },
        {
            "name": "ChargeZone EV Hub",
            "location": "Madhapar Road, Bhuj",
            "power": "60 kW DC Fast",
            "rate": "₹19.00 / kWh",
            "charging_time": "20% to 80% in ~40 mins",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        }
    ],
    "rajkot": [
        {
            "name": "Tata Power EV Station",
            "location": "Kalawad Road, Near Crystal Mall, Rajkot",
            "power": "60 kW (60,000 Watts/hr) DC Fast",
            "rate": "₹18.50 / kWh",
            "charging_time": "10% to 80% in ~45 mins",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        },
        {
            "name": "Jio-bp pulse Station",
            "location": "150 Feet Ring Road, Rajkot",
            "power": "60 kW DC Fast",
            "rate": "₹17.90 / kWh",
            "charging_time": "20% to 80% in ~40 mins",
            "connectors": "CCS2",
            "hours": "24/7 Open"
        }
    ],
    "surat": [
        {
            "name": "ChargeZone Superfast Hub",
            "location": "Dumas Road, Near VR Mall, Surat",
            "power": "60 kW / 120 kW Ultra-Fast DC",
            "rate": "₹19.50 / kWh",
            "charging_time": "10% to 80% in ~30-40 mins",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        },
        {
            "name": "Tata Power EZ Charge",
            "location": "Varachha Main Road, Surat",
            "power": "30 kW / 60 kW DC Fast",
            "rate": "₹18.00 / kWh",
            "charging_time": "20% to 80% in ~45 mins",
            "connectors": "CCS2, Type-2",
            "hours": "24/7 Open"
        }
    ],
    "vadodara": [
        {
            "name": "Tata Power EV Station",
            "location": "Old Padra Road, Vadodara",
            "power": "60 kW DC Fast & 7.4 kW AC",
            "rate": "₹18.50 / kWh",
            "charging_time": "10% to 80% in ~45 mins",
            "connectors": "CCS2, Type-2",
            "hours": "24/7 Open"
        },
        {
            "name": "ChargeZone EV Point",
            "location": "Alkapuri, Vadodara",
            "power": "60 kW DC Fast",
            "rate": "₹19.00 / kWh",
            "charging_time": "20% to 80% in ~40 mins",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        }
    ],
    "mumbai": [
        {
            "name": "Tata Power Superfast Hub",
            "location": "Bandra Kurla Complex (BKC), Mumbai",
            "power": "120 kW (120,000 Watts/hr) Ultra-Fast & 60 kW DC",
            "rate": "₹20.00 / kWh",
            "charging_time": "10% to 80% in ~25-35 mins",
            "connectors": "CCS2, Type-2",
            "hours": "24/7 Open"
        },
        {
            "name": "Jio-bp pulse Hub",
            "location": "Western Express Highway, Andheri East, Mumbai",
            "power": "60 kW DC Fast",
            "rate": "₹18.50 / kWh",
            "charging_time": "20% to 80% in ~40 mins",
            "connectors": "CCS2 Dual Gun",
            "hours": "24/7 Open"
        }
    ],
    "delhi": [
        {
            "name": "BSES / Tata Power EV Hub",
            "location": "Connaught Place, Central Delhi",
            "power": "60 kW DC Fast & 22 kW AC",
            "rate": "₹17.00 / kWh",
            "charging_time": "10% to 80% in ~45 mins",
            "connectors": "CCS2, Type-2 AC",
            "hours": "24/7 Open"
        },
        {
            "name": "Statiq Superfast Hub",
            "location": "Aerocity, New Delhi",
            "power": "120 kW (120,000 Watts/hr) Ultra-Fast DC",
            "rate": "₹19.50 / kWh",
            "charging_time": "10% to 80% in ~25-30 mins",
            "connectors": "CCS2 High-Power",
            "hours": "24/7 Open"
        }
    ],
    "bangalore": [
        {
            "name": "Tata Power EV Charging Station",
            "location": "Indiranagar 100ft Road, Bangalore",
            "power": "60 kW (60,000 Watts/hr) DC Fast",
            "rate": "₹18.50 / kWh",
            "charging_time": "10% to 80% in ~45 mins",
            "connectors": "CCS2, Type-2",
            "hours": "24/7 Open"
        },
        {
            "name": "Ather Grid & Statiq Hub",
            "location": "Koramangala 5th Block, Bangalore",
            "power": "60 kW DC Fast + 3.3 kW 2W Charging",
            "rate": "₹18.00 / kWh",
            "charging_time": "20% to 80% in ~40 mins",
            "connectors": "CCS2 & Ather Grid",
            "hours": "24/7 Open"
        }
    ]
}

def find_city_in_query(msg_lower):
    for city in CITY_STATIONS:
        if city in msg_lower:
            return city
    return None

def format_city_stations_response(city, language="en"):
    stations = CITY_STATIONS.get(city, [])
    city_name = city.capitalize()
    
    if language == "hinglish":
        header = f"⚡ {city_name} mein live EV Charging Stations, Power (Watts), Rates & Timings:\n\n"
    elif language == "gu":
        header = f"⚡ {city_name} માં EV ચાર્જિંગ સ્ટેશન, પાવર (વોટ્સ), રેટ અને ચાર્જિંગ સમય:\n\n"
    elif language == "hi":
        header = f"⚡ {city_name} में EV चार्जنگ स्टेशन, पावर (वॉट्स), दरें और चार्जिंग समय:\n\n"
    else:
        header = f"⚡ Live EV Charging Stations in {city_name} — Power (Watts/hr), Rates & Charging Time:\n\n"
        
    lines = [header]
    for i, s in enumerate(stations, 1):
        lines.append(
            f"{i}. {s['name']}\n"
            f"   📍 Location: {s['location']}\n"
            f"   ⚡ Power Output: {s['power']}\n"
            f"   💰 Tariff / Rate: {s['rate']}\n"
            f"   ⏱️ Charging Time: {s['charging_time']}\n"
            f"   🔌 Connectors: {s['connectors']}\n"
            f"   🕒 Availability: {s['hours']}\n"
        )
        
    lines.append(
        "\n📊 Quick EV Charging Guide:\n"
        "• 60 kW DC Fast: Consumes ~60 units (kWh) per hour | Charges a 40kWh battery (Nexon EV / ZS EV) to 80% in ~40 mins (~₹700-₹850)\n"
        "• 7.4 kW AC Home/Public: Consumes ~7.4 units/hr | Full charge in 6-8 hours (~₹350-₹450)\n"
        "💡 You can view live directions and live map routes directly on the Charge IQ map above!"
    )
    return "\n".join(lines)

def get_fallback_response(message, language="en"):
    """Smart fallback response for EV station queries, power/rate questions, greetings, and EV tips"""
    msg_lower = message.lower().strip()
    
    # Standalone greeting check using word boundaries
    if re.search(r'\b(hi|hello|hey|namaste|kem\s+cho|kaise\s+ho|greetings|hola)\b', msg_lower) and len(msg_lower.split()) <= 3:
        responses = {
            "en": "Hello! I'm your EV Assistant. How can I help you find charging stations, check power (Watts), rates (₹/kWh), or estimate charging times today? ⚡",
            "hinglish": "Hello! Main aapka EV Assistant hun. Charging stations, power wattage, rates (₹/unit), ya charging time calculate karne mein kaise help kar sakta hun? ⚡",
            "gu": "નમસ્તે! હું તમારો EV આસિસ્ટન્ટ છું. આજે ચાર્જિંગ સ્ટેશન, પાવર (વોટ્સ), રેટ અને ચાર્જિંગ સમય જાણવામાં હું તમારી કેવી રીતે મદદ કરી શકું? ⚡",
            "hi": "नमस्ते! मैं आपका EV असिस्टेंट हूं। आज चार्जिंग स्टेशन, पावर (वॉट्स), दरें और समय की जानकारी के लिए मैं आपकी कैसे मदद कर सकता हूं? ⚡"
        }
        return responses.get(language, responses["en"])
    
    # Check if a known city was queried
    matched_city = find_city_in_query(msg_lower)
    if matched_city:
        return format_city_stations_response(matched_city, language)
        
    # Rate, Watt, or Pricing specific questions
    if any(k in msg_lower for k in ["rate", "price", "cost", "tariff", "watt", "walt", "kw", "kwh", "unit", "time", "hour", "how much"]):
        if language == "hinglish":
            return (
                "⚡ EV Charging Power, Rates & Charging Time Specs in India:\n\n"
                "1. 🚀 Ultra-Fast DC (120 kW / 120,000 Watts/hr):\n"
                "   • Rate: ₹19 - ₹22 per kWh (unit)\n"
                "   • Time: 10% to 80% in 25 - 30 minutes\n\n"
                "2. ⚡ Fast DC Charger (60 kW / 60,000 Watts/hr):\n"
                "   • Rate: ₹17 - ₹19.50 per kWh (unit)\n"
                "   • Time: 10% to 80% in 40 - 45 minutes\n\n"
                "3. 🔌 Standard DC (30 kW / 30,000 Watts/hr):\n"
                "   • Rate: ₹16 - ₹18.50 per kWh\n"
                "   • Time: 15% to 80% in 55 - 65 minutes\n\n"
                "4. 🏠 AC Slow / Type 2 (7.4 kW / 7,400 Watts/hr):\n"
                "   • Rate: ₹12 - ₹15 per kWh\n"
                "   • Time: 0% to 100% in 6 - 8 hours\n\n"
                "Kisi bhi specific city (jaise Gandhidham, Ahmedabad, Delhi) ke live rates dekhne ke liye city ka naam puchein!"
            )
        return (
            "⚡ EV Charging Power (Watts/hr), Rates & Charging Time Overview across India:\n\n"
            "1. 🚀 Ultra-Fast DC (120 kW = 120,000 Watts/hr):\n"
            "   • Average Rate: ₹19.00 – ₹22.00 / kWh (unit) + GST\n"
            "   • Charging Time: 10% to 80% in ~25–30 mins (for 40–60 kWh EV battery)\n\n"
            "2. ⚡ Fast DC (60 kW = 60,000 Watts/hr):\n"
            "   • Average Rate: ₹17.50 – ₹19.50 / kWh (unit)\n"
            "   • Charging Time: 10% to 80% in ~40–45 mins (e.g. Nexon EV, Tiago EV, ZS EV)\n\n"
            "3. 🔌 Standard DC (30 kW = 30,000 Watts/hr):\n"
            "   • Average Rate: ₹16.00 – ₹18.50 / kWh\n"
            "   • Charging Time: 15% to 80% in ~55–65 mins\n\n"
            "4. 🏠 AC Public / Home (7.4 kW = 7,400 Watts/hr):\n"
            "   • Average Rate: ₹12.00 – ₹15.00 / kWh\n"
            "   • Charging Time: 0% to 100% in ~6–8 hours\n\n"
            "💡 To view exact station-by-station rates and power output for your area, tell me your city (e.g., Gandhidham, Ahmedabad, Delhi, Bangalore)!"
        )

    # General station query fallback
    if any(k in msg_lower for k in ["station", "charging", "charger", "near", "find", "nearest", "kahan"]):
        if language == "hinglish":
            return (
                "⚡ EV Charging Stations khojne ke liye aap city ka naam bata sakte hain (jaise Gandhidham, Ahmedabad, Delhi, Mumbai).\n\n"
                "Aapko live Power Output (kW/Watts), per kWh Rates, aur charging time mil jayega!\n"
                "Major networks available: Tata Power, Jio-bp pulse, ChargeZone, Statiq, Ather Grid."
            )
        return (
            "⚡ To find the nearest charging stations with live power ratings (Watts), pricing (₹/kWh), and charging times, please specify your city (e.g. Gandhidham, Ahmedabad, Delhi, Bangalore, Mumbai).\n\n"
            "• Major Networks: Tata Power EZ Charge, Jio-bp pulse, ChargeZone, Statiq, Ather Grid\n"
            "• Connector Types: CCS2 (Fast DC), Type 2 (AC), CHAdeMO\n\n"
            "💡 You can also use the interactive Live Map on the screen to view stations near your GPS location!"
        )
        
    # Default fallback
    if language == "hinglish":
        return "Electric vehicle charging stations, power output (Watts/hr), rates (₹/kWh), ya charging time ke baare mein kuch bhi puch sakte hain! ⚡"
    return "I'm here to help with all EV questions — find charging stations by city, check power ratings (Watts/kW), per-unit rates (₹/kWh), or estimate charging times! ⚡"

def get_greeting(language):
    greetings = {
        "en": "Hello! I'm your EV Assistant. How can I help you with electric vehicle stations, rates, power (Watts), or charging times today? ⚡",
        "hinglish": "Hello! Main aapka EV Assistant hun. Aaj electric vehicles, charging rates (₹/kWh), power wattage, ya station locations ke baare mein kaise help kar sakta hun? ⚡",
        "hi": "नमस्ते! मैं आपका EV असिस्टेंट हूं। आज इलेक्ट्रिक वाहनों के चार्जિંગ स्टेशन, दरें (₹/kWh) और पावर के बारे में मैं आपकी कैसे मदद कर सकता हूं? ⚡",
        "gu": "નમસ્તે! હું તમારો EV આસિસ્ટન્ટ છું. આજે ઇલેક્ટ્રિક વાહનો, ચાર્જિંગ રેટ અને પાવર વિશે હું તમારી કેવી રીતે મદદ કરી શકું? ⚡"
    }
    return greetings.get(language, greetings["en"])

def ev_chat(message, language="en"):
    groq_keys = get_groq_keys()
    
    # Try each Groq API key in rotation if keys exist
    for i, api_key in enumerate(groq_keys):
        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": get_system_prompt(language)},
                    {"role": "user", "content": message}
                ],
                temperature=0.2,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq Key {i+1} Error: {e}")
            continue

    # Try HuggingFace as backup
    hf_response = huggingface_chat(message, language)
    if hf_response:
        return hf_response

    # Smart fallback with city station knowledge & regex greeting matching
    return get_fallback_response(message, language)