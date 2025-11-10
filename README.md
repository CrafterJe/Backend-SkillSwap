# SkillSwap Backend API

Backend API for SkillSwap, a comprehensive skill-sharing mobile application that connects users for bidirectional knowledge exchange.

## 🎯 Overview

SkillSwap backend is a high-performance FastAPI application designed to support a social platform where users can both offer and request skills. Built with modern async patterns, it handles real-time messaging, social interactions, and a comprehensive posts system with comments.

**Current Version:** 1.5.0  
**Status:** Closed Testing on Google Play Store

## ✨ Core Features

### Authentication & Security
- **JWT Refresh Token System** - Access tokens (1h) + Refresh tokens (30 days)
- **Automatic Token Renewal** - Seamless token refresh on expiration
- **Secure Password Hashing** - bcrypt implementation
- **Token Invalidation** - Secure logout with token blacklisting

### Social Platform
- **User Profiles** - Complete profile management with images
- **Follow System** - Bidirectional following with follower/following counts
- **Posts & Comments** - Full CRUD operations with nested comments support
- **Likes System** - Like posts and comments
- **Search** - User search with optimized queries

### Real-time Communication
- **WebSocket Messaging** - Live message delivery with ~100ms latency
- **Conversation Management** - Thread-based messaging system
- **Optimized Chat Loading** - Reduced from 1s to ~100ms through aggregation pipelines
- **Message Caching** - Frontend caching for instant conversation access
- **Reconnection Logic** - Exponential backoff for connection stability

### Notifications
- **Push Notifications** - Firebase/Expo push notification integration
- **Activity Notifications** - Follows, likes, comments, mentions
- **Real-time Delivery** - Instant notification updates via WebSocket
- **Read/Unread Status** - Notification state management

### Explore & Discovery
- **Skill Categories** - 20+ categorized skill exploration
- **Category Images** - Visual skill category representation
- **Lazy Loading** - Efficient pagination for large datasets
- **Optimized Queries** - Reduced from 100+ to 2 aggregation pipelines

## 🛠 Tech Stack

- **FastAPI** - Modern async web framework
- **MongoDB** - NoSQL database with Motor async driver
- **WebSocket** - Real-time bidirectional communication
- **JWT** - JSON Web Tokens for authentication
- **Pydantic** - Data validation and settings management
- **Python 3.11+** - Latest Python features
- **Firebase Storage** - Image storage and delivery
- **Expo Push Notifications** - Mobile push notification service

## 📋 Prerequisites

- Python 3.11+
- MongoDB 4.4+
- pip or poetry
- Firebase account (for storage and push notifications)

## 🚀 Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create `.env` file:

```env
# Server
SECRET_KEY=your-secret-key-here
API_URL=http://localhost:8000

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=skillswap

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Firebase (optional for local dev)
FIREBASE_CREDENTIALS_PATH=path/to/credentials.json
```

### 3. Run Server

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server runs at `http://localhost:8000`

## 📁 Project Structure

```
app/
├── main.py                      # FastAPI app initialization & CORS
├── config.py                    # Environment configuration
├── database.py                  # MongoDB connection
│
├── models/                      # Database models
│   ├── authModel.py            # User model
│   └── messageModel.py         # Message & conversation models
│
├── schemas/                     # Pydantic schemas (request/response)
│   ├── authSchema.py           # Auth schemas
│   ├── explore/
│   │   └── exploreSchema.py    # Explore feature schemas
│   ├── messages/
│   │   └── messageSchema.py    # Message schemas
│   ├── navigation/
│   │   ├── notificationsSchema.py
│   │   ├── searchSchema.py
│   │   └── profileTabSchema/
│   │       ├── profileScreenSchema.py
│   │       └── profileSettingsSchema.py
│   └── posts/
│       └── postSchema.py       # Posts & comments schemas
│
├── routes/                      # API endpoints
│   ├── auth.py                 # Authentication routes
│   ├── messageRoute.py         # Messaging endpoints
│   ├── websocketRoute.py       # WebSocket connections
│   ├── explore/
│   │   └── exploreRoute.py     # Skill categories & exploration
│   ├── navigation/
│   │   ├── homeRoute.py        # Home feed
│   │   ├── notificationsRoute.py
│   │   ├── searchRoute.py
│   │   └── profileTabRoute/
│   │       ├── profileScreenRoute.py
│   │       └── profileSettingsRoute.py
│   └── posts/
│       ├── postRoute.py        # Post CRUD operations
│       └── commentRoute.py     # Comment operations
│
├── utils/                       # Utility functions
│   ├── authUtils.py            # JWT token management
│   ├── securityUtils.py        # Password hashing (bcrypt)
│   ├── auth_guardUtils.py      # Auth middleware
│   ├── websocket_manager.py    # WebSocket connection management
│   └── push_notifications.py   # Expo push notification service
│
└── scripts/
    └── migration_script.py      # Database migration utilities
```

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | User login (returns access + refresh tokens) |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout and invalidate tokens |
| GET | `/auth/verify` | Verify token validity |
| GET | `/auth/me` | Get current user info |

### User Profiles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/navigation/profileTab/profileSettings` | Get own profile |
| PUT | `/navigation/profileTab/profileSettings` | Update profile |
| PATCH | `/navigation/profileTab/profileSettings/password` | Change password |
| GET | `/navigation/profileTab/profileScreen/{username}` | Get public profile |
| POST | `/navigation/profileTab/profileScreen/{username}/follow` | Follow user |
| POST | `/navigation/profileTab/profileScreen/{username}/unfollow` | Unfollow user |

### Posts & Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/posts/` | Get all posts (feed) |
| POST | `/posts/` | Create new post |
| GET | `/posts/{post_id}` | Get single post |
| PUT | `/posts/{post_id}` | Update post |
| DELETE | `/posts/{post_id}` | Delete post |
| POST | `/posts/{post_id}/like` | Like/unlike post |
| GET | `/posts/{post_id}/comments` | Get post comments |
| POST | `/posts/{post_id}/comments` | Add comment |
| PUT | `/posts/comments/{comment_id}` | Update comment |
| DELETE | `/posts/comments/{comment_id}` | Delete comment |
| POST | `/posts/comments/{comment_id}/like` | Like/unlike comment |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/messages/conversations` | Get all conversations (optimized) |
| GET | `/messages/conversation/{username}` | Get messages with user |
| POST | `/messages/send` | Send message |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | Get user notifications |
| PATCH | `/notifications/{id}/read` | Mark notification as read |
| PATCH | `/notifications/read/all` | Mark all as read |
| POST | `/notifications/push-token` | Register push token |

### Explore

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/explore/categories` | Get all skill categories |
| GET | `/explore/categories/{category}` | Get category details |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/users?query={query}` | Search users |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| WS | `/ws?token={jwt_token}` | Real-time messaging and notifications |

## 🔐 Authentication Flow

### 1. Login
```bash
POST /auth/login
{
  "username": "user123",
  "password": "securepass"
}

Response:
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {...}
}
```

### 2. Authenticated Requests
```bash
GET /auth/me
Headers: {
  "Authorization": "Bearer <access_token>"
}
```

### 3. Token Refresh
```bash
POST /auth/refresh
{
  "refresh_token": "<refresh_token>"
}

Response:
{
  "access_token": "new_token...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 💾 Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  username: String (unique),
  email: String (unique),
  password: String (hashed),
  first_name: String,
  last_name: String,
  gender: String,
  birth_date: DateTime,
  profile_image: String (URL),
  bio: String,
  skills_offered: [String],
  skills_wanted: [String],
  followers: [ObjectId],
  following: [ObjectId],
  expo_push_token: String,
  created_at: DateTime,
  last_login: DateTime,
  is_active: Boolean
}
```

### Posts Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  content: String,
  images: [String],
  likes: [ObjectId],
  comment_count: Integer,
  created_at: DateTime,
  updated_at: DateTime
}
```

### Comments Collection
```javascript
{
  _id: ObjectId,
  post_id: ObjectId,
  user_id: ObjectId,
  content: String,
  likes: [ObjectId],
  created_at: DateTime,
  updated_at: DateTime
}
```

### Conversations Collection
```javascript
{
  _id: ObjectId,
  participants: [ObjectId] (2 users),
  last_message: String,
  last_message_at: DateTime,
  created_at: DateTime,
  updated_at: DateTime
}
```

### Messages Collection
```javascript
{
  _id: ObjectId,
  conversation_id: ObjectId,
  sender_id: ObjectId,
  content: String,
  is_read: Boolean,
  created_at: DateTime
}
```

### Notifications Collection
```javascript
{
  _id: ObjectId,
  to_user: ObjectId,
  from_user: ObjectId,
  type: String (follow|like|comment|mention),
  message: String,
  reference_id: ObjectId (post/comment),
  read: Boolean,
  created_at: DateTime
}
```

## 🚀 Performance Optimizations

### Chat System (v1.4.0)
- **Before:** 1000ms load time, 100+ database queries
- **After:** ~100ms load time, 2 optimized aggregation pipelines
- **Method:** MongoDB aggregation with $lookup and $unwind
- **Impact:** 90% reduction in load time

### Explore Feature
- **Lazy Loading:** Pagination for large category lists
- **Image Optimization:** Cached category images
- **Query Reduction:** Consolidated queries from 100+ to 2

### General
- **Async Operations:** All database operations use Motor async driver
- **Connection Pooling:** MongoDB connection pool management
- **WebSocket Efficiency:** Single connection per user with heartbeat

## 🔧 Development

### Running Tests
```bash
pytest
pytest --cov=app tests/
```

### Code Quality
```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### Database Migrations
```bash
python -m app.scripts.migration_script
```

## 🌐 WebSocket Usage

### Client Connection
```javascript
const token = "your_jwt_token";
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message:', data);
};

ws.onclose = () => {
  console.log('Disconnected');
  // Implement reconnection with exponential backoff
};
```

### Message Types
```javascript
// New message
{
  type: "new_message",
  data: {
    conversation_id: "...",
    sender: {...},
    content: "...",
    created_at: "..."
  }
}

// User status
{
  type: "user_status",
  user_id: "...",
  status: "online|offline"
}

// Notification
{
  type: "notification",
  data: {
    type: "follow|like|comment",
    from_user: {...},
    message: "..."
  }
}
```

## 📱 Push Notifications

### Register Token
```bash
POST /notifications/push-token
{
  "expo_push_token": "ExponentPushToken[xxxxxx]"
}
```

### Notification Types
- **Follow:** "X started following you"
- **Like:** "X liked your post"
- **Comment:** "X commented on your post"
- **Mention:** "X mentioned you in a comment"

## 🚢 Deployment

### Railway (Recommended)
1. Connect GitHub repository
2. Set environment variables:
   ```
   SECRET_KEY
   MONGODB_URL
   DATABASE_NAME
   JWT_SECRET_KEY
   ```
3. Add `Procfile`:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Deploy automatically on push to main

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t skillswap-backend .
docker run -p 8000:8000 --env-file .env skillswap-backend
```

## 📚 API Documentation

Interactive documentation available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## 🔒 Security Features

- ✅ Password hashing with bcrypt (12 rounds)
- ✅ JWT token signing with HS256
- ✅ Token expiration and refresh mechanism
- ✅ Input validation with Pydantic
- ✅ WebSocket authentication
- ✅ CORS configuration
- ✅ SQL injection prevention (NoSQL)
- ✅ Rate limiting (planned)
- ✅ Secure push notification tokens

## 🐛 Known Issues & Limitations

- WebSocket requires manual reconnection on app backgrounding (handled in frontend)
- iOS push notifications work natively, Android requires development build
- Maximum message size: 1MB
- Image upload size limit: 5MB per image

## 📝 Commit Convention

```
Short, single-line messages in English
Examples:
- "Add user profile endpoint"
- "Fix message loading performance"
- "Update authentication flow"
```

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature-name`
2. Make changes following code style
3. Test thoroughly with Postman
4. Write meaningful commit messages
5. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 👥 Authors

- Juarez Suarez Raúl
- Mauricio Popoca Coatl
- Omar Anzures Campos  
- Rojas Cortes Rodrigo Zuriel

## 📞 Support

- Issues: GitHub Issues
- Email: support@skillswap.com