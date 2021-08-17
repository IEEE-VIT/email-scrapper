# An item is like a temporary container (and we make use of an item or [temporary container] to organise the way in which we will store our data)

import scrapy


class CompanyItem(scrapy.Item):
    
    name = scrapy.Field()
    website = scrapy.Field()
    emails = scrapy.Field()
    source = scrapy.Field()
    
    
