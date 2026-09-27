def test_ci_verification_deliberate_failure():
    # Temporary -- proves the CI workflow actually catches a real failure.
    # Safe to delete once the Actions tab shows a red X for this commit.
    assert False, "Deliberate failure to verify CI catches broken tests"
