# WebChat Assistant

A Chrome extension that allows you to chat with any webpage using AI-powered conversational assistance. Ask questions about the content of any website and get intelligent answers based on the page content with full conversation history.

<img width="352" height="498" alt="Screenshot 2025-11-03 at 6 56 27 AM" src="https://github.com/user-attachments/assets/8838ac20-5c22-47c4-9ec2-a6e589c8c1a4" />



## Features

- 🤖 **AI-Powered Q&A**: Ask questions about any webpage using OpenAI's GPT-3.5-turbo
- 💬 **Conversation History**: Maintains context across multiple questions on the same page
- 🔍 **Smart Retrieval**: Uses vector embeddings to find relevant content from the page
- 🌐 **Works on Any Website**: Compatible with most websites (excluding authentication-required pages)
- ⚡ **Fast & Responsive**: Real-time responses with typing indicators
- 🔒 **Privacy-Focused**: Each URL maintains its own isolated conversation

## Installation

### Prerequisites
- Python 3.8 or higher
- Chrome/Chromium browser
- OpenAI API key

### Step 1: Clone the Repository

```bash
git clone https://github.com/sasazan18/WebChatAssistant.git
cd WebChat
```

### Step 2: Set Up Backend

1. Create a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the `Backend` folder:
```bash
cd Backend
touch .env
```

4. Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=your_api_key_here
```

Get your API key from: https://platform.openai.com/api-keys

5. Start the backend server:
```bash
python chatBot.py
```

The server will start on `http://localhost:8000`

### Step 3: Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (top right corner)
3. Click **Load unpacked**
4. Navigate to the WebChat folder and select it
5. The extension should now appear in your Chrome extensions list

## Usage

### Using the Extension

1. **Open any webpage** in your Chrome browser
2. **Click the WebChat icon** in your Chrome extension menu (top right)
3. **A popup will appear** with the WebChat interface
4. **Type your question** about the current webpage
5. **Click Send** or press Enter
6. **Wait for the AI response** - it will analyze the page and answer your question

### Example Questions

- "What is this website about?"
- "Summarize the main content"
- "What are the key features mentioned?"
- "Tell me more about [specific topic]"
- "What are the pricing details?"

## Project Structure

```
WebChat/
├── Backend/
│   ├── chatBot.py          # Main FastAPI backend server
│   ├── .env                # Environment variables (OpenAI API key)
│   └── requirements.txt    # Python dependencies
├── popup.html              # Extension popup UI
├── popup.js                # Extension popup functionality
├── popup.css               # Extension styling
├── manifest.json           # Chrome extension manifest
├── logo.png                # Extension icon
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Architecture

### Frontend (Chrome Extension)
- **popup.html**: User interface for the chat
- **popup.js**: Handles communication with the backend
- **popup.css**: Styling for the extension popup

### Backend (FastAPI)
- **chatBot.py**: 
  - Loads and processes webpage content using WebBaseLoader
  - Creates vector embeddings with Chroma and OpenAI embeddings
  - Maintains conversation memory per URL
  - Generates AI responses using GPT-3.5-turbo

## How It Works

1. **Page Loading**: When you submit a URL, the backend fetches the webpage content
2. **Text Processing**: Content is split into manageable chunks for processing
3. **Embeddings**: Text is converted to vector embeddings for semantic search
4. **Vector Store**: Embeddings are stored in a Chroma vector database
5. **Query Processing**: Your question is converted to embeddings and matched against page content
6. **Context Generation**: Relevant content, chat history, and your question are combined
7. **AI Response**: GPT-3.5-turbo generates an answer based on the context
8. **History Management**: Conversation is saved for future context (limited to last 20 messages)

## Limitations

- ⚠️ **Authentication-Required Pages**: Cannot access pages behind login (Gmail, Outlook, etc.)
- ⚠️ **Dynamic Content**: JavaScript-rendered content may not be fully captured
- ⚠️ **File Size**: Large pages may be truncated
- ⚠️ **API Usage**: Each query uses OpenAI API credits
- ⚠️ **Same-Origin**: Extension works on standard HTTP/HTTPS websites

## Troubleshooting

### Issue: "Backend is not running"
**Solution**: Make sure the backend server is running on `http://localhost:8000`
```bash
cd Backend
python chatBot.py
```

### Issue: "The webpage appears to have no readable content"
**Solution**: This typically means:
- The page requires authentication (Gmail, Outlook, banking sites)
- The page is heavily JavaScript-based and not readable by the scraper
- The page blocks automated access

### Issue: "CORS error"
**Solution**: The backend's CORS middleware should handle this, but if issues persist, check that the backend is running properly

### Issue: "OpenAI API key not found"
**Solution**: 
- Verify your `.env` file exists in the Backend folder
- Check that `OPENAI_API_KEY=your_key` is correctly set
- Restart the backend server after adding the key

### Issue: Extension not appearing in Chrome
**Solution**:
1. Go to `chrome://extensions/`
2. Enable Developer mode (top right)
3. Click "Refresh" on the WebChat extension
4. If still not working, remove and reload the extension

## Environment Variables

Create a `.env` file in the `Backend` folder:

```env
# Required: Your OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Customize these settings
OPENAI_MODEL=gpt-3.5-turbo
TEMPERATURE=0
```

## Dependencies

### Backend (Python)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-dotenv` - Environment variable management
- `langchain` - LLM framework
- `langchain-openai` - OpenAI integration
- `langchain-community` - Community integrations
- `chroma-db` - Vector database
- `pydantic` - Data validation

### Frontend (Chrome Extension)
- Chrome 90+
- Manifest V3 compatible

## Future Enhancements

- [ ] Support for PDF file uploads
- [ ] Multi-language support
- [ ] Conversation export/download
- [ ] Custom model selection
- [ ] Rate limiting and usage tracking
- [ ] Offline support for cached pages
- [ ] Advanced context filtering
- [ ] User preferences/settings panel

## Security Considerations

- 🔐 Never commit your `.env` file with API keys
- 🔐 Keep your OpenAI API key confidential
- 🔐 Each URL maintains isolated conversation history
- 🔐 No personal data is stored on external servers
- 🔐 Consider implementing API rate limiting in production

## Development

### Running in Development Mode

1. Make changes to the frontend files (`popup.js`, `popup.html`, `popup.css`)
2. Go to `chrome://extensions/`
3. Click the refresh button on the WebChat extension
4. Changes take effect immediately

### Backend Development

The backend automatically reloads on file changes if you have `auto-reload` enabled in uvicorn.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is open source

## Author

**Saad Ahmed Sazan**
- GitHub: https://github.com/sasazan18

---

**Made with passion for better web browsing**
