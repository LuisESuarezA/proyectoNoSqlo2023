from pymongo import MongoClient
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Connect to MongoDB
mongo_client = MongoClient('mongodb://mongo:27017/')
mongo_db = mongo_client['world']
mongo_collection = mongo_db['countries']

# Connect to Cassandra
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
cassandra_cluster = Cluster(['cassandra'], auth_provider=auth_provider)
cassandra_session = cassandra_cluster.connect()
cassandra_session.set_keyspace('world')

# Prepare a Cassandra statement
cassandra_stmt = cassandra_session.prepare("""
    INSERT INTO countries (id, startOfWeek, capitalInfo_lat, capitalInfo_lng, name_common, name_official, name_nativeName, unMember, capital, region, subregion, languages, landlocked, borders, population, gini, car_signs, car_side, timezones)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""")

# Read data from MongoDB and write it to Cassandra
for doc in mongo_collection.find():
    cassandra_session.execute(cassandra_stmt, (
        str(doc['_id']),
        doc['startOfWeek'],
        doc['capitalInfo']['latlng'][0],
        doc['capitalInfo']['latlng'][1],
        doc['name']['common'],
        doc['name']['official'],
        doc['name']['nativeName']['eng']['common'],
        doc['unMember'],
        doc['capital'][0] if doc['capital'] else None,
        doc['region'],
        doc['subregion'],
        doc['languages']['eng'],
        doc['landlocked'],
        ', '.join(doc['borders']),
        doc['population'],
        doc['gini']['2018'],
        ', '.join(doc['car']['signs']),
        doc['car']['side'],
        ', '.join(doc['timezones'])
    ))

# Write to alerta.txt
try:
    with open('alerta.txt', 'w') as f:
        f.write('The code ran correctly.')
except Exception as e:
    with open('alerta.txt', 'w') as f:
        f.write(f'The code did not run correctly. Error message: {str(e)}')

