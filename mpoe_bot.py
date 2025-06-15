import os
import modal
from typing import AsyncIterable
import fastapi_poe as fp

# ——————————————————————————————————————————————————————————————
# ⚙️  Modal App & Secrets Configuration
# ——————————————————————————————————————————————————————————————
app = modal.App("poe-server-bot")
poe_secrets = modal.Secret.from_name("poe-bot-secrets")

# ——————————————————————————————————————————————————————————————
# 📦  Container Image & Dependencies
# ——————————————————————————————————————————————————————————————
image = modal.Image.debian_slim().pip_install_from_requirements("requirements.txt")

# ——————————————————————————————————————————————————————————————
# 🤖  The Chained Bot Logic (DRBanger)
# ——————————————————————————————————————————————————————————————
class ChainedBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
    user_message = request.query[-1].content
    user_access_key = request.access_key

    # 🟢 STEP 1: VG-Secbot Research (Flash-powered)
    yield fp.PartialResponse(text="🔍 **Research Phase:** VG-Secbot investigating...\n\n")

    segbot_research = ""  # 📦 ACCUMULATOR
    try:
        async for msg in fp.stream_request(request, "VG-Secbot", user_access_key):
            if hasattr(msg, 'text') and msg.text:
                segbot_research += msg.text  # 🔄 COLLECT research
                yield fp.PartialResponse(text=msg.text)  # 👀 STREAM live
    except Exception as e:
        yield fp.PartialResponse(text=f"\n\n⚠️ **Error:** VG-Secbot failed. {e}")
        return

    # 🧠 STEP 2: Build Combined-Query for Qwen
    yield fp.PartialResponse(text="\n\n---\n\n🧠 **Analysis Phase:** Qwen processing...\n\n")

    combined_message = f"""Original Query: {user_message}

Research Results: {segbot_research}

Please analyze and provide final insights:"""

    # 🔧 REQUEST-CONSTRUCTION-MAGIC HERE!
    new_request = fp.QueryRequest(
        query=[fp.ProtocolMessage(role="user", content=combined_message)],
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        message_id=request.message_id + "_processed",
        access_key=request.access_key
    )

    # 🎯 STEP 3: Send Enhanced-Request to Qwen
    try:
        async for msg in fp.stream_request(new_request, "Qwen3-32B-nitro", user_access_key):
            if hasattr(msg, 'text') and msg.text:
                yield fp.PartialResponse(text=msg.text)
    except Exception as e:
        yield fp.PartialResponse(text=f"\n\n⚠️ **Error:** Qwen failed. {e}")
        return

    yield fp.PartialResponse(text="\n\n---\n**✅ Chain Complete**")

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
    return fp.SettingsResponse(
        server_bot_dependencies={
            "VG-Secbot": 2,          # 🔄 Changed from Gemini-2.0-Flash
            "Qwen3-32B-nitro": 2     # 🔄 Changed from VG-Secbot
        },
        allow_attachments=False,
        introduction_message="🔗 **DRBanger Chain Bot** - VG-Secbot researches, Qwen analyzes!"
    )
        )

# ——————————————————————————————————————————————————————————————
# 🚀  Deployment Entrypoint
# ——————————————————————————————————————————————————————————————
@app.function(image=image, secrets=[poe_secrets])
@modal.asgi_app()
def fastapi_entry():
    """This function connects our bot logic to Poe's servers."""
    bot = ChainedBot()

    # ✅ THE FINAL TOGGLE: We now provide BOTH the bot_name and access_key
    # to enable the automatic settings sync feature.
    return fp.make_app(
        bot,
        bot_name="DRBanger",
        access_key=os.environ["POE_BOT_API_KEY"]
    )
