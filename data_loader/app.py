import requests
from pymongo import MongoClient
from py2neo import Graph, Node, NodeMatcher
from neo4j import GraphDatabase
import pandas as pd
from cassandra.cluster import Cluster

# Nos conectamos a MongoDB
client = MongoClient('mongodb://mongo:27017/')
db = client['world']
collection = db['countries']

# hacemos nuestro reques al API
response = requests.get('https://restcountries.com/v3.1/all?fields=name,languages,gini,borders,timezones,unMember,capital,region,subregion,car,population,startOfWeek,capitalInfo,landlocked')
countries = response.json()

# Insertamos los datos en MongoDB
for country in countries:
    collection.insert_one(country)

# Creamos una función para crear nodos de países
def add_country(tx, name, population):
    query = (
        "MERGE (c:Country {name: $name, population: $population}) "
    )
    tx.run(query, name=name, population=population)

# Creamos una función para crear nodos de regiones
def add_region(tx, region_name):
    query = (
        "MERGE (r:Region {name: $name}) "
    )
    tx.run(query, name=region_name)

# Creamos una función para crear nodos de subregiones
def add_subregion(tx, subregion_name):
    query = (
        "MERGE (s:Subregion {name: $name}) "
    )
    tx.run(query, name=subregion_name)

# Conectamos a Neo4j
neo4j_uri = "neo4j://neo4j:7687"
neo4j_user = "neo4j"
neo4j_password = "neoneoneo"
driver = GraphDatabase.driver(neo4j_uri, auth= (neo4j_user, neo4j_password))
session = driver.session()


# Obtenemos los datos datos de nuestro MongoDB
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


# Realizar la solicitud a la API
url = 'https://restcountries.com/v3.1/all?fields=name,languages,gini,borders,timezones,unMember,capital,region,subregion,car,population,startOfWeek,capitalInfo,landlocked'
response = requests.get(url)

# Verificar si la solicitud fue exitosa (código de estado 200)
if response.status_code == 200:
    # Convertir la respuesta a formato JSON
    data = response.json()

    # Convertir JSON a un DataFrame de pandas
    df = pd.json_normalize(data)

    # Guardar el DataFrame como un archivo CSV
    df.to_csv('countries_data.csv', index=False)

    print("¡Datos guardados exitosamente como 'countries_data.csv'!")
else:
    print("Error al obtener los datos de la API.")


# Crear una conexión con el clúster de Cassandra
KEYSPACE = "world"
contact_points = ['cassandra']
cluster = Cluster(contact_points,port=9042)
session = cluster.connect()

# Crear un keyspace si no existe
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS %s 
    WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }
""" % KEYSPACE)

# Usar el keyspace
session.set_keyspace(KEYSPACE)

# Cargar el archivo CSV en un DataFrame
df_countries = pd.read_csv('countries_data.csv')

# Columnas con las que trabajaremos
relevant_columns = [
    'startOfWeek', 'unMember', 'capital', 'region', 'subregion',
    'landlocked', 'borders', 'population', 'timezones'
]

from ast import literal_eval

# Lee el archivo CSV
df = df_countries[relevant_columns]

# Limpiar un poco los datos

df['capital'] = df['capital'].apply(literal_eval)
df['borders'] = df['borders'].apply(literal_eval)
df['timezones'] = df['timezones'].apply(literal_eval)

df['subregion'].fillna('', inplace=True)

session.execute("""
    CREATE TABLE IF NOT EXISTS countries (
        startOfWeek text,
        unMember boolean,
        capital list<text>,
        region text,
        subregion text,
        landlocked boolean,
        borders list<text>,
        population bigint,
        timezones list<text>,
        PRIMARY KEY (startOfWeek, region, population)
    )
""")

# Suponiendo que 'df' es tu DataFrame y ya tienes la conexión establecida a tu cluster de Cassandra en 'session'

for _, row in df.iterrows():
    query = """
        INSERT INTO countries (
            startOfWeek, unMember, capital, region, subregion, landlocked, borders, population, timezones
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    # Estructura explícitamente la tupla de inserción para coincidir con los marcadores de posición en la consulta
    insert_values = (
        row['startOfWeek'], row['unMember'], row['capital'], row['region'], row['subregion'],
        row['landlocked'], row['borders'], row['population'], row['timezones']
    )
    
    session.execute(query, insert_values)

# Realiza una consulta para verificar que los datos se hayan insertado correctamente
result = session.execute("SELECT * FROM countries LIMIT 5")
for row in result:
    print(row)

# 1. Países en África con poblaciones superiores a 50 millones

result = session.execute("SELECT * FROM countries WHERE region = 'Africa' AND population > 50000000 ALLOW FILTERING")
for row in result:
    print(row)


# 2. Países en Asia que tienen fronteras con más de cinco países

result = session.execute("SELECT * FROM countries WHERE region = 'Asia' ALLOW FILTERING")
filtered_rows = [row for row in result if row.borders and len(row.borders) > 5]
for row in filtered_rows:
    print(row)

# 3. Países que tienen una capital con más de 6 letras y están en una región de África sin litoral

result = session.execute("SELECT * FROM countries WHERE region = 'Africa' AND landlocked = True ALLOW FILTERING")
filtered_rows = [row for row in result if len(row.capital[0]) > 6]
for row in filtered_rows:
    print(row)
