const express = require('express');
const client = require('prom-client');

// Create a Registry which registers the metrics
const register = new client.Registry();
// Add a default label which is added to all metrics
register.setDefaultLabels({
  app: 'hello-world-node-app'
});
// Enable the collection of default metrics
client.collectDefaultMetrics({ register });

// Create a histogram metric for request timing
const httpRequestDurationMicroseconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'code'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10] // 0.1 to 10 seconds
});
register.registerMetric(httpRequestDurationMicroseconds);

const app = express();
const port = 3100;

// Middleware to track request duration
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const responseTime = Date.now() - start;
    httpRequestDurationMicroseconds
  .labels(req.method, req.path, res.statusCode)
  .observe(responseTime / 1000);
  });
  next();
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.setHeader('Content-Type', register.contentType);
  res.send(await register.metrics());
});

// Your main endpoint
app.get('/', (req, res) => {
  res.send('Hello World from Node.js!');
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});