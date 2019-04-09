from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()



#Build test category 1
category1 = Category(name = "Test Category 1", user_id = 1)

session.add(category1)
session.commit()


item1 = Item(name = "Test Item 1", description = "This is a test item for category 1", category = category1, user_id = 1)

session.add(item1)
session.commit()

item2 = Item(name = "Test Item 2", description = "This is a test item for category 1", category = category1, user_id = 1)

session.add(item2)
session.commit()

item3 = Item(name = "Test Item 3", description = "This is a test item for category 1", category = category1, user_id = 1)

session.add(item3)
session.commit()


#Build test category 2
category2 = Category(name = "Test Category 2", user_id = 1)

session.add(category2)
session.commit()


item1 = Item(name = "Test Item 1", description = "This is a test item for category 2", category = category2, user_id = 1)

session.add(item1)
session.commit()

item2 = Item(name = "Test Item 2", description = "This is a test item for category 2", category = category2, user_id = 1)

session.add(item2)
session.commit()

item3 = Item(name = "Test Item 3", description = "This is a test item for category 2", category = category2, user_id = 1)

session.add(item3)
session.commit()


#Build test category 2
category3 = Category(name = "Test Category 3", user_id = 2)

session.add(category3)
session.commit()


item1 = Item(name = "Test Item 1", description = "This is a test item for category 3", category = category3, user_id = 2)

session.add(item1)
session.commit()

item2 = Item(name = "Test Item 2", description = "This is a test item for category 3", category = category3, user_id = 2)

session.add(item2)
session.commit()

item3 = Item(name = "Test Item 3", description = "This is a test item for category 3", category = category3, user_id = 2)

session.add(item3)
session.commit()

print "ADDED NEW ITEMS TO DATABASE"
