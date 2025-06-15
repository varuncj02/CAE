# AGI House Chat UI

A Chainlit-based frontend for the AGI House chat application.

## Architecture

```
ui/
├── app.py                 # Main Chainlit application
├── api_client.py         # Backend API client
├── config.py             # UI configuration
├── components/           # UI components
│   ├── user_selector.py  # User management
│   ├── chat_display.py   # Chat interface
│   └── side_panel.py     # Analysis panel
├── utils/                # Utilities
│   └── logger.py         # Logging setup
├── chainlit.md           # Welcome screen
└── requirements.txt      # Dependencies
```

## Setup

1. **Install dependencies:**
   ```bash
   cd ui
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   Create a `.env` file in the `ui` directory:
   ```env
   # API Configuration
   API_BASE_URL=http://localhost:8000
   API_TIMEOUT=30
   
   # Logging
   LOG_LEVEL=INFO
   ```

3. **Ensure the backend is running:**
   The FastAPI backend should be running on `http://localhost:8000`

## Running the UI

```bash
cd ui
chainlit run app.py --port 8080
```

The UI will be available at `http://localhost:8080`

## Features

### User Management
- Create new users with names
- Switch between user profiles
- Each user has separate chat history

### Chat Interface
- Real-time AI conversations
- Message history persistence
- Load previous conversations
- Start new chat sessions

### Analysis Panel (Preview)
- Right sidebar for future mindmap/tree visualization
- Currently shows feature roadmap
- Extensible for conversation analysis

## Development

### Component Structure

1. **UserSelector**: Handles user creation, selection, and switching
2. **ChatDisplay**: Manages chat messages and history display
3. **SidePanel**: Placeholder for future analysis features

### API Client

The `api_client.py` module provides async methods for all backend endpoints:
- User management (create, list, get, delete)
- Chat operations (send message, get history, delete chat)
- Error handling with custom `APIError` exception

### Logging

Comprehensive logging with:
- Colored console output
- Rotating file logs
- Configurable log levels
- Structured logging with extra context

### Error Handling

- Graceful API error handling with user-friendly messages
- Network error recovery
- Input validation
- Session state management

## Configuration Options

See `config.py` for all available options:
- API settings (base URL, timeout)
- UI preferences (timestamps, message length)
- Feature flags (chat history, user switching, analysis panel)
- Layout options (side panel width)

## Future Enhancements

The side panel is designed to accommodate:
- Interactive mindmap visualization
- Semantic search through conversations
- Topic clustering and analysis
- Conversation flow diagrams
- Key insights extraction

## Troubleshooting

1. **"Failed to load users" error:**
   - Ensure the backend is running
   - Check API_BASE_URL in .env
   - Verify network connectivity

2. **Messages not sending:**
   - Check backend logs for errors
   - Ensure user is selected
   - Verify API endpoints are accessible

3. **UI not loading:**
   - Check Chainlit installation
   - Verify Python version (3.10+)
   - Check for port conflicts 