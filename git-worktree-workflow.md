# Git Worktree and Branches Workflow Documentation

This document describes the git worktree and branch management workflow for the prompt compression system project.

## Project Overview

This project demonstrates a comprehensive git worktree workflow with multiple feature branches working in parallel. The main system consists of a prompt compression application with database persistence functionality.

## Repository Structure

### Main Directory: `/home/kenneth/Projects/git-worktree-demo`
- **Branch**: `master`
- **Commit**: `cd12c70`
- **Purpose**: Main development branch containing the integrated system

### Worktree Structure

```
git-worktree-demo/                          # Main repo (master)
├── prompt-compressor-worktree/             # Worktree for prompt-compressor-branch
├── save-compressed-prompt-worktree/        # Worktree for save-compressed-prompt-branch
└── scripts-worktree/                       # Worktree for scripts-branch
```

## Branch Overview

| Branch | Worktree Directory | Purpose | Current Commit |
|--------|-------------------|---------|----------------|
| `master` | `.` (main) | Integrated system with all features | `cd12c70` |
| `prompt-compressor-branch` | `prompt-compressor-worktree/` | Core prompt compression functionality | `9f299f9` |
| `save-compressed-prompt-branch` | `save-compressed-prompt-worktree/` | Database persistence and save functionality | `ab1d57f` |
| `scripts-branch` | `scripts-worktree/` | Automation scripts and deployment tools | `1d8e2b1` |
| `prompt-compressor-branchv2` | N/A | Alternative implementation (not active) | - |
| `scripts` | N/A | Legacy scripts branch (not active) | - |

## Key Components by Branch

### Master Branch
**Location**: Main directory
**Key Files**:
- `app.py` - Main Flask application
- `save_app.py` - Database persistence service
- `templates/result.html` - UI template with Save to DB functionality
- `deploy.sh` - Automated deployment script
- `undeploy.sh` - Stop services script
- `query_prompts.sh` - Database query utility

### Prompt Compressor Branch
**Location**: `prompt-compressor-worktree/`
**Purpose**: Core compression engine and web interface
**Key Files**:
- `app.py` - Prompt compression Flask application
- `templates/` - Web interface templates
- `static/` - CSS and JavaScript assets

### Save Compressed Prompt Branch
**Location**: `save-compressed-prompt-worktree/`
**Purpose**: Database persistence functionality
**Key Files**:
- `app.py` - Database service application
- SQLite database schema and operations
- CORS configuration for cross-origin requests

### Scripts Branch
**Location**: `scripts-worktree/`
**Purpose**: Deployment automation and utility scripts
**Key Files**:
- `start.sh` - Start prompt compressor service
- `stop.sh` - Stop prompt compressor service
- `start_save_app.sh` - Start database service
- `stop_save_app.sh` - Stop database service
- `modify-core.sh` - Dynamic template modification

## Workflow Commands

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/kenken64/git-worktree-demo.git
cd git-worktree-demo

# Create worktrees for each feature branch
git worktree add prompt-compressor-worktree prompt-compressor-branch
git worktree add save-compressed-prompt-worktree save-compressed-prompt-branch
git worktree add scripts-worktree scripts-branch
```

### Development Workflow

#### Working on Individual Features
```bash
# Work on prompt compression features
cd prompt-compressor-worktree
# Make changes, commit, push

# Work on database features
cd save-compressed-prompt-worktree
# Make changes, commit, push

# Work on automation scripts
cd scripts-worktree
# Make changes, commit, push
```

#### Integration to Master
```bash
# Return to main directory
cd /home/kenneth/Projects/git-worktree-demo

# Merge feature branches into master
git merge prompt-compressor-branch
git merge save-compressed-prompt-branch
git merge scripts-branch

# Push integrated changes
git push origin master
```

### Deployment Operations

#### Automated Deployment
```bash
# Deploy entire system
./deploy.sh
# This runs: modify-core.sh → start.sh → start_save_app.sh → git commit & push

# Stop all services
./undeploy.sh
# This runs: stop.sh → stop_save_app.sh
```

#### Manual Operations
```bash
# Start individual services
./start.sh                    # Prompt compressor (port 5000)
./start_save_app.sh          # Database service (port 5001)

# Stop individual services
./stop.sh                    # Stop prompt compressor
./stop_save_app.sh          # Stop database service

# Modify templates dynamically
./modify-core.sh            # Add Save to DB functionality

# Query database
./query_prompts.sh          # Show summary statistics
./query_prompts.sh all      # List all saved prompts
./query_prompts.sh recent   # Show recent prompts
```

## Service Architecture

### Port Allocation
- **Port 5000**: Prompt compressor web interface (`app.py`)
- **Port 5001**: Database persistence service (`save_app.py`)

### Process Management
Services run as background processes with PID tracking:
- PID files stored for process management
- Logs stored in `logs/` directory
- Automatic cleanup of stale PID files

### Database
- **Engine**: SQLite (`prompts.db`)
- **Table**: `compressed_prompts`
- **Features**: Compression ratio tracking, deduplication via hash

## Integration Features

### Cross-Service Communication
- CORS enabled for cross-origin requests between services
- REST API for saving compressed prompts
- Real-time compression statistics

### Dynamic Template Modification
The `modify-core.sh` script dynamically injects database functionality:
- Adds "Save to DB" button to compression results
- Includes JavaScript for AJAX communication
- Maintains template compatibility across branches

## Branch Synchronization

### Syncing Changes Between Branches
```bash
# Sync changes from master to feature branch
cd save-compressed-prompt-worktree
git merge master

# Or sync specific changes
git cherry-pick <commit-hash>
```

### Cross-Branch Features
Some features span multiple branches:
- CORS configuration (save-compressed-prompt-branch → master)
- Template modifications (scripts-branch → master)
- UI enhancements (prompt-compressor-branch → master)

## Best Practices

### Development
1. **Feature Isolation**: Keep feature development in respective worktrees
2. **Regular Integration**: Merge to master frequently to avoid conflicts
3. **Testing**: Test integrated system in master before deployment
4. **Documentation**: Update this workflow documentation when adding new branches

### Deployment
1. **Automated Scripts**: Use `deploy.sh` for consistent deployments
2. **Service Management**: Always use provided start/stop scripts
3. **Monitoring**: Check logs in `logs/` directory for debugging
4. **Database Backup**: Query and backup database regularly

### Git Management
1. **Worktree Cleanup**: Remove unused worktrees with `git worktree remove`
2. **Branch Cleanup**: Delete merged feature branches when no longer needed
3. **Remote Sync**: Keep remotes updated with `git fetch --all`
4. **Conflict Resolution**: Resolve conflicts in feature branches before merging

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Check if services are already running on ports 5000/5001
2. **CORS Errors**: Ensure save_app.py has correct CORS headers
3. **Template Issues**: Run `modify-core.sh` if Save to DB button is missing
4. **Database Errors**: Check if `prompts.db` exists and has correct permissions

### Debug Commands
```bash
# Check running processes
ps aux | grep python

# Check port usage
netstat -tlnp | grep :500

# View logs
tail -f logs/prompt-compressor.out
tail -f logs/save-app.out

# Check worktree status
git worktree list
git status --porcelain
```

## Future Enhancements

### Potential Improvements
1. **CI/CD Pipeline**: Automated testing and deployment
2. **Docker Integration**: Containerized services
3. **Production Config**: Production-ready WSGI server setup
4. **Monitoring**: Health checks and metrics collection
5. **Security**: Authentication and input validation

### Branch Strategy Evolution
- Consider adopting GitFlow for more complex feature development
- Implement automated testing before merging to master
- Add staging environment for pre-production testing

---

**Last Updated**: September 17, 2025
**Repository**: https://github.com/kenken64/git-worktree-demo
**Maintainer**: Project Team