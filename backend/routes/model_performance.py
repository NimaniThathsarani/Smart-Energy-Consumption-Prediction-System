from fastapi import APIRouter, HTTPException

from backend.services.model_performance_service import get_model_performance


router = APIRouter(
    tags=["Model Performance"]
)


@router.get("/model-performance")
def model_performance():
    try:
        data = get_model_performance()

        return {
            "status": "success",
            "count": len(data),
            "data": data
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while loading model performance data"
        )