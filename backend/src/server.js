import app from './app.js';
import { config } from './config/index.js';
import { connectMongo, connectRedis } from './config/db.js';

async function bootstrap() {
  console.log(`[System] Initializing AI-BOS Enterprise API Gateway...`);
  
  // 1. Connect to database layers
  await connectMongo();
  await connectRedis();

  // 2. Start Express Listener
  const server = app.listen(config.port, () => {
    console.log(`==========================================================`);
    console.log(`[Gateway] Express running at http://localhost:${config.port}`);
    console.log(`[Gateway] Mode: ${config.environment}`);
    console.log(`==========================================================`);
  });

  // Handle graceful shutdowns
  const shutdown = (signal) => {
    console.log(`\n[System] Received ${signal}. Terminating server processes...`);
    server.close(() => {
      console.log('[System] HTTP gateway terminated.');
      process.exit(0);
    });
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
}

bootstrap().catch(err => {
  console.error('[System] Bootstrapping failed:', err);
  process.exit(1);
});
