from core.action.action_framework.registry import action


@action(
    name="send_discord_message",
    description="Send a message to a Discord channel.",
    action_sets=["discord"],
    input_schema={
        "channel_id": {"type": "string", "description": "Discord channel ID.", "example": "123456789012345678"},
        "content": {"type": "string", "description": "Message content.", "example": "Hello!"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_discord_message(input_data: dict) -> dict:
    from core.external_libraries.discord.external_app_library import DiscordAppLibrary
    DiscordAppLibrary.initialize()
    creds = DiscordAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Discord credential. Use /discord-bot login first."}
    cred = creds[0]
    from core.external_libraries.discord.helpers.discord_bot_helpers import send_message
    result = send_message(cred.bot_token, input_data["channel_id"], input_data["content"])
    return {"status": "success", "result": result}


@action(
    name="get_discord_messages",
    description="Get messages from a Discord channel.",
    action_sets=["discord"],
    input_schema={
        "channel_id": {"type": "string", "description": "Discord channel ID.", "example": "123456789012345678"},
        "limit": {"type": "integer", "description": "Max messages to return (1-100).", "example": 50},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_discord_messages(input_data: dict) -> dict:
    from core.external_libraries.discord.external_app_library import DiscordAppLibrary
    DiscordAppLibrary.initialize()
    creds = DiscordAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Discord credential. Use /discord-bot login first."}
    cred = creds[0]
    from core.external_libraries.discord.helpers.discord_bot_helpers import get_messages
    result = get_messages(cred.bot_token, input_data["channel_id"],
                          limit=input_data.get("limit", 50))
    return {"status": "success", "result": result}


@action(
    name="list_discord_guilds",
    description="List Discord guilds (servers) the bot is in.",
    action_sets=["discord"],
    input_schema={
        "limit": {"type": "integer", "description": "Max guilds to return.", "example": 100},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def list_discord_guilds(input_data: dict) -> dict:
    from core.external_libraries.discord.external_app_library import DiscordAppLibrary
    DiscordAppLibrary.initialize()
    creds = DiscordAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Discord credential. Use /discord-bot login first."}
    cred = creds[0]
    from core.external_libraries.discord.helpers.discord_bot_helpers import get_bot_guilds
    result = get_bot_guilds(cred.bot_token, limit=input_data.get("limit", 100))
    return {"status": "success", "result": result}


@action(
    name="get_discord_channels",
    description="Get all channels in a Discord guild.",
    action_sets=["discord"],
    input_schema={
        "guild_id": {"type": "string", "description": "Discord guild (server) ID.", "example": "123456789012345678"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_discord_channels(input_data: dict) -> dict:
    from core.external_libraries.discord.external_app_library import DiscordAppLibrary
    DiscordAppLibrary.initialize()
    creds = DiscordAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Discord credential. Use /discord-bot login first."}
    cred = creds[0]
    from core.external_libraries.discord.helpers.discord_bot_helpers import get_guild_channels
    result = get_guild_channels(cred.bot_token, input_data["guild_id"])
    return {"status": "success", "result": result}


@action(
    name="send_discord_dm",
    description="Send a direct message to a Discord user.",
    action_sets=["discord"],
    input_schema={
        "recipient_id": {"type": "string", "description": "Discord user ID to DM.", "example": "123456789012345678"},
        "content": {"type": "string", "description": "Message content.", "example": "Hey there!"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_discord_dm(input_data: dict) -> dict:
    from core.external_libraries.discord.external_app_library import DiscordAppLibrary
    DiscordAppLibrary.initialize()
    creds = DiscordAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Discord credential. Use /discord-bot login first."}
    cred = creds[0]
    from core.external_libraries.discord.helpers.discord_bot_helpers import send_dm
    result = send_dm(cred.bot_token, input_data["recipient_id"], input_data["content"])
    return {"status": "success", "result": result}
