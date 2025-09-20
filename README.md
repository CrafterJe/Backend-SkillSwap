# SkillSwap Backend API

Backend API for SkillSwap, a social platform for skill exchange and learning.

## Features

- **JWT Refresh Token Authentication** - Secure authentication with automatic token renewal
- **User Management** - Registration, login, profile management
- **Social Features** - Follow/unfollow users, notifications
- **Search** - User search functionality
- **Real-time Notifications** - Push notification support

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **MongoDB** - NoSQL database with Motor async driver
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
  "created_at": "datetime",
  "last_login": "datetime"
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
├── routes/             # API endpoints
│   ├── auth.py         # Authentication routes
│   └── navigation/     # Feature routes
├── schemas/            # Pydantic schemas
├── utils/              # Utility functions
│   ├── authUtils.py    # JWT token management
│   ├── securityUtils.py # Password hashing
│   └── auth_guardUtils.py # Auth middleware
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
- Rate limiting and CORS configuration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@skillswap.com or create an issue in the repository.