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

        yield fp.PartialResponse(text="🔍 **Research Phase:** Querying Gemini Flash...\n\n")
        flash_response = ""
        try:
            async for msg in fp.stream_request(request, "Gemini-2.0-Flash", user_access_key):
                if hasattr(msg, 'text') and msg.text:
                    flash_response += msg.text
                    yield fp.PartialResponse(text=msg.text)
        except Exception as e:
            yield fp.PartialResponse(text=f"\n\n⚠️ **Error:** Could not reach Gemini-2.0-Flash. {e}")
            return

        yield fp.PartialResponse(text="\n\n---\n\n🧠 **Processing Phase:** Analyzing with VG-Secbot...\n\n")
        try:
            async for msg in fp.stream_request(request, "VG-Secbot", user_access_key):
                if hasattr(msg, 'text') and msg.text:
                    yield fp.PartialResponse(text=msg.text)
        except Exception as e:
            yield fp.PartialResponse(text=f"\n\n⚠️ **Error:** Could not reach VG-Secbot. {e}")
            return

        yield fp.PartialResponse(text="\n\n---\n**✅ Chain Complete**")

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={
                "Gemini-2.0-Flash": 2,
                "VG-Secbot": 2
            },
            allow_attachments=False,
            introduction_message="🔗 **DRBanger Chain Bot** - I research with Gemini Flash, then analyze with VG-Secbot!"
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
