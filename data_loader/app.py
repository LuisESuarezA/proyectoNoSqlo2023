import requests
from pymongo import MongoClient
from py2neo import Graph, Node, NodeMatcher
from neo4j import GraphDatabase

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

def add_country(tx, name, population):
    query = (
        "CREATE (c:Country {name: $name, population: $population}) "
    )
    tx.run(query, name=name, population=population)

def add_region(tx, region_name):
    query = (
        "MERGE (r:Region {name: $name}) "
    )
    tx.run(query, name=region_name)

def add_subregion(tx, subregion_name):
    query = (
        "MERGE (s:Subregion {name: $name}) "
    )
    tx.run(query, name=subregion_name)

neo4j_uri = "neo4j://neo4j:7687"
neo4j_user = "neo4j"
neo4j_password = "neoneoneo"
driver = GraphDatabase.driver(neo4j_uri, auth= (neo4j_user, neo4j_password))
session = driver.session()


# Obtener datos de MongoDB
countries_data = collection.find()

# Transferir datos a Neo4j
for country_data in countries_data:
    # Crear nodo de país
    country_name = country_data.get('name').get('common')
    population = country_data.get('population')
    session.execute_write(add_country, name=country_name, population=population)

    # Crear nodo de región
    region_name = country_data.get('region')
    if region_name:
        session.execute_write(add_region, region_name)

        # Relacionar país con región
        session.run("MATCH (c:Country {name: $country_name}), (r:Region {name: $region_name}) "
                    "MERGE (c)-[:IN_REGION]->(r)",
                    country_name=country_name, region_name=region_name)

    # Crear nodo de subregión
    subregion_name = country_data.get('subregion')
    if subregion_name:
        add_subregion(session, subregion_name)

        # Relacionar país con subregión
        session.run("MATCH (c:Country {name: $country_name}), (s:Subregion {name: $subregion_name}) "
                    "MERGE (c)-[:IN_SUBREGION]->(s)",
                    country_name=country_name, subregion_name=subregion_name)
        session.run("MATCH (s:Subregion {name: $subregion_name}), (r:Region {name: $region_name}) "
                    "MERGE (s)-[:PART_OF]->(r)",
                    subregion_name=subregion_name, region_name=region_name)

# Write to alerta.txt
try:
    with open('alerta.txt', 'w') as f:
        f.write('The code ran correctly.')
except Exception as e:
    with open('alerta.txt', 'w') as f:
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


 
