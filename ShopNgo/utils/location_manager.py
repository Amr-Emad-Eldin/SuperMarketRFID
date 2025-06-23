from bson import ObjectId

def init_location_manager(db):
    """Initialize location manager with database connection"""
    class LocationManager:
        def __init__(self, db):
            self.db = db
            self.locations_collection = db.locations

        def get_all_locations(self):
            """Get all store locations"""
            return list(self.locations_collection.find())

        def get_location(self, location_id):
            """Get specific store location"""
            return self.locations_collection.find_one({'_id': ObjectId(location_id)})

        def add_location(self, location_data):
            """Add new store location"""
            result = self.locations_collection.insert_one(location_data)
            return str(result.inserted_id)

        def update_location(self, location_id, location_data):
            """Update store location"""
            result = self.locations_collection.update_one(
                {'_id': ObjectId(location_id)},
                {'$set': location_data}
            )
            return result.modified_count > 0

        def delete_location(self, location_id):
            """Delete store location"""
            result = self.locations_collection.delete_one({'_id': ObjectId(location_id)})
            return result.deleted_count > 0

        def get_nearby_locations(self, latitude, longitude, max_distance=5000):
            """Get nearby store locations within max_distance meters"""
            return list(self.locations_collection.find({
                'location': {
                    '$near': {
                        '$geometry': {
                            'type': 'Point',
                            'coordinates': [longitude, latitude]
                        },
                        '$maxDistance': max_distance
                    }
                }
            }))

    return LocationManager(db) 