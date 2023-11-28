# proyectoNoSqlo2023
A partir de la API de REST Countries hacemos una conexión a través de python con una base de datos MongoDB. Posteriormente, hacemos un ETL que cargue la base de datos procesada una base de datos estilo grafo (Neo4j). Por último, cargamos la base de datos a Cassandra y hacemos 3 consultas para cada base. 

Integrantes:
- Karen Arteaga Mendoza
- Luis E. Suarez
- Sebastián

## Instrucciones para la insatalación de contenedores y carga de datos

Por medio de **docker-compose** generamos cuatro contenedores. Los servicios se definen en el archivo `docker-compose.yaml` que se ejecutan en un ambiente aislado. Cuando se creen los contenedores se ejecutará de manera automática el archivo `app.py`. Este archivo hace las conexiones a Mongodb, Neo4j y Cassandra, y llena las bases con los datos.

1. En la terminal ejecuta el siguiente comando. Asegúrate de tener encendido Docker. 
```shell
docker-compose up --build -d
```
No te preocupes si la ejecución no termina, esta seguirá activa mientras haya conexión a los servicios.

2. Para probar las consultas es necesario iniciar cada uno de los servicios.

Para Mongodb ejecutar los siguientes comandos en una nueva terminal:
  ```shell
  docker start mongo
  ```

  ```shell
  docker exec -it mongo mongosh
  ```

  ```shell
  use world
  ```
  
Para Neo4j ejecutar los siguientes comandos en una nueva terminal (tambien puedes acceder al link http://localhost:7474):
  ```shell
  docker start neo4jdb
  ```

  ```shell
  docker exec -it neo4jdb cypher-shell
  ```
  
  
3. Ahora ya puedes copiar y pegar las consultas en cada servicio  

## Queries de Mongodb
```js

```

```js

```

```js

```

## Queries de Neo4j
Consulta para encontrar países que comparten fronteras y tienen un índice de Gini similar:
```cypher
  MATCH (c1:Country)-[:BORDERS]->(c2:Country)
  WHERE abs(c1.gini - c2.gini) < 5
  RETURN c1.name AS Country1, c2.name AS Country2, c1.gini AS GiniCountry1, c2.gini AS GiniCountry2;
```

Consulta para obtener las subregiones con la mayor cantidad de idiomas distintos:
```cypher
  MATCH (s:Subregion)-[:PART_OF]->(r:Region)-[:CONTAINS]->(c:Country)
  WITH s, COLLECT(DISTINCT c.languages) AS countryLanguages
  WITH s, REDUCE(s1 = [], lang IN countryLanguages | s1 + lang) AS allLanguages
  RETURN s.name AS Subregion, SIZE(allLanguages) AS DistinctLanguagesCount
  ORDER BY DistinctLanguagesCount DESC
  LIMIT 5;
```

Consulta para encontrar la capital con la mayor población en cada región:
```cypher
  MATCH (r:Region)-[:CONTAINS]->(c:Country)-[:HAS_CAPITAL]->(capital:CapitalInfo)
  WITH r, capital, MAX(c.population) AS maxPopulation
  WHERE c.population = maxPopulation
  RETURN r.name AS Region, capital.name AS Capital, maxPopulation AS Population;
```
## Queries de Cassandra
