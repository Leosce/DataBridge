import chainlit as cl
from dotenv import load_dotenv
import os
from main import AIAgent

load_dotenv()

@cl.on_chat_start
async def start():
    keys = {
        "groq": os.getenv("GROQ_API_KEY"),
        "nvidia": os.getenv("NVIDIA_API_KEY"),
        "gemini": os.getenv("GEMINI_API_KEY")
    }

    actions = [
        cl.Action(name="model_select", value="Groq (Llama 3.3)", label="Groq: Llama 3.3", payload={}),
        cl.Action(name="model_select", value="NVIDIA (Llama 3.3)", label="NVIDIA: Llama 3.3", payload={}),
        cl.Action(name="model_select", value="Gemini (2.5 Flash Lite)", label="Gemini: 2.5 Flash Lite", payload={})
    ]
    
    res = await cl.AskActionMessage(
        content="Welcome to DataBridge! Please select a model:",
        actions=actions
    ).send()

    print(f"DEBUG res type: {type(res)}, value: {res}")

    model_name = None
    if res is not None:
        if isinstance(res, dict):
            model_name = res.get("value") or res.get("label")
        elif hasattr(res, "value"):
            model_name = res.value
        elif isinstance(res, str):
            label_to_value = {
                "Groq: Llama 3.3": "Groq (Llama 3.3)",
                "NVIDIA: Llama 3.3": "NVIDIA (Llama 3.3)",
                "Gemini: 2.5 Flash": "Gemini (2.5 Flash Lite)"
            }
            model_name = label_to_value.get(res, res)

    if not model_name:
        model_name = "Groq (Llama 3.3)"

    agent = AIAgent(model_choice=model_name, api_keys=keys)
    cl.user_session.set("agent", agent)
    
    await cl.Message(content=f"Connected to **{model_name}**. How can I help?").send()


async def ask_confirmation(preview_text: str) -> bool:
    res = await cl.AskActionMessage(
        content=f"📋 **Preview of changes:**\n\n{preview_text}\n\nDo you want to proceed?",
        actions=[
            cl.Action(name="confirm", value="yes", label="✅ Yes, proceed", payload={}),
            cl.Action(name="confirm", value="no", label="❌ Cancel", payload={})
        ],
        timeout=60
    ).send()

    print(f"DEBUG confirmation res: {type(res)}, {res}")  # add this to see what comes back

    if res is None:
        return False
    # Handle all possible return types
    if isinstance(res, dict):
        val = res.get("value") or res.get("label", "")
        return "yes" in str(val).lower()
    elif hasattr(res, "value"):
        return "yes" in str(res.value).lower()
    elif isinstance(res, str):
        return "yes" in res.lower()
    return False


@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    if not agent:
        return

    async for step in agent.chat(message.content):
        if not step:
            continue

        if step.startswith("__CONFIRM__:"):
            preview = step.replace("__CONFIRM__:", "", 1).strip()
            confirmed = await ask_confirmation(preview)

            if confirmed:
                result = agent.confirm_pending()
                await cl.Message(content="✅ Changes applied successfully.").send()
                if result:
                    await cl.Message(content=f"**⚙️ Result:**\n{result}").send()
                
                # Continue the agent loop after confirmation
                async for continued_step in agent.continue_after_confirm():
                    if not continued_step:
                        continue
                    if continued_step.startswith("__CONFIRM__:"):
                        preview = continued_step.replace("__CONFIRM__:", "", 1).strip()
                        confirmed = await ask_confirmation(preview)
                        if confirmed:
                            result = agent.confirm_pending()
                            await cl.Message(content="✅ Changes applied successfully.").send()
                            if result:
                                await cl.Message(content=f"**⚙️ Result:**\n{result}").send()
                        else:
                            agent.cancel_pending()
                            await cl.Message(content="❌ Operation cancelled.").send()
                            break
                    else:
                        await cl.Message(content=continued_step).send()
            else:
                agent.cancel_pending()
                await cl.Message(content="❌ Operation cancelled.").send()
        else:
            await cl.Message(content=step).send()