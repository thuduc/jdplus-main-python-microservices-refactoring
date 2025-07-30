"""Model storage and retrieval."""

import json
import pickle
from uuid import UUID, uuid4
from typing import Optional

from jdemetra_common.models import ArimaModel, TsData


class ModelStorage:
    """Handle model storage in Redis."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours
    
    async def save_model(self, model: ArimaModel, ts_data: TsData) -> UUID:
        """Save model and return ID."""
        model_id = uuid4()
        
        # Serialize model and data
        model_data = {
            "model": model.to_dict(),
            "ts_data": ts_data.to_dict()
        }
        
        # Store in Redis
        key = f"arima_model:{model_id}"
        await self.redis.setex(
            key,
            self.ttl,
            pickle.dumps(model_data)
        )
        
        return model_id
    
    async def get_model(self, model_id: UUID) -> Optional[tuple[ArimaModel, TsData]]:
        """Retrieve model by ID."""
        key = f"arima_model:{model_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        # Deserialize
        model_data = pickle.loads(data)
        model = ArimaModel.from_dict(model_data["model"])
        ts_data = TsData.from_dict(model_data["ts_data"])
        
        return model, ts_data
    
    async def delete_model(self, model_id: UUID) -> bool:
        """Delete model."""
        key = f"arima_model:{model_id}"
        result = await self.redis.delete(key)
        return result > 0