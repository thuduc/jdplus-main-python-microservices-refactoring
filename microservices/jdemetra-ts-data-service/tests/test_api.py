"""API endpoint tests."""

import pytest
from httpx import AsyncClient
from uuid import UUID


class TestTimeSeriesAPI:
    """Test time series API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_timeseries(self, client: AsyncClient, sample_timeseries_data):
        """Test creating a time series."""
        response = await client.post(
            "/api/v1/timeseries/create",
            json=sample_timeseries_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert UUID(data["id"])  # Valid UUID
        assert data["name"] == "Test Series"
        assert data["values"] == sample_timeseries_data["values"]
        assert data["frequency"] == "M"
        assert data["metadata"]["source"] == "test"
    
    @pytest.mark.asyncio
    async def test_get_timeseries(self, client: AsyncClient, sample_timeseries_data):
        """Test retrieving a time series."""
        # Create first
        create_response = await client.post(
            "/api/v1/timeseries/create",
            json=sample_timeseries_data
        )
        ts_id = create_response.json()["id"]
        
        # Get
        response = await client.get(f"/api/v1/timeseries/{ts_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == ts_id
        assert data["values"] == sample_timeseries_data["values"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_timeseries(self, client: AsyncClient):
        """Test getting non-existent time series."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/timeseries/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_transform_timeseries(self, client: AsyncClient, sample_timeseries_data):
        """Test transforming a time series."""
        # Create first
        create_response = await client.post(
            "/api/v1/timeseries/create",
            json=sample_timeseries_data
        )
        ts_id = create_response.json()["id"]
        
        # Apply log transformation
        transform_request = {
            "operation": "log",
            "parameters": {}
        }
        response = await client.put(
            f"/api/v1/timeseries/{ts_id}/transform",
            json=transform_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Values should be transformed
        assert data["values"][0] != sample_timeseries_data["values"][0]
        assert data["metadata"]["transformation"] == "log"
    
    @pytest.mark.asyncio
    async def test_delete_timeseries(self, client: AsyncClient, sample_timeseries_data):
        """Test deleting a time series."""
        # Create first
        create_response = await client.post(
            "/api/v1/timeseries/create",
            json=sample_timeseries_data
        )
        ts_id = create_response.json()["id"]
        
        # Delete
        response = await client.delete(f"/api/v1/timeseries/{ts_id}")
        assert response.status_code == 200
        
        # Verify it's gone
        get_response = await client.get(f"/api/v1/timeseries/{ts_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_validate_timeseries(self, client: AsyncClient):
        """Test time series validation."""
        # Valid series
        valid_data = {
            "values": [1.0, 2.0, 3.0],
            "start_period": {"year": 2023, "period": 1, "frequency": "Q"},
            "frequency": "Q"
        }
        response = await client.post("/api/v1/timeseries/validate", json=valid_data)
        assert response.status_code == 200
        assert response.json()["valid"] is True
        
        # Invalid series (empty)
        invalid_data = {
            "values": [],
            "start_period": {"year": 2023, "period": 1, "frequency": "Q"},
            "frequency": "Q"
        }
        response = await client.post("/api/v1/timeseries/validate", json=invalid_data)
        assert response.status_code == 200
        assert response.json()["valid"] is False
        assert "empty" in response.json()["errors"][0]
    
    @pytest.mark.asyncio
    async def test_list_timeseries(self, client: AsyncClient, sample_timeseries_data):
        """Test listing time series."""
        # Create a few series
        for i in range(3):
            data = sample_timeseries_data.copy()
            data["name"] = f"Test Series {i}"
            await client.post("/api/v1/timeseries/create", json=data)
        
        # List all
        response = await client.get("/api/v1/timeseries")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 3
        assert len(data["series"]) >= 3
        assert data["page"] == 1
        
        # Test pagination
        response = await client.get("/api/v1/timeseries?page=1&page_size=2")
        data = response.json()
        assert len(data["series"]) <= 2
        
        # Test filtering
        response = await client.get("/api/v1/timeseries?frequency=M")
        data = response.json()
        assert all(s["frequency"] == "M" for s in data["series"])
    
    @pytest.mark.asyncio
    async def test_batch_create(self, client: AsyncClient):
        """Test batch creation of time series."""
        batch_request = {
            "series": [
                {
                    "values": [1.0, 2.0, 3.0],
                    "start_period": {"year": 2023, "period": 1, "frequency": "Q"},
                    "frequency": "Q",
                    "name": "Series 1"
                },
                {
                    "values": [4.0, 5.0, 6.0],
                    "start_period": {"year": 2023, "period": 2, "frequency": "Q"},
                    "frequency": "Q",
                    "name": "Series 2"
                }
            ]
        }
        
        response = await client.post("/api/v1/timeseries/batch", json=batch_request)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Series 1"
        assert data[1]["name"] == "Series 2"
    
    @pytest.mark.asyncio
    async def test_invalid_transformation(self, client: AsyncClient, sample_timeseries_data):
        """Test invalid transformation request."""
        # Create series
        create_response = await client.post(
            "/api/v1/timeseries/create",
            json=sample_timeseries_data
        )
        ts_id = create_response.json()["id"]
        
        # Invalid operation
        transform_request = {
            "operation": "invalid_op",
            "parameters": {}
        }
        response = await client.put(
            f"/api/v1/timeseries/{ts_id}/transform",
            json=transform_request
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_series_length_limit(self, client: AsyncClient):
        """Test series length validation."""
        from src.core.config import settings
        
        # Create series exceeding max length
        oversized_data = {
            "values": [1.0] * (settings.MAX_SERIES_LENGTH + 1),
            "start_period": {"year": 2023, "period": 1, "frequency": "Y"},
            "frequency": "Y"
        }
        
        response = await client.post("/api/v1/timeseries/create", json=oversized_data)
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]