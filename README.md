# proyectoNoSqlo2023


## Queries de Neo4j
Consulta para encontrar países que comparten fronteras y tienen un índice de Gini similar:
#+begin_src cypher
MATCH (c1:Country)-[:BORDERS]->(c2:Country)
WHERE abs(c1.gini - c2.gini) < 5
RETURN c1.name AS Country1, c2.name AS Country2, c1.gini AS GiniCountry1, c2.gini AS GiniCountry2;
#+end_src

Consulta para obtener las subregiones con la mayor cantidad de idiomas distintos:
#+begin_src cypher
MATCH (s:Subregion)-[:PART_OF]->(r:Region)-[:CONTAINS]->(c:Country)
WITH s, COLLECT(DISTINCT c.languages) AS countryLanguages
WITH s, REDUCE(s1 = [], lang IN countryLanguages | s1 + lang) AS allLanguages
RETURN s.name AS Subregion, SIZE(allLanguages) AS DistinctLanguagesCount
ORDER BY DistinctLanguagesCount DESC
LIMIT 5;
#+end_src

Consulta para encontrar la capital con la mayor población en cada región
#+begin_src cypher
MATCH (r:Region)-[:CONTAINS]->(c:Country)-[:HAS_CAPITAL]->(capital:CapitalInfo)
WITH r, capital, MAX(c.population) AS maxPopulation
WHERE c.population = maxPopulation
RETURN r.name AS Region, capital.name AS Capital, maxPopulation AS Population;
#+end_src
