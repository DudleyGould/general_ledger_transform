def log_issues(issues, log_file):
    """Logs validation or transformation issues to a file."""
    with open(log_file, 'a') as f:
        for issue in issues:
            f.write(issue + '\n')
