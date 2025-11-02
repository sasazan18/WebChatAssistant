from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.document_loaders import WebBaseLoader
from typing import List


load_dotenv()

app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Store memory, vectorstore, and chat history per URL
session_data = {}


class QueryRequest(BaseModel):
    url: str
    query: str


def format_chat_history(chat_history: List) -> str:
    """Format chat history for use in prompts"""
    if not chat_history:
        return "No previous conversation history."

    formatted_history = []
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            formatted_history.append(f"Human: {msg.content}")
        elif isinstance(msg, AIMessage):
            formatted_history.append(f"AI Assistant: {msg.content}")
        elif isinstance(msg, SystemMessage):
            formatted_history.append(f"System: {msg.content}")

    return "\n".join(formatted_history)


def create_context_aware_prompt():
    """Create a prompt template that uses both retrieved content and chat history"""

    template = """You are a helpful AI assistant that answers questions about web pages. You maintain context across conversations and have access to both the current page content and the complete conversation history.

=== CURRENT PAGE CONTENT ===
{context}

=== CONVERSATION HISTORY ===
{chat_history}

=== INSTRUCTIONS ===
1. **Primary Source**: Use the current page content to answer questions about the webpage
2. **Memory**: Reference the actual conversation history above when users ask about previous topics or continue discussions
3. **No Hallucination**: If asked about previous conversations, only use the exact history provided - never make up past interactions
4. **Contextual Awareness**: Build upon previous exchanges to provide coherent, continuous conversations
5. **Clarity**: If information isn't available in either the page content or conversation history, clearly state this
6. **Conversational**: Be natural and engaging while maintaining accuracy
7. **Formatting Rule**:
   - Always answer in **a single well-structured paragraph** unless the user explicitly asks for a list, steps, or ordered explanation.
   - Do **not** use bullet points, headings, or markdown formatting by default.
   - Keep sentences clear and concise, ensuring smooth transitions between ideas.

=== CURRENT QUESTION ===
{query}

=== RESPONSE ===
Provide a concise, accurate answer based on the above information. If you can't find the answer, say "You don't have enough information to answer that." rather than guessing.
"""

    return PromptTemplate(
        input_variables=["context", "chat_history", "query"], template=template
    )


@app.post("/query")
async def chat_service(req: QueryRequest):
    # Use only URL as the key - each URL gets its own conversation
    url_key = req.url
    print(f"Processing request for URL: {url_key}")

    # If this URL is new, create new session data
    if url_key not in session_data:
        print(f"Creating new session for URL: {url_key}")
        try:
            loader = WebBaseLoader(req.url)
            docs = loader.load()
            if not docs:
                return {"error": "Failed to load content from the provided URL"}

            # Check if documents have meaningful content
            total_content = "".join([doc.page_content for doc in docs]).strip()
            if not total_content:
                return {
                    "error": "The webpage appears to have no readable content. This may be due to authentication requirements or dynamic content loading."
                }

            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            splits = splitter.split_documents(docs)

            # Check if we have any text splits
            if not splits:
                return {
                    "error": "Unable to process the webpage content into readable chunks."
                }

            # Build new vectorstore
            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma.from_documents(splits, embeddings)
        except Exception as e:
            print(f"Error loading URL {req.url}: {str(e)}")
            return {
                "error": f"The webpage appears to have no readable content. This may be due to authentication requirements or dynamic content loading."
            }

        # Initialize session data with vectorstore and empty chat history
        session_data[url_key] = {
            "vectorstore": vectorstore,
            "chat_history": [],
            "page_title": (
                docs[0].metadata.get("title", "Unknown Page")
                if docs
                else "Unknown Page"
            ),
        }
        print(f"Created new session for URL: {url_key}")

        # Add system message to chat history
        system_msg = SystemMessage(
            content=f"Started new conversation about: {session_data[url_key]['page_title']}"
        )
        session_data[url_key]["chat_history"].append(system_msg)

    # Get session data
    vectorstore = session_data[url_key]["vectorstore"]
    chat_history = session_data[url_key]["chat_history"]

    print(f"Chat history length before adding new message: {len(chat_history)}")
    # chat history
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            print(f"Human: {msg.content}")
        elif isinstance(msg, AIMessage):
            print(f"AI Assistant: {msg.content}")
        elif isinstance(msg, SystemMessage):
            print(f"System: {msg.content}")

    # Add current human message to history
    human_msg = HumanMessage(content=req.query)
    chat_history.append(human_msg)

    # Retrieve relevant content from the page
    retriever = vectorstore.as_retriever(k=6)
    relevant_docs = retriever.get_relevant_documents(req.query)
    context = "\n".join([doc.page_content for doc in relevant_docs])

    # Format chat history for prompt
    formatted_history = format_chat_history(
        chat_history[:-1]
    )  # Exclude current question

    # Create prompt and get response
    prompt = create_context_aware_prompt()

    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

    # Generate response
    response = llm.invoke(
        prompt.format(context=context, chat_history=formatted_history, query=req.query)
    )

    ai_response = response.content

    # Add AI response to chat history
    ai_msg = AIMessage(content=ai_response)
    chat_history.append(ai_msg)

    # Keep chat history manageable (last 20 messages)
    if len(chat_history) > 20:
        # Keep system message and last 19 messages
        session_data[url_key]["chat_history"] = [chat_history[0]] + chat_history[-19:]

    return {"answer": ai_response}


# Clear chat history for a URL
class ResetRequest(BaseModel):
    url: str


@app.post("/reset")
async def reset_session(req: ResetRequest):
    url_key = req.url
    if url_key in session_data:
        # Keep vectorstore but clear chat history
        page_title = session_data[url_key].get("page_title", "Unknown Page")
        session_data[url_key]["chat_history"] = []

        # Add fresh system message
        system_msg = SystemMessage(
            content=f"Chat history cleared. Restarted conversation about: {page_title}"
        )
        session_data[url_key]["chat_history"].append(system_msg)

        print(f"Cleared chat history for URL: {url_key}")
        return {
            "status": "reset",
            "message": f"Chat history for {req.url} has been cleared",
        }
    return {"status": "not_found", "message": "No chat history found for this URL"}


@app.get("/")
async def root():
    return {"message": "WebChat API is running!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
