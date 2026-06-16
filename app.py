import streamlit as st
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
import json
import re

# Lade API Keys
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("❌ OPENAI_API_KEY nicht in .env gefunden!")
    st.stop()

client = OpenAI(api_key=api_key)

# Hilfsfunktion: Extrahiert Video-ID aus YouTube-Link
def get_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|$)',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Hilfsfunktion: Holt das Transkript
def fetch_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript = transcript_list.find_transcript(['de', 'en'])
        transcript_pieces = transcript.fetch()
        text = " ".join([t.text for t in transcript_pieces])
        return text
    except Exception as e:
        return str(e)

# Seitenkonfiguration
st.set_page_config(page_title="ContentPilot Pro", page_icon="🚀", layout="wide")

# Header
st.title("🚀 ContentPilot Pro")
st.subheader("1 Video → Multi-Plattform Content-Strategie in 30 Sekunden")

# Sidebar für Einstellungen
with st.sidebar:
    st.header("⚙️ Einstellungen")
    
    tone = st.selectbox("Tonfall", ["Professionell", "Locker & humorvoll", "Direkt & verkaufsstark", "Inspirierend"])
    
    st.divider()
    st.subheader("🎯 Phase 1 Features")
    
    num_posts = st.slider("Anzahl der Varianten (A/B Testing)", 1, 5, 3)
    
    formats = st.multiselect(
        "Content-Formate", 
        ["Standard Post", "LinkedIn Carousel", "Twitter Thread", "Instagram Story", "Newsletter"], 
        default=["Standard Post"]
    )
    
    cta_type = st.selectbox(
        "Call-to-Action (CTA) Fokus", 
        ["Kein spezifischer CTA", "Engagement (Kommentare/Likes)", "Sales (Kauf/Anmeldung)", "Lead Gen (Newsletter/Download)", "Traffic (Link klicken)"]
    )
    
    platform = st.multiselect("Plattformen", ["LinkedIn", "Twitter/X", "Instagram", "Newsletter"], default=["LinkedIn", "Twitter/X"])

# Hauptbereich
st.divider()
input_method = st.radio("Quelle wählen:", ["YouTube-Link", "Manuelles Transkript einfügen"])

user_input = ""
if input_method == "YouTube-Link":
    user_input = st.text_input("YouTube-Link einfügen:", placeholder="https://www.youtube.com/watch?v=...")
else:
    user_input = st.text_area("Transkript einfügen:", placeholder="Füge hier das vollständige Transkript ein...", height=200)

if st.button("🔥 Content generieren", type="primary"):
    if not user_input:
        st.error("Bitte gib einen Link oder Text ein!")
    elif not formats:
        st.error("Bitte wähle mindestens ein Content-Format aus!")
    else:
        final_text = user_input
        
        # WENN YOUTUBE-LINK: Transkript holen
        if input_method == "YouTube-Link":
            video_id = get_video_id(user_input)
            if not video_id:
                st.error("❌ Ungültiger YouTube-Link!")
                st.stop()
            
            with st.spinner("📺 Transkript wird vom Video geladen..."):
                result = fetch_transcript(video_id)
                if isinstance(result, str) and len(result) < 100: 
                    st.error("❌ Konnte kein Transkript laden.")
                    st.warning("⚠️ YouTube Fehler-Detail: " + result)
                    st.stop()
                else:
                    final_text = result
                    st.success("✅ Transkript geladen! (" + str(len(final_text)) + " Zeichen)")

        # JETZT CONTENT GENERIEREN
        with st.spinner("🤖 KI erstellt Multi-Format Content-Strategie..."):
            try:
                platform_list = ", ".join(platform)
                format_list = ", ".join(formats)
                
                system_prompt = (
                    "Du bist ein erfahrener Social-Media-Stratege und Conversion-Experte. "
                    "Erstelle aus dem gegebenen Inhalt hochwertige Posts.\n\n"
                    "ANFORDERUNGEN:\n"
                    "- Plattformen: " + platform_list + "\n"
                    "- Formate: " + format_list + "\n"
                    "- Erstelle für JEDE Plattform und JEDES Format genau " + str(num_posts) + " verschiedene Varianten (für A/B Testing).\n"
                    "- Tonfall: " + tone + "\n"
                    "- CTA-Typ: " + cta_type + " (Baue diesen CTA-Typ in jeden Post ein).\n\n"
                    "FORMAT-REGELN:\n"
                    "- 'Standard Post': Max 280 Zeichen, Hook + Value + CTA.\n"
                    "- 'LinkedIn Carousel': Erstelle ein Skript für 5 Slides (Slide 1: Hook, Slide 2-4: Value, Slide 5: CTA).\n"
                    "- 'Twitter Thread': Erstelle einen Thread aus 5 Tweets (Tweet 1: Hook, Tweet 2-4: Value, Tweet 5: CTA).\n"
                    "- 'Instagram Story': Skript für 3 Story-Slides mit Text-Overlay und CTA-Sticker.\n"
                    "- 'Newsletter': Betreffzeile + kurzer Teaser-Text (max 100 Wörter) mit CTA.\n\n"
                    "JSON-STRUKTUR (SEHR WICHTIG):\n"
                    "Antworte NUR mit einem reinen JSON-Objekt. Die Keys müssen exakt so aufgebaut sein: 'plattform_format' (alles klein, mit Unterstrich). "
                    "Beispiel-Keys: 'linkedin_standard_post', 'linkedin_carousel', 'twitter_thread', 'instagram_story', 'newsletter_newsletter'. "
                    "Der Value für jeden Key ist eine Liste von Strings (die " + str(num_posts) + " Varianten).\n"
                    "Keine Einleitung, keine Erklärungen, keine Markdown-Blöcke."
                )
                
                user_message = "Inhalt: " + final_text

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=2500
                )
                
                raw_content = response.choices[0].message.content
                clean_json_str = raw_content.replace("```json", "").replace("```", "").strip()
                content = json.loads(clean_json_str)
                
                # Ergebnisse anzeigen
                st.success("✅ Content-Strategie erfolgreich generiert!")
                st.divider()
                
                for plat in platform:
                    st.markdown("## " + plat)
                    plat_key_base = plat.lower().split('/')[0]
                    
                    for fmt in formats:
                        fmt_key_base = fmt.lower().replace(" ", "_").replace("/", "")
                        full_key = plat_key_base + "_" + fmt_key_base
                        
                        matching_keys = [k for k in content.keys() if plat_key_base in k and fmt_key_base in k]
                        if not matching_keys:
                            matching_keys = [k for k in content.keys() if plat_key_base in k]
                        
                        if matching_keys:
                            posts = content[matching_keys[0]]
                        else:
                            posts = ["Format nicht generiert."]
                        
                        if isinstance(posts, str):
                            posts = [posts]
                            
                        st.markdown("### 📝 " + fmt)
                        
                        if isinstance(posts, list):
                            for idx, post in enumerate(posts, 1):
                                with st.expander("📋 Variante " + str(idx) + " (Klicken zum Anzeigen/Kopieren)", expanded=(idx==1)):
                                    st.text_area("Inhalt", post, height=150, key="area_" + full_key + "_" + str(idx))
                                    st.markdown("---")
                        else:
                            st.text_area("Inhalt", posts, height=150)
                            
                st.divider()
                st.download_button(
                    label="💾 Komplette Strategie als JSON herunterladen",
                    data=json.dumps(content, indent=2, ensure_ascii=False),
                    file_name="contentpilot_pro_export.json",
                    mime="application/json"
                )
                
            except json.JSONDecodeError:
                st.error("❌ KI hat kein gültiges JSON zurückgegeben.")
                st.text("Roh-Antwort der KI:")
                st.code(raw_content)
            except Exception as e:
                st.error("❌ Fehler: " + str(e))

# Footer
st.divider()
st.caption("ContentPilot Pro | Multi-Format Content-Strategie | Early Access: 79€/Monat")
