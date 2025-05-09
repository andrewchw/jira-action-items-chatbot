import uvicorn
from fastapi import FastAPI

# Create the FastAPI application
app = FastAPI()

# Define a simple root endpoint
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Define a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 