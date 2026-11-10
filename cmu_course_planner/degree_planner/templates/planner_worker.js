let plannerData;
let plannerTerms;
self.addEventListener('message', event => {
  const {id, type, payload} = event.data;
  try {
    let result;
    if (type === 'initialize') {
      plannerData = payload;
      plannerTerms = payload.terms.map((_, index) => enumerateTerm(payload, index));
      result = {terms: plannerTerms};
    } else if (type === 'count') {
      result = countPaths(plannerTerms, payload.required, payload.excluded);
    } else if (type === 'route') {
      result = routeWhatIf(plannerData, plannerTerms, payload.choices);
    } else {
      throw new Error(`Unknown planner request: ${type}`);
    }
    self.postMessage({id, result});
  } catch (error) {
    self.postMessage({id, error: error.message});
  }
});
