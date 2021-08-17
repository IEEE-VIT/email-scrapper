from itemadapter import ItemAdapter

from pymongo import MongoClient


class SponsorshipPipeline:

    def __init__(self):
        connection = MongoClient('mongodb://localhost:27017/')
        db = connection.get_database('sponsorship')
        self.collection = db.test_collection

    def process_item(self, item, spider):
        self.collection.insert_one({"name": item["name"], "website": item["website"], "emails": item["emails"], "source": item["source"]})
        return item
