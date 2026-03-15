Plan and implement a new feature for Tabot. Usage: /new-feature <description>

Steps:
1. Read the issue description (if issue number provided, fetch from GitHub)
2. Identify which files need to change (backend, frontend, or both)
3. Create a branch: `feat/issue-N-short-description`
4. Implement the feature following CLAUDE.md conventions
5. Write tests for the new feature
6. Run /lint and /test to verify
7. Commit with descriptive message in Spanish
8. Report what was done and what needs review
