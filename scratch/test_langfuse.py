import os
from dotenv import load_dotenv

load_dotenv()

print("LANGFUSE_PUBLIC_KEY:", repr(os.getenv("LANGFUSE_PUBLIC_KEY")))
print("LANGFUSE_SECRET_KEY:", repr(os.getenv("LANGFUSE_SECRET_KEY")))
print("LANGFUSE_HOST:", repr(os.getenv("LANGFUSE_HOST")))
print("LANGFUSE_BASE_URL:", repr(os.getenv("LANGFUSE_BASE_URL")))

from langfuse import Langfuse
try:
    lf = Langfuse()
    print("Langfuse client initialized successfully.")
    trace = lf.trace(name="test-trace-diagnostic")
    trace.generation(name="test-generation", input="Hello Langfuse", output="Hello World")
    lf.flush()
    print("Trace sent and flushed.")
except Exception as e:
    print("Error initializing or sending trace via langfuse client:", e)

from langfuse.langchain import CallbackHandler
try:
    handler = CallbackHandler()
    print("Langfuse CallbackHandler initialized successfully.")
except Exception as e:
    print("Error initializing Langchain CallbackHandler:", e)
