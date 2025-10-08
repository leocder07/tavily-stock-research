"""WebSocket connection manager with robust error handling and reconnection"""

from typing import Dict, List, Set, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import uuid

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with automatic cleanup and error handling"""

    def __init__(self):
        # Active connections by client_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Track connection metadata
        self.connection_metadata: Dict[str, Dict] = {}
        # Room subscriptions
        self.rooms: Dict[str, Set[str]] = {}
        # Heartbeat tasks
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        # Ping interval in seconds
        self.ping_interval = 30
        # Connection timeout in seconds
        self.connection_timeout = 60

    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """
        Accept WebSocket connection and start heartbeat monitoring.

        Args:
            websocket: FastAPI WebSocket instance
            client_id: Optional client identifier

        Returns:
            client_id used for the connection
        """
        try:
            # Generate client_id if not provided
            if not client_id:
                client_id = str(uuid.uuid4())

            # Accept connection
            await websocket.accept()

            # Store connection
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = {
                'connected_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'rooms': set()
            }

            # Start heartbeat monitoring
            self.heartbeat_tasks[client_id] = asyncio.create_task(
                self._heartbeat_monitor(client_id, websocket)
            )

            logger.info(f"WebSocket connected: {client_id}")

            # Send connection confirmation
            await self.send_personal_message(
                {
                    "type": "connection",
                    "status": "connected",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                client_id
            )

            return client_id

        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            raise

    async def disconnect(self, client_id: str):
        """
        Disconnect client and clean up resources.

        Args:
            client_id: Client identifier to disconnect
        """
        try:
            # Cancel heartbeat task
            if client_id in self.heartbeat_tasks:
                self.heartbeat_tasks[client_id].cancel()
                del self.heartbeat_tasks[client_id]

            # Remove from rooms
            if client_id in self.connection_metadata:
                for room in self.connection_metadata[client_id].get('rooms', set()):
                    await self.leave_room(client_id, room)

            # Remove connection
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].close()
                except:
                    pass  # Connection might already be closed
                del self.active_connections[client_id]

            # Clean up metadata
            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]

            logger.info(f"WebSocket disconnected: {client_id}")

        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {client_id}: {e}")

    async def send_personal_message(self, message: Any, client_id: str) -> bool:
        """
        Send message to specific client with error handling.

        Args:
            message: Message to send (will be JSON serialized)
            client_id: Target client identifier

        Returns:
            True if message sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            logger.warning(f"Client {client_id} not connected")
            return False

        try:
            websocket = self.active_connections[client_id]

            # Convert message to JSON if needed
            if not isinstance(message, str):
                message = json.dumps(message)

            await websocket.send_text(message)

            # Update last activity
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]['last_activity'] = datetime.utcnow()

            return True

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected during send")
            await self.disconnect(client_id)
            return False

        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {e}")
            await self.disconnect(client_id)
            return False

    async def broadcast(self, message: Any, exclude: List[str] = None) -> int:
        """
        Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
            exclude: List of client_ids to exclude

        Returns:
            Number of clients successfully sent to
        """
        if exclude is None:
            exclude = []

        # Convert message to JSON once
        if not isinstance(message, str):
            message = json.dumps(message)

        sent_count = 0
        disconnected_clients = []

        for client_id in self.active_connections:
            if client_id not in exclude:
                try:
                    await self.active_connections[client_id].send_text(message)
                    sent_count += 1
                except:
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

        return sent_count

    async def join_room(self, client_id: str, room_name: str):
        """
        Add client to a room for grouped messaging.

        Args:
            client_id: Client identifier
            room_name: Room name to join
        """
        if room_name not in self.rooms:
            self.rooms[room_name] = set()

        self.rooms[room_name].add(client_id)

        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]['rooms'].add(room_name)

        logger.info(f"Client {client_id} joined room {room_name}")

        # Notify room members
        await self.send_to_room(
            {
                "type": "room_event",
                "event": "member_joined",
                "room": room_name,
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            room_name,
            exclude=[client_id]
        )

    async def leave_room(self, client_id: str, room_name: str):
        """
        Remove client from a room.

        Args:
            client_id: Client identifier
            room_name: Room name to leave
        """
        if room_name in self.rooms and client_id in self.rooms[room_name]:
            self.rooms[room_name].remove(client_id)

            if not self.rooms[room_name]:
                del self.rooms[room_name]

        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]['rooms'].discard(room_name)

        logger.info(f"Client {client_id} left room {room_name}")

        # Notify remaining room members
        if room_name in self.rooms:
            await self.send_to_room(
                {
                    "type": "room_event",
                    "event": "member_left",
                    "room": room_name,
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                room_name
            )

    async def send_to_room(self, message: Any, room_name: str, exclude: List[str] = None) -> int:
        """
        Send message to all clients in a room.

        Args:
            message: Message to send
            room_name: Target room
            exclude: List of client_ids to exclude

        Returns:
            Number of clients successfully sent to
        """
        if room_name not in self.rooms:
            return 0

        if exclude is None:
            exclude = []

        sent_count = 0
        for client_id in self.rooms[room_name]:
            if client_id not in exclude:
                success = await self.send_personal_message(message, client_id)
                if success:
                    sent_count += 1

        return sent_count

    async def _heartbeat_monitor(self, client_id: str, websocket: WebSocket):
        """
        Monitor connection health with periodic pings.

        Args:
            client_id: Client identifier
            websocket: WebSocket connection to monitor
        """
        try:
            while client_id in self.active_connections:
                await asyncio.sleep(self.ping_interval)

                try:
                    # Send ping
                    await websocket.send_json({"type": "ping"})

                    # Check for timeout
                    if client_id in self.connection_metadata:
                        last_activity = self.connection_metadata[client_id]['last_activity']
                        time_since_activity = (datetime.utcnow() - last_activity).total_seconds()

                        if time_since_activity > self.connection_timeout:
                            logger.warning(f"Client {client_id} timed out")
                            await self.disconnect(client_id)
                            break

                except:
                    # Connection lost
                    logger.info(f"Lost connection to {client_id}")
                    await self.disconnect(client_id)
                    break

        except asyncio.CancelledError:
            logger.debug(f"Heartbeat monitor cancelled for {client_id}")
        except Exception as e:
            logger.error(f"Heartbeat monitor error for {client_id}: {e}")
            await self.disconnect(client_id)

    async def handle_client_message(self, client_id: str, message: str) -> Dict:
        """
        Process incoming client message.

        Args:
            client_id: Client identifier
            message: Raw message string

        Returns:
            Response to send back to client
        """
        try:
            # Parse message
            try:
                data = json.loads(message) if isinstance(message, str) else message
            except json.JSONDecodeError:
                return {"error": "Invalid JSON"}

            # Update last activity
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]['last_activity'] = datetime.utcnow()

            # Handle different message types
            message_type = data.get('type', 'unknown')

            if message_type == 'pong':
                # Response to ping
                return None

            elif message_type == 'join_room':
                room_name = data.get('room')
                if room_name:
                    await self.join_room(client_id, room_name)
                    return {
                        "type": "room_joined",
                        "room": room_name,
                        "members": len(self.rooms.get(room_name, set()))
                    }

            elif message_type == 'leave_room':
                room_name = data.get('room')
                if room_name:
                    await self.leave_room(client_id, room_name)
                    return {"type": "room_left", "room": room_name}

            elif message_type == 'broadcast':
                # Broadcast to all clients
                await self.broadcast(
                    {
                        "type": "broadcast_message",
                        "from": client_id,
                        "message": data.get('message'),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    exclude=[client_id]
                )
                return {"type": "broadcast_sent", "recipients": len(self.active_connections) - 1}

            else:
                return {"error": f"Unknown message type: {message_type}"}

        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            return {"error": str(e)}

    def get_connection_info(self, client_id: str) -> Optional[Dict]:
        """
        Get information about a specific connection.

        Args:
            client_id: Client identifier

        Returns:
            Connection information or None if not found
        """
        if client_id not in self.connection_metadata:
            return None

        metadata = self.connection_metadata[client_id]
        return {
            'client_id': client_id,
            'connected_at': metadata['connected_at'].isoformat(),
            'last_activity': metadata['last_activity'].isoformat(),
            'rooms': list(metadata['rooms']),
            'connection_duration': (datetime.utcnow() - metadata['connected_at']).total_seconds()
        }

    def get_all_connections(self) -> List[Dict]:
        """
        Get information about all active connections.

        Returns:
            List of connection information
        """
        return [
            self.get_connection_info(client_id)
            for client_id in self.active_connections
        ]

    def get_room_members(self, room_name: str) -> List[str]:
        """
        Get list of clients in a room.

        Args:
            room_name: Room name

        Returns:
            List of client IDs in the room
        """
        return list(self.rooms.get(room_name, set()))


# Global WebSocket manager instance
websocket_manager = ConnectionManager()