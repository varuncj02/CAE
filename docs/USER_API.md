# User Management API

This document describes the user management endpoints added to the AGIHouse API.

## Endpoints

### Create User
Creates a new user in the system.

**Endpoint:** `POST /users/`

**Request Body:**
```json
{
  "name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "created_at": "2025-06-14T17:00:00.000Z"
}
```

### List Users
Retrieves all users in the system.

**Endpoint:** `GET /users/`

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "created_at": "2025-06-14T17:00:00.000Z"
  }
]
```

### Get User
Retrieves a specific user by ID.

**Endpoint:** `GET /users/{user_id}`

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "created_at": "2025-06-14T17:00:00.000Z"
}
```

### Get User Chats
Retrieves all chat sessions for a specific user.

**Endpoint:** `GET /users/{user_id}/chats`

**Response:** `200 OK`
```json
[
  {
    "id": "chat-uuid-here",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-06-14T17:00:00.000Z"
  }
]
```

### Delete User
Deletes a user and all associated chats and messages (cascade delete).

**Endpoint:** `DELETE /users/{user_id}`

**Response:** `204 No Content`

## Error Responses

All endpoints return appropriate error responses:

- `404 Not Found` - When the requested user doesn't exist
- `422 Unprocessable Entity` - When request validation fails
- `500 Internal Server Error` - For server-side errors

## Features

- **Cascade Deletion**: Deleting a user automatically deletes all their chats and messages
- **Legacy User Support**: Existing chats were migrated with placeholder users
- **Comprehensive Logging**: All operations are logged with structured logging
- **Type Safety**: Full Python 3.10+ type hints throughout

## Example Usage

```bash
# Create a new user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith"}'

# Get all users
curl http://localhost:8000/users/

# Get user's chats
curl http://localhost:8000/users/{user_id}/chats

# Delete a user
curl -X DELETE http://localhost:8000/users/{user_id}
``` 