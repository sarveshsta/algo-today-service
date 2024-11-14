# import aioredis
import redis.asyncio as aioredis

class PubSubClient:
    client = None
    pubsub = None

    def create_connection(self, host, port, password):
        try:
            self.client = aioredis.Redis.from_url(
                f"redis://{host}:{port}/", encoding="utf-8", decode_responses=True, password=password
            )
            return self.client
        except Exception as e:
            print("The error", e)
            return None

    def get_client(self):
        return self.client

    def create_psub(self):
        self.pubsub = self.get_client().pubsub()
        return self.pubsub

    def subscribe(self, channel_name):
        return self.pubsub.subscribe(channel_name)

    def unsubscribe(self, channel_name):
        return self.pubsub.unsubscribe(channel_name)

    def listen(self):
        return self.pubsub.listen()

    def get_message(self):
        return self.pubsub.get_message()

    def message_handler(self, message):
        return message

    async def subscribe_to_channel(self, channel_name):
        await self.subscribe(channel_name)

    async def unsubscribe_from_channel(self, channel_name):
        await self.unsubscribe(channel_name)

    def publish(self, channel_name: str, message: dict) -> None:
        return self.client.publish(channel_name, message)
