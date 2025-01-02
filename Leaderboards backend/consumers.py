import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class LeaderboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"] == AnonymousUser():
            logger.info("Unauthenticated WebSocket connection attempt")
            await self.close()
            return

        # Assign a group name for the user
        self.group_name = f"leaderboard_{self.scope['user'].id}"
        
        try:
            # Add the user's WebSocket to the group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            logger.info(f"User {self.scope['user'].id} connected to WebSocket group {self.group_name}")
            await self.accept()  # Accept the WebSocket connection
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        # Ensure group_name exists before attempting to remove it from the group
        if hasattr(self, 'group_name'):
            try:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
                logger.info(f"User disconnected from group {self.group_name}")
            except Exception as e:
                logger.error(f"Error during WebSocket disconnect: {e}")

    async def receive(self, text_data):
        """
        Currently no client-sent data is handled. If future features require
        client messages, they can be processed here.
        """
        logger.info(f"Received unexpected data from WebSocket: {text_data}")

    async def send_leaderboard_update(self, event):
        """
        Send a leaderboard update along with the user's current league
        to the WebSocket client.
        """
        leaderboard = event["leaderboard"]
        current_league = event.get("current_league", "Unknown League")
        try:
            await self.send(text_data=json.dumps({
                "leaderboard": leaderboard,
                "currentLeague": current_league,
            }))
            logger.debug(f"Sending leaderboard data: {leaderboard} with league: {current_league}")
            logger.info("Leaderboard update sent to WebSocket")
        except Exception as e:
            logger.error(f"Error sending leaderboard update: {e}")
