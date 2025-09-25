# SkillSwap Backend API

Backend API for SkillSwap, a social platform for skill exchange and learning.

## Features

- **JWT Refresh Token Authentication** - Secure authentication with automatic token renewal
- **User Management** - Registration, login, profile management
- **Social Features** - Follow/unfollow users, notifications
- **Real-time Messaging** - Private messaging system with conversation management
- **WebSocket Support** - Real-time message delivery and user status
- **Search** - User search functionality
- **Push Notifications** - Mobile push notification support

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **MongoDB** - NoSQL database with Motor async driver
- **WebSocket** - Real-time bidirectional communication
- **JWT** - JSON Web Tokens for authentication
- **Pydantic** - Data validation and settings management
- **Python 3.11+** - Latest Python features

## Authentication System

This API implements a secure JWT refresh token system:

- **Access Tokens**: Short-lived (1 hour) for API requests
- **Refresh Tokens**: Long-lived (30 days) for token renewal
- **Automatic Renewal**: Transparent token refresh on expiration
- **Secure Logout**: Token invalidation on logout

## Installation

### Prerequisites

- Python 3.11+
- MongoDB
- pip or poetry

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## Environment Variables

```env
SECRET_KEY=your-secret-key-here
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=skillswap
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | User login |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout user |
| GET | `/auth/verify` | Verify token validity |
| GET | `/auth/me` | Get current user info |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/navigation/profileTab/profileSettings` | Get user profile |
| PUT | `/navigation/profileTab/profileSettings` | Update user profile |
| PATCH | `/navigation/profileTab/profileSettings/password` | Change password |

### Social Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/navigation/profileTab/profileScreen/{username}` | Get public profile |
| POST | `/navigation/profileTab/profileScreen/{username}/follow` | Follow user |
| POST | `/navigation/profileTab/profileScreen/{username}/unfollow` | Unfollow user |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/messages/conversations` | Get user conversations |
| GET | `/messages/conversation/{username}` | Get messages with specific user |
| POST | `/messages/send` | Send message to user |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | Get user notifications |
| PATCH | `/notifications/{id}/read` | Mark notification as read |
| PATCH | `/notifications/read/all` | Mark all notifications as read |
| POST | `/notifications/push-token` | Update push notification token |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/users?query={query}` | Search users |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws?token={jwt_token}` | Real-time message delivery and user status |

## Authentication Usage

### Login Response
```json
{
  "message": "Login exitoso",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_id",
    "username": "username",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Making Authenticated Requests
```bash
curl -H "Authorization: Bearer <access_token>" \
     https://api.skillswap.com/auth/me
```

### Token Refresh
```bash
curl -X POST https://api.skillswap.com/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "<refresh_token>"}'
```

## Database Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string", 
  "password": "hashed_string",
  "first_name": "string",
  "last_name": "string",
  "gender": "string",
  "birth_date": "datetime",
  "profile_image": "string",
  "followers": ["ObjectId"],
  "following": ["ObjectId"],
  "expo_push_token": "string",
  "created_at": "datetime",
  "last_login": "datetime"
}
```

### Conversations Collection
```json
{
  "_id": "ObjectId",
  "participants": ["ObjectId"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Messages Collection
```json
{
  "_id": "ObjectId",
  "conversation_id": "ObjectId",
  "sender_id": "ObjectId",
  "content": "string",
  "created_at": "datetime",
  "is_read": "boolean"
}
```

### Notifications Collection
```json
{
  "_id": "ObjectId",
  "to_user": "ObjectId",
  "from_user": "ObjectId", 
  "type": "string",
  "message": "string",
  "read": "boolean",
  "created_at": "datetime"
}
```

## Real-time Messaging

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=your_jwt_token');

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

### Message Types
- `new_message` - New message received
- `user_status` - User online/offline status
- `ping/pong` - Connection heartbeat

### Sending Messages
```bash
curl -X POST http://localhost:8000/messages/send \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "recipient_username": "john_doe",
       "content": "Hello there!"
     }'
```

## Development

### Running Tests
```bash
pytest
```

### Code Style
```bash
black .
flake8 .
```

### Project Structure
```
app/
├── main.py              # FastAPI app initialization
├── database.py          # MongoDB connection
├── models/             # Data models
│   ├── authModel.py    # User authentication models
│   └── messageModel.py # Message and conversation models
├── routes/             # API endpoints
│   ├── auth.py         # Authentication routes
│   ├── messageRoute.py # Messaging endpoints
│   ├── websocketRoute.py # WebSocket connections
│   └── navigation/     # Feature routes
├── schemas/            # Pydantic schemas
│   ├── authSchema.py   # Auth request/response models
│   └── messages/       # Message schemas
├── utils/              # Utility functions
│   ├── authUtils.py    # JWT token management
│   ├── securityUtils.py # Password hashing
│   ├── auth_guardUtils.py # Auth middleware
│   ├── websocket_manager.py # WebSocket management
│   └── push_notifications.py # Push notification service
```

## Deployment

### Railway (Recommended)
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main branch

### Docker
```bash
docker build -t skillswap-backend .
docker run -p 8000:8000 skillswap-backend
```

## API Documentation

When the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests and ensure they pass
5. Submit a pull request

## Security

- All passwords are hashed using bcrypt
- JWT tokens are signed with HS256 algorithm
- Refresh tokens have longer expiration than access tokens
- Input validation using Pydantic schemas
- WebSocket connections require JWT authentication
- Rate limiting and CORS configuration
- Push notifications use secure tokens

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@skillswap.com or create an issue in the repository.