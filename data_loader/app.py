import requests
from pymongo import MongoClient
from py2neo import Graph, Node, NodeMatcher

# Connect to MongoDB
client = MongoClient('mongodb://mongo:27017/')
db = client['world']
collection = db['countries']

# Make request to REST Countries API
response = requests.get('https://restcountries.com/v3.1/all?fields=name,languages,gini,borders,timezones,unMember,capital,region,subregion,car,population,startOfWeek,capitalInfo,landlocked')
countries = response.json()

# Insert country data into MongoDB
for country in countries:
    collection.insert_one(country)

try:
    with open('alert.txt', 'w') as f:
        f.write('The code ran correctly.')
except Exception as e:
    with open('alert.txt', 'w') as f:
        f.write(f'The code did not run correctly. Error message: {str(e)}')

from cassandra.cluster import Cluster

# Connect to Cassandra
cassandra_host = 'cassandra'
cassandra_port = '9042'
cassandra_keyspace = 'world'
cassandra_table = 'countries'

# Connect to MongoDB
mongo_uri = 'mongodb://mongo:27017/'
mongo_database = 'world'
mongo_collection = 'countries'

# Create SparkSession
spark = SparkSession.builder.appName('MongoDB to Cassandra ETL').getOrCreate()

# Read data from MongoDB
mongo_df = spark.read.format('mongo').option('uri', mongo_uri).option('database', mongo_database).option('collection', mongo_collection).load()

# Transform data
cassandra_df = mongo_df.select(
    col('_id').cast('string').alias('id'),
    col('startOfWeek'),
    col('capitalInfo.latlng')[0].alias('capitalInfo_lat'),
    col('capitalInfo.latlng')[1].alias('capitalInfo_lng'),
    col('name.common').alias('name_common'),
    col('name.official').alias('name_official'),
    col('name.nativeName.eng.common').alias('name_nativeName'),
    col('unMember'),
    col('capital')[0].alias('capital').cast('string'),
    col('region'),
    col('subregion'),
    col('languages.eng').alias('languages'),
    col('landlocked'),
    col('borders').cast('string'),
    col('population'),
    col('gini.2018').alias('gini'),
    col('car.signs').cast('string').alias('car_signs'),
    col('car.side').alias('car_side'),
    col('timezones').cast('string')
)

# Write data to Cassandra
cassandra_df.write.format('org.apache.spark.sql.cassandra').options(
    **{
        "table": cassandra_table,
        "keyspace": cassandra_keyspace,
        "spark.cassandra.connection.host": cassandra_host,
        "spark.cassandra.connection.port": cassandra_port,
    }
).mode('append').save()


# Write to alerta.txt
try:
    with open('alerta.txt', 'w') as f:
        f.write('The code ran correctly.')
except Exception as e:
    with open('alerta.txt', 'w') as f:
        f.write(f'The code did not run correctly. Error message: {str(e)}')
from cassandra.auth import PlainTextAuthProvider
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


 # Conectar a Neo4j
 neo4j_uri = "neo4j://localhost:7687"
 neo4j_user = "neo4j"
 neo4j_password = "neo4j"
 graph = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))
 matcher = NodeMatcher(graph)

 # Creación de nodos de países
 for country in mongo_countries:
     # Manejar el caso en que 'capital' no exista
     capital = country['capital'][0] if 'capital' in country and country['capital'] else None

     country_node = Node("Country",
                         _id=country['_id'],
                         startOfWeek=country.get("startOfWeek"),
                         capitalInfo_lat=country['capitalInfo']['latlng'][0],
                         capitalInfo_lng=country['capitalInfo']['latlng'][1],
                         name_common=country['name']['common'],
                         name_official=country["name"]['official'],
                         name_nativeName=country["name"]['nativeName']['eng']['common'],
                         unMember=country.get("unMember"),
                         capital=capital,
                         region=country.get("region"),
                         subregion=country.get("subregion"),
                         languages=country.get("languages"),
                         landlocked=country.get("landlocked"),
                         population=country.get("population"),
                         gini=country.get("gini", {}).get("2018"),
                         car=country.get("car", {}).get("side"))

     graph.merge(country_node)

 # Write to alerta.txt
 try:
     with open('alerta.txt', 'w') as f:
         f.write('The code ran correctly.')
 except Exception as e:
     with open('alerta.txt', 'w') as f:
         f.write(f'The code did not run correctly. Error message: {str(e)}')
