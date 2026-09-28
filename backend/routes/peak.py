from fastapi import APIRouter, HTTPException, Query

from backend.services.peak_service import get_peak_data


router = APIRouter(
    tags=["Peak Prediction"]
)


@router.get("/peak")
def get_peak(
    limit: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of latest peak prediction records to return"
    )
):
    try:
        data = get_peak_data(limit)

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
            detail="An unexpected error occurred while loading peak prediction data"
        )