from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from config import config
from schemas import (
    GenerationRequest, 
    GenerationResponse, 
    PromptEnhanceRequest, 
    PromptEnhanceResponse, 
    CameraTrajectoryRequest, 
    CameraTrajectoryResponse
)
from ml_pipeline import ml_engine

app = FastAPI(
    title="GimbalFlow Python ML Service",
    description="High-performance, asynchronous REST API for Machine Learning pipelines, models, and camera trajectory calculation.",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "service": "GimbalFlow Python ML Engine",
        "status": "healthy",
        "models_loaded": len(ml_engine.MODELS)
    }

@app.get("/api/v1/ml/models")
def list_models():
    return {
        "models": ml_engine.MODELS
    }

@app.post("/api/v1/ml/enhance-prompt", response_model=PromptEnhanceResponse)
def enhance_prompt(req: PromptEnhanceRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    result = ml_engine.enhance_prompt(req.prompt)
    return result

@app.post("/api/v1/ml/camera-trajectory", response_model=CameraTrajectoryResponse)
def compute_camera_trajectory(req: CameraTrajectoryRequest):
    result = ml_engine.generate_camera_trajectory(
        camera_type=req.camera_type,
        fov=req.fov,
        roll=req.roll,
        pitch=req.pitch,
        speed=req.speed
    )
    return result

@app.post("/api/v1/ml/generate", response_model=GenerationResponse)
def execute_generation(req: GenerationRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required for generation")
    
    result = ml_engine.execute_generation_pipeline(req.dict())
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
