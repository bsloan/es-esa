score = _score;
concepts = _source.concepts;

for (concept in concepts) {
  queryConcept = queryConcepts.find { it.id == concept.id };
  if (queryConcept) {
    score += (queryConcept.score * concept.score);
  }
};

return score;
