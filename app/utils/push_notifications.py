import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

async def send_push_notification(token: str, title: str, body: str, data: dict = {}):
    message = {
        "to": token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(EXPO_PUSH_URL, json=message)
        if response.status_code != 200:
            print("Error al enviar notificación:", response.text)
