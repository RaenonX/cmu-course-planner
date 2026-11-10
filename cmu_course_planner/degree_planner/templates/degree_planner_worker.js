<script>
const pathSource = document.getElementById('degree-path-data');
const degreePaths = JSON.parse(pathSource.textContent);
pathSource.remove();
degreePaths.courses.forEach(course => { course.mask = BigInt(course.mask); });
const workerSource = document.getElementById('degree-worker-source');
const workerUrl = URL.createObjectURL(new Blob([workerSource.textContent], {type: 'text/javascript'}));
const plannerWorker = new Worker(workerUrl);
URL.revokeObjectURL(workerUrl);
workerSource.remove();
let requestId = 0;
const requests = new Map();
plannerWorker.addEventListener('message', event => {
  const pending = requests.get(event.data.id);
  if (!pending) return;
  requests.delete(event.data.id);
  if (event.data.error) pending.reject(new Error(event.data.error));
  else pending.resolve(event.data.result);
});
plannerWorker.addEventListener('error', event => {
  for (const pending of requests.values()) pending.reject(new Error(event.message || 'The planner worker could not start.'));
  requests.clear();
});
function workerRequest(type, payload) {
  return new Promise((resolve, reject) => {
    const id = ++requestId;
    requests.set(id, {resolve, reject});
    plannerWorker.postMessage({id, type, payload});
  });
}
const plannerReady = workerRequest('initialize', degreePaths).then(result => {
  result.terms.forEach((term, index) => Object.assign(degreePaths.terms[index], term));
});
</script>
