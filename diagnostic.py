import os
import sys
from dotenv import load_dotenv

# Redirect stdout and stderr to a file so we can view them easily
sys.stdout = open("diagnostic_output.txt", "w", encoding="utf-8")
sys.stderr = sys.stdout

load_dotenv()

print("Loaded environment variables:")
print("LANGFUSE_PUBLIC_KEY:", repr(os.getenv("LANGFUSE_PUBLIC_KEY")))
print("LANGFUSE_SECRET_KEY:", repr(os.getenv("LANGFUSE_SECRET_KEY")))
print("LANGFUSE_HOST:", repr(os.getenv("LANGFUSE_HOST")))
print("LANGFUSE_BASE_URL:", repr(os.getenv("LANGFUSE_BASE_URL")))

from langfuse import Langfuse
try:
    lf = Langfuse()
    print("Langfuse client initialized successfully.")
    
    # Run auth check
    auth_ok = lf.auth_check()
    print("Langfuse auth_check() returned:", auth_ok)
    
    trace = lf.trace(name="test-diagnostic-trace")
    trace.generation(name="test-generation", input="Hello Langfuse", output="Hello World")
    lf.flush()
    print("Trace sent and flushed.")
except Exception as e:
    print("Error during Langfuse client test:", e)

from langfuse.langchain import CallbackHandler
try:
    handler = CallbackHandler()
    print("Langfuse CallbackHandler initialized successfully.")
except Exception as e:
    print("Error during Langfuse CallbackHandler initialization:", e)

sys.stdout.close()
