# proyectoNoSqlo2023
A partir de la API de REST Countries hacemos una conexión a través de python con una base de datos MongoDB. Posteriormente, hacemos un ETL que cargue la base de datos procesada una base de datos estilo grafo (Neo4j). Por último, cargamos la base de datos a Cassandra y hacemos 3 consultas para cada base. 
Un resumen de los datos se puede consultar en la [Presentación del proyecto](https://github.com/LuisESuarezA/proyectoNoSqlo2023/blob/master/Presentacion.pdf)

Integrantes:
- Karen Arteaga Mendoza
- Luis Eduardo Suarez Arroyo
- Sebastián Cordoba

## Instrucciones para la insatalación de contenedores y carga de datos

Por medio de **docker-compose** generamos cuatro contenedores. Los servicios se definen en el archivo `docker-compose.yaml` que se ejecutan en un ambiente aislado. Cuando se creen los contenedores se ejecutará de manera automática el archivo `app.py`. Este archivo hace las conexiones a Mongodb, Neo4j y Cassandra, y llena las bases con los datos.

1. En la terminal ejecuta el siguiente comando. Asegúrate de tener encendido Docker.
```shell
docker-compose down --volumes && docker-compose up --build -d
```
No te preocupes si la ejecución no termina, esta seguirá activa mientras haya conexión a los servicios.

2. Para probar las consultas es necesario iniciar cada uno de los servicios.

Para Mongodb ejecutar los siguientes comandos en una nueva terminal:

  ```shell
  docker exec -it mongo mongosh
  ```

  ```shell
  use world
  ```
  
Para Neo4j ejecutar los siguientes comandos en una nueva terminal (tambien puedes acceder al link http://localhost:7474):
Si se ejecuta desde el navegador se usa el usuario neo4j con la contraseña neoneoneo.
  ```shell
  docker exec -it neo4jdb cypher-shell
  ```
  
  
3. Ahora ya puedes copiar y pegar las consultas en cada servicio  

## Queries de Mongodb
En el caso de Mongo vamos a aprovechar su flexibilidad para hacer queries que nos dejen explotar la estructura de diccionarios anidados y de listas que pueden tener los datos en la base. Mongo es perfecto para explorar este tipo de estructuras con diccionarios y listas.

Con esta consulta se obtienen las subregiones donde hay más países en los que se maneja a la derecha (como ingleses).
Además, agregamos otra consulta para las subregiones.
```js
db.countries.aggregate([
  {
    $match: {
      'car.side': 'left'
    }
  },
  {
    $group: {
      _id: { subregion: '$subregion', region: '$region' },
      count: { $sum: 1 }
    }
  },
  {
    $sort: { count: -1 }
  },
  {
    $limit: 1
  }
]);

db.countries.aggregate([
  {
    $match: {
      'car.side': 'left'
    }
  },
  {
    $group: {
      _id: { subregion: '$subregion', region: '$region' },
      count: { $sum: 1 }
    }
  },
  {
    $sort: { count: 1 }
  },
  {
    $limit: 1
  }
]);
```
Esta consulta nos regresa las subregiones ordenadas por cuales hablan la mayor variedad de idiomas distintos. 
Además,agregamos otra consulta similar para obtener los mismos resultados para los continentes.
```js
db.countries.aggregate([
  {
    $unwind: '$languages'
  },
  {
    $group: {
      _id: '$subregion',
      total: { $addToSet: '$languages' }
    }
  },
  {
    $project: {
      _id: 1,
      total: { $size: '$total' }
    }
  },
  {
    $sort: {total: -1}
  }
]);

db.countries.aggregate([
  {
    $unwind: '$languages'
  },
  {
    $group: {
      _id: '$region',
      total: { $addToSet: '$languages' }
    }
  },
  {
    $project: {
      _id: 1,
      total: { $size: '$total' }
    }
  },
  {
    $sort: {total: -1}
  }
]);
```
Este último query es para ver cuál es el día de la semana menos popular para iniciar la semana.
Fuera de broma, el de verdad es analizar la subregión y región con la mayor cantidad de países fuera de la ONU.
```js
db.countries.aggregate([
  {
    $group: {
      _id: '$startOfWeek',
      conteo: { $sum: 1 }
    }
  },
  {
    $sort: { conteo: 1 }
  }
]);

db.countries.aggregate([
  {
    $match: {
      'unMember': false
    }
  },
  {
    $group: {
      _id: { subregion: '$subregion', region: '$region' },
      count: { $sum: 1 }
    }
  },
  {
    $sort: { count: -1 }
  }
]);
```

## Queries de Neo4j
Usamos Neo4j para obtener resultados sobre nodos que tienen una relación. En este caso en específico usamos el código para trabajar en las relaciones entre los países, continentes y subregiones del continente. De esta forma conseguimos queries que nos dirigen al análisis de relaciones entre nodos.

Consulta para obtener las regiones con la mayor cantidad de poblacion y de países, en orden descendente:
```cypher
  MATCH (c:Country)-[:IN_REGION]->(s:Region)
  WITH s, COUNT(c) AS numberOfCountries, SUM(c.population) AS totalPopulation
  RETURN s.name AS Subregion, numberOfCountries AS NumberOfCountries, totalPopulation AS TotalPopulation
  ORDER BY totalPopulation DESC, numberOfCountries DESC;
```
Consulta para encontrar los países con la mayor población en cada subregión:
```cypher
  MATCH (c:Country)-[:IN_SUBREGION]->(s:Subregion)
  WITH s, c, max(c.population) AS MaxPopulation
  ORDER BY MaxPopulation DESC
  WITH s, COLLECT({name: c.name, population: MaxPopulation}) AS countries
  WITH s, countries[0] AS topCountry
  RETURN s.name AS Subregion, topCountry.name AS Country, topCountry.population AS Population
```
Número de países por región en orden descendente
```cypher
  MATCH (c:Country)-[:IN_SUBREGION]->(s:Subregion)
  WITH s, COUNT(c) AS numberOfCountries
  RETURN s.name AS Subregion, numberOfCountries AS NumberOfCountries
  ORDER BY numberOfCountries DESC;
```
## Queries de Cassandra

Primero debemos iniciar Cassandra con 
```shell
  docker exec -it cassandra cqlsh
```
Ahora usamos nuestro keyspace
```cql
  use world
```
En los queries de Cassandra realizaremos queries que usen la función de filtros de cql sobre columnas específicas para generar queries que indagan más sobre columnas en específico. Es importante denotar que se usaron metodos de filtrado en la parte del código de python para obtener los mejores resultados. En este caso, obtendremos las columnas donde aplicamos nuestros filtros.

Países en África con poblaciones superiores a 50 millones
```cql
SELECT * FROM countries WHERE region = 'Africa' AND population > 50000000 ALLOW FILTERING
```

Países en Asia que tienen fronteras con más de cinco países
```cql
SELECT * FROM countries WHERE region = 'Asia' ALLOW FILTERING
```

Países que tienen una capital con más de 6 letras y están en una región de África sin litoral
```cql
SELECT * FROM countries WHERE region = 'Africa' AND landlocked = True ALLOW FILTERING
```

## Resultados

Los resultados de las consultas se pueden consultar en la [Presentación del proyecto](https://github.com/LuisESuarezA/proyectoNoSqlo2023/blob/master/Presentacion.pdf)
