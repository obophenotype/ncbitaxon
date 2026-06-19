PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
  ?entity rdfs:label ?label .
  ?entity rdfs:subClassOf ?parent .
}
WHERE {
  {
    ?entity rdfs:label ?label .
  }
  UNION
  {
    ?entity rdfs:subClassOf ?parent .
  }
}
