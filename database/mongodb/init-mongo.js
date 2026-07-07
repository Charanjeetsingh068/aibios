// AI-BOS Enterprise NoSQL database initialization script
// Target: MongoDB

db = db.getSiblingDB('aibios_nosql');

// Create collections
db.createCollection('agent_runs');
db.createCollection('telemetry_logs');

// Create Indexes on agent_runs
db.agent_runs.createIndex(
  { "run_id": 1 }, 
  { unique: true, name: "idx_unique_run_id" }
);
db.agent_runs.createIndex(
  { "user_id": 1, "created_at": -1 }, 
  { name: "idx_user_runs" }
);
db.agent_runs.createIndex(
  { "status": 1 }, 
  { name: "idx_run_status" }
);

// Create Indexes on telemetry_logs
db.telemetry_logs.createIndex(
  { "timestamp": -1 }, 
  { name: "idx_telemetry_time" }
);
db.telemetry_logs.createIndex(
  { "component": 1, "level": 1 }, 
  { name: "idx_component_level" }
);

print("MongoDB: AI-BOS Initial Collections and Indexes created successfully.");
