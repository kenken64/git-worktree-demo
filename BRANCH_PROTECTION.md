# Branch Protection Strategy

This repository uses a specialized branching strategy with merge protection between different functional branches.

## Protected Branches

The following branches are designed to be independent and should not be automatically merged:

- **master**: Main development branch
- **save-compressed-prompt-branch**: Save compressed prompt functionality
- **prompt-compressor-branch**: Prompt compression functionality
- **scripts-branch**: Utility scripts

## Merge Protection

### .gitattributes Configuration
The `.gitattributes` file configures custom merge drivers for key file types to prevent automatic merging:
- Python files (*.py)
- Shell scripts (*.sh)
- Documentation (*.md)
- Text files (*.txt)
- Database files (*.db)
- Process ID files (*.pid)

### Custom Merge Driver
A custom merge driver `no-auto-merge` is configured to fail automatic merges and require manual conflict resolution.

### Pre-merge Hook
A `pre-merge-commit` hook prevents automatic merging between protected branches and provides clear error messages.

## Working with Protected Branches

### If You Need to Merge
1. Understand that these branches serve different purposes
2. Manually resolve conflicts if absolutely necessary
3. Use `git merge --no-verify <branch>` to bypass the pre-merge hook
4. Carefully review all changes before committing

### Recommended Workflow
- Keep branches separate and independent
- Use worktrees for parallel development
- Cherry-pick specific commits if needed instead of full merges
- Maintain clear separation of concerns between branches

## Git Configuration
The merge protection is configured with:
```bash
git config merge.no-auto-merge.driver 'echo "ERROR: Automatic merge prevented..." && exit 1'
git config merge.no-auto-merge.name "No automatic merge driver"
```