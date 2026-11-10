function compareKeys(a, b) {
  for (let index = 0; index < Math.min(a.length, b.length); index++) {
    const left = a[index];
    const right = b[index];
    const comparison = Array.isArray(left) ? compareKeys(left, right) : left < right ? -1 : left > right ? 1 : 0;
    if (comparison) return comparison;
  }
  return a.length - b.length;
}

function choicePriority(data, index, selected, variant) {
  const electives = selected.filter(([course]) => data.courses[course].fixed == null);
  const ratings = [5, 4, 3, 2, 1].map(rating => -electives.filter(([course]) => data.courses[course].rating === rating).length);
  const gap = continuity(data, index, selected).gap;
  const identity = selected.map(([course, option]) => [data.courses[course].id,
    data.terms[index].options[course][option].mini || 0, data.terms[index].options[course][option].label]);
  return variant === 1 ? [-selectedUnits(data, electives), gap, ratings, identity] : [ratings, gap, identity];
}

function enumerateTerm(data, index) {
  const term = data.terms[index];
  const candidates = data.courses.map((_, course) => course).filter(course =>
    data.courses[course].fixed === index + 1
    || (data.courses[course].fixed == null && term.options[course].length));
  candidates.sort((a, b) => Number(data.courses[a].fixed == null) - Number(data.courses[b].fixed == null)
    || compareKeys([data.courses[a].id], [data.courses[b].id]));
  const baseline = continuity(data, index, []).overlap;
  const choices = [];
  function visit(position, selected) {
    if (position === candidates.length) {
      choices.push([...selected].sort((a, b) => compareKeys([data.courses[a[0]].id], [data.courses[b[0]].id])));
      return;
    }
    const course = candidates[position];
    term.options[course].forEach((_, option) => {
      const next = [...selected, [course, option]];
      if (withinCapacity(data, index, next) && continuity(data, index, next).overlap === baseline) visit(position + 1, next);
    });
    if (data.courses[course].fixed == null) visit(position + 1, selected);
  }
  visit(0, []);
  if (!choices.length) {
    const fixed = candidates.filter(course => data.courses[course].fixed != null).map(course => data.courses[course].id);
    throw new Error(`Fixed course ${fixed.join(', ')} cannot be placed in semester ${index + 1}; check offerings, units, mini workload, and time conflicts.`);
  }
  const groupsByMask = new Map();
  const labels = choices.map((selected, choice) => {
    const mask = selected.reduce((used, [course]) => used | BigInt(data.courses[course].mask), 0n);
    const electives = selected.filter(([course]) => data.courses[course].fixed == null);
    if (!groupsByMask.has(mask)) groupsByMask.set(mask, {
      mask, label: electives.map(([course]) => data.courses[course].id).join(' + ') || 'No electives', choices: [],
    });
    groupsByMask.get(mask).choices.push(choice);
    return electives.map(([course, option]) => {
      const section = term.options[course][option];
      return `${data.courses[course].id} ${section.label || 'Section unknown'}${section.mini ? ' M' + section.mini : ''}`;
    }).join(' · ');
  });
  const priorities = [0, 1].map(variant => choices.map(choice => choicePriority(data, index, choice, variant)));
  const groups = [...groupsByMask.values()].map(group => ({...group, choices:
    priorities.map(keys => [...group.choices].sort((a, b) => compareKeys(keys[a], keys[b])))}));
  const orders = [0, 1].map(variant => groups.map((_, id) => id).sort((a, b) =>
    compareKeys(priorities[variant][groups[a].choices[variant][0]], priorities[variant][groups[b].choices[variant][0]])));
  return {choices, groups, orders, labels};
}

function countPaths(terms, required = 0n, excluded = 0n) {
  const memo = new Map();
  const suffix = Array(terms.length + 1).fill(0n);
  for (let index = terms.length - 1; index >= 0; index--) {
    suffix[index] = terms[index].groups.reduce((mask, group) => mask | group.mask, suffix[index + 1]);
  }
  function count(index, used) {
    if ((used & excluded) || (required & ~(used | suffix[index]))) return 0n;
    if (index === terms.length) return (required & ~used) ? 0n : 1n;
    const key = `${index}:${used}`;
    if (memo.has(key)) return memo.get(key);
    let total = 0n;
    for (const group of terms[index].groups) {
      if (!(used & group.mask)) total += BigInt(group.choices[0].length) * count(index + 1, used | group.mask);
    }
    memo.set(key, total);
    return total;
  }
  return {total: count(0, 0n), memo};
}
