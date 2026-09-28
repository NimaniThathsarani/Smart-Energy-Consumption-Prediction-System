from fastapi import APIRouter, HTTPException, Query

from backend.services.anomaly_service import get_anomaly_data


router = APIRouter(
    tags=["Anomaly Detection"]
)


@router.get("/anomalies")
def get_anomalies(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Number of latest anomaly records to return"
    )
):
    try:
        data = get_anomaly_data(limit)

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
            detail="An unexpected error occurred while loading anomaly data"
        )