from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.forecast import router as forecast_router
from backend.routes.peak import router as peak_router
from backend.routes.anomalies import router as anomalies_router
from backend.routes.clusters import router as clusters_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.model_performance import router as model_performance_router


app = FastAPI(
    title="Smart Energy Consumption Prediction API",
    description="Backend API for the Smart Energy Consumption Prediction System",
    version="1.0.0"
)


# Allow the local dashboard/frontend to communicate with the backend API
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(forecast_router)
app.include_router(peak_router)
app.include_router(anomalies_router)
app.include_router(clusters_router)
app.include_router(recommendations_router)
app.include_router(model_performance_router)


@app.get("/")
def root():
    return {
        "status": "success",
        "message": "Smart Energy Consumption Prediction API is running"
    }