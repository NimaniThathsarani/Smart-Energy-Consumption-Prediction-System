from fastapi import APIRouter, HTTPException, Query

from backend.services.cluster_service import get_cluster_data


router = APIRouter(
    tags=["Consumption Clustering"]
)


@router.get("/clusters")
def get_clusters(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Number of latest cluster records to return"
    )
):
    try:
        result = get_cluster_data(limit)

        return {
            "status": "success",
            "count": len(result["records"]),
            "data": result
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
            detail="An unexpected error occurred while loading cluster data"
        )