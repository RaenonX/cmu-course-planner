const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..', 'cmu_course_planner', 'degree_planner', 'templates');
for (const file of ['planner_constraints.js', 'planner_search.js', 'planner_what_if.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(root, file), 'utf8'), {filename: file});
}
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
try {
  const terms = ['first', 'filterCount', undefined].includes(input.operation)
    ? input.data.terms.map((_, index) => enumerateTerm(input.data, index)) : [];
  let result;
  if (input.operation === 'first') {
    let used = 0n;
    const choices = terms.map(term => {
      const group = term.orders[input.variant].map(id => term.groups[id]).find(group => !(group.mask & used));
      used |= group.mask;
      return term.choices[group.choices[input.variant][0]];
    });
    result = {choices};
  } else if (input.operation === 'filterCount') {
    const mask = ids => ids.reduce((value, id) => value | BigInt(input.data.courses[id].mask), 0n);
    result = {count: countPaths(terms, mask(input.required), mask(input.excluded)).total};
  } else if (input.operation === 'whatIf') {
    result = analyzeClientSwap(input.data, input.index, input.selected, input.course, input.remove);
  } else if (input.operation === 'routeWhatIf') {
    result = routeWhatIf(input.data, input.schedule.map(choice => ({choices: [choice]})), input.schedule.map(() => 0));
  } else {
    result = {choices: terms.map(term => term.choices), count: countPaths(terms).total};
  }
  process.stdout.write(JSON.stringify(result, (_, value) => typeof value === 'bigint' ? String(value) : value));
} catch (error) {
  process.stdout.write(JSON.stringify({error: error.message}));
}
