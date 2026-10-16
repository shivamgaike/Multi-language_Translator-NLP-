
import streamlit as st
import pandas as pd
import requests
from gtts import gTTS
from io import BytesIO

# -------------------- PAGE CONFIGURATION --------------------
st.set_page_config(
    page_title="Language Translator",
    page_icon="🌐",
    layout="wide"
)

# -------------------- LOAD LANGUAGE DATASET --------------------
CSV_PATH = (
    "/home/shivam/Development/vscode-project/A_VS_CODE/"
    "4. NLP/NLP project/MULTIPLE LANGUAGE TRANSLATION/language.csv"
)


@st.cache_data
def load_languages():
    df = pd.read_csv(CSV_PATH)
    df.dropna(subset=["name", "iso"], inplace=True)
    df["name"] = df["name"].astype(str).str.strip()
    df["iso"] = df["iso"].astype(str).str.strip()
    df = df[(df["name"] != "") & (df["iso"] != "")]
    df = df.drop_duplicates(subset="name")
    return df


# -------------------- TRANSLATION FUNCTION --------------------
def translate_text(text, source_code, target_code):
    url = "https://api.mymemory.translated.net/get"

    params = {
        "q": text,
        "langpair": f"{source_code}|{target_code}"
    }

    try:
        response = requests.get(url, params=params, timeout=20)

        if response.status_code == 429:
            raise RuntimeError(
                "Translation limit reached. Please wait and try again."
            )

        response.raise_for_status()
        data = response.json()

        if data.get("responseStatus") != 200:
            message = data.get("responseDetails", "Translation failed.")
            raise RuntimeError(str(message))

        translated = data.get("responseData", {}).get("translatedText")

        if not translated:
            raise RuntimeError("The translation service returned no text.")

        return translated

    except requests.exceptions.Timeout:
        raise RuntimeError("The translation service took too long to respond.")

    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"Network error: {error}")


# -------------------- TEXT-TO-SPEECH --------------------
# These are gTTS language codes, not necessarily the same as
# every translation API's supported language codes.
TTS_CODE_MAP = {
    "af": "af",
    "ar": "ar",
    "bn": "bn",
    "ca": "ca",
    "cs": "cs",
    "cy": "cy",
    "da": "da",
    "de": "de",
    "el": "el",
    "en": "en",
    "eo": "eo",
    "es": "es",
    "et": "et",
    "fi": "fi",
    "fr": "fr",
    "gu": "gu",
    "hi": "hi",
    "hr": "hr",
    "hu": "hu",
    "id": "id",
    "is": "is",
    "it": "it",
    "ja": "ja",
    "jw": "jw",
    "km": "km",
    "kn": "kn",
    "ko": "ko",
    "la": "la",
    "lv": "lv",
    "ml": "ml",
    "mr": "mr",
    "ne": "ne",
    "nl": "nl",
    "no": "no",
    "pl": "pl",
    "pt": "pt",
    "ro": "ro",
    "ru": "ru",
    "si": "si",
    "sk": "sk",
    "sq": "sq",
    "sr": "sr",
    "su": "su",
    "sv": "sv",
    "sw": "sw",
    "ta": "ta",
    "te": "te",
    "th": "th",
    "tl": "tl",
    "tr": "tr",
    "uk": "uk",
    "ur": "ur",
    "vi": "vi",
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "or": "or",
    "od": "or",
}


# -------------------- LOAD LANGUAGES --------------------
st.title("🌐 Language Translation")
st.write("Enter text, choose languages, and translate it.")

try:
    languages_df = load_languages()
except FileNotFoundError:
    st.error(
        "language.csv was not found. Check the CSV_PATH in your code."
    )
    st.stop()
except Exception as error:
    st.error(f"Could not load the language dataset: {error}")
    st.stop()

language_names = languages_df["name"].tolist()
language_codes = dict(
    zip(languages_df["name"], languages_df["iso"])
)

# -------------------- INPUT FORM --------------------
with st.form("translation_form"):
    col1, col2 = st.columns(2)

    with col1:
        source_name = st.selectbox(
            "Translate from",
            language_names,
            index=language_names.index("English")
            if "English" in language_names else 0
        )

    with col2:
        target_name = st.selectbox(
            "Translate to",
            language_names,
            index=language_names.index("Italian")
            if "Italian" in language_names else 0
        )

    input_text = st.text_area(
        "Enter text to translate",
        height=150,
        placeholder="Example: Hello, how are you?"
    )

    submitted = st.form_submit_button(
        "🌍 Translate",
        use_container_width=True
    )

# -------------------- PROCESS TRANSLATION --------------------
if submitted:
    if not input_text.strip():
        st.warning("Please enter some text first.")

    elif source_name == target_name:
        st.info("Source and target languages are the same.")
        st.text_area(
            "Translated text",
            value=input_text,
            height=150,
            disabled=True
        )

    else:
        source_code = language_codes[source_name]
        target_code = language_codes[target_name]

        with st.spinner("Translating your text..."):
            try:
                output = translate_text(
                    input_text.strip(),
                    source_code,
                    target_code
                )

                st.success(
                    f"Translated from {source_name} to {target_name}"
                )

                st.text_area(
                    "Translated text",
                    value=output,
                    height=180
                )

                st.download_button(
                    "⬇️ Download translated text",
                    data=output,
                    file_name="translated_text.txt",
                    mime="text/plain",
                    use_container_width=True
                )

                # Generate speech only if gTTS supports the target code.
                tts_code = TTS_CODE_MAP.get(target_code)

                if tts_code:
                    try:
                        audio_buffer = BytesIO()
                        speech = gTTS(
                            text=output,
                            lang=tts_code,
                            slow=False
                        )
                        speech.write_to_fp(audio_buffer)
                        audio_buffer.seek(0)

                        st.subheader("🔊 Listen to translation")
                        st.audio(audio_buffer, format="audio/mpeg")

                        st.download_button(
                            "⬇️ Download audio",
                            data=audio_buffer.getvalue(),
                            file_name="translation.mp3",
                            mime="audio/mpeg",
                            use_container_width=True
                        )

                    except Exception as audio_error:
                        st.warning(
                            "Translation succeeded, but audio generation "
                            f"failed: {audio_error}"
                        )
                else:
                    st.info(
                        "Text-to-speech is not configured for this language."
                    )

            except Exception as error:
                st.error(f"Translation failed: {error}")
