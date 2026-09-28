from fastapi import APIRouter, HTTPException, Query

from backend.services.forecast_service import get_forecast_data


router = APIRouter(
    tags=["Forecast"]
)


@router.get("/forecast")
def get_forecast(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Number of latest forecast records to return"
    )
):
    try:
        data = get_forecast_data(limit)

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
            detail="An unexpected error occurred while loading forecast data"
        )