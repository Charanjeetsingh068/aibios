import mongoose from 'mongoose';
import dotenv from 'dotenv';
import Company from '../models/Company.js';
import Workspace from '../models/Workspace.js';
import Permission from '../models/Permission.js';
import Role from '../models/Role.js';
import User from '../models/User.js';
import Session from '../models/Session.js';

dotenv.config();

const mongoUri = process.env.MONGODB_URL || 'mongodb://localhost:27017/aibios_nosql';

const permissionsSeed = [
  { name: 'admin:all', description: 'Full global system administration control' },
  { name: 'org:read', description: 'Read organization configurations' },
  { name: 'org:write', description: 'Write or modify organization configurations' },
  { name: 'leads:read', description: 'Access and read client leads listings' },
  { name: 'leads:write', description: 'Create, update and delete client leads' },
  { name: 'agents:read', description: 'Read cognitive agents statuses and flows' },
  { name: 'agents:write', description: 'Deploy and modify cognitive agents behaviors' }
];

async function seed() {
  try {
    console.log(`[Seed] Connecting to MongoDB at ${mongoUri}...`);
    await mongoose.connect(mongoUri);
    console.log(`[Seed] Connection established. Starting purge...`);

    // Clear existing collections to ensure consistency
    await User.deleteMany({});
    await Session.deleteMany({});
    await Workspace.deleteMany({});
    await Company.deleteMany({});
    await Role.deleteMany({});
    await Permission.deleteMany({});
    
    // Import custom Session model in scope to purge
    const SessionModel = mongoose.model('Session');
    await SessionModel.deleteMany({});

    console.log(`[Seed] Purge completed. Seeding Permissions...`);
    const permissionsMap = {};
    for (const perm of permissionsSeed) {
      const created = await Permission.create(perm);
      permissionsMap[created.name] = created._id;
    }
    console.log(`[Seed] Seeded ${Object.keys(permissionsMap).length} Permissions.`);

    console.log(`[Seed] Seeding Roles...`);
    
    const superAdminRole = await Role.create({
      name: 'super_admin',
      description: 'Super System Administrator with global system clearance',
      permissions: [permissionsMap['admin:all']]
    });

    const orgAdminRole = await Role.create({
      name: 'org_admin',
      description: 'Tenant Administrator with full company control',
      permissions: [
        permissionsMap['org:read'],
        permissionsMap['org:write'],
        permissionsMap['leads:read'],
        permissionsMap['leads:write'],
        permissionsMap['agents:read'],
        permissionsMap['agents:write']
      ]
    });

    const managerRole = await Role.create({
      name: 'manager',
      description: 'CRM Manager with lead and reading clearance',
      permissions: [
        permissionsMap['leads:read'],
        permissionsMap['leads:write'],
        permissionsMap['agents:read']
      ]
    });

    const salesExecRole = await Role.create({
      name: 'sales_executive',
      description: 'Sales Agent handling lead pipelines',
      permissions: [
        permissionsMap['leads:read'],
        permissionsMap['leads:write']
      ]
    });

    const viewerRole = await Role.create({
      name: 'viewer',
      description: 'Read-only viewer',
      permissions: [permissionsMap['leads:read']]
    });

    console.log(`[Seed] Roles seeded successfully.`);

    console.log(`[Seed] Seeding Companies...`);
    const company = await Company.create({
      name: 'Demo Corp',
      slug: 'demo',
      status: 'active'
    });
    console.log(`[Seed] Seeded Company: ${company.name} (${company.slug})`);

    console.log(`[Seed] Seeding Workspaces...`);
    const defaultWorkspace = await Workspace.create({
      name: 'Default Workspace',
      slug: 'default',
      company_id: company._id,
      status: 'active'
    });

    const salesWorkspace = await Workspace.create({
      name: 'Sales Workspace',
      slug: 'sales',
      company_id: company._id,
      status: 'active'
    });
    console.log(`[Seed] Seeded 2 Workspaces: ${defaultWorkspace.name}, ${salesWorkspace.name}`);

    console.log(`[Seed] Seeding Users...`);
    
    // Super Admin user
    const superAdmin = await User.create({
      first_name: 'System',
      last_name: 'Admin',
      email: 'admin@aibios.com',
      password: 'admin123', // Will be hashed in model pre-save hook
      company_id: company._id,
      role_id: superAdminRole._id,
      workspaces: [defaultWorkspace._id, salesWorkspace._id],
      status: 'active',
      timezone: 'Asia/Kolkata',
      language: 'en'
    });

    // Org Admin user
    const orgAdmin = await User.create({
      first_name: 'Organization',
      last_name: 'Admin',
      email: 'orgadmin@aibios.com',
      password: 'admin123',
      company_id: company._id,
      role_id: orgAdminRole._id,
      workspaces: [defaultWorkspace._id, salesWorkspace._id],
      status: 'active',
      timezone: 'UTC',
      language: 'en'
    });

    // Manager user
    const manager = await User.create({
      first_name: 'Jane',
      last_name: 'Manager',
      email: 'manager@aibios.com',
      password: 'admin123',
      company_id: company._id,
      role_id: managerRole._id,
      workspaces: [defaultWorkspace._id],
      status: 'active',
      timezone: 'UTC',
      language: 'en'
    });

    // Sales Executive user
    const salesExec = await User.create({
      first_name: 'John',
      last_name: 'Sales',
      email: 'sales@aibios.com',
      password: 'admin123',
      company_id: company._id,
      role_id: salesExecRole._id,
      workspaces: [salesWorkspace._id],
      status: 'active',
      timezone: 'UTC',
      language: 'en'
    });

    console.log(`[Seed] Users seeded successfully.`);
    console.log(`==========================================================`);
    console.log(`[Seed] DB SEED COMPLETED SUCCESSFULLY.`);
    console.log(`Default Super Admin Email: admin@aibios.com / Pass: admin123`);
    console.log(`Default Org Admin Email: orgadmin@aibios.com / Pass: admin123`);
    console.log(`==========================================================`);

    await mongoose.disconnect();
    process.exit(0);
  } catch (error) {
    console.error('[Seed] Database Seeding Error:', error);
    process.exit(1);
  }
}

seed();
